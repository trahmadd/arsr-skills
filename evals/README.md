# Evals: test the skills on free models in OpenCode

Goal: find out whether a weaker model, using only `AGENTS.md` and `.opencode/skills/`, completes real tasks. Each task has a prompt (copy it), an automatic grader where possible, and a manual checklist.

## Run one task (Windows, repo folder open in OpenCode)

1. Start a new OpenCode session in the repo folder. Choose the model to test. Do not paste any extra hints.
2. Prepare: `python tools/eval_check.py snapshot` (once per task) and, where the task says, `python tools/eval_check.py seed E2 C:\work\e2`.
3. Paste the prompt from `evals/tasks/E?.md`. Let the model work. Do not help; note every time you had to.
4. Grade: `python tools/eval_check.py check E2 C:\work\e2` (PASS/FAIL lines), then the manual checklist.
5. Record one row in `evals/RESULTS.md` (copy the table): model, task, auto result, manual score, turns, notes.

## Tasks

| Id | Skill tested | Grader |
|---|---|---|
| E1 | arsr-start, arsr-data-spec: new company project | auto + manual |
| E2 | arsr-validate-qa: fix seeded data errors | auto |
| E3 | indesign-jsx-basics: fix ES3 errors in a script | auto |
| E4 | arsr-data-spec, catalogs: regulation numbering questions | manual |
| E5 | arsr-style-system: change palette/fonts via config only | auto + manual |
| E6 | arsr-build-test: fix a build error from a real InDesign log | manual |

Pass bar for a model to be called "usable": E2, E3 auto PASS; E1 and E5 auto PASS with no edits under `engine/`, `catalogs/`, `tools/`; E4 no invented codes.

## Reading results
- Models that invent GRI/OJK codes (E4) fail regardless of other scores.
- If many models fail the same step, fix the skill text (shorter, more concrete), not the model.
- Keep failures in `RESULTS.md`; they are the backlog for the next skill edit.
