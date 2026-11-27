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
