# Validation rules (ids reported in the log)

The validator is read-only. It writes one log file to the Desktop (`ARSR_Validate_Log.txt`). First line: `ERROR n | WARN n | pages n`. Fix errors from the top, rerun after every fix.

Status: **R2** = implemented now (Python). **R3** = planned (InDesign QA script).

## Config (R2)

| id | rule | level |
|---|---|---|
| CFG-01 | Missing section, key, table or wrong table header in `00_config.md` | error |
| CFG-02 | Invalid value (jenis, years, jumlah-halaman not multiple of 4, gri.versi, hex, topic id, unknown profile, unknown swatch) | error |

## Structure (R2)

| id | rule | level |
|---|---|---|
| STR-01 | Chapter file list matches config BAB; header number equals file prefix; first page equals `halaman-awal` | error |
| STR-02 | Page numbers continuous from 1, count equals `jumlah-halaman`, multiple of 4 | error |
| STR-03 | Page `tipe` is in `page-types.md` | error |
| STR-04 | Required keys present; card count 3-6; `dummy` value is `ya` | error |
| STR-05 | Every `.id` key has a `.en` key and the reverse | error |
| STR-06 | Empty value, `[isi]`, `[contoh]`, TBD, lorem ipsum, or an inline tag | error |
| STR-07 | Table header/row structure (id:/en: pairs, same cell count, period columns last) | error |
| STR-08 | `berjalan`, `periode`, `lebar` consistent with the table | error |
| STR-09 | `topik` id exists in config TOPIK | error |
| STR-11 | Unknown key on a page | warning |
| STR-12 | A line that cannot be parsed | error |

## Numbers (R2)

| id | rule | level |
|---|---|---|
| NUM-01 | `cek` formula fails, is malformed, or hits a non-numeric cell | error |
| NUM-03 | Table number is not in the format of `format-angka-tabel` | warning |
| NUM-04 | Last period column differs from `tahun-laporan` | warning |

Planned: NUM-02 (same fact, same value across pages, needs a project facts file).

## Regulation (R2, from the profile)

Defined in `catalogs/profiles/*.md`: `GRI-01..09`, `OJK-01..09`. Log lines show rule id, location and message.

## Dummy (R2)

| id | rule | level |
|---|---|---|
| DUM-01 | Count and page list of `dummy: ya` pages and `{dummy}` rows (appears as INFO in the log) | info |

Planned: DUM-02 (dummy content copying a verifiable fact; manual review).

## Document QA (R3, InDesign, read-only)

| id | rule | level |
|---|---|---|
| DOC-01 | No visible `<...>` tag (tag text must carry Hide_Tags) | error |
| DOC-02 | No empty text frame | error |
| DOC-03 | No overflow (text frame or table) | error |
| DOC-04 | No `[isi]`, `[contoh]`, TBD, lorem | error |
| DOC-05 | Page count equals plan page count | error |
| DOC-06 | Every table header cell is tagged (`<id>`) or a period label | error |
| DOC-07 | TOC entries show the plan page numbers | error |
| DOC-08 | Required swatches and paragraph styles exist | error |
| PLN-01 | Index / TOC rows do not fit the index pages in the data (plan step) | error |
