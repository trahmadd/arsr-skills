# Report structures / Struktur laporan

One file per report type, chosen by `jenis:` in `data/00_config.md`:

| File | jenis | Report |
|---|---|---|
| `lk.md` | LK | Sustainability Report / Laporan Keberlanjutan |
| `lt.md` | LT | Annual Report / Laporan Tahunan |
| `lt-lk.md` | LT+LK | Integrated report / Laporan terintegrasi |

The validator reads the file that matches `jenis:` and checks:

- every chapter marked `wajib: ya` exists in config `BAB` (by `slug`) - STR-20;
- every page type listed under `HALAMAN-WAJIB` appears at least once - STR-21;
- GRI and OJK rules are skipped for LT, SEOJK rules for LK.

`bagian.id` / `bagian.en` list the sections a chapter normally holds. They are writing guidance for the copywriter and
the importer, not an official checklist: confirm against SEOJK 16/SEOJK.04/2021 and POJK 51/POJK.03/2017 before printing
(mapping status `verified: no`). Chapter titles are defaults; rename them in your own config `BAB` table, keep the `slug`.
The structures name no company. Add a new report type by adding a file here and a `jenis` value in the validator.
