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

PDF Table Traps does not parse PDF text or infer these column positions. After converting a document to a supported Markdown or JSON table, you can use its existing checker to compare selected cells against values verified in the original.
