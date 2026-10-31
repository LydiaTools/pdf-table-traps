# Every label survived—but two rows became headers

[中文](CONTINUATION.zh-CN.md) · [Single-header report](https://lydiatools.github.io/pdf-table-traps/cases/continuation/single-report.html) · [Repeated-header control](https://lydiatools.github.io/pdf-table-traps/cases/continuation/repeat-report.html)

A successful conversion can keep every word and still change what the table means. This case starts with three pages of fictional nursery inventory: 24 rows, eight per page. Two original PDFs contain the same rows. One prints `Item / Zone / Count / Price` only on page 1; the control repeats the headers on each page.

On 2026-11-01 we converted both with local **firecrawl-anydoc 0.2.4**, using its Python `to_markdown` defaults. In the single-header output all 24 item labels are present as text, but `Plant-09` and `Plant-17` are parsed as the headers of two new Markdown tables. They are not data rows in those tables. In the repeated-header control, all 24 are data rows in one Markdown table. A separate read with pypdf 6.1.1 found the expected eight labels on each original page.

Our [three supplied checks](cases/continuation/rules.json) ask for the `Count` of `Plant-01`, `Plant-09` and `Plant-17` in the first table. The single-header output returns **1 match, 2 unknown** (exit 2): the latter rows cannot be found in that table. The control returns **3 matches** (exit 0). Unknown means the checker cannot verify the supplied relationship; it does not automatically establish why or identify every affected row. Review the original and all output tables.

The related [upstream report](https://github.com/firecrawl/anydoc/issues/214) describes first rows being omitted from a different multi-page fixture. A [pdf-inspector fix](https://github.com/firecrawl/pdf-inspector/pull/648) was open when checked on 2026-11-01. Our independently generated example has a different observed output: the labels remain but are treated as headers. We have not tested that proposed fix or inferred that it solves this case. This small synthetic comparison is not a benchmark or a claim about other PDF layouts.

## Reproduce

From the repository root, use Python 3.10+ and a clean environment:

```sh
python -m pip install -r requirements.txt 'reportlab==4.4.9' 'firecrawl-anydoc==0.2.4'
python docs/cases/continuation/generate.py --output /tmp/continuation-example
python -m table_traps check --input /tmp/continuation-example/single-header.md --rules /tmp/continuation-example/rules.json
python -m table_traps check --input /tmp/continuation-example/repeat-header.md --rules /tmp/continuation-example/rules.json
```

Use a **new** output directory; the generator refuses to replace an existing one. The first check should exit 2 and the second 0. On Windows, replace `/tmp/continuation-example` with a new local path. The [PDFs, measured Markdown, rules, JSON and HTML reports](cases/continuation/) are included for review; no private documents or hosted conversion are involved. PDF hashes are in [SHA256SUMS](cases/continuation/SHA256SUMS.txt). This case was added to main after the v0.2.0 preview and is not in that ZIP.
