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

**`project.yaml`** is the single source of truth for metadata (title, fonts, margins, paper size) and content ordering. `build.py` reads it, injects all values as YAML front matter into the combined markdown, and pandoc substitutes them into the template via `$variable$` tokens.

**`templates/pandoc-template.typ`** is a pandoc template (dollar-sign variable syntax), not a plain Typst file. Pandoc renders it into a complete `.typ` file. It imports `@preview/auto-bidi:0.1.0` for automatic per-paragraph RTL/LTR detection — no manual direction wrappers are needed in content.

**`scripts/preprocess.py`** currently only rewrites image paths (`../images/` → `images/`). It runs per content file before pandoc.

## Pandoc filter: semantic layout classes

`scripts/typst_filter.py` is a pandoc JSON filter that runs between markdown
parsing and Typst output.  Markdown inside the divs/spans is still fully
processed by pandoc; only the wrapper changes.

**Block divs** — use a fenced div with the class:

```markdown
::: cover-page
[מדריך הגבאי]{.cover-title-he}
[Gabbai Handbook]{.cover-title}
[Subtitle]{.cover-subtitle}
[Author]{.cover-author}
[Date]{.cover-date}
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
