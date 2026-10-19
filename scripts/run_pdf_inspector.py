"""Measure one pinned, local pdf-inspector integration on our original fixtures."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

from table_traps.core import evaluate, parse_input

ROOT = Path(__file__).resolve().parents[1]
VERSION = '1.25.2'
EXPECTED = [
    ('pass', {'pass': 4, 'fail': 0, 'unknown': 0}),
    ('fail', {'pass': 1, 'fail': 3, 'unknown': 0}),
    ('pass', {'pass': 1, 'fail': 0, 'unknown': 0}),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect-observed', action='store_true',
                        help='Require the recorded assertion outcomes, not universal converter accuracy.')
    args = parser.parse_args()
    try:
        version = importlib.metadata.version('pdf-inspector')
    except importlib.metadata.PackageNotFoundError:
        parser.error('Install the optional requirements-inspector.txt dependencies first.')
    if version != VERSION:
        parser.error(f'This integration records pdf-inspector {VERSION}; installed {version}.')
    import pdf_inspector

    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for name in ['ruled', 'borderless', 'prose']:
        source = ROOT/'fixtures'/f'{name}.pdf'
        result = pdf_inspector.process_pdf(str(source))
        raw = result.markdown or ''
        filename = f'{name}.pdf-inspector.md'
        (args.output/filename).write_bytes(raw.encode('utf-8'))
        rules = json.loads((ROOT/'cases'/f'{name}.json').read_text(encoding='utf-8'))
        report = evaluate(parse_input(raw, 'markdown'), rules, filename)
        (args.output/f'{name}.report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        results.append({
            'case': name, 'status': report['status'], 'counts': report['counts'],
            'pdf_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'output_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(),
            'pdf_type': result.pdf_type, 'page_count': result.page_count,
        })
    record = {
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'engine': 'pdf-inspector', 'version': version,
        'python': platform.python_version(), 'platform': platform.system(), 'machine': platform.machine(),
        'entrypoint': 'process_pdf(path), default local non-OCR; no credentials or OCR runtime supplied.',
        'scope': 'Three original synthetic fixtures and supplied checks, not a representative accuracy ranking.',
        'results': results,
    }
    (args.output/'run.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, indent=2))
    observed = [(r['status'], r['counts']) for r in results]
    if args.expect_observed and observed != EXPECTED:
        raise SystemExit('Observed outcomes changed. Inspect raw outputs; do not silently rewrite expectations.')


if __name__ == '__main__':
    main()
