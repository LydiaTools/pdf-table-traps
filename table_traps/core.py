import json
import re
import unicodedata

from markdown_it import MarkdownIt

MAX_BYTES = 2 * 1024 * 1024
MAX_TABLES = 100
MAX_ROWS = 1000
MAX_COLUMNS = 100
MAX_CHECKS = 200


def normal(value):
    """NFC and whitespace only: never coerce numbers, punctuation, units or case."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def validate_tables(tables):
    if not isinstance(tables, list) or len(tables) > MAX_TABLES:
        raise ValueError("Expected at most 100 table matrices.")
    for table in tables:
        if not isinstance(table, list) or not table or len(table) > MAX_ROWS:
            raise ValueError("Each table needs a header and at most 999 data rows.")
        for row in table:
            if not isinstance(row, list) or len(row) > MAX_COLUMNS:
                raise ValueError("Each row must be an array with at most 100 cells.")
            if any(value is not None and not isinstance(value, str) for value in row):
                raise ValueError("Cells must be strings or null. Numeric JSON values lose formatting evidence.")
            if any(isinstance(value, str) and len(value) > 20000 for value in row):
                raise ValueError("Cell text exceeds 20,000 characters.")
    return [[[(value or "") for value in row] for row in table] for table in tables]


def parse_markdown(text):
    tokens = MarkdownIt("commonmark").enable("table").parse(text)
    tables, maps, unsupported = [], [], []
    table, row = None, None
    for token in tokens:
        if token.type == "html_block" and re.search(r"<table\b", token.content, re.I):
            unsupported.append("Raw HTML tables require conversion to explicit table matrices.")
        if token.type == "table_open":
            table = []
            maps.append([n + 1 for n in token.map] if token.map else None)
        elif token.type == "tr_open" and table is not None:
            row = []
        elif token.type == "inline" and table is not None and row is not None:
            parts = []
            for child in token.children or []:
                if child.type in ("text", "code_inline"):
                    parts.append(child.content)
                elif child.type in ("softbreak", "hardbreak"):
                    parts.append(" ")
                elif child.type == "html_inline":
                    if re.fullmatch(r"<br\s*/?>", child.content, re.I):
                        parts.append(" ")
                    else:
                        unsupported.append("Unsupported inline HTML in a table cell.")
                elif child.type == "image":
                    unsupported.append("Image-only cell content needs manual interpretation.")
            row.append("".join(parts))
        elif token.type == "tr_close" and table is not None:
            table.append(row)
            row = None
        elif token.type == "table_close":
            tables.append(table)
            table = None
    return {"tables": validate_tables(tables), "line_ranges": maps,
            "unsupported": sorted(set(unsupported)), "format": "markdown"}


def parse_input(text, kind="markdown"):
    if len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Input exceeds 2 MiB.")
    if kind == "markdown":
        parsed = parse_markdown(text)
        if not text.strip():
            parsed["unsupported"].append("Empty converted document.")
        return parsed
    if kind == "tables-json":
        data = json.loads(text)
        if not isinstance(data, dict) or set(data) != {"tables"}:
            raise ValueError('Expected exactly {"tables": [header-and-row matrices]}.')
        return {"tables": validate_tables(data["tables"]), "line_ranges": [],
                "unsupported": [], "format": "tables-json"}
    raise ValueError("Unsupported input format.")


def validate_rules(rules):
    if not isinstance(rules, dict) or set(rules) != {"version", "name", "checks"} or type(rules["version"]) is not int or rules["version"] != 1:
        raise ValueError("Expected rule version 1 with name and checks; unknown fields are rejected.")
    if not isinstance(rules["name"], str) or not 1 <= len(rules["name"]) <= 200:
        raise ValueError("Rule name must contain 1-200 characters.")
    checks = rules["checks"]
    if not isinstance(checks, list) or not 1 <= len(checks) <= MAX_CHECKS:
        raise ValueError("A rule file needs 1-200 explicit checks; empty suites never pass.")
    ids = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("Each check must be an object.")
        ident = check.get("id")
        if not isinstance(ident, str) or not 1 <= len(ident) <= 100 or ident in ids:
            raise ValueError("Check IDs must be unique strings with 1-100 characters.")
        ids.add(ident)
        if check.get("kind") == "table_count":
            if set(check) != {"id", "kind", "equals"} or type(check["equals"]) is not int or not 0 <= check["equals"] <= MAX_TABLES:
                raise ValueError("table_count requires an integer equals between 0 and 100.")
        elif check.get("kind") == "cell":
            keys = {"id", "kind", "table", "row_key", "row", "column", "equals"}
            if set(check) != keys or type(check["table"]) is not int or not 1 <= check["table"] <= MAX_TABLES:
                raise ValueError("A cell check requires table (1-based), row_key, row, column and equals.")
            for field in ["row_key", "row", "column", "equals"]:
                value = check[field]
                if not isinstance(value, str) or len(value) > 2000 or (field != "equals" and not normal(value)):
                    raise ValueError("Cell selectors must be nonempty strings; expected values are strings.")
        else:
            raise ValueError("Unknown check kind.")
    return rules


def evaluate(parsed, rules, source_name="input"):
    validate_rules(rules)
    findings = []
    for check in rules["checks"]:
        item = {"id": check["id"], "kind": check["kind"], "expected": check["equals"],
                "actual": None, "status": "unknown", "reason": "", "selector": dict(check)}
        if parsed["unsupported"]:
            item["reason"] = "unsupported_structure"
        elif check["kind"] == "table_count":
            item["actual"] = len(parsed["tables"])
            item["status"] = "pass" if item["actual"] == check["equals"] else "fail"
            item["reason"] = "table_count_match" if item["status"] == "pass" else "table_count_mismatch"
        elif check["table"] > len(parsed["tables"]):
            item["reason"] = "table_missing"
        else:
            table = parsed["tables"][check["table"] - 1]
            headers = [normal(x) for x in table[0]]
            row_keys = [i for i, x in enumerate(headers) if x == normal(check["row_key"])]
            columns = [i for i, x in enumerate(headers) if x == normal(check["column"])]
            if len(row_keys) != 1 or len(columns) != 1:
                item["reason"] = "header_missing_or_ambiguous"
            else:
                matches = [(i, row) for i, row in enumerate(table[1:], 1)
                           if len(row) > row_keys[0] and normal(row[row_keys[0]]) == normal(check["row"])]
                if len(matches) != 1:
                    item["reason"] = "row_missing_or_ambiguous"
                else:
                    index, row = matches[0]
                    if len(row) != len(headers):
                        item["reason"] = "ragged_row"
                    else:
                        item["actual"] = row[columns[0]]
                        item["location"] = {"table": check["table"], "row": index, "column": columns[0]}
                        item["status"] = "pass" if normal(item["actual"]) == normal(check["equals"]) else "fail"
                        item["reason"] = "cell_match" if item["status"] == "pass" else "cell_mismatch"
        findings.append(item)
    counts = {state: sum(x["status"] == state for x in findings) for state in ["pass", "fail", "unknown"]}
    status = "fail" if counts["fail"] else "unknown" if counts["unknown"] else "pass"
    return {"schema_version": 1, "suite": rules["name"], "source_name": source_name,
            "status": status, "counts": counts, "parsed_table_count": len(parsed["tables"]),
            "findings": findings, "unsupported": parsed["unsupported"],
            "scope": "Only user-supplied checks under NFC/whitespace normalization. Not document-wide accuracy, source verification, OCR or certification."}
