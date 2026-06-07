# Gabbai Handbook / מדריך הגבאי

A bilingual Hebrew–English handbook for synagogue officers (gabbaim), built with a Markdown → Pandoc → Typst → PDF pipeline.

## Features

- Write content in Hebrew and English naturally in the same Markdown files
- Automatic bidirectional text handling via [`auto-bidi`](https://typst.app/universe/package/auto-bidi)
- Semantic layout classes for cover pages, prayers, and centered blocks
- Configurable typography (fonts, sizes, margins) via `project.yaml`
- Outputs a print-ready PDF

## Prerequisites

- [Pandoc](https://pandoc.org/)
- [Typst](https://typst.app/)
- Python 3 + [PyYAML](https://pyyaml.org/)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Verify all tools are installed:

```bash
make check
```

## Building

```bash
make all       # full build → publication.pdf
make clean     # remove build/ and output PDF
make watch     # rebuild on file changes (requires fswatch on macOS)
```

The build is driven by `scripts/build.py`. It reads `project.yaml`, preprocesses Markdown files, runs Pandoc with a Typst template, and compiles the result with Typst.

## Project structure

```
content/          Markdown source files (listed in order in project.yaml)
images/           Images referenced in content
fonts/            Font files (Shofar, Source Sans 3, Source Code Pro, ...)
templates/        Pandoc → Typst template
scripts/          build.py, preprocess.py, typst_filter.py
project.yaml      Metadata, content order, typography, layout settings
```

## Customizing

Edit `project.yaml` to change the title, author, fonts, paper size, margins, and the order of content files.

Content files live in `content/` and are standard Markdown. Hebrew and English can be mixed freely; `auto-bidi` detects the direction of each paragraph automatically.

For layout details and the full list of available Markdown classes (cover pages, prayer blocks, etc.) see [CLAUDE.md](CLAUDE.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
