"""Create the original two-page positional-column example (ReportLab 4.4.9)."""
import argparse
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New PDF path; existing files are not overwritten')
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f'output already exists: {args.out}')
    c = canvas.Canvas(str(args.out), pagesize=letter, invariant=1)
    for page, header in [(1, 'Report'), (2, 'Wide page header: monthly records for long-running systems and projects')]:
        c.setFont('Helvetica', 10)
        c.drawString(40, 750, header)
        for y, label, quantity, price in [(700, 'Cedar', '12.5', '64.00'), (680, 'Compost', '3.25', '88.00')]:
            c.drawString(50, y, label)
            c.drawString(260, y, quantity)
            c.drawString(430, y, price)
        c.drawString(40, 35, str(page))
        c.showPage()
    c.save()


if __name__ == '__main__':
    main()
