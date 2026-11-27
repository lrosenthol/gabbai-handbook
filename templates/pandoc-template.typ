// pandoc-template.typ
// Pandoc template (uses dollar-sign-variable syntax) for Hebrew+English publications.
// Pandoc fills in all tokens; the output is plain Typst fed to `typst compile`.
//
// Variables set by build.py via YAML front matter:
//   title, title-he, subtitle, author, date
//   rtl (bool), hebrew-font, latin-font, code-font
//   body-size, heading-scale, paper
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
  header: context {
    if counter(page).get().first() > 1 [
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

#set par(
  justify:           true,
  leading:           0.75em,
  first-line-indent: 1.2em,
)

// ── Headings ──────────────────────────────────────────────────────────────────

#show heading.where(level: 1): it => block(above: 2em, below: 0.9em)[
  #set text(size: $heading-scale$em, weight: "bold")
  #it.body
]
#show heading.where(level: 2): it => block(above: 1.6em, below: 0.7em)[
  #set text(size: calc.sqrt($heading-scale$) * 1em, weight: "bold")
  #it.body
]
#show heading.where(level: 3): it => block(above: 1.2em, below: 0.5em)[
  #set text(size: 1.05em, weight: "bold")
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
