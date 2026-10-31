import json
from pathlib import Path
import unittest

from table_traps.core import evaluate, parse_input


CASE = Path(__file__).resolve().parents[1] / 'docs' / 'cases' / 'continuation'


class ContinuationCase(unittest.TestCase):
    def test_saved_converter_outputs_show_header_promotion(self):
        rules = json.loads((CASE / 'rules.json').read_text())
        for stem, status, counts, rows in [
            ('single', 'unknown', {'pass': 1, 'fail': 0, 'unknown': 2}, 22),
            ('repeat', 'pass', {'pass': 3, 'fail': 0, 'unknown': 0}, 24),
        ]:
            with self.subTest(case=stem):
                markdown = (CASE / (stem + '-header.md')).read_text()
                self.assertTrue(all(f'Plant-{n:02}' in markdown for n in range(1, 25)))
                parsed = parse_input(markdown)
                self.assertEqual(sum(len(table)-1 for table in parsed['tables']), rows)
                result = evaluate(parsed, rules)
                self.assertEqual(result['status'], status)
                self.assertEqual(result['counts'], counts)
                if stem == 'single':
                    self.assertEqual(parsed['tables'][1][0][0], 'Plant-09')
                    self.assertEqual(parsed['tables'][2][0][0], 'Plant-17')


if __name__ == '__main__':
    unittest.main()
