---
name: kdp-publisher
description: Use when turning a Google Doc (or exported .docx) manuscript into print-ready Amazon KDP files — a paperback interior PDF, a wraparound cover PDF, a cover-spec sheet, or a Kindle EPUB. Triggers on "publish to KDP", "make a KDP cover", "KDP interior PDF", "turn my doc into a paperback / Kindle book", "self-publish this manuscript".
---

# KDP Publisher

Turn a Google Doc manuscript into print-ready Amazon KDP files. This file is the
process; the engine (a Python CLI) and the KDP rules it encodes are described in
[README.md](../../README.md). KDP has no publishing API — the tool produces
files; the human uploads and proofs them in KDP's own tools.

The engine exposes three subcommands — `interior`, `cover`, `epub` — run as
`${CLAUDE_PLUGIN_ROOT}/.venv/bin/python -m kdp_publisher <subcommand> …`.

## Process

### 1. Ensure the engine is available

Once per machine:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/install.sh
```

This creates the venv and installs the package. WeasyPrint (the interior
re-render engine) needs native libraries — if `python -m kdp_publisher` errors on
a missing `libpango`/`gobject`, install them (macOS: `brew install pango
gdk-pixbuf libffi`; Debian: the `libpango-1.0-0 libpangocairo-1.0-0
libgdk-pixbuf-2.0-0 libffi-dev` packages), then retry.

### 2. Get the manuscript as a local file

The engine ingests a `.docx` (and, for the cheap interior path, a Google-exported
PDF). Do NOT feed it Google's EPUB export.

- **Google Drive link or doc name** → use the connected **Google Drive MCP** to
  export the Doc as **.docx** (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`)
  to a local file. For the interior, also export the same Doc as **PDF**
  (`application/pdf`) to pass as `--google-pdf` — but only if the author set the
  Doc's Page setup to the KDP trim + margins (ask; if they didn't, skip the PDF
  and let the tool re-render).
- **Local file** → use the `.docx` the user exported (File → Download → .docx).

If no Google Drive MCP is connected and the user only has a Drive link, ask them
to download the Doc as `.docx` and give you the path.

### 3. Confirm metadata (front-matter page)

The Doc's first page should carry labeled settings (`Title:`, `Author:`, `Trim:`,
`Paper:`, `Copyright:`) — see the README. The engine parses these. If required
fields (title, author, trim, paper) are missing, the CLI prints exactly which,
and exits non-zero. Ask the user for the missing values and re-run with
`--title/--author/--trim/--paper`. Smart defaults:

- **Trim:** `6x9` is the common default for prose; `8.5x11` for photo-heavy.
- **Paper:** if the manuscript has color photos, suggest **premium color**
  (`premium-color`); otherwise **cream** (`cream-bw`) for prose, **white**
  (`white-bw`) for diagram/reference.

### 4. Produce what the user asked for

Write outputs to a directory you choose (e.g. alongside the source, or a
user-named folder). Use `${CLAUDE_PLUGIN_ROOT}/.venv/bin/python -m kdp_publisher`:

- **Interior PDF** (validate Google's export, else re-render):
  ```
  … interior book.docx --google-pdf book-google.pdf -o interior.pdf
  ```
  Without `--google-pdf`, it always re-renders from the doc. Read the printed
  check report (`trim`/`fonts`/`min_pages`/`image_dpi`/`gutter`) back to the user;
  a `fail` on the Google PDF means the tool fell back to a re-render.
- **Wraparound cover PDF** — needs a **finished front image that already
  includes the title** (the renderer does not overlay front text):
  ```
  … cover book.docx --cover-image front.png -o cover.pdf
  ```
  If the user has no cover image, run WITHOUT `--cover-image` to produce a
  spec-sheet + AI-art prompt they (or you) can use to generate the front art:
  ```
  … cover book.docx -o cover-spec.txt
  ```
- **Kindle EPUB:**
  ```
  … epub book.docx --cover-image front.png -o book.epub
  ```

Paperbacks need ≥ 24 pages; the tool refuses to emit an interior/cover below
that. Spine text appears only at ≥ 79 pages.

### 5. Hand off to KDP (there is no upload API)

Tell the user the concrete next steps (also in the README):

1. Skim the PDFs locally.
2. Upload to KDP — interior + cover for the paperback, EPUB for Kindle. **Match
   the paper type you chose here** when you set up the paperback, so the spine
   lines up.
3. Proof in the **KDP online previewer** (authoritative — shows trim + bleed) and
   **Kindle Previewer** (EPUB reflow).
4. **Order a printed proof** before publishing the paperback — especially to
   confirm image quality (Google can downsample images on PDF export).
5. Publish. KDP prints the barcode itself in the reserved back-cover area.

## Notes

- Everything the tool does is offline and local; nothing is uploaded on the
  user's behalf.
- The cover's spine width depends on the exact page count and paper thickness, so
  regenerate the cover if the interior's page count changes.
- Prefer the validate-Google-PDF interior path when the author has set their Doc's
  Page setup correctly — it preserves exactly what they see in Docs. Fall back to
  the re-render for photo books or when validation flags a problem.
