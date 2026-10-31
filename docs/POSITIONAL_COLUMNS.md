# When the same PDF column moves in extracted text

Two PDF pages can place text at the same physical x-coordinates while `pdftotext -layout` puts it at different character offsets. A parser that copies character-column boundaries from page one can then read the continuation page incorrectly. This case follows the question raised in [anthropics/skills #1078](https://github.com/anthropics/skills/issues/1078); [a documentation proposal](https://github.com/anthropics/skills/pull/1567) was open when we checked.

The [original synthetic PDF](../fixtures/positional-two-page.pdf) places `Cedar`, `12.5` and `64.00` at x = 50, 260 and 430 points on both pages. Page one has a short header; page two has a longer header. The pages contain fictional values and no ruled table.

On macOS arm64 with Poppler `pdftotext` 26.05.0, `-layout` placed `12.5` and `64.00` at zero-based character offsets **14 / 21** on page one and **47 / 74** on page two. pdfplumber 0.11.9 reported the same x-coordinates on each page. When the PDF region containing the table was selected *before* extraction, excluding the headers, both pages produced offsets **10 / 17** in this sample. Removing a header from already extracted text cannot change positions that were already emitted.

This is one controlled example, not a claim that every PDF, Poppler version, or coordinate-based parser behaves this way. PDF coordinates can vary too: inspect the actual source and verify important row/column values. This case is separate from the three measured converter fixtures, and is not included in the older v0.1.0 ZIP.

## Reproduce

Requires Poppler's `pdftotext` and Python 3.10+. From the repository root:

```sh
pdftotext -layout fixtures/positional-two-page.pdf - | python3 -c 'import sys; p=sys.stdin.read().split("\f"); print([[(s.index("12.5"),s.index("64.00")) for s in page.splitlines() if "Cedar" in s] for page in p if page.strip()])'
pdftotext -r 72 -layout -x 0 -y 60 -W 612 -H 500 fixtures/positional-two-page.pdf - | python3 -c 'import sys; p=sys.stdin.read().split("\f"); print([[(s.index("12.5"),s.index("64.00")) for s in page.splitlines() if "Cedar" in s] for page in p if page.strip()])'
```

To inspect PDF-space coordinates, install `pdfplumber==0.11.9` in a virtual environment, then:

```sh
python3 -c 'import pdfplumber; p=pdfplumber.open("fixtures/positional-two-page.pdf"); print([[(w["text"],w["x0"]) for w in page.extract_words() if w["text"] in ("Cedar","12.5","64.00")] for page in p.pages]); p.close()'
```

To recreate the PDF, install `reportlab==4.4.9` and run `python3 scripts/generate_positional.py --out /tmp/positional-two-page.pdf` with a new output path. The committed PDF has SHA-256 `0938b3d14f6acbaeb0ecb40395fe6ce843d338f57117c60c1b591b9062b1b50d`.

## Try positioned extraction

For a simple text-based table with the same layout on every page, the optional helper can group words using **your** region and column edges. Install the checker and the pinned optional PDF dependency in a virtual environment, then run:

```sh
python -m pip install -r requirements.txt -r requirements-positioned.txt
mkdir -p artifacts
python -m scripts.positional_table fixtures/positional-two-page.pdf --inspect-page 1 --output artifacts/positioned-words.json
python -m scripts.positional_table fixtures/positional-two-page.pdf --region 0,60,612,500 --edges 0,200,350,612 --headers 'Material,Quantity,Unit price' --output artifacts/positioned.json --evidence artifacts/positioned-evidence.json
python -m table_traps check --input artifacts/positioned.json --format tables-json --rules cases/positional-two-page.json
```

The inspection file lists the selected page bounds and each word’s coordinates, which helps choose the region and edges; it contains the page text. The extractor produces one table per page, and the evidence lists the page, top coordinate and extracted cells for each row. In this example four rows are extracted and the two source-checked Cedar price rules match. Output paths must be new. For another PDF, inspect the page in a PDF tool and supply its own bounds and expected values; coordinates are PDF points measured from the page's top left. `--edges` must start and end at the region's x bounds, with one more edge than headers. An intersected region or column boundary, an empty region on any page, or an out-of-bounds region stops extraction.

The helper is a deliberately limited grouping heuristic for text-based, **single-line rows**. It applies the same region and columns to every page (up to 100 pages); it does not detect tables, infer headers, merge wrapped rows, perform OCR, or verify values against the original. `--row-tolerance` changes the maximum top-coordinate difference in a row (default 3 points). Row alignment, fonts, rotation, repeated headers and words near boundaries can still change the result: review the evidence and source PDF before use. A passing rule checks only the values you supplied; it does not certify the document. This helper is in current source, not the older v0.1.0 ZIP.
