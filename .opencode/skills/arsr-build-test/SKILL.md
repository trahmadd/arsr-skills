---
name: arsr-build-test
description: Build the InDesign document from a validated project and test it - plan generation, running build_report.jsx (COM or manual), mock tests, reading the build log, fixing errors from the real InDesign. Use when the user wants to build, rebuild or debug the document.
---

# arsr-build-test

## Pipeline

1. `python engine/run.py validate <project>` -> ERROR 0.
2. `python engine/run.py plan <project>` -> `<project>/build/build_plan.json` and pointer `%APPDATA%\ARSR\last_plan.txt`.
3. In InDesign: File > Scripts > Scripts Panel > Scripts Panel folder... open the `engine/jsx` folder (or double-click `build_report.jsx`). It finds the plan through the pointer file; if none, it asks for the file.
4. Read `Desktop/ARSR_Build_Log.txt`. `Desktop/Dummy_Register.txt` lists dummy items.
5. Run `qa_document.jsx` on the result (see `arsr-validate-qa`).

Optional automation from Python on Windows: `win32com.client.Dispatch('InDesign.Application')` then `DoScript(path, 1246973031)` (ScriptLanguage.JAVASCRIPT). Not required; manual run is the baseline.

## Developing without InDesign
- `python tools/jsx_lint.py engine/jsx` (ES3 rules).
- `python -m unittest discover -s tests` runs a Node mock of the DOM (`tests/mock_indesign.js`) that executes the build flow. It proves logic and tag balance, not InDesign API names.
- Install Node 18+ for the mock test; without it the test is skipped.

## Fixing a real-InDesign error
1. Copy the first ERROR line from the build log.
2. Locate `where` in `build_report.jsx`; make one minimal change.
3. Lint, test, run again in InDesign. Record any API name correction in `.opencode/skills/indesign-jsx-basics/references/pitfalls.md`.
4. Do not rewrite the build; do not add project data to the script.

## Honest status
`build_report.jsx` and `qa_document.jsx` were written without a real InDesign. Expect first-run errors in enum names, tints, numbering styles and corner options; each is isolated by `safe()` and logged.
