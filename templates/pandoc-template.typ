// pandoc-template.typ
// Pandoc template (uses dollar-sign-variable syntax) for Hebrew+English publications.
// Pandoc fills in all tokens; the output is plain Typst fed to `typst compile`.
//
// Variables set by build.py via YAML front matter:
//   title, title-he, subtitle, author, date
//   rtl (bool), hebrew-font, latin-font, code-font
//   body-size, prayer-size, prayer-hebrew-size, heading-scale, paper
//   top-margin, bottom-margin, right-margin, left-margin, two-sided

// ── PDF document properties ──────────────────────────────────────────────────
// Title and author come from project.yaml (publication.title / .author), the
// same values used for the cover page and running header.  Typst requires the
// author as plain strings, so flatten the rendered content.

#let _plain-text(it) = {
  if type(it) == str { it }
  else if it.has("text") { it.text }
  else if it.has("children") { it.children.map(_plain-text).join() }
  else if it.has("body") { _plain-text(it.body) }
  else if it == [ ] { " " }
  else { "" }
}

#set document(
$if(title)$
  title: [$title$],
$endif$
$if(author)$
  author: ($for(author)$_plain-text([$author$]), $endfor$),
$endif$
)

// ── Bidirectional text (auto-bidi) ────────────────────────────────────────────
// auto-bidi detects RTL/LTR per paragraph automatically; no manual direction
// wrappers are needed in the source text.

#import "@preview/auto-bidi:0.1.0": *
#show: auto-dir.with(
  hebrew-font: ("$hebrew-font$",),
  english-font: ("$latin-font$",),
  base-font:    "$latin-font$",
)

// ── Page layout ──────────────────────────────────────────────────────────────

#set page(
  paper: "$paper$",
  margin: (
    top:    $top-margin$,
    bottom: $bottom-margin$,
    right:  $right-margin$,
    left:   $left-margin$,
  ),
$if(two-sided)$
  binding: $if(rtl)$right$else$left$endif$,
$endif$
  // Page numbers run consecutively through the whole book: the counter is
  // reset once, after the table of contents, and never per chapter.  Pages
  // set with `numbering: none` (cover, TOC, `typst-page-unnumbered`) get no
  // running header.  The footer is disabled so the number appears only here.
  numbering: "1",
  header: context {
    if here().page-numbering() != none [
      #set text(size: 0.85em)
      #if calc.odd(counter(page).get().first()) [
        #grid(columns: (1fr, 1fr),
          align(left)[#counter(page).display()],
          align(right)[$title$],
        )
      ] else [
        #grid(columns: (1fr, 1fr),
          align(left)[$title$],
          align(right)[#counter(page).display()],
        )
      ]
      #line(length: 100%, stroke: 0.4pt)
    ]
  },
  footer: none,
)

// ── Typography ────────────────────────────────────────────────────────────────

// Font assignment is owned entirely by auto-dir above (with covers-based
// per-script stacks). We only set size and other non-font attributes here.
#set text(size: $body-size$)

#show raw: set text(font: "$code-font$", size: 0.9em)

// ── Paragraph style ───────────────────────────────────────────────────────────

// Paragraphs are separated by vertical space only — no first-line indent.
#set par(
  justify:           true,
  leading:           0.75em,
  first-line-indent: 0em,
)

// ── Headings ──────────────────────────────────────────────────────────────────

// Rule: H1–H3 must never LOOK smaller than any running text.  The largest
// running text is prayer text (Hebrew at prayer-hebrew-size, Latin at
// prayer-size).  Point size alone is not enough because the scripts differ: Shofar's Hebrew letters stand taller per
// em than Source Sans lowercase.  So we measure, at render time, the ink
// height of a Hebrew letter and of a Latin x-height in the configured fonts,
// and size H3 so that its smallest-looking glyphs are at least as tall as the
// biggest-looking glyphs in prayer text.  H2 and H1 then step up
// geometrically, H1 = heading-scale x H3.
//
// H4 and deeper may be smaller than prayer text; they use body size and are
// distinguished by weight/style only.
//
// Shofar registers its bold face with an expanded stretch (112.5%), and
// Typst matches stretch before weight, so "bold" alone silently selects the
// regular face.  Headings request that stretch so Hebrew renders in bold too;
// Latin fonts without an expanded face fall back to their normal width.

#let prayer-size = $prayer-size$
#let prayer-hebrew-size = $prayer-hebrew-size$
#let heading-text = (weight: "bold", stretch: 112.5%)

// Ink height (baseline to top of glyph) at 100pt.  Requires context.
#let _ink(font, glyph) = measure(text(
  font: font, size: 100pt, top-edge: "bounds", bottom-edge: "baseline",
  ..heading-text, glyph,
)).height

#let heading-size(level) = {
  if level >= 4 { return $body-size$ }
  let hebrew = _ink("$hebrew-font$", "ה")
  let latin  = _ink("$latin-font$", "x")
  // Make the smallest heading glyph match the largest prayer glyph.  The
  // ink heights are at 100pt, so scale each by its prayer size / 100pt.
  let prayer-ink = calc.max(hebrew * (prayer-hebrew-size / 100pt),
                            latin  * (prayer-size / 100pt))
  let h3 = 100pt * (prayer-ink / calc.min(hebrew, latin))
  h3 * calc.pow($heading-scale$, (3 - level) / 2)
}

#show heading.where(level: 1): it => context block(above: 2em, below: 0.9em)[
  #set text(size: heading-size(1), ..heading-text)
  #it.body
]
#show heading.where(level: 2): it => context block(above: 1.6em, below: 0.7em)[
  #set text(size: heading-size(2), ..heading-text)
  #it.body
]
#show heading.where(level: 3): it => context block(above: 1.2em, below: 0.5em)[
  #set text(size: heading-size(3), ..heading-text)
  #it.body
]
#show heading.where(level: 4): it => block(above: 1em, below: 0.4em)[
  #set text(size: heading-size(4), ..heading-text)
  #it.body
]
#show heading.where(level: 5): it => block(above: 1em, below: 0.4em)[
  #set text(size: heading-size(5), weight: "semibold", style: "italic")
  #it.body
]
#show heading.where(level: 6): it => block(above: 1em, below: 0.4em)[
  #set text(size: heading-size(6), weight: "semibold", style: "italic")
  #it.body
]

// ── Lists ─────────────────────────────────────────────────────────────────────

#set list(indent: 1.2em, body-indent: 0.5em)
#set enum(indent: 1.2em, body-indent: 0.5em)

// ── Tables ────────────────────────────────────────────────────────────────────

// Header row: bold text on a light grey band.  Body rows: a hairline under
// each row; no vertical rules.  Column widths are left to Typst (the filter
// strips pandoc's markdown-derived widths).

#let table-header-fill = luma(225)
#let table-rule        = 0.5pt + luma(195)

#set table(
  inset:  (x: 7pt, y: 5pt),
  fill:   (x, y) => if y == 0 { table-header-fill },
  stroke: (x, y) => if y > 0 { (bottom: table-rule) },
)
// pandoc emits a table.hline() under the header; the grey band already marks it
#set table.hline(stroke: none)
#show table.cell.where(y: 0): set text(weight: "bold")
// pandoc wraps tables in align(center); keep that for the table's placement
// but start-align cell text (columns marked :---: in markdown stay centred).
// Justification opens wide gaps in narrow cells, so turn it off.
#show table: set align(start)
#show table: set par(justify: false)

// ── Horizontal rule ──────────────────────────────────────────────────────────

#let horizontalrule = block(above: 1em, below: 1em)[
  #line(length: 100%, stroke: 0.4pt)
]

// ── Block quotes ─────────────────────────────────────────────────────────────

#show quote: it => block(
  inset: (left: 2em, right: 2em),
  above: 0.8em,
  below: 0.8em,
)[#it]

// ── Admonitions (NOTE, TIP, …) ───────────────────────────────────────────────
// Emitted by scripts/typst_filter.py for `::: note` (and tip / important /
// warning / caution) divs, and for paragraphs that begin with "NOTE:".
// Styled after ISO notes / AsciiDoc admonitions: a bold label above slightly
// smaller body text in a lightly tinted, fully bordered box (a full border
// rather than a side bar, so it reads the same in RTL and LTR paragraphs).

#let admonition(label, color: luma(90), body) = block(
  width:  100%,
  inset:  (x: 10pt, y: 8pt),
  radius: 3pt,
  stroke: 0.6pt + color,
  fill:   color.lighten(92%),
  above:  1em,
  below:  1em,
  breakable: true,
)[
  #text(size: 0.8em, weight: "bold", fill: color, tracking: 0.08em)[#label]
  #v(0.3em, weak: true)
  #set text(size: 0.92em)
  #body
]

// ── Cross-references ─────────────────────────────────────────────────────────
// Internal markdown links ([text](#heading-id)) become links to Typst labels.
// Append the target's page number so the reference also works in print.

#show link: it => {
  if type(it.dest) == label {
    it
    context [ (p.~#counter(page).at(it.dest).first())]
  } else {
    it
  }
}

// ── Body ──────────────────────────────────────────────────────────────────────

$body$
