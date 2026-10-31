"""Extract user-selected, single-line, positioned PDF rows for manual review.

The caller supplies PDF-space bounds and column edges; this is not a table detector.
"""
import argparse
import bisect
import json
import math
from pathlib import Path

MAX_PAGES = 100
MAX_WORDS = 100_000
MAX_INPUT_BYTES = 2 * 1024 * 1024


def inspect_page(path, page_number):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        if not pdf.pages or len(pdf.pages) > MAX_PAGES:
            raise ValueError("PDF must contain 1–100 pages; split longer documents first.")
        if not 1 <= page_number <= len(pdf.pages):
            raise ValueError("Page number is outside the PDF.")
        page = pdf.pages[page_number - 1]
        words = page.extract_words()
        if len(words) > MAX_WORDS:
            raise ValueError("Page exceeds the 100,000-word safety limit.")
        result = {"page": page_number, "page_bbox": list(page.bbox), "coordinate_unit": "PDF points, top-left origin",
                  "words": [{key: word[key] for key in ("text", "x0", "top", "x1", "bottom")} for word in words]}
        page.close()
        return result


def numbers(text, count=None):
    try:
        values = [float(x.strip()) for x in text.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Expected comma-separated numbers.") from exc
    if (count is not None and len(values) != count) or not all(math.isfinite(x) for x in values):
        raise argparse.ArgumentTypeError("Wrong number of coordinates, or a non-finite value.")
    return values


def extract(path, region, edges, headers, tolerance=3):
    # Imported only for this optional feature, not for the regular table checker.
    import pdfplumber

    if len(region) != 4 or not all(math.isfinite(x) for x in region):
        raise ValueError("Region must contain four finite coordinates.")
    x0, top, x1, bottom = region
    if x0 < 0 or top < 0 or x1 <= x0 or bottom <= top:
        raise ValueError("Region must be x0,top,x1,bottom with positive width and height.")
    if not 1 <= len(headers) <= 100 or any(not h.strip() or len(h) > 20_000 for h in headers) or len(set(headers)) != len(headers):
        raise ValueError("Supply 1–100 distinct, nonempty column headers, each at most 20,000 characters.")
    if len(edges) != len(headers) + 1 or not all(math.isfinite(x) for x in edges):
        raise ValueError("Supply one more column edge than headers.")
    if edges[0] != x0 or edges[-1] != x1 or any(a >= b for a, b in zip(edges, edges[1:])):
        raise ValueError("Column edges must increase and begin/end at the region's x bounds.")
    if not math.isfinite(tolerance) or not 0 <= tolerance <= 20:
        raise ValueError("Row tolerance must be between 0 and 20 points.")

    tables, evidence, total_words = [], [], 0
    with pdfplumber.open(path) as pdf:
        if not pdf.pages or len(pdf.pages) > MAX_PAGES:
            raise ValueError("PDF must contain 1–100 pages; split longer documents first.")
        for index, page in enumerate(pdf.pages, 1):
            px0, ptop, px1, pbottom = page.bbox
            if x0 < px0 or top < ptop or x1 > px1 or bottom > pbottom:
                raise ValueError(f"Region falls outside page {index}; check page dimensions and rotation.")
            # include words only when wholly inside the region; cropped text isn't silently returned.
            all_words = page.extract_words()
            total_words += len(all_words)
            if total_words > MAX_WORDS:
                raise ValueError("PDF exceeds the 100,000-word safety limit.")
            selected = []
            for word in all_words:
                intersects = word["x1"] > x0 and word["x0"] < x1 and word["bottom"] > top and word["top"] < bottom
                wholly_inside = word["x0"] >= x0 and word["x1"] <= x1 and word["top"] >= top and word["bottom"] <= bottom
                if intersects and not wholly_inside:
                    raise ValueError(f"A word crosses the region boundary on page {index}; adjust the region.")
                if wholly_inside:
                    if any(word["x0"] < edge < word["x1"] for edge in edges[1:-1]):
                        raise ValueError(f"A word crosses a column edge on page {index}; adjust the edges.")
                    selected.append(word)
            if not selected:
                raise ValueError(f"No words found in region on page {index}; check the region or OCR the PDF first.")
            selected.sort(key=lambda w: (w["top"], w["x0"]))
            groups = []
            for word in selected:
                if not groups or abs(word["top"] - groups[-1][0]["top"]) > tolerance:
                    groups.append([word])
                else:
                    groups[-1].append(word)
            page_rows = [headers]
            for group in groups:
                cells = [[] for _ in headers]
                for word in sorted(group, key=lambda w: w["x0"]):
                    col = min(bisect.bisect_right(edges, word["x0"]) - 1, len(headers) - 1)
                    cells[col].append(word["text"])
                row = [" ".join(cell) for cell in cells]
                if any(len(cell) > 20_000 for cell in row) or len(page_rows) >= 1000:
                    raise ValueError(f"Page {index} exceeds the table checker's row or cell limits.")
                page_rows.append(row)
                evidence.append({"page": index, "top": round(group[0]["top"], 3), "cells": row})
            tables.append(page_rows)
            page.close()
    table_output = {"tables": tables}
    if len(json.dumps(table_output, ensure_ascii=False, indent=2).encode("utf-8")) + 1 > MAX_INPUT_BYTES:
        raise ValueError("Extracted table JSON exceeds the table checker's 2 MiB input limit.")
    return table_output, {"region": region, "column_edges": edges,
                               "row_tolerance": tolerance, "rows": evidence,
                               "scope": "Heuristic single-line rows in a user-selected region; inspect the original PDF. Not OCR, table detection, or accuracy certification."}


def main():
    parser = argparse.ArgumentParser(description="Extract explicitly positioned, single-line PDF table rows for review.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--inspect-page", type=int, help="inspect one page's text coordinates instead of extracting a table")
    parser.add_argument("--region", help="x0,top,x1,bottom in PDF points, applied to every page")
    parser.add_argument("--edges", help="increasing x coordinates, including region left and right edges")
    parser.add_argument("--headers", help="comma-separated column names")
    parser.add_argument("--row-tolerance", type=float, default=3, help="maximum top-coordinate difference in a row, points (default 3)")
    parser.add_argument("--output", required=True, type=Path, help="new output file in tables-json format")
    parser.add_argument("--evidence", type=Path, help="new JSON file listing page and row positions (required for extraction)")
    args = parser.parse_args()
    try:
        if args.inspect_page is not None:
            if any(x is not None for x in (args.region, args.edges, args.headers, args.evidence)):
                raise ValueError("Inspect mode cannot be combined with extraction options.")
            if args.output.resolve() == args.pdf.resolve() or args.output.exists():
                raise ValueError("Output must be a new file, not the input PDF.")
            result = inspect_page(args.pdf, args.inspect_page)
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(result, handle, ensure_ascii=False, indent=2); handle.write("\n")
            print(f"Listed {len(result['words'])} words on page {args.inspect_page}.")
            return 0
        if any(x is None for x in (args.region, args.edges, args.headers, args.evidence)):
            raise ValueError("Extraction requires --region, --edges, --headers and --evidence.")
        region, edges = numbers(args.region, 4), numbers(args.edges)
        headers = [x.strip() for x in args.headers.split(",")]
        paths = [args.output.resolve(), args.evidence.resolve()]
        if len(set(paths)) != 2 or args.pdf.resolve() in paths or any(p.exists() for p in paths):
            raise ValueError("Output and evidence must be distinct new files, not the input PDF.")
        table, evidence = extract(args.pdf, region, edges, headers, args.row_tolerance)
        # Avoid partial results: create both exclusively; remove our first new output if the second fails.
        first_created = False
        second_created = False
        try:
            with args.output.open("x", encoding="utf-8") as handle:
                first_created = True
                json.dump(table, handle, ensure_ascii=False, indent=2); handle.write("\n")
            with args.evidence.open("x", encoding="utf-8") as handle:
                second_created = True
                json.dump(evidence, handle, ensure_ascii=False, indent=2); handle.write("\n")
        except OSError:
            if second_created:
                args.evidence.unlink(missing_ok=True)
            if first_created:
                args.output.unlink(missing_ok=True)
            raise
        print(f"Extracted {len(evidence['rows'])} rows. Review them against the source PDF.")
        return 0
    except (ValueError, OSError, ImportError, argparse.ArgumentTypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
