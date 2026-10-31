import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.positional_table import extract, inspect_page
from table_traps.core import evaluate, parse_input

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / 'fixtures' / 'positional-two-page.pdf'
REGION = [0, 60, 612, 500]
EDGES = [0, 200, 350, 612]
HEADERS = ['Material', 'Quantity', 'Unit price']


class PositionalTableTests(unittest.TestCase):
    def test_coordinate_inspection_lists_actual_words_on_requested_page(self):
        page = inspect_page(PDF, 2)
        cedar = [word for word in page['words'] if word['text'] == 'Cedar']
        self.assertEqual(page['page_bbox'], [0, 0, 612, 792])
        self.assertEqual(len(cedar), 1)
        self.assertAlmostEqual(cedar[0]['x0'], 50)
        with self.assertRaisesRegex(ValueError, 'outside the PDF'):
            inspect_page(PDF, 3)

    def test_two_pages_match_critical_cells_and_preserve_page_evidence(self):
        table, evidence = extract(PDF, REGION, EDGES, HEADERS)
        self.assertEqual(len(table['tables']), 2)
        for page in table['tables']:
            self.assertEqual(page, [HEADERS, ['Cedar', '12.5', '64.00'], ['Compost', '3.25', '88.00']])
        self.assertEqual([row['page'] for row in evidence['rows']], [1, 1, 2, 2])
        rules = {'version': 1, 'name': 'source-checked sample', 'checks': [
            {'id': f'cedar-{n}', 'kind': 'cell', 'table': n, 'row_key': 'Material',
             'row': 'Cedar', 'column': 'Unit price', 'equals': '64.00'} for n in (1, 2)]}
        report = evaluate(parse_input(json.dumps(table), 'tables-json'), rules)
        self.assertEqual(report['status'], 'pass')

    def test_edges_cannot_cut_words_and_missing_pages_do_not_pass(self):
        with self.assertRaisesRegex(ValueError, 'crosses a column edge'):
            extract(PDF, REGION, [0, 55, 350, 612], HEADERS)
        with self.assertRaisesRegex(ValueError, 'No words found'):
            extract(PDF, [0, 200, 612, 300], EDGES, HEADERS)
        with self.assertRaisesRegex(ValueError, 'outside page'):
            extract(PDF, [0, 0, 700, 500], [0, 200, 350, 700], HEADERS)
        with self.assertRaisesRegex(ValueError, 'Column edges'):
            extract(PDF, REGION, [0, 350, 200, 612], HEADERS)
        with self.assertRaisesRegex(ValueError, 'tolerance'):
            extract(PDF, REGION, EDGES, HEADERS, float('nan'))

    def test_cli_writes_two_new_files_and_refuses_to_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            output, evidence = Path(directory) / 'table.json', Path(directory) / 'evidence.json'
            cmd = [sys.executable, str(ROOT / 'scripts' / 'positional_table.py'), str(PDF),
                   '--region', '0,60,612,500', '--edges', '0,200,350,612',
                   '--headers', 'Material,Quantity,Unit price', '--output', str(output), '--evidence', str(evidence)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            before = output.read_bytes(), evidence.read_bytes()
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(before, (output.read_bytes(), evidence.read_bytes()))
            self.assertEqual(json.loads(output.read_text())['tables'][1][1][2], '64.00')


if __name__ == '__main__':
    unittest.main()
