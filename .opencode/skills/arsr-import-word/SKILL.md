---
name: arsr-import-word
description: Turn the copywriter's Word (DOCX) and Excel (XLSX) files into the Markdown data files of a project. Use when the user has source documents instead of Markdown, or asks how copywriters should write.
---

# arsr-import-word

Python (standard library only) reads `<project>/source/*.docx` and `*.xlsx` and writes `<project>/data/*.md`. PDF is not imported.

## Steps

1. Project exists? If not: `python engine/run.py new <project> --jenis LK|LT|LT+LK --divider 1|2 --config <config.md>`.
2. Put the Word files (and any Excel tables they reference) in `<project>/source/`.
3. `python engine/run.py import <project>`. Read `<project>/logs/ARSR_Import_Log.txt`. Fix the Word file for each ERROR, rerun. Old data is kept in `<project>/build/data_before_import`.
4. `python engine/run.py validate <project>`; fix the first ERROR (usually a missing regulation code in a Meta line); then `plan`.

## The convention (full text: `docs/penulisan-word.md`)

- Heading 1 = chapter, Heading 2 = section/page, Heading 3 = sub heading; each `Indonesian | English`.
- Normal = Indonesian paragraph, style `English` = its translation (write in pairs).
- Style `Meta` = one line `tipe: ... | gri: ... | ojk: ... | seojk: ... | topik: ... | cek: ... | nama: ... | jabatan: ... | tabel: File.xlsx#Sheet | dummy: ya`.
- Table header cell with 2 lines = text column; 1 line = period column. Numbers written as printed (`1.234,5`).
- Cover, table of contents, dividers, indexes, filler pages, back cover are generated. Never write them in Word.

## Rules

- The importer never edits the Word/Excel files. It writes only `data/`, `build/data_before_import/` and the import log.
- Data is plain text: bold, italic, colour and lists from Word are dropped (the log says so).
- A chapter missing in Word gets one dummy page (`dummy: ya`) and a warning. Do not invent content for it.
- Index pages are reserved as 4 (GRI) and 2 (POJK); if `plan` reports PLN-01, rerun import with `--gri-pages N` or `--ojk-pages N`.
- Example file for copywriters: `templates/contoh-word/` (made by `python tools/make_word_example.py <folder> --jenis LT+LK`).
