#!/usr/bin/env python3
"""Main build script: Markdown → Pandoc → Typst → PDF."""

import subprocess
import sys
import shutil
from pathlib import Path
from typing import Any

import yaml
from typing import Optional

# Make sibling scripts importable
sys.path.insert(0, str(Path(__file__).parent))
from preprocess import preprocess  # noqa: E402

ROOT       = Path(__file__).resolve().parent.parent
BUILD_DIR  = ROOT / "build"
CONTENT    = ROOT / "content"
IMAGES     = ROOT / "images"
FONTS      = ROOT / "fonts"
TEMPLATES  = ROOT / "templates"


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_project(path: Path) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    BUILD_DIR.mkdir(exist_ok=True)
    (BUILD_DIR / "images").mkdir(exist_ok=True)


def copy_assets() -> None:
    """Copy images into build directory so Typst can resolve them."""
    if IMAGES.exists():
        for src in IMAGES.iterdir():
            if src.is_file():
                shutil.copy2(src, BUILD_DIR / "images" / src.name)


# ── Front-matter construction ─────────────────────────────────────────────────

def build_front_matter(project: dict[str, Any]) -> dict[str, Any]:
    pub   = project.get("publication", {})
    typo  = project.get("typography",  {})
    layout = project.get("layout",     {})

    direction = pub.get("direction", "rtl")
    language  = pub.get("language",  "he")

    fm: dict[str, Any] = {
        # Standard pandoc metadata
        "title":    pub.get("title",    ""),
        "subtitle": pub.get("subtitle", ""),
        "author":   pub.get("author",   ""),
        "date":     pub.get("date",     ""),
        "lang":     language,
        # Custom template variables
        "title-he":      pub.get("title_he", pub.get("title", "")),
        "rtl":           direction == "rtl",
        "hebrew-font":   typo.get("hebrew_font", "Frank Ruehl CLM"),
        "latin-font":    typo.get("latin_font",  "TeX Gyre Pagella"),
        "code-font":     typo.get("code_font",   "DejaVu Sans Mono"),
        "body-size":     typo.get("body_size",   "12pt"),
        "heading-scale": typo.get("heading_scale", 1.4),
        "paper":         layout.get("paper",          "a4"),
        "top-margin":    layout.get("top_margin",    "2.5cm"),
        "bottom-margin": layout.get("bottom_margin", "2.5cm"),
        "right-margin":  layout.get("right_margin",  "3cm"),
        "left-margin":   layout.get("left_margin",   "2cm"),
        "two-sided":     layout.get("two_sided",     True),
    }
    return fm


# ── Markdown assembly ─────────────────────────────────────────────────────────

def assemble_markdown(project: dict[str, Any]) -> Path:
    """Combine content files in project order into one markdown document."""
    fm = build_front_matter(project)
    entries = project.get("content", [])

    parts = [
        "---",
        yaml.dump(fm, allow_unicode=True, default_flow_style=False).rstrip(),
        "---",
    ]

    for entry in entries:
        if "folder" in entry:
            folder_path = CONTENT / entry["folder"]
            folder_title = entry.get("title") or entry["folder"].rstrip("/").replace("-", " ").title()
            parts.append("")
            parts.append(f"# {folder_title}")
            for filename in entry.get("files", []):
                md_path = folder_path / filename
                if not md_path.exists():
                    print(f"Warning: {md_path} not found — skipping.", file=sys.stderr)
                    continue
                raw = md_path.read_text(encoding="utf-8")
                processed = preprocess(raw, project)
                parts.append("")
                parts.append(processed)
            continue

        md_path = CONTENT / entry["file"]
        if not md_path.exists():
            print(f"Warning: {md_path} not found — skipping.", file=sys.stderr)
            continue

        raw = md_path.read_text(encoding="utf-8")
        processed = preprocess(raw, project)
        parts.append("")
        parts.append(processed)

    combined_path = BUILD_DIR / "combined.md"
    combined_path.write_text("\n".join(parts), encoding="utf-8")
    return combined_path


# ── Pandoc step ───────────────────────────────────────────────────────────────

def run_pandoc(md_file: Path, out_typ: Path) -> None:
    template = TEMPLATES / "pandoc-template.typ"
    typst_filter = ROOT / "scripts" / "typst_filter.py"

    cmd = [
        "pandoc",
        str(md_file),
        "--from",          "markdown+smart+fenced_divs+bracketed_spans",
        "--to",            "typst",
        "--output",        str(out_typ),
        "--standalone",
        "--template",      str(template),
        "--filter",        str(typst_filter),
        "--resource-path", str(BUILD_DIR),
    ]

    _run(cmd, "Pandoc")


# ── Typst step ────────────────────────────────────────────────────────────────

def run_typst(typ_file: Path, pdf_file: Path) -> None:
    cmd = [
        "typst", "compile",
        str(typ_file),
        str(pdf_file),
    ]

    if FONTS.exists():
        cmd += ["--font-path", str(FONTS)]

    _run(cmd, "Typst", cwd=BUILD_DIR)


# ── Low-level runner ──────────────────────────────────────────────────────────

def _run(cmd: list[str], label: str, cwd: Optional[Path] = None) -> None:
    print(f"[{label}] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if result.stderr:
        print(f"[{label}] {result.stderr.rstrip()}", file=sys.stderr)
    if result.returncode != 0:
        sys.exit(result.returncode)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    project_file = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "project.yaml"
    project      = load_project(project_file)
    output_pdf   = ROOT / project.get("output", {}).get("filename", "publication.pdf")

    ensure_dirs()
    copy_assets()

    print("Assembling markdown...")
    combined_md = assemble_markdown(project)

    print("Converting to Typst via Pandoc...")
    typst_file = BUILD_DIR / "document.typ"
    run_pandoc(combined_md, typst_file)

    print("Compiling PDF via Typst...")
    run_typst(typst_file, output_pdf)

    print(f"\nDone → {output_pdf.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
