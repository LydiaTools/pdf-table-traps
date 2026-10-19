"""Run two local, default extraction paths on the committed synthetic PDFs."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time

import pdfplumber
from markitdown import MarkItDown

from table_traps.core import evaluate, parse_input

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-observed', action='store_true', help='Check the six recorded smoke outcomes, not converter accuracy.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    engine = MarkItDown(enable_plugins=False)
    results = []
    for name in ['ruled', 'borderless', 'prose']:
        source = ROOT/'fixtures'/f'{name}.pdf'
        rules = json.loads((ROOT/'cases'/f'{name}.json').read_text())
        start = time.perf_counter()
        markdown = engine.convert_local(source, file_extension='.pdf').markdown
        with pdfplumber.open(source) as pdf:
            tables = [table for page in pdf.pages for table in page.extract_tables()]
        outputs = [('markitdown', 'md', markdown, 'markdown'),
                   ('pdfplumber', 'json', json.dumps({'tables': tables}, indent=2) + '\n', 'tables-json')]
        for label, extension, raw, fmt in outputs:
            filename = f'{name}.{label}.{extension}'
            (args.output/filename).write_text(raw, encoding='utf-8')
            report = evaluate(parse_input(raw, fmt), rules, filename)
            (args.output/f'{name}.{label}.report.json').write_text(json.dumps(report, indent=2) + '\n')
            results.append({'case': name, 'engine': label, 'status': report['status'], 'counts': report['counts'],
                            'pdf_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                            'output_sha256': hashlib.sha256(raw.encode()).hexdigest(),
                            'case_wall_seconds': round(time.perf_counter() - start, 4)})
    record = {'captured_at': datetime.now(timezone.utc).isoformat(),
              'versions': {key: importlib.metadata.version(key) for key in ['markitdown', 'pdfplumber', 'pdfminer-six', 'magika', 'markdown-it-py']},
              'mode': 'Local defaults, plugins disabled; no LLM client, credentials or remote API supplied.',
              'scope': 'Three synthetic cases; these results are not a representative accuracy ranking.', 'results': results}
    (args.output/'run.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))
    expected = ['fail', 'pass', 'fail', 'fail', 'pass', 'pass']
    if args.expect_observed and [r['status'] for r in results] != expected:
        raise SystemExit('Observed smoke outcomes changed. Inspect evidence instead of updating expectations blindly.')


if __name__ == '__main__':
    main()
