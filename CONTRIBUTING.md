# Contributing

Start with a specific table relationship that a current parser loses. Include the parser version/configuration, a minimal original or explicitly redistributable PDF, expected headers/rows, and the unmodified output. Do not upload confidential documents, credentials or third-party bug attachments without permission.

Add a small `cases/*.json` rule file and explain the exact scope. Include a positive control. Missing data, unsupported structures or ambiguity must not pass. Preserve decimal strings, signs, leading zeros and units; do not silently normalize a mismatch away.

Run `python -m unittest discover -s tests -v`. If changing parsing or rule behavior, add a meaningful counterexample. For a converter reproduction install `requirements-validation.lock` and run `python -m scripts.run_converters --output artifacts/your-run`. Do not replace recorded results just to make CI green; review the changed source/output and document it.

The project is a small regression kit, not a leaderboard or universal PDF verifier. Contributions should keep that boundary clear.
