import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from table_traps.core import evaluate, parse_input, validate_rules
from table_traps.report import render_report

ROOT = Path(__file__).resolve().parents[1]
GOOD = "| Material | Unit price |\n| --- | --- |\n| Cedar | 64.00 |\n| Compost | 88.00 |\n"
RULES = {"version": 1, "name": "control", "checks": [
    {"id": "price", "kind": "cell", "table": 1, "row_key": "Material", "row": "Cedar", "column": "Unit price", "equals": "64.00"}]}


class Checks(unittest.TestCase):
    def run_check(self, text, rules=RULES):
        return evaluate(parse_input(text), rules)

    def test_swapped_prices_fail_even_when_every_number_survives(self):
        bad = GOOD.replace("64.00", "TEMP").replace("88.00", "64.00").replace("TEMP", "88.00")
        self.assertIn("64.00", bad)
        report = self.run_check(bad)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(report["findings"][0]["actual"], "88.00")

    def test_row_reorder_still_matches_key_but_duplicates_stay_unknown(self):
        reordered = GOOD.splitlines()[:2] + list(reversed(GOOD.splitlines()[2:]))
        self.assertEqual(self.run_check('\n'.join(reordered))["status"], "pass")
        self.assertEqual(self.run_check(GOOD + "| Cedar | 64.00 |\n")["status"], "unknown")

    def test_unknown_header_or_table_never_passes(self):
        self.assertEqual(self.run_check(GOOD.replace("Unit price", "Cost"))["status"], "unknown")
        self.assertEqual(self.run_check("There is no table; Cedar costs 64.00.")["status"], "unknown")
        duplicated = GOOD.replace("| Unit price |", "| Unit price | Unit price |").replace("| --- | --- |", "| --- | --- | --- |")
        self.assertEqual(self.run_check(duplicated)["status"], "unknown")

    def test_fenced_pseudo_table_not_counted_and_empty_document_unknown(self):
        parsed = parse_input("```md\n" + GOOD + "```\n")
        self.assertEqual(parsed["tables"], [])
        rules = {"version": 1, "name": "prose", "checks": [{"id": "count", "kind": "table_count", "equals": 0}]}
        self.assertEqual(self.run_check("Ordinary prose.", rules)["status"], "pass")
        self.assertEqual(self.run_check("", rules)["status"], "unknown")

    def test_numeric_format_and_units_are_not_coerced(self):
        for wrong in ["64", "64.0", "$64.00", "064.00", "64,00"]:
            with self.subTest(wrong=wrong):
                self.assertEqual(self.run_check(GOOD.replace("64.00", wrong))["status"], "fail")
        self.assertEqual(self.run_check(GOOD.replace("Cedar", "**Cedar**").replace("64.00", "`64.00`"))["status"], "pass")

    def test_escaped_pipe_is_one_cell_and_html_is_not_silently_ignored(self):
        rules = copy.deepcopy(RULES); rules['checks'][0]['row'] = 'Cedar | fine'
        self.assertEqual(self.run_check(GOOD.replace('Cedar', r'Cedar \| fine'), rules)["status"], "pass")
        self.assertEqual(self.run_check(GOOD.replace("64.00", "<b>64.00</b>"))["status"], "unknown")
        self.assertEqual(self.run_check('<table><tr><td>64.00</td></tr></table>')["status"], "unknown")

    def test_bad_rule_schema_never_becomes_an_empty_success(self):
        for mutation in [{**RULES, "checks": []}, {**RULES, "version": True}, {**RULES, "unrecognised": True}]:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                validate_rules(mutation)

    def test_json_table_cells_keep_strings_and_ragged_rows_need_review(self):
        with self.assertRaises(ValueError):
            parse_input('{"tables":[[["bad"],[64.00]]]}', "tables-json")
        parsed = parse_input(json.dumps({"tables": [[["Material", "Unit price"], ["Cedar"]]]}), "tables-json")
        self.assertEqual(evaluate(parsed, RULES)["status"], "unknown")

    def test_untrusted_strings_are_escaped_in_export(self):
        rules = copy.deepcopy(RULES); rules['name'] = '</h2><script>alert(1)</script>'
        parsed = parse_input(GOOD); report = evaluate(parsed, rules)
        html = render_report(report, parsed, '<script>window.stolen=true</script>')
        self.assertNotIn('<script>alert(1)', html)
        self.assertNotIn('<script>window.stolen', html)
        self.assertIn('&lt;script&gt;', html)

    def test_measured_converter_outputs_have_expected_bounded_results(self):
        outcomes = {}
        for name in ['ruled', 'borderless', 'prose']:
            rules = json.loads((ROOT/'cases'/f'{name}.json').read_text())
            for engine, ext, fmt in [('markitdown', 'md', 'markdown'), ('pdfplumber', 'json', 'tables-json')]:
                raw = (ROOT/'measured'/f'{name}.{engine}.{ext}').read_text()
                outcomes[(name, engine)] = evaluate(parse_input(raw, fmt), rules)['status']
        self.assertEqual(outcomes, {('ruled', 'markitdown'): 'fail', ('ruled', 'pdfplumber'): 'pass',
                                   ('borderless', 'markitdown'): 'fail', ('borderless', 'pdfplumber'): 'fail',
                                   ('prose', 'markitdown'): 'pass', ('prose', 'pdfplumber'): 'pass'})

    def test_cli_reports_failure_and_preserves_input_and_existing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); source = p/'input.md'; rules = p/'rules.json'; out = p/'report.json'
            source.write_bytes(GOOD.replace('64.00', '65.00').replace('\n', '\r\n').encode())
            rules.write_text(json.dumps(RULES))
            cmd = [sys.executable, '-m', 'table_traps', 'check', '--input', str(source), '--rules', str(rules), '--json', str(out)]
            result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            report = json.loads(out.read_text())
            self.assertEqual(report['input_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
            before = out.read_bytes()
            again = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(again.returncode, 3)
            self.assertEqual(out.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
