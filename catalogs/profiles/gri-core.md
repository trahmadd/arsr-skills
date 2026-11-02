# Profile: gri-core

Use for any company, any country. GRI only.

```
profil: gri-core
katalog: gri
```

## Rules

| id | rule | level |
|---|---|---|
| GRI-01 | Every page `gri:` code exists in `catalogs/gri.md` | error |
| GRI-02 | Code with `verified: no` is cited (one summary warning, full list in INFO) | warning |
| GRI-03 | Code belongs to a standard that is replaced or withdrawn for the project's `gri.versi` | error |
| GRI-04 | GRI 2 disclosures 2-1..2-30 each appear on at least one page or are listed as omission with a reason | error (in-accordance) / warning (with-reference) |
| GRI-05 | GRI 3-1 and 3-2 appear on at least one page; each material topic has a page with `3-3` and its `topik`; a page citing 3-3 has `topik` | error / warning |
| GRI-06 | Topic standards cited only for topics listed as material in config | warning |
| GRI-07 | Omission has a reason (`alasan`) | error |
| GRI-08 | Statement of use (`pernyataan-penggunaan`) is set to `in accordance with` or `with reference to` | error |
| GRI-09 | Every valid disclosure of a material topic standard is cited on a page or listed in OMISI | warning |
