"""Original, synthetic fixtures for checking PDF-to-Markdown table relationships."""
import argparse
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


ROWS = [
    ["Cedar mulch", "12.5", "64.00", "800.00"],
    ["Screened compost", "3.25", "88.00", "286.00"],
    ["River gravel", "1.8", "145.00", "261.00"],
]
HEADERS = ["Material", "Volume (m3)", "Unit price ($)", "Line total ($)"]


def base(path, title, subtitle):
    c = canvas.Canvas(str(path), pagesize=letter, invariant=1)
    c.setAuthor("LydiaTools")
    c.setTitle(title + " - synthetic fixture")
    c.setSubject("Original test material. Fictional quantities and prices. MIT licensed.")
    c.setFillColor(colors.HexColor("#244D59"))
    c.rect(42, 718, 528, 5, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(42, 678, title)
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#41545B"))
    c.drawString(42, 653, subtitle)
    c.setFont("Helvetica", 9)
    c.drawString(42, 54, "Synthetic test fixture by LydiaTools. Fictional values; not a supplier quote.")
    c.drawRightString(570, 54, "1 / 1")
    c.setFillColor(colors.HexColor("#122A32"))
    return c


def ruled(path):
    c = base(path, "Garden materials estimate", "Case A: ruled table, one header row, three material rows")
    xs = [42, 238, 344, 456, 570]
    ys = [592, 556, 516, 476, 436]
    c.setFillColor(colors.HexColor("#E6F0F2"))
    c.rect(xs[0], ys[1], xs[-1] - xs[0], ys[0] - ys[1], fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#78959D"))
    c.setLineWidth(0.7)
    for x in xs:
        c.line(x, ys[-1], x, ys[0])
    for y in ys:
        c.line(xs[0], y, xs[-1], y)
    c.setFillColor(colors.HexColor("#122A32"))
    c.setFont("Helvetica-Bold", 10)
    for idx, label in enumerate(HEADERS):
        c.drawString(xs[idx] + 10, 570, label)
    c.setFont("Helvetica", 11)
    for row, y in zip(ROWS, [531, 491, 451]):
        c.drawString(xs[0] + 10, y, row[0])
        for idx in range(1, 4):
            c.drawRightString(xs[idx + 1] - 10, y, row[idx])
    c.setFont("Helvetica-Bold", 12)
    c.drawString(42, 392, "Materials total")
    c.drawRightString(560, 392, "$1,347.00")
    c.setFont("Helvetica", 10)
    c.drawString(42, 362, "Keep each price attached to its material. The total alone is not a table check.")
    c.save()


def borderless(path):
    c = base(path, "Garden materials estimate", "Case B: borderless table with one material name wrapped onto a second line")
    lefts = [42, 251, 365, 473]
    rights = [232, 342, 454, 566]
    c.setFont("Helvetica-Bold", 10)
    for x, label in zip(lefts, HEADERS):
        c.drawString(x, 582, label)
    c.setFont("Helvetica", 11)
    for idx, (row, y) in enumerate(zip(ROWS, [544, 484, 424])):
        c.drawString(lefts[0], y, row[0])
        if idx == 0:
            c.drawString(lefts[0], y - 15, "fine-grade")
        for column in range(1, 4):
            c.drawRightString(rights[column], y, row[column])
    c.setFont("Helvetica-Bold", 12)
    c.drawString(42, 360, "Materials total")
    c.drawRightString(566, 360, "$1,347.00")
    c.setFont("Helvetica", 10)
    c.drawString(42, 324, "A wrapped name belongs to its original row, not a new empty-price material.")
    c.save()


def prose(path):
    c = base(path, "Reading a garden estimate", "Case C: prose with aligned text and repeated numbers; no table exists")
    lines = [
        "A list of familiar numbers is not proof that a table survived conversion.",
        "The estimate mentions Cedar mulch at 64.00 dollars per cubic metre.",
        "It also mentions Screened compost at 88.00 dollars per cubic metre.",
        "River gravel is priced at 145.00 dollars per cubic metre in this example.",
        "These are independent sentences in a paragraph, not cells in a grid.",
        "A checker must not infer a table merely because all three values occur.",
    ]
    c.setFont("Helvetica", 11)
    for index, line in enumerate(lines):
        c.drawString(42, 588 - 24 * index, line)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(42, 376, "What should remain true")
    c.setFont("Helvetica", 11)
    for index, line in enumerate([
        "The prose stays prose. Material names retain their own prices.",
        "A missing table is different from a table with a wrong cell.",
        "Review the source before trusting a tidy-looking Markdown preview.",
    ]):
        c.drawString(42, 344 - 24 * index, line)
    c.save()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, func in [("ruled", ruled), ("borderless", borderless), ("prose", prose)]:
        path = args.output / (name + ".pdf")
        if path.exists():
            raise SystemExit(f"Refusing to replace existing fixture: {path}")
        func(path)
    expected = {
        "provenance": "Original synthetic fixtures generated by LydiaTools; MIT. No production/user data.",
        "scope": "Three deliberately small cases; not an accuracy benchmark or representative corpus.",
        "headers": HEADERS,
        "ruled": {"tables": 1, "rows": ROWS},
        "borderless": {"tables": 1, "rows": [["Cedar mulch fine-grade", *ROWS[0][1:]], *ROWS[1:]]},
        "prose": {"tables": 0},
    }
    (args.output / "expected.json").write_text(json.dumps(expected, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "pdfs": 3}))


if __name__ == "__main__":
    main()
