# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build commands

```bash
make all        # full build: Markdown → Pandoc → Typst → PDF
make clean      # remove build/ and the output PDF
make check      # verify pandoc, typst, and pyyaml are installed
make watch      # rebuild on file changes (needs fswatch on macOS)
make deps       # pip install -r requirements.txt
```

The build is driven by `scripts/build.py`, invoked as `python3 scripts/build.py [project.yaml]`.

## Pipeline architecture

```
project.yaml  ──►  scripts/build.py
                        │
                        ├─ scripts/preprocess.py  (image path rewriting)
                        │         │
                        │    content/*.md  (combined into build/combined.md)
                        │
                        ├─ pandoc  --template templates/pandoc-template.typ
                        │         → build/document.typ
                        │
                        └─ typst compile
                                  → publication.pdf
```

**`project.yaml`** is the single source of truth for metadata (title, Hebrew title, subtitle, author, date, fonts, margins, paper size) and content ordering. The cover page, running header and PDF document properties (title/author) are all generated from it. `build.py` reads it, injects all values as YAML front matter into the combined markdown, and pandoc substitutes them into the template via `$variable$` tokens.

**`templates/pandoc-template.typ`** is a pandoc template (dollar-sign variable syntax), not a plain Typst file. Pandoc renders it into a complete `.typ` file. It imports `@preview/auto-bidi:0.1.0` for automatic per-paragraph RTL/LTR detection — no manual direction wrappers are needed in content.

**`scripts/preprocess.py`** currently only rewrites image paths (`../images/` → `images/`). It runs per content file before pandoc.

## Pandoc filter: semantic layout classes

`scripts/typst_filter.py` is a pandoc JSON filter that runs between markdown
parsing and Typst output.  Markdown inside the divs/spans is still fully
processed by pandoc; only the wrapper changes.

**Block divs** — use a fenced div with the class:

The `cover-page` div is filled entirely from the `publication:` block of
`project.yaml` (`title_he`, `title`, `subtitle`, `author`, `date`); do not put
title text in `content/00-cover.md`. For RTL publications the Hebrew title is
shown first. Any paragraphs inside the div are rendered centred below the date.

```markdown
::: cover-page
:::

::: typst-centered
Any markdown here is centred.
:::

::: typst-page-unnumbered
Content on a page with no page number.
:::

::: prayer
16pt bold text (for Hebrew prayer passages).
:::

::: prayer-shabbat
Same as prayer, coloured red.
:::

::: prayer-chaggim
Same as prayer, coloured green.
:::

::: prayer-high-holidays
Same as prayer, coloured yellow.
:::
```

**Inline spans** — add a class to bracketed text:

```markdown
[some text]{.typst-sc}   ← small caps
```

**Extending the filter** — open `scripts/typst_filter.py` and add to:
- `DIV_WRAPPERS` for a simple before/after Typst wrapper around block content
- `DIV_HANDLERS` for a Python function with full control (like `cover-page`)
- `SPAN_STYLES` for an inline Typst template

**Native Typst pass-through** — for one-off Typst with no reusable class:
````markdown
```{=typst}
#pagebreak()
```
````

## Content authoring

- Markdown files live in `content/`, listed in order under the `content:` key in `project.yaml`.
- Write Hebrew and English naturally in the same file; `auto-bidi` detects direction per paragraph from the first strong character.
- Images go in `images/` and are referenced as `![alt](images/foo.png)` or `![alt](../images/foo.png)` — preprocess normalises paths.
- Fonts go in `fonts/`; names used in `project.yaml` must match the font's internal name exactly.

## Researching and sourcing content

When adding or checking halachic content, prayer texts or citations, use these
references rather than relying on memory. Hebrew liturgical text in particular
must be copied from a reliable source, never reconstructed.

- **[Sefaria](https://www.sefaria.org/)**: the main source for primary texts:
  Tanakh, Talmud, Mishnah Berurah, Shulchan Aruch, Kitzur Shulchan Aruch,
  siddurim and commentaries, in Hebrew with English translations. Use it to
  check citations (e.g. `Shulchan Aruch, Orach Chayim 135–149` for Torah reading
  laws) and to get exact Hebrew wording. Its public API returns text as JSON,
  e.g. `https://www.sefaria.org/api/v3/texts/Shulchan_Arukh,_Orach_Chayim.135`.
- **[Chabad.org Knowledge Base](https://www.chabad.org/search/default_cdo/aid/67250/jewish/Knowledge-Base.htm)**:
  plain-language explanations of practice and custom (aliyot, Kaddish, Mi
  Sheberach, haftarah, holiday readings). Good for explanatory prose and for
  checking common practice. Note that it reflects Chabad custom, so mention
  where other communities differ.
- **[OpenSiddur](https://opensiddur.org/)**: freely licensed siddur texts and
  translations. Its source repository
  ([github.com/opensiddur/opensiddur](https://github.com/opensiddur/opensiddur))
  holds the texts in machine-readable form. Use it for prayer passages when
  Sefaria's version isn't suitable, or to compare versions (nusach).

Guidelines:

- Cite the primary source (book, siman, se'if) in the content where it helps the
  gabbai. Don't cite a website as the authority.
- Check the licence before copying a translation. Many Sefaria and OpenSiddur
  texts are CC-BY or CC-BY-SA and need attribution. Chabad.org content is
  copyrighted, so paraphrase it rather than copying it.
- When sources disagree on nusach (Ashkenaz, Sefard, Edot HaMizrach), say which
  one the text follows.

## Key variables passed through the template

Boolean `rtl` (derived from `direction: rtl` in `project.yaml`) controls title-page order (Hebrew title first vs. English first) and binding side. All other typography and layout values (`hebrew-font`, `latin-font`, `body-size`, `paper`, margins, etc.) flow directly from `project.yaml` → front matter → pandoc template substitution.

## Dependencies

- `pandoc` — Markdown → Typst conversion
- `typst` — Typst → PDF compilation (fetches `auto-bidi` from the package registry on first run)
- `python3` + `pyyaml`

## Fonts in use

| Role       | Family           | Files in `fonts/`         |
|------------|------------------|---------------------------|
| Hebrew     | Shofar           | `ShofarRegular.ttf`, etc. |
| Body/Latin | Source Sans 3    | `source-sans-3/`          |
| Code       | Source Code Pro  | `source-code-pro/`        |
