# arsr-skills

**EN.** Skills and data standards that let any AI agent build an Annual Report (AR) / Sustainability Report (SR) in Adobe InDesign. Python is the "brain" (parse, validate, plan); JSX is the executor inside InDesign. Report content is plain Markdown. Validators only read and write a log to your Desktop.

**ID.** Skill dan standar data agar agen AI mana pun dapat membangun Laporan Tahunan (AR) / Laporan Keberlanjutan (SR) di Adobe InDesign. Python adalah "otak" (baca, validasi, rencana); JSX adalah eksekutor di InDesign. Isi laporan berupa Markdown biasa. Validator hanya membaca dan menulis log ke Desktop.

## Quick start (OpenCode, Windows 11)

1. Open this folder as the project in OpenCode. Skills in `.opencode/skills/` are discovered automatically.
2. Ask: `Use skill arsr-start. I want a new report from the dummy template.`
3. The skill creates a project with `python engine/run.py dummy <folder>`; edit `data/00_config.md` (name, year, palette, fonts), then follow the skill steps.

## What is here now (R1 + R2)

- `AGENTS.md` - rules every agent must follow.
- `.opencode/skills/arsr-start`, `arsr-data-spec` - router and data standard.
- `catalogs/` - GRI / OJK / SEOJK numbering, version rules, regulation profiles. Rows marked `verified: no` come from general knowledge and must be checked against the official text before printing.
- `templates/dummy-company/data/00_config.md` - config for a fictional company.

- `engine/` - Python parser, read-only validator, dummy generator, build planner (`run.py`) and `engine/jsx/` (build + QA scripts). Tests in `tests/`; ES3 linter in `tools/`.

Try it (Windows, Python 3.8+ installed):

```
python engine\run.py dummy C:\work\demo
python engine\run.py validate C:\work\demo
python engine\run.py plan C:\work\demo
```

Then in InDesign run `engine\jsx\build_report.jsx` (File > Scripts) and, on the result, `qa_document.jsx`. The JSX files are not yet tested in real InDesign: expect to fix first-run errors from the Desktop logs (`ARSR_Build_Log.txt`, `ARSR_QA_Log.txt`).

The log `ARSR_Validate_Log.txt` is written to your Desktop. Evals for free OpenCode models: see `evals/README.md`.

## Scope notes

- No real company data is included. All sample content is fictional and flagged `dummy: ya`.
- Regulation catalogs are an aid for validation, not legal advice.
