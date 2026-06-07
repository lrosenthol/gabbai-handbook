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
        '#block[\n  #set text(size: 16pt, weight: "bold", dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-shabbat": (
        '#block[\n  #set text(size: 16pt, weight: "bold", fill: red, dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-chaggim": (
        '#block[\n  #set text(size: 16pt, weight: "bold", fill: green, dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-high-holidays": (
        '#block[\n  #set text(size: 16pt, weight: "bold", fill: yellow, dir: rtl)\n',
        "\n]\n",
    ),
    "prayer-shabbat-chaggim": (
        '#block[\n  #set text(size: 16pt, weight: "bold", fill: purple, dir: rtl)\n',
        "\n]\n",
    ),
}


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
    """Render a .toc div as a Typst outline page, then reset the page counter."""
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
        "]\n"
        "#counter(page).update(1)\n"
    )
    return [RawBlock("typst", typst)]


def _handle_cover_page(blocks, classes, kvs, meta):
    """Render a .cover-page div as a centred Typst title page.

    Expected paragraph content (each as its own paragraph using span classes):

        [Hebrew title]{.cover-title-he}
        [English title]{.cover-title}
        [Subtitle]{.cover-subtitle}
        [Author]{.cover-author}
        [Date]{.cover-date}

    Any paragraph not carrying one of these span classes is rendered as plain
    centred text so arbitrary notes or epigraphs still work.
    """
    SPAN_MAP = {
        "cover-title-he": '#text(size: 2em,  weight: "bold")[{text}]',
        "cover-title":    '#text(size: 1.5em, weight: "bold")[{text}]',
        "cover-subtitle": '#text(size: 1.2em)[{text}]',
        "cover-author":   '#text(size: 1.1em)[{text}]',
        "cover-date":     '#text(size: 1em)[{text}]',
    }
    SPAN_SPACING = {
        "cover-title-he": "#v(0.4em)",
        "cover-title":    "#v(3em)",
        "cover-subtitle": "#v(1em)",
        "cover-author":   "#v(0.5em)",
        "cover-date":     "",
    }

    lines = []
    for block in blocks:
        if block["t"] != "Para":
            continue
        inlines = block["c"]
        # Single span with a known class → styled text
        if len(inlines) == 1 and inlines[0]["t"] == "Span":
            span_attrs, span_inlines = inlines[0]["c"]
            _, span_classes, _ = span_attrs
            text = stringify(span_inlines)
            for cls in span_classes:
                if cls in SPAN_MAP:
                    lines.append(SPAN_MAP[cls].format(text=text))
                    if SPAN_SPACING[cls]:
                        lines.append(SPAN_SPACING[cls])
                    break
            else:
                # Span with unknown class: fall through to plain text
                lines.append(stringify(inlines))
        else:
            lines.append(stringify(inlines))

    inner = "\n".join(lines)
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
        else:
            result.append(block)
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
