"""Generate two original synthetic multi-page inventory tables and convert them locally."""
import argparse
import json
from pathlib import Path
from importlib.metadata import version

import anydoc
from reportlab.pdfgen import canvas

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True, type=Path, help='new directory for generated files')
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=False)

for repeat in (False, True):
    stem = 'repeat-header' if repeat else 'single-header'
    path = args.output / (stem + '.pdf')
    pdf = canvas.Canvas(str(path), pagesize=(612, 792), invariant=1)
    pdf.setTitle('Synthetic nursery inventory')
    headers = ['Item', 'Zone', 'Count', 'Price']
    edges = [45, 210, 320, 430, 565]
    for page in range(3):
        rows = [headers] if page == 0 or repeat else []
        for r in range(8):
            n = page * 8 + r + 1
            rows.append([f'Plant-{n:02}', f'Z{n%3+1}', str(20+n), f'{n+1}.25'])
        y = 730
        for row in rows:
            for i, cell in enumerate(row):
                pdf.rect(edges[i], y-5, edges[i+1]-edges[i], 23)
                pdf.setFont('Helvetica', 10)
                pdf.drawString(edges[i]+5, y+2, cell)
            y -= 23
        pdf.showPage()
    pdf.save()
    markdown = anydoc.to_markdown(str(path))
    (args.output / (stem + '.md')).write_text(markdown, encoding='utf-8')

checks = [{'id': f'plant-{n:02}-count', 'kind': 'cell', 'table': 1,
           'row_key': 'Item', 'row': f'Plant-{n:02}', 'column': 'Count',
           'equals': str(20+n)} for n in (1, 9, 17)]
(args.output / 'rules.json').write_text(
    json.dumps({'version': 1, 'name': 'Three page-start rows', 'checks': checks}, indent=2) + '\n',
    encoding='utf-8')
print(json.dumps({'anydoc': version('firecrawl-anydoc'), 'reportlab': version('reportlab'),
                  'files': str(args.output)}))
