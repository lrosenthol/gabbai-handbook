#!/usr/bin/env python3
"""Pandoc JSON filter: convert semantic div/span classes to Typst layout.

Run automatically by build.py via pandoc --filter.  Processes the pandoc AST
between markdown parsing and Typst serialisation, so markdown inside divs
(headings, bold, lists, tables, etc.) is still converted normally — only the
wrapper/layout changes.

Adding new layouts
──────────────────
• Simple block wrapper (e.g. centred section): add an entry to DIV_WRAPPERS.
  The dict maps a CSS class name → (typst_before, typst_after) strings that
  are inserted as raw Typst around the already-converted block content.

• Complex block layout (e.g. cover page): add a function to DIV_HANDLERS.
  The function receives (blocks, classes, kvs, meta) and must return a list
  of pandoc block elements (mix of RawBlock and normal AST blocks freely).

• Inline styling (e.g. a styled run of text): add an entry to SPAN_STYLES.
  The value is a Typst template string; use {text} as the placeholder for
  the span's plain-text content.

Native Typst pass-through
──────────────────────────
For one-off Typst that doesn't need a reusable class, use pandoc's own raw
block or inline syntax directly in the markdown:

    ```{=typst}
    #pagebreak()
    ```

    [some text]{=typst}   ← inline raw (rarely needed)
"""

import sys
from pandocfilters import toJSONFilter, RawBlock, RawInline, stringify, Para


# ── Prayer blocks ─────────────────────────────────────────────────────────────
# Sizes come from project.yaml via Typst variables defined in the template:
#   prayer-size         — the block's base size (English instructions, etc.)
#   prayer-hebrew-size  — Hebrew-script runs.  Shofar looks noticeably smaller
#                         than Source Sans 3 at the same point size, so the
#                         Hebrew (the actual prayer) is set larger to stay
#                         visually dominant over interleaved English.
# The heading sizes in the template are derived from both values, so H1–H3
# never look smaller than prayer text.
#
# Shofar's bold face (ShofarDemi-Bold.ttf) is registered as a *wider* stretch
# (112.5%) than the regular face.  Typst matches stretch before weight, so a
# plain weight: "bold" silently falls back to Shofar Regular.  Hebrew runs
# therefore also request PRAYER_HEBREW_STRETCH so the bold face is selected.

PRAYER_HEBREW_STRETCH = "112.5%"  # selects ShofarDemi-Bold for weight: bold


def _prayer_wrapper(fill: str = "") -> tuple[str, str]:
    fill_arg = f", fill: {fill}" if fill else ""
    return (
        "#block[\n"
        f'  #set text(size: prayer-size, weight: "bold"{fill_arg}, dir: rtl)\n'
        f'  #show regex("\\p{{Hebrew}}+"): set text('
        f'size: prayer-hebrew-size, stretch: {PRAYER_HEBREW_STRETCH})\n',
        "\n]\n",
    )


# ── Simple div wrappers ───────────────────────────────────────────────────────
# Each entry: css-class → (typst_before, typst_after)
# The inner content is converted to Typst by pandoc's writer as normal.

DIV_WRAPPERS: dict[str, tuple[str, str]] = {
    "pagebreak": ("#pagebreak()\n", ""),
    "typst-centered": (
        "#align(center)[\n",
        "\n]\n",
    ),
    "typst-right": (
        "#align(right)[\n",
        "\n]\n",
    ),
    "typst-left": (
        "#align(left)[\n",
        "\n]\n",
    ),
    "typst-page": (
        "#page()[\n",
        "\n]\n",
    ),
    "typst-page-unnumbered": (
        "#page(numbering: none)[\n",
        "\n]\n",
    ),
    "prayer": (
        '#block[\n  #set text(size: prayer-size, weight: "bold", dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-shabbat": (
        '#block[\n  #set text(size: prayer-size, weight: "bold", fill: red, dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-chaggim": (
        '#block[\n  #set text(size: prayer-size, weight: "bold", fill: green, dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-high-holidays": (
        '#block[\n  #set text(size: prayer-size, weight: "bold", fill: yellow, dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-shabbat-chaggim": (
        '#block[\n  #set text(size: prayer-size, weight: "bold", fill: purple, dir: rtl)\n',
        "\n]\n",
    ),
    # Community-specific note boxes
    "note-chabad": (
        '#block(stroke: (left: 2pt + blue), inset: (left: 8pt), width: 100%)[\n'
        '  #text(size: 9pt, fill: blue)[*Chabad / חב"ד*]\\\n',
        "\n]\n",
    ),
    "note-sephardic": (
        "#block(stroke: (left: 2pt + eastern), inset: (left: 8pt), width: 100%)[\n"
        "  #text(size: 9pt, fill: eastern)[*Sephardic / ספרדי*]\\\n",
        "\n]\n",
    ),
    "note-ashkenazic": (
        "#block(stroke: (left: 2pt + maroon), inset: (left: 8pt), width: 100%)[\n"
        "  #text(size: 9pt, fill: maroon)[*Ashkenazic / אשכנזי*]\\\n",
        "\n]\n",
    ),
}


# ── Admonitions ───────────────────────────────────────────────────────────────
# css-class → (label, Typst colour).  Rendered with the `admonition` function
# defined in templates/pandoc-template.typ.  A paragraph that begins with one
# of the labels followed by a colon (e.g. "NOTE: …") is converted the same way.

ADMONITIONS: dict[str, tuple[str, str]] = {
    "note":      ("NOTE",      "luma(90)"),
    "tip":       ("TIP",       "rgb(\"#2e7d32\")"),
    "important": ("IMPORTANT", "rgb(\"#1565c0\")"),
    "warning":   ("WARNING",   "rgb(\"#e65100\")"),
    "caution":   ("CAUTION",   "rgb(\"#c62828\")"),
}

for _cls, (_label, _color) in ADMONITIONS.items():
    DIV_WRAPPERS[_cls] = (
        f"#admonition([{_label}], color: {_color})[\n",
        "\n]\n",
    )

_ADMONITION_PREFIXES = {f"{label}:": cls for cls, (label, _) in ADMONITIONS.items()}


def _admonition_para(block):
    """If `block` is a Para starting with e.g. "NOTE:", return it as an
    admonition (list of blocks); otherwise return None."""
    if block.get("t") != "Para":
        return None
    inlines = block["c"]
    if not inlines or inlines[0].get("t") != "Str":
        return None
    cls = _ADMONITION_PREFIXES.get(inlines[0]["c"])
    if cls is None:
        return None
    rest = inlines[1:]
    while rest and rest[0].get("t") in ("Space", "SoftBreak"):
        rest = rest[1:]
    before, after = DIV_WRAPPERS[cls]
    return [RawBlock("typst", before), Para(rest), RawBlock("typst", after)]


# ── Span styles ───────────────────────────────────────────────────────────────
# Each entry: css-class → Typst template  ({text} = the span's plain text)

SPAN_STYLES: dict[str, str] = {
    "typst-sc":       '#smallcaps[{text}]',
    "typst-em":       '#emph[{text}]',
    "typst-strong":   '#strong[{text}]',
    "typst-mono":     '#raw("{text}")',
}


# ── Complex div handlers ──────────────────────────────────────────────────────
# Each function: (blocks, classes, kvs, meta) → list[pandoc block element]
# Use stringify(inlines) to pull plain text out of inline AST nodes.

def _meta_bool(meta, key, default=False):
    """Read a boolean value from the pandoc metadata dict."""
    v = meta.get(key)
    if v is None:
        return default
    t = v.get("t")
    if t == "MetaBool":
        return bool(v["c"])
    if t in ("MetaInlines", "MetaBlocks"):
        return stringify(v["c"]).strip().lower() in ("true", "yes", "1")
    return default


def _handle_toc(blocks, classes, kvs, meta):
    """Render a .toc div as an unnumbered Typst outline; the page after it is page 1."""
    rtl = _meta_bool(meta, "rtl")
    title = "תוכן העניינים / Contents" if rtl else "Contents / תוכן העניינים"
    # Each outline entry is rendered as a 3-column grid (body | dots | page)
    # so that the page number lives in its own cell and can never be pulled
    # into the RTL bidi run that ends bilingual headings like
    # "Introduction / מָבוֹא".
    typst = (
        "#page(numbering: none)[\n"
        "  #show outline.entry: it => {\n"
        "    set par(justify: false)\n"
        "    link(it.element.location())[\n"
        "      #grid(\n"
        "        columns: (auto, 1fr, auto),\n"
        "        h((it.level - 1) * 1em) + it.element.body,\n"
        "        box(width: 1fr, align(bottom, repeat[.])),\n"
        "        context counter(page).at(it.element.location()).first(),\n"
        "      )\n"
        "    ]\n"
        "  }\n"
        "  #outline(\n"
        f"    title: [{title}],\n"
        "    depth: 2,\n"
        "    indent: 1em,\n"
        "  )\n"
        # Reset at the end of the (last) TOC page so the following page is
        # numbered 1.  An update placed *after* the TOC would land on the
        # next page after its header was drawn, so that header would still
        # show the old number.
        "  #counter(page).update(0)\n"
        "]\n"
    )
    return [RawBlock("typst", typst)]


def _meta_text(meta, key):
    """Return a metadata value as plain text ('' if missing).

    Lists (e.g. several authors) are joined with ", ".
    """
    v = meta.get(key)
    if v is None:
        return ""
    if v.get("t") == "MetaList":
        return ", ".join(t for t in (stringify(item).strip() for item in v["c"]) if t)
    return stringify(v).strip()


def _typst_str(text):
    """Quote text as a Typst string literal (no markup interpretation)."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _handle_cover_page(blocks, classes, kvs, meta):
    """Render a .cover-page div as a centred Typst title page.

    All cover text comes from the document metadata, which build.py fills
    from the `publication:` block of project.yaml — that file is the single
    source of truth:

        title-he  ← publication.title_he
        title     ← publication.title
        subtitle  ← publication.subtitle
        author    ← publication.author
        date      ← publication.date

    For RTL publications the Hebrew title comes first; for LTR the English
    title does.  Empty fields are omitted.  Any paragraphs written inside the
    div are rendered as plain centred text below the date (for notes or
    epigraphs).
    """
    rtl = _meta_bool(meta, "rtl")

    # (text, typst size/weight args, spacing after)
    title_he = (_meta_text(meta, "title-he"), 'size: 2em, weight: "bold"')
    title_en = (_meta_text(meta, "title"),    'size: 1.5em, weight: "bold"')
    first, second = (title_he, title_en) if rtl else (title_en, title_he)
    items = [
        (*first,  "#v(0.4em)"),
        (*second, "#v(3em)"),
        (_meta_text(meta, "subtitle"), "size: 1.2em", "#v(1em)"),
        (_meta_text(meta, "author"),   "size: 1.1em", "#v(0.5em)"),
        (_meta_text(meta, "date"),     "size: 1em",   ""),
    ]

    lines = []
    for text, args, spacing in items:
        if not text:
            continue
        lines.append(f"#text({args}, {_typst_str(text)})")
        if spacing:
            lines.append(spacing)

    for block in blocks:
        if block["t"] == "Para":
            extra = stringify(block["c"]).strip()
            if extra:
                lines.append("#v(1em)")
                lines.append(f"#text({_typst_str(extra)})")

    inner = "\n    ".join(lines)
    typst = (
        "#page(numbering: none)[\n"
        "  #v(1fr)\n"
        "  #align(center)[\n"
        f"    {inner}\n"
        "  ]\n"
        "  #v(1fr)\n"
        "]\n"
    )
    return [RawBlock("typst", typst)]


DIV_HANDLERS = {
    "cover-page": _handle_cover_page,
    "toc":        _handle_toc,
}


# ── Tables ────────────────────────────────────────────────────────────────────
# For a pipe table with any row wider than 72 characters, pandoc derives
# relative column widths from the lengths of the `---` separator lines.  Those
# reflect how the markdown happens to be padded, not the content (e.g. a
# "Number of Scrolls" column squeezed to 9% of the width).  Drop them so the
# template's table rules let Typst size each column to its content.

def _auto_table_widths(value):
    attr, caption, colspecs, head, bodies, foot = value
    colspecs = [[align, {"t": "ColWidthDefault"}] for align, _ in colspecs]
    return {"t": "Table", "c": [attr, caption, colspecs, head, bodies, foot]}


# ── Recursive block processor ─────────────────────────────────────────────────
# pandocfilters.walk does NOT call action() on dicts returned as replacements —
# only on items encountered inside lists.  When an outer Div returns its inner
# blocks as part of its replacement list, those inner Div nodes are walked as
# plain dicts and are never matched by the filter.  We therefore pre-process
# blocks ourselves before inserting them into any replacement.

def _process_blocks(blocks, meta):
    result = []
    for block in blocks:
        if block.get('t') == 'Div':
            attrs, inner_blocks = block['c']
            ident, classes, kvs = attrs
            matched = False
            for cls in classes:
                if cls in DIV_HANDLERS:
                    result.extend(DIV_HANDLERS[cls](_process_blocks(inner_blocks, meta), classes, kvs, meta))
                    matched = True
                    break
            if not matched:
                for cls in classes:
                    if cls in DIV_WRAPPERS:
                        before, after = DIV_WRAPPERS[cls]
                        result.append(RawBlock("typst", before))
                        result.extend(_process_blocks(inner_blocks, meta))
                        result.append(RawBlock("typst", after))
                        matched = True
                        break
            if not matched:
                result.append(block)
        elif block.get('t') == 'Table':
            result.append(_auto_table_widths(block['c']))
        else:
            converted = _admonition_para(block)
            result.extend(converted if converted is not None else [block])
    return result


# ── Filter entry point ────────────────────────────────────────────────────────

def _transform(key, value, fmt, meta):
    if fmt != "typst":
        return None

    if key == "Div":
        attrs, blocks = value
        ident, classes, kvs = attrs

        # Complex handler takes precedence
        for cls in classes:
            if cls in DIV_HANDLERS:
                return DIV_HANDLERS[cls](_process_blocks(blocks, meta), classes, kvs, meta)

        # Simple wrapper: first matching class wins
        for cls in classes:
            if cls in DIV_WRAPPERS:
                before, after = DIV_WRAPPERS[cls]
                return [RawBlock("typst", before)] + _process_blocks(blocks, meta) + [RawBlock("typst", after)]

    if key == "Table":
        return _auto_table_widths(value)

    if key == "Para":
        return _admonition_para({"t": key, "c": value})

    if key == "Span":
        attrs, inlines = value
        _, classes, _ = attrs
        for cls in classes:
            if cls in SPAN_STYLES:
                text = stringify(inlines)
                return RawInline("typst", SPAN_STYLES[cls].format(text=text))

    return None


if __name__ == "__main__":
    toJSONFilter(_transform)
