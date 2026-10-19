import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from .core import MAX_BYTES, evaluate, parse_input
    from .report import render_report
except ModuleNotFoundError as error:
    print(json.dumps({"status": "error", "message": "Install dependencies: python -m pip install -r requirements.txt", "missing_module": error.name}), file=sys.stderr)
    raise SystemExit(3)


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(3, f"error: {message}\n")


def read(path):
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Input exceeds 2 MiB.")
    return path.read_bytes().decode("utf-8")


def main():
    parser = Parser(description="Check explicit row/header/value assertions in converted tables.")
    parser.add_argument("command", choices=["check"])
    parser.add_argument("--rules", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--format", choices=["markdown", "tables-json"], default="markdown")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    try:
        inputs = {args.input.resolve(), args.rules.resolve()}
        outputs = [p for p in [args.json, args.html] if p]
        if len({p.resolve() for p in outputs}) != len(outputs):
            raise ValueError("JSON and HTML outputs must be distinct.")
        if any(p.resolve() in inputs or p.exists() for p in outputs):
            raise ValueError("Output must be a new file and must not replace an input.")
        raw = read(args.input)
        rules = json.loads(read(args.rules))
        parsed = parse_input(raw, args.format)
        report = evaluate(parsed, rules, args.input.name)
        report["input_sha256"] = hashlib.sha256(raw.encode()).hexdigest()
        for path, content in [(args.json, json.dumps(report, ensure_ascii=False, indent=2) + "\n"),
                              (args.html, render_report(report, parsed, raw))]:
            if path:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('x', encoding='utf-8') as handle:
                    handle.write(content)
        print(json.dumps({"status": report["status"], "counts": report["counts"], "input": args.input.name}))
        return {"pass": 0, "fail": 1, "unknown": 2}[report["status"]]
    except (ValueError, OSError, RecursionError) as error:
        print(json.dumps({"status": "error", "message": str(error)[:500]}), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
