---
name: arsr-start
description: Entry point for building an Annual Report or Sustainability Report (AR/SR, GRI, OJK) in Adobe InDesign from Markdown data. Use first for any task in this repo - new project, editing report data, regulation numbering, or fixing a validation or InDesign error.
---

# arsr-start

Router. Pick the row that matches the user's goal, then load only that skill.

| Goal | Do |
|---|---|
| New report for a company | `python engine/run.py dummy <new_folder>` (full fictional starter), edit `data/00_config.md`, then load `arsr-data-spec` |
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
2. Create the project folder with `python engine/run.py dummy <new_folder>`. Keep the engine and catalogs untouched. (The template folder alone has only the config and does not validate.)
3. Fill `data/00_config.md`. Keep section names and table headers exactly as in the template.
4. Load `arsr-data-spec` and fill or adapt chapter files.
5. Validate: `python engine/run.py validate <project_dir>`. Read `ARSR_Validate_Log.txt` on the Desktop. Fix the first ERROR, rerun until 0 errors. WARN lines are reviewed, not ignored.

## Rules to remember

- Data is Markdown. Scripts hold no company data.
- Never invent regulation codes; use `catalogs/` only. `verified: no` rows give warnings, not facts.
- Validators are read-only; output is a Desktop log.
- Dummy content must be flagged `dummy: ya`.
- If the user's request is ambiguous about output format or scope, ask one short question; otherwise state your assumption and continue.
