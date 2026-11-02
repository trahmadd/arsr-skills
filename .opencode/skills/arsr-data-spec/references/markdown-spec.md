# Markdown data spec

## File names

`data/00_config.md`, then `01_<slug>.md` ... `09_<slug>.md`. One file per chapter. Slug: lowercase ASCII, no spaces. Files are UTF-8 (characters like ², ±, en dash, curly quotes are allowed in data).

## Chapter header (first line, exactly once per file)

```
# BAB 05 | id: Kinerja Sosial | en: Social Performance
```

`BAB nn` is two digits and equals the file prefix.

## Page block

```
## HAL 40 | tipe: tabel | gri: 2-29 | ojk: C.3 | seojk: LT.8 | topik: T01, T02
```

- `HAL n`: physical page number, continuous from 1. Front cover = 1.
- `tipe`: one value from `page-types.md`.
- `gri`, `ojk`, `seojk`: comma-separated codes from `catalogs/`. Optional per page, but every code in the profile must be covered by some page (see `validation-rules.md`).
- `topik`: ids of material topics from config (optional).

Lines after the heading are `key: value` until the next `## HAL` or `# BAB`. A value may continue on following lines if they are indented by two spaces.

## Keys

| key | meaning |
|---|---|
| `judul.id` / `judul.en` | page title, both required |
| `isi.id` / `isi.en` | body text; blank line = new paragraph (indent continuation lines by two spaces) |
| `sumber` | source note, or `dummy` |
| `dummy` | `ya` marks the whole page as dummy content |
| `cek` | numeric checks for a table, e.g. `total = a + b`, `persen(c) = c / total` |
| `berjalan` | number of current-period columns (right side), default 1 |
| `lebar` | optional column widths in mm, comma-separated |
| `periode` | optional period labels, comma-separated |

Do not write inline tags (`<e>`, `<id>`, `<b>`). Values are plain text only.

## Tables

Key `tabel:` followed by a pipe table indented by two spaces.

```
tabel:
  | id: Deskripsi | en: Description | id: Satuan | en: Unit | 2024 | 2025 | 2026 |
  | Jumlah karyawan | Number of employees | orang | persons | 118 | 126 | 134 |
```

Rules:
1. Row 1 is the header. Label cells use `id:` and `en:` prefixes.
2. Data rows: bilingual text cells written as `Indonesian | English` in two adjacent cells; numeric cells are single.
3. Header cells that do not start with `id:` or `en:` are period (numeric) columns and must come last. One `id:` + `en:` pair is one logical column (counts for `lebar`).
4. Append `{dummy}` to the first cell of a row to flag that row as dummy.
5. Numbers use the Indonesian format `1.234,5` in `.id` context and the English format in `.en` context; in tables write the value once, using `format-angka-tabel` from config.

## Checks (`cek`)

Arithmetic between data rows, evaluated separately in every period column. Rows are numbered `r1`, `r2`, ... in the order of the data rows (header excluded). The left side is one row; the right side uses `+ - * /`, numbers and parentheses. Separate formulas with `;`.

```
cek: r3 = r1 - r2; r4 = r3 * 0.8
cek: r3 = r2 / r1 * 100
```

The tolerance is one unit of the last decimal shown in the left cell (1,0 shown as `12,5` allows 0,1). The validator reads it; the build never edits numbers. A failing check is error NUM-01.

## Language

Indonesian first, English second, always paired. Missing `.en` is an error.

## Forbidden

Empty values, `[isi]`, `[contoh]`, `TBD`, lorem ipsum, HTML or XML tags, tabs inside table rows.
