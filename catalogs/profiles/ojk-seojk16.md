# Profile: ojk-seojk16

Indonesian listed issuers (Emiten / Perusahaan Publik). Extends `gri-core`.

```
profil: ojk-seojk16
turunan: gri-core
katalog: gri, ojk, seojk, mapping-ojk-gri
```

## Rules

| id | rule | level |
|---|---|---|
| OJK-01 | Every `ojk:` code exists in `catalogs/ojk.md` | error |
| OJK-02 | Every `seojk:` code exists in `catalogs/seojk.md` | error |
| OJK-03 | Every OJK code A.1..G.4 appears on at least one page, or is listed in config `omisi-ojk` with a reason (applicability rule: F.3 non-financial; B.2 and F.9-F.16 depend on business type) | error |
| OJK-04 | A page cites an OJK code but none of its suggested GRI codes (mapping file). Suggestions replaced under `gri.versi` are ignored | warning |
| OJK-05 | G.4 index page exists (type `indeks-ojk`) | error |
| OJK-06 | Annual report: all 10 SEOJK items LT.1..LT.10 appear (or listed in `omisi-seojk` with a reason) | error (AR) / skipped (SR only) |
| OJK-07 | Bilingual: Indonesian plus English (enforced by STR-05, no separate check) | error |
| OJK-08 | Economic and social tables (B.1, B.3, F.2, F.3, F.17-F.30) have 3 periods when the company operated more than 3 years (`berdiri`) | warning |
| OJK-09 | Report year and publication year consistent with `gri.versi` choice | warning |

## Information only

PSPK 1 and 2 (IFRS S1/S2 aligned) are effective for periods starting 1 January 2027. Mention in "About this report"; do not use as a compilation basis for 2026 reports.
