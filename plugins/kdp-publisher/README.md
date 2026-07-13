# kdp-publisher

[![CI](https://github.com/robsartin/claude-config/actions/workflows/kdp-publisher.yml/badge.svg)](https://github.com/robsartin/claude-config/actions/workflows/kdp-publisher.yml)

Turn a Google Doc manuscript into print-ready Amazon **KDP** (Kindle Direct
Publishing) files, delivered as a Claude skill. KDP has no publishing API for
individual authors, so this tool produces the files; you upload and proof them
in KDP's own tools.

From one manuscript it produces:

- **Interior PDF** — the paperback interior at the exact trim size, with the KDP
  gutter margins and embedded fonts. Primary path *validates your own Google
  "Save as PDF"* against the KDP rules; it only re-renders (WeasyPrint) when that
  fails (photo-heavy/downsampled, needs bleed, or the gutter crosses a bracket).
- **Wraparound cover PDF** — back + spine + front, full-bleed, with the spine
  width computed from the real page count and your paper choice.
- **Cover-spec sheet + AI-art prompt** — exact canvas/spine/bleed/barcode
  dimensions for designing the cover elsewhere, emitted whenever you don't supply
  a front image.
- **Kindle EPUB** — a reflowable eBook from the same manuscript.

The KDP rules it encodes (trim, 0.125in bleed, gutter brackets by page count,
spine = pages × paper-thickness, 24-page minimum, 79-page spine-text threshold,
barcode keep-out, font embedding, image DPI) are distilled from real KDP
requirements.

## Install

Once per machine, bootstrap the engine's venv:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/install.sh
```

WeasyPrint needs native libraries. On macOS: `brew install pango gdk-pixbuf
libffi`. On Debian/Ubuntu: `apt-get install libpango-1.0-0 libpangocairo-1.0-0
libgdk-pixbuf-2.0-0 libffi-dev`.

## Prepare your Google Doc

- **First page = a labeled front-matter/title page** carrying the settings:

  ```
  Title: My Book
  Subtitle: (optional)
  Author: Your Name
  Trim: 6x9
  Paper: cream
  Copyright: © 2026 Your Name
  ```

  Anything missing is asked for interactively (with smart defaults — color images
  suggest premium-color paper).
- **Heading 1 starts each chapter.** Heading 2+ are in-chapter headings.
- For the **cheap interior path**, set File → Page setup → "Pages", custom size to
  your trim (e.g. 6 × 9 in) with margins = the gutter bracket, then File →
  Download → PDF. The tool validates that export; if it passes, that's your
  interior with no re-rendering.

## CLI

The skill drives this CLI; you can also run it directly:

```bash
# Interior (validate your Google PDF, else re-render):
python -m kdp_publisher interior book.docx --google-pdf book-google.pdf -o interior.pdf

# Interior from the doc alone (always re-render):
python -m kdp_publisher interior book.docx -o interior.pdf

# Wraparound cover (needs a finished front image that already includes the title):
python -m kdp_publisher cover book.docx --cover-image front.png -o cover.pdf

# No front image → spec sheet + AI-art prompt instead:
python -m kdp_publisher cover book.docx -o cover-spec.txt

# Kindle EPUB:
python -m kdp_publisher epub book.docx --cover-image front.png -o book.epub
```

Missing metadata can be supplied with `--title/--author/--trim/--paper`.

## Proofing (there is no upload API)

1. Produce the interior + cover PDFs (and EPUB for Kindle).
2. Skim the PDFs locally.
3. Upload to KDP.
4. Proof in the **KDP online previewer** (authoritative) and **Kindle Previewer**
   (EPUB reflow).
5. **Order a printed proof** for the paperback.
6. Publish.

## Notes & limitations

- The cover renderer does **not** overlay the title on the front panel — supply a
  finished front cover that already carries the title, or use the spec-sheet's
  AI-art prompt, which bakes the title into generated art.
- Google Docs can silently downsample images on PDF export; the validator flags
  low-DPI images so photo-forward books fall back to the re-render path. **Always
  confirm with a printed proof.**
- Not PDF/X-1a (KDP print-on-demand accepts standard embedded-font PDFs).

## Development

```bash
cd plugins/kdp-publisher
./bin/install.sh
.venv/bin/ruff check . && .venv/bin/ruff format --check .
.venv/bin/mypy
.venv/bin/coverage run -m pytest && .venv/bin/coverage report
```
