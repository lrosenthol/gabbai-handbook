// pandoc-template.typ
// Pandoc template (uses dollar-sign-variable syntax) for Hebrew+English publications.
// Pandoc fills in all tokens; the output is plain Typst fed to `typst compile`.
//
// Variables set by build.py via YAML front matter:
//   title, title-he, subtitle, author, date
//   rtl (bool), hebrew-font, latin-font, code-font
//   body-size, heading-scale, paper
//   top-margin, bottom-margin, right-margin, left-margin, two-sided

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

#set table(stroke: 0.5pt, inset: 6pt)
#show table.header: set text(weight: "bold")

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

// ── Body ──────────────────────────────────────────────────────────────────────

$body$
