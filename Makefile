.PHONY: all clean watch deps check

PYTHON     := python3
BUILD_DIR  := build
PROJECT    := project.yaml
OUTPUT     := $(shell $(PYTHON) -c "import yaml; p=yaml.safe_load(open('$(PROJECT)')); print(p['output']['filename'])" 2>/dev/null || echo publication.pdf)

# Source dependencies
MD_FILES   := $(wildcard content/*.md)
TYP_FILES  := $(wildcard templates/*.typ)
IMAGES     := $(wildcard images/*)
FONTS      := $(wildcard fonts/*)

# ── Main target ──────────────────────────────────────────────────────────────

all: $(OUTPUT)

$(OUTPUT): $(PROJECT) $(MD_FILES) $(TYP_FILES) $(IMAGES) $(FONTS) scripts/build.py scripts/preprocess.py
	$(PYTHON) scripts/build.py $(PROJECT)

# ── Utility targets ───────────────────────────────────────────────────────────

clean:
	rm -rf $(BUILD_DIR)
	rm -f $(OUTPUT)

# Check that required tools are installed
check:
	@echo "Checking dependencies..."
	@command -v pandoc  >/dev/null 2>&1 && echo "  pandoc:  OK ($(shell pandoc --version | head -1))" || echo "  pandoc:  MISSING — install from https://pandoc.org/"
	@command -v typst   >/dev/null 2>&1 && echo "  typst:   OK ($(shell typst --version))"            || echo "  typst:   MISSING — install from https://typst.app/"
	@$(PYTHON) -c "import yaml" 2>/dev/null && echo "  pyyaml:  OK" || echo "  pyyaml:  MISSING — pip install pyyaml"
	@$(PYTHON) -c "import sys; print(f'  python:  OK ({sys.version.split()[0]})')"

# Install Python dependencies
deps:
	$(PYTHON) -m pip install -r requirements.txt

# Watch for changes and rebuild (requires fswatch on macOS or inotifywait on Linux)
watch:
	@echo "Watching for changes (Ctrl-C to stop)..."
	@$(MAKE) all
	@if command -v fswatch >/dev/null 2>&1; then \
		fswatch -o content/ templates/ images/ fonts/ $(PROJECT) scripts/ | xargs -n1 -I{} $(MAKE) all; \
	elif command -v inotifywait >/dev/null 2>&1; then \
		while inotifywait -qre modify content/ templates/ images/ fonts/ $(PROJECT) scripts/; do $(MAKE) all; done; \
	else \
		echo "Install fswatch (macOS: brew install fswatch) or inotify-tools (Linux) for watch support."; \
	fi
