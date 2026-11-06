---
name: arsr-validate-qa
description: Run and read the read-only checks - Python data validation (GRI, OJK, SEOJK numbering, tables, dummy flags) and the InDesign document QA (tags, overflow, empty frames, page numbers). Use after editing data or after a build, and to turn a log into fixes.
---

# arsr-validate-qa

All checks are read-only. They write only a log in `<project>/logs/`. Nothing in the data or document is modified.

## Three checks, in order

| Step | Command | Log |
|---|---|---|
| 1 data | `python engine/run.py validate <project>` | `<project>/logs/ARSR_Validate_Log.txt` |
| 2 plan | `python engine/run.py plan <project>` (refuses if step 1 has errors; PLN-01 = index/TOC capacity) | same log |
| 3 document | In InDesign open the built document, run `engine/jsx/qa_document.jsx` | `<project>/logs/ARSR_QA_Log.txt` |

Log line: `[RULE] where | message`. First line: `ERROR n | WARN n | ...`.

## Fix loop
1. Read the first ERROR. Look up the rule in `.opencode/skills/arsr-data-spec/references/validation-rules.md`.
2. Fix the data (never the validator) unless the rule itself is wrong; then change the rule and add a test.
3. Re-run the same step. Repeat until ERROR 0. Review every WARN; unverified GRI items (`verified: no`) stay warnings.

## Where the numbering comes from
`catalogs/gri.md`, `catalogs/ojk.md`, `catalogs/seojk.md` and the profiles in `catalogs/profiles/`. A code in a page header that is not in a catalog is an error. Do not invent codes. To add a regulation follow `catalogs/README.md`.

## Document QA rules
DOC-01 visible tags, DOC-02 empty frames, DOC-03 overflow, DOC-04 forbidden text, DOC-05 page count, DOC-06 table header tags, DOC-07 TOC pages, DOC-08 missing styles/swatches. The QA script itself is untested in real InDesign; if it crashes, the log shows `QA-00`.
