---
name: arsr-start
description: Entry point for building an Annual Report or Sustainability Report (AR/SR, GRI, OJK) in Adobe InDesign from Markdown data. Use first for any task in this repo - new project, editing report data, regulation numbering, or fixing a validation or InDesign error.
---

# arsr-start

Router. Pick the row that matches the user's goal, then load only that skill.

| Goal | Do |
|---|---|
| New report for a company | copy `templates/dummy-company/data/00_config.md`, edit it, then `python engine/run.py new <folder> --jenis LK\|LT\|LT+LK --divider 1\|2 --config <your_config.md>`; load `arsr-data-spec` |
| Copywriter gives Word / Excel files | Load `arsr-import-word` |
| Write or fix report data (Markdown) | Load `arsr-data-spec` |
| Check GRI / OJK / SEOJK numbering | Read `catalogs/README.md`, then the profile in `catalogs/profiles/` |
| Change design (colors, fonts, margins) | Change only `data/00_config.md`. Never edit the engine for a project-specific change |
| Add a regulation (new country or standard) | Add a catalog file + a profile following `catalogs/README.md` |
| Write or fix a JSX script / InDesign error | Load `indesign-jsx-basics` |
| Change styles, tags, tables, page templates | Load `arsr-style-system` |
| Run validation or document QA, read a log | Load `arsr-validate-qa` |
| Build the document / debug the build | Load `arsr-build-test` |

## Steps for a new project

1. Ask for: company name, report year, publication year, theme, palette (10 swatch hex values), main font, language pair.
2. Copy `templates/dummy-company/data/00_config.md` to your own file and fill it first (name, year, theme, palette, font). Choose the report type (`--jenis LK` sustainability, `LT` annual, `LT+LK` integrated; chapters come from `structures/`) and the chapter divider (`--divider 1` one page, `2` two facing pages; default 2). Then create the project: `python engine/run.py new <new_folder> --jenis LT+LK --divider 2 --config <your_config.md>`. It makes `data/ source/ build/ logs/`. The year and names flow into every chapter and table column. Keep the engine and catalogs untouched.
   If you change `tahun-laporan` or the company name later, regenerate with `--force`; editing only the config leaves old year columns and the validator reports NUM-04.
3. Palette, fonts and margins can still be edited later in `<new_folder>/data/00_config.md` (no regeneration needed). Keep section names and table headers exactly as in the template.
4. Content: load `arsr-import-word` when the text arrives as Word/Excel (put it in `<folder>/source/`, run `import`), otherwise load `arsr-data-spec` and edit the chapter files.
5. Validate: `python engine/run.py validate <project_dir>`. Read `<project>/logs/ARSR_Validate_Log.txt`. Fix the first ERROR, rerun until 0 errors. WARN lines are reviewed, not ignored.

## Rules to remember

- Data is Markdown. Scripts hold no company data.
- Never invent regulation codes; use `catalogs/` only. `verified: no` rows give warnings, not facts.
- Validators are read-only; output is a log in `<project>/logs/`. The only thing they create is the empty `source/ build/ logs/` folders.
- Dummy content must be flagged `dummy: ya`.
- If the user's request is ambiguous about output format or scope, ask one short question; otherwise state your assumption and continue.
