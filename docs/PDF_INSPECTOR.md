# Check a pdf-inspector pipeline

[中文](PDF_INSPECTOR.zh-CN.md) · [Raw measurements](../measured/pdf-inspector-1.25.2/) · [Main quick start](../README.md#try-a-known-failure)

This is a small integration example, not a new PDF converter. [Firecrawl's pdf-inspector](https://github.com/firecrawl/pdf-inspector) already extracts local text and detects tables. Our separate checker asks whether a supplied value still belongs to its supplied row and header.

We ran **pdf-inspector 1.25.2**, `process_pdf(path)` with defaults, on the same three original PDFs. No OCR runtime, credentials or hosted service was supplied. The recorded run was Python 3.12 on macOS arm64; CI runs the integration separately on Ubuntu. Check the actual run evidence rather than assuming every platform has been tested.

| Fixture | Supplied checks | What happened |
| --- | --- | --- |
| Ruled table | 4 match | The tested row/header/value pairs remain intact. |
| Wrapped row, no borders | 1 match, 3 mismatch | The `Unit price ($)` column contains `12.5`, `3.25`, `1.8` instead of `64.00`, `88.00`, `145.00`. Those prices still occur elsewhere in the output. |
| Prose | 1 match | No supported table was found, as expected. This does not certify the prose transcription. |

Both successful and failing raw outputs are kept. These three cases do not measure general accuracy, OCR or tuned settings, and do not establish the cause of anyone else's document error.

## Reproduce

From the current source checkout, in a Python 3.10+ virtual environment:

```sh
python -m pip install --only-binary=:all: -r requirements-inspector.txt
python -m scripts.run_pdf_inspector --output artifacts/inspector-run --expect-observed
```

Use a new output directory. This runner exits `0` when the recorded assertion outcomes reproduce, including the known borderless failure. It is a regression-smoke check, **not** an all-documents-correct verdict. Changed outcomes stop that smoke check for inspection. The integration intentionally pins the converter version rather than quietly testing a different release. Binary wheels must be available for your platform; no source compilation or OCR download is attempted by the install command.

To see how a pipeline gate would handle the saved borderless output:

```sh
python -m table_traps check --input measured/pdf-inspector-1.25.2/borderless.pdf-inspector.md --rules cases/borderless.json
```

Expected: exit **1**, three supplied cell mismatches. Swap in `ruled.pdf-inspector.md` and `cases/ruled.json` for the positive control, exit **0**. For your own document, author expectations against its original; do not reuse the synthetic garden values.

The existing six-panel online viewer and v0.1.0 release are unchanged snapshots of the initial MarkItDown/pdfplumber run. This extra integration is available from the current source branch. It neither replaces nor implies endorsement by pdf-inspector.
