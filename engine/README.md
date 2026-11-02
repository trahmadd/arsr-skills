# engine/

Python 3.8+, standard library only. No InDesign needed for anything here.

| File | Role |
|---|---|
| `run.py` | CLI: `validate <project>`, `dummy <out>` |
| `arsr/mdparse.py` | Parse `00_config.md` and chapter files |
| `arsr/catalog.py` | Load `catalogs/*.md` and profiles |
| `arsr/validate.py` | Config, structure, table and number checks (read-only) |
| `arsr/regrules.py` | GRI / OJK rules from the active profile |
| `arsr/report.py` | Log writer (Desktop, OneDrive Desktop, or `--log-dir`) |
| `arsr/dummy.py` | Fictional 80-page data set with one consistent fact table |
| `arsr/numfmt.py` | `1.234,5` / `1,234.5` parsing and formatting |

Planned R3: `jsx/build_report.jsx` (reads `build_plan.json`), `jsx/qa_document.jsx` (read-only), `arsr/plan.py`.
