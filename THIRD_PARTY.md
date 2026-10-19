# Third-party software and related work

No upstream implementation code or third-party PDF documents are vendored. Dependencies are installed separately; their licenses continue to apply.

- [markdown-it-py](https://github.com/executablebooks/markdown-it-py), MIT, parses Markdown tables. [mdurl](https://github.com/executablebooks/mdurl), MIT, is its URL parser dependency.
- Optional measurement: [MarkItDown](https://github.com/microsoft/markitdown), MIT; [pdfplumber](https://github.com/jsvine/pdfplumber), MIT; [ReportLab](https://www.reportlab.com/opensource/), BSD. Their transitive dependencies retain their respective licenses. Version pins are in `requirements-validation.lock`.
- Additional optional integration: [pdf-inspector](https://github.com/firecrawl/pdf-inspector), MIT, installed separately and pinned in `requirements-inspector.txt`. Only our original fixtures and the resulting measurements are included here; its source/binaries, OCR models and runtime libraries are not vendored.
- Related evaluation tools: [OmniDocBench](https://github.com/opendatalab/OmniDocBench), [ParseArena](https://github.com/shubham23471/parsearena). Referencing them does not imply affiliation or endorsement.

Original fixtures and the checker/report implementation are copyright 2026 LydiaTools, licensed under the root MIT license.
