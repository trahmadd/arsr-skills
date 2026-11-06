# AGENTS.md - arsr-skills

Repository for building an Annual Report (AR) and Sustainability Report (SR) in Adobe InDesign from Markdown data, by any AI agent.
This file and all skills are written in English. Report data is bilingual (Indonesian + English).

## Start here

1. Load skill `arsr-start` (the router).
2. Load only the one skill that matches the task. Do not load every skill.
3. Read reference files only when a skill tells you to.

## Hard rules (never break)

1. Never invent GRI, OJK or SEOJK codes. Use only codes listed in `catalogs/*.md`. A code not in a catalog is a validation error.
2. Company data lives only in Markdown under a project `data/` folder. Never put company data in scripts.
3. Never write inline tags (`<e>`, `<id>`, `<b>` ...) in data. The build adds them.
4. ExtendScript (JSX) is ES3. Forbidden: `let`, `const`, arrow functions, template strings, `JSON`, `forEach/map/filter/reduce`, `String.trim`, trailing commas, `Object.keys`. Use `var`, `for` loops, `try/catch`.
5. Validators and QA scripts are read-only. They never edit documents or data. Their only output is a log file in `<project>/logs/`.
6. Content that is not real must carry `dummy: ya`. Dummy content must never copy verifiable facts (real people, certificate numbers, audit figures, quotes).
7. One change, one check: after any edit, rerun validation and read the log before continuing.
8. Do not guess when a catalog row has `verified: no`. Report it as a warning and ask the user to verify against the official text.

## Layout

| Path | Purpose | State |
|---|---|---|
| `.opencode/skills/` | Skills (OpenCode format, one folder per skill) | `arsr-start`, `arsr-import-word`, `arsr-data-spec`, `indesign-jsx-basics`, `arsr-style-system`, `arsr-validate-qa`, `arsr-build-test` |
| `catalogs/` | Numbering catalogs (GRI, OJK, SEOJK) and regulation profiles | done |
| `templates/dummy-company/` | Fictional company config (chapters are generated) | done |
| `structures/` | Chapters and required pages per report type (`lk.md`, `lt.md`, `lt-lk.md`) | done |
| `docs/penulisan-word.md`, `templates/contoh-word/` | Word writing guide and example file for copywriters | done |
| `engine/` | Python: parse, validate, dummy, plan (R2/R3). `engine/jsx/build_report.jsx`, `qa_document.jsx` (R3, untested in real InDesign) | R3 done, R4 skills done (evals R5) |
| `evals/` + `tools/eval_check.py` | R5 tasks E1-E6 for testing skills on free OpenCode models | done |
| `tools/jsx_lint.py` | Static ES3 linter for JSX (`python tools/jsx_lint.py engine/jsx`) | done |
| `tools/indesign_run.ps1` | Runs a JSX in InDesign through COM (untested on real InDesign until confirmed) | new |

## Build rule
Run `<project>/build/run_build.jsx` once per change, with `powershell -ExecutionPolicy Bypass -File tools/indesign_run.ps1 <project>/build/run_build.jsx` (COM; no manual step). It shows no dialog; read the logs in `<project>/logs/`. Never loop on it. If COM fails, ask the user to run the launcher from the Scripts panel.

## Commands (Python 3.8+, standard library only)

```
python engine/run.py new <folder> --jenis LK|LT|LT+LK --divider 1|2   # project folders + dummy data (dummy = same)
python engine/run.py import <project_dir>      # Word/Excel in source/ -> data/*.md
python engine/run.py validate <project_dir>    # read-only; log goes to `<project>/logs/`
python engine/run.py plan <project_dir>        # writes build/build_plan.json + run_build.jsx, run_qa.jsx; run run_build.jsx in InDesign once
python tools/jsx_lint.py engine/jsx            # ES3 check of JSX files
python -m unittest discover -s tests           # engine tests
```

A project folder contains `data/` (config + chapter files), `source/` (copywriter Word/Excel), `build/` and `logs/`. Keep it outside the repo. Read the log, fix the first ERROR, rerun.

## Phases

R1 spec + catalogs + config | R2 Python parser/validator/dummy | R3 JSX build + read-only QA | R4 all skills + linter | R5 evals on OpenCode. Each phase ends with a user check before the next starts.

## Conventions

- Skill ids: lowercase kebab-case, equal to the folder name.
- Data keys are Indonesian (`judul.id`, `isi.en`, `tipe`, `sumber`); code, comments and skills are English.
- Log files: written to `<project>/logs/`, plain text, first line is a one-line summary with counts.
