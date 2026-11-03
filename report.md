# Session Report — arsr-skills build/debug (InDesign)

Date: 2026-11-03 (session)
Repo: C:\Users\admin\Documents\repository\arsr-skills
Project: pt-contoh-laporan (80 pages, dummy)

## User requests
1. Invoked skill `arsr-start` (router).
2. Selected goal: Build/debug document.
3. Selected project: pt-contoh-laporan.
4. Interrupted during a build run; asked for a session report.

## Workflow summary

### 1. Entry / routing
- Loaded `arsr-start` then `arsr-build-test`.
- Checked repo status (clean, main branch).
- Inspected project folder and JSX files.

### 2. Validation and plan
- Ran: `python engine/run.py validate pt-contoh-laporan`
  - Result: ERROR 0 | WARN 2 | pages 80
  - Warnings: GRI-02 (85 unverified codes), OJK-09 (tahun-terbit != tahun-laporan + 1)
- Ran: `python engine/run.py plan pt-contoh-laporan`
  - Result: plan written, 80 pages, pointer `%APPDATA%\ARSR\last_plan.txt`

### 3. Static checks
- Ran: `python tools/jsx_lint.py engine/jsx` → 0 errors (1 warn in qa_document.jsx)
- Ran: `python -m unittest discover -s tests` → 36 tests OK (seeded-fault lines are expected)

### 4. InDesign automation (COM)
- Discovered InDesign (PID 29188) running; no Node.js; no pywin32.
- Used PowerShell COM (`InDesign.Application`) via `-ExecutionPolicy Bypass` to run `DoScript(..., 1246973031)`.
- Created helper scripts in temp:
  - `test_com.ps1` (connection test)
  - `run_build.ps1` (runs build_report.jsx)
  - `diag.jsx` + `run_diag.ps1` (DOM introspection)

### 5. Iterative fixes to `engine/jsx/build_report.jsx`
First real-InDesign run log: ERROR 1 (`NEVER_INTERACT_WITH_USER` line 581).

| # | Log error | Fix applied | Pitfall recorded |
|---|---|---|---|
| 1 | `UserInteractionLevels.NEVER_INTERACT_WITH_USER` (line 581) | `UserInteractionLevels.NEVER_INTERACT` | yes |
| 2 | `doc.lists` not found (line 243) | `doc.numberingLists` (add + itemByName) | yes |
| 3 | `masterSpread.name` read-only (line 309) | `ms.namePrefix = 'A'` | yes |
| 4 | `NumberingStyle.LOWERCASE_LETTERS` / `LOWERCASE_ROMAN` (line 244) | `LOWER_LETTERS` / `LOWER_ROMAN` | yes |
| 5 | `paragraphStyle.numberingList` not found (line 249) | `appliedNumberingList` | yes |

Also updated: `.opencode/skills/indesign-jsx-basics/references/pitfalls.md` with all five corrections.

### 6. Remaining issue
- Build log still shows: `ERROR | p2 | TOC overflows; add a daftar-isi page`.
- This is a layout/data condition, not an API-name error. The plan estimated TOC height at 435 mm (TOC_MM 9/6) but real InDesign overflowed; actual styles (`toc.bab` leading 11 + spaceBefore 3, two lines per entry) need more.
- Suggested next step: add a second `daftar-isi` page in `01_pendahuluan.md` and renumber subsequent pages (or adjust plan TOC_MM / page count), then rerun validation + plan + build.

### 7. Lint/tests after edits
- `python tools/jsx_lint.py engine/jsx` → 0 errors.
- `python -m unittest discover -s tests` → OK.

## Shell commands used (chronological)
```
git status; ls
python engine/run.py validate pt-contoh-laporan
python engine/run.py plan pt-contoh-laporan
python tools/jsx_lint.py engine/jsx
python -m unittest discover -s tests
where node / Get-Command node
Get-Process InDesign
python -c "import win32com.client"  (failed: not installed)
pip list | Select-String win32/comtypes
powershell test_com.ps1  (connected to Adobe InDesign)
powershell run_build.ps1  (multiple iterations)
Get-Content ARSR_Build_Log.txt
python -c "json ... toc count/height"
Select-String data files for daftar-isi
Get-Content evals/tasks/E6.md
```

## Files changed
- `engine/jsx/build_report.jsx` (5 edits: userInteractionLevel, numberingLists, namePrefix, numbering styles, appliedNumberingList)
- `.opencode/skills/indesign-jsx-basics/references/pitfalls.md` (5 rows added)

## Status at interruption
- A build run was in progress via PowerShell COM; final log not yet captured in this report.
- Remaining known error: TOC overflow on page 2.

## Notes
- Each COM build run creates a new InDesign document; repeated runs accumulate open docs. Close unused documents in InDesign between iterations.
- No project data was added to scripts; all fixes are API-name corrections.
- Fixes are untested until rerun in real InDesign (per E6 checklist).