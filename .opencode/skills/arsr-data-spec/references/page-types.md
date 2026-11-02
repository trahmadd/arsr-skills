# Page types (`tipe:`)

Each type lists required and optional keys. `judul.id/en` is required on every type except `kutipan`. Unknown keys give warning STR-11.

| tipe | purpose | required | optional |
|---|---|---|---|
| `sampul` | front or back cover | `judul.*`, `subjudul.*`, `tahun` | `sumber` |
| `divider` | chapter opener (large number, title) | `judul.*` | `subjudul.*` |
| `teks` | one or two-column text | `isi.*` | `kutipan.*`, `gambar` |
| `kartu` | statistic cards (3 to 6 cards) | `kartu:` list | `isi.*` |
| `kutipan` | pull quote or message page | `kutipan.*`, `nama`, `jabatan` | `isi.*` |
| `tabel` | one native table | `tabel:` | `isi.*`, `cek`, `berjalan`, `lebar`, `periode` |
| `daftar-isi` | table of contents, generated from the build registry | none | |
| `indeks-gri` | GRI content index, generated from `gri:` attributes | none | |
| `indeks-ojk` | OJK G.4 index, generated from `ojk:` attributes | none | |
| `indeks-seojk` | SEOJK 16 cross index, generated from `seojk:` attributes | none | |

## Cards

```
kartu:
  - angka: 134 | label.id: Karyawan | label.en: Employees
  - angka: 31% | label.id: Perempuan | label.en: Women
```

Each card has `angka`, `label.id`, `label.en`. Label max two lines. Numbers never contain tags.

## Rules

1. Generated types (`daftar-isi`, `indeks-*`) carry no content; the build writes them. Tell the validator which pages they are with the `tipe`.
2. A page without a fitting type is a design change: add the type to this file and the engine together. Do not stretch an existing type.
3. `dummy: ya` is allowed on every type.
