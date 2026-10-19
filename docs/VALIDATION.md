# Validation and provenance

Local measurement: 2026-10-20 Asia/Shanghai (UTC timestamps in `measured/run.json`). Source PDFs are original ReportLab drawings with fictional gardening quantities and prices, not customer documents, supplier quotations or copied bug attachments. Source text and expected rows are in `scripts/generate_samples.py` and `fixtures/expected.json`. Code, source fixtures and expected data are MIT licensed.

## Exact measurement

- Python 3.12.14 on macOS; MarkItDown 0.1.8, pdfplumber 0.11.10, pdfminer-six 20260107, Magika 0.6.3.
- `MarkItDown(enable_plugins=False).convert_local(...)`; no LLM client, API credentials, plugin or remote service supplied.
- `pdfplumber.open(...); page.extract_tables()` with defaults, then explicit table matrices. It is not a full Markdown converter in this comparison.
- Three source PDFs, two paths, six reports. Rules assert table count and three unit prices for table samples; prose asserts only zero tables.
- The checker only normalizes NFC and whitespace. It does not infer the correct source values. These were authored in advance and inspected in the rendered PDFs.

| Case / path | Match | Mismatch | Unknown |
| --- | ---: | ---: | ---: |
| ruled / MarkItDown | 1 | 3 | 0 |
| ruled / pdfplumber | 4 | 0 | 0 |
| borderless / MarkItDown | 1 | 2 | 1 |
| borderless / pdfplumber | 0 | 1 | 3 |
| prose / MarkItDown | 1 | 0 | 0 |
| prose / pdfplumber | 1 | 0 | 0 |

These are assertion counts, not accuracy percentages. A report with a mismatch takes overall `fail` even when it also has unknowns. A known correct ruled table and an intentionally swapped-price unit control demonstrate that the checker can both pass and fail; strings occurring somewhere are insufficient.

The recorded outputs were run again through the project runner after the checker was implemented; source and raw output hashes matched the initial isolated extraction. Tests assert the six bounded outcomes, not the general quality of either library. Remote CI is a separate execution, not proof of real-user adoption.

## Additional integration: pdf-inspector 1.25.2

The current source also includes `scripts/run_pdf_inspector.py` and [`measured/pdf-inspector-1.25.2/`](../measured/pdf-inspector-1.25.2/). A separate local macOS arm64 / Python 3.12.14 run used `process_pdf(path)` defaults on the identical original fixtures and rule files. Ruled: 4 match; borderless: 1 match and 3 mismatch; prose: 1 zero-table check match. Raw output and source hashes are recorded. The pinned integration has its own Ubuntu CI job and artifact; inspect each run for its observed platform/results. None of these extra measurements changes the original six-panel viewer or fixed v0.1.0 release. [Reproduction instructions](PDF_INSPECTOR.md)

## Measurement limits

Real-world accuracy, unseen layouts, OCR, scans, merged/multi-level headers, source authentication, full-document meaning, Arabic/RTL behavior, tuned extraction settings, semantic numeric equivalence, formula correctness or downstream model answers. No user trial or Star outcome has been established by this test.

Raw HTML tables are intentionally unsupported in v0.1.0; convert them to the documented matrix format rather than treating no parse as success. Input limits and empty/ambiguous conditions fail closed. Reports display the actual input values and can be sensitive when users supply their own data.

## Rendering and UI

The demo shows direct PDF region renders (crop margins left/right 30 pt, bottom 280 pt, top 175 pt, scale 2), without retouching or overlaid arrows. Full originals are downloadable. Highlighting is applied only to failed cells in the parsed output, never to the source image. English/Chinese labels do not translate fixture data.

The saved-report page performs no parser/API calls and has no analytics. A runtime CSP blocks network connections; static files still need loading when hosted. A single generated CLI HTML report embeds styles/scripts and can open locally. Initial installation and optional converter reproduction need dependency downloads.

Browser validation uses Playwright 1.64.1 against actual Chrome on macOS, with six sample/path selections, the expected/observed primary cell, three highlighted mismatches, a source-PDF download checksum, language switching, a fresh 390 px mobile page, and a generated standalone report. No external HTTP requests or page errors occurred in the local check. A long screenshot made after resizing an already-loaded desktop page showed repeated compositor tiles despite a single-header DOM; it was rejected. Selected mobile evidence uses fresh-page viewport captures with no overflow.

Optional browser QA: `npm ci`, then `npm run test:browser` with Chrome installed. `BROWSER_CHANNEL=chromium` uses a Playwright-installed Chromium instead. `TABLE_TRAPS_PYTHON` selects the Python interpreter with the checker dependencies. Screenshots default to ignored artifacts; `TABLE_TRAPS_SCREENSHOT_DIR` can direct them to an external evidence folder. CI runs these checks on Ubuntu with bundled Chromium; results are separate from local Chrome validation.
