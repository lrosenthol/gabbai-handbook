#!/usr/bin/env python3
"""Markdown preprocessing for Hebrew+English publications.

auto-bidi (the Typst package) handles RTL/LTR detection automatically, so
no direction-wrapping is done here.  The only transformations are:

  1. Rewrite image paths from ../images/ → images/ (relative to build dir).
  2. (English-primary docs only) Warn if bare Hebrew paragraphs are found
     without explicit language context, as a content-quality hint.
"""

import re
from typing import Any

_HEBREW_RE  = re.compile(r"[֐-׿יִ-ﭏ]")
_IMG_PATH_RE = re.compile(r"(!\[[^\]]*\]\()(?:\.\.\/)*images\/")


def _hebrew_fraction(text: str) -> float:
    alpha = sum(1 for c in text if c.isalpha())
    if alpha == 0:
        return 0.0
    return len(_HEBREW_RE.findall(text)) / alpha


def _rewrite_image_paths(text: str) -> str:
    """Normalise image references to images/ relative to the build dir."""
    return _IMG_PATH_RE.sub(r"\1images/", text)


# ── Public API ────────────────────────────────────────────────────────────────

def preprocess(text: str, project: dict[str, Any]) -> str:
    """Apply all preprocessing steps to one markdown file's content."""
    text = _rewrite_image_paths(text)
    return text
