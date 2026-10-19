# Design decision

Audience: a developer maintaining a PDF-to-Markdown pipeline. First task: see which explicit row/header/value assertion failed, compare the original source, then reproduce the check locally.

This is a test kit with a measured report viewer, not another converter or annotation workbench. ParseArena already supplies broad side-by-side parser evaluation; OmniDocBench supplies a much broader annotated benchmark. Our small contribution is an easy-to-reproduce set of original traps and exact semantic-pair checks, with no model or converter required to inspect saved outputs.

- Ink `#173D34`, pale green `#EAF0E9`, paper `#FAFCF8`, boundary `#BECBBF`, mismatch `#A52F37`, review `#846013`.
- Avenir Next / Segoe UI for the report; system monospace only for raw output. No remote fonts or images.
- Compact utility header; sample and engine selectors; failures first; PDF excerpt on the left and exact expected/observed values plus parsed table on the right. On phones the source and results stack.
- The memorable element is a number under the wrong header, highlighted in the actual parsed output. No decorative statistics, generated product imagery or pretend results.

Review of the first plan: a large full-page PDF would shrink the table into unreadable text. The default source view therefore uses a clearly labelled, unaltered PDF region rendered directly from the source page. The full original PDF remains downloadable. Do not paint labels over the source or move values; red cells belong only to the parsed-output table.

Report labels are bilingual. Source fixture text stays as authored. All user-supplied strings are escaped; file contents never become executable HTML. The demo is a viewer for measured outputs, not a live parser, and must say so.
