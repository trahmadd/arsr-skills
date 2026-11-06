---
name: arsr-build-test
description: Build the InDesign document from a validated project and test it - plan generation, running build_report.jsx (COM or manual), mock tests, reading the build log, fixing errors from the real InDesign. Use when the user wants to build, rebuild or debug the document.
---

# arsr-build-test

## Pipeline

1. `python engine/run.py validate <project>` -> ERROR 0.
2. `python engine/run.py plan <project>` -> `<project>/build/build_plan.json`, the launchers `<project>/build/run_build.jsx` and `run_qa.jsx`, and the pointer `%APPDATA%\ARSR\last_plan.txt`.
3. Run the launcher in InDesign. DEFAULT for an agent on Windows (no manual step):
   `powershell -ExecutionPolicy Bypass -File tools/indesign_run.ps1 <project>/build/run_build.jsx`
   It starts InDesign through COM, runs the file with DoScript, blocks dialogs, and returns when done. Output `OK:` = it ran; `ERROR:` = read the message.
   Fallback when COM fails (exit code 2 or an error): ask the user to copy the launcher into `%APPDATA%\Adobe\InDesign\Version <n>\en_US\Scripts\Scripts Panel` and double-click it in the Scripts panel.
   The launcher names this project's plan, so no pointer or dialog is needed.
4. Read `<project>/logs/ARSR_Build_Log.txt`. `<project>/logs/Dummy_Register.txt` lists dummy items.
5. Run QA the same way: `... tools/indesign_run.ps1 <project>/build/run_qa.jsx` (see `arsr-validate-qa`).

A run ends with exit code 0 even if the build logged errors: always read `ARSR_Build_Done.txt`.

## Run the build ONCE
- The build creates ONE new document. Run it a single time, then read `<project>/logs/ARSR_Build_Done.txt` (first line DONE OK or DONE WITH ERRORS) and `<project>/logs/ARSR_Build_Log.txt`.
- There is no popup. Never run again to "verify" or "wait for the popup"; a second run is skipped while a built document is open.
- Rerun only after you changed code or data because of an ERROR in the log. Close the old document first (or `$.global.ARSR_FORCE = true`).
- Look at the result in InDesign (Pages panel and a few spreads) before declaring success: items must sit inside their pages and text must be normal size.

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
