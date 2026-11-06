---
name: arsr-data-spec
description: Standard for report data Markdown files (00_config.md and chapter files with "## HAL n" page blocks) - keys, page types, bilingual id/en pairs, tables, dummy flags, validation rules. Use when reading, writing or fixing any report data file.
---

# arsr-data-spec

Report data = one `data/` folder: `00_config.md` plus one file per chapter (`01_*.md` ... `09_*.md`). One `## HAL n` block = one physical page (front cover = page 1).

## Minimal example

```
# BAB 02 | id: Profil | en: Profile

## HAL 14 | tipe: teks | gri: 2-1, 2-6 | ojk: C.2, C.4 | seojk: LT.5
judul.id: Profil Perusahaan
judul.en: Company Profile
isi.id: Paragraf Indonesia.
isi.en: English paragraph.
sumber: dummy
dummy: ya
```

## Core rules

1. Every text key exists twice: `key.id` and `key.en`. Both non-empty.
2. No inline tags in data. The build creates `<e>...</e>` and other tags.
3. Page numbers are continuous from 1; total pages is a multiple of 4.
4. Regulation codes in `gri:`, `ojk:`, `seojk:` must exist in `catalogs/`.
5. Forbidden text: `[isi]`, `[contoh]`, `TBD`, lorem ipsum, empty values.
6. Not-real content needs `dummy: ya` (page) or `{dummy}` after the first cell of a table row.
7. Numbers: Indonesian `1.234,5`, English `1,234.5`. Table cells follow `format-angka-tabel` in config.

## Where to read next (load only what you need)

- `references/markdown-spec.md` - exact syntax, keys, table format, checks (`cek`).
- `references/page-types.md` - required and optional keys per `tipe`.
- `references/config-spec.md` - sections and keys of `00_config.md`.
- `references/validation-rules.md` - rule ids the validator and QA will report.

## Working method

1. Open the nearest example block in a generated dummy project (`python engine/run.py dummy <folder>`) and copy its key order.
2. Fill one page at a time. Keep ID and EN meaning equal.
3. After each chapter file run `python engine/run.py validate <project_dir>` and fix errors from the top of the log `<project>/logs/ARSR_Validate_Log.txt`.
