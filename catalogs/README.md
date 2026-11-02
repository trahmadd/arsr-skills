# catalogs/

Numbering catalogs used by validators and QA. The validator accepts a regulation code only if it appears in a catalog row. Never invent codes.

## Files

| File | Content | Code pattern |
|---|---|---|
| `gri.md` | GRI Standards 2021 universal + topic standards | `2-1`, `3-3`, `201-1`, `305-1` |
| `ojk.md` | SEOJK 16/SEOJK.04/2021 Lampiran II Bagian III (SR guideline, POJK 51/2017) | `A.1` ... `G.4` |
| `seojk.md` | SEOJK 16/SEOJK.04/2021 Annual Report mandatory sections (item 3a) | `LT.1` ... `LT.10` |
| `mapping-ojk-gri.md` | Suggested cross map OJK -> GRI -> page type | n/a (advice, not law) |
| `profiles/*.md` | Which catalogs and rules a project uses | n/a |

## Row format

Markdown pipe tables. The first column is always `code`. Every catalog table has a `verified` column with `yes` or `no`.

- `verified: yes` - checked against an official or full-text source.
- `verified: no` - from general knowledge. Validator reports a WARNING (not an error) when a page cites it. Check against the official text before printing.

Column order is fixed per file (see the header row). Do not reorder or rename headers; parsers read headers by name.

## Version rules

- GRI 101 (2024) replaces GRI 304. GRI 102 (2025) replaces 305-1..305-5 and 201-2. GRI 103 (2025) replaces GRI 302. Effective dates are in `gri.md` (Standards table).
- Which version applies depends on the report publication date. The project decides in `00_config.md` (`gri.versi`: `pra-2027` or `2027`). The validator rejects codes of a standard marked as replaced for the chosen version.
- Disclosure numbers inside GRI 101/102/103 are not listed yet (`verified: no`, empty). Add them from the official text before using those standards.
- GRI 307 and 419 were withdrawn; use 2-27.

## Adding a regulation

1. Create `catalogs/<name>.md` with a pipe table: `code | title | verified | note`.
2. Create `catalogs/profiles/<profile>.md` listing the catalog files and rules.
3. Reference the profile from the project's `00_config.md` (`profil-regulasi`).
4. No code changes are needed.
