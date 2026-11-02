# `00_config.md` spec

Sections are `## SECTION` headings with `key: value` lines or pipe tables. Section names and table headers are fixed; do not rename.

## PROYEK

`nama-perusahaan`, `nama-singkat`, `kode-emiten`, `tahun-laporan`, `tahun-terbit`, `tema.id`, `tema.en`, `jenis` (`LK`, `LT`, or `LT+LK`), optional `berdiri` (founding year; used by rule OJK-08).

## HALAMAN

`ukuran: A4`, `facing: ya`, `bleed-mm: 3`, `jumlah-halaman` (multiple of 4), margin: `margin-atas-mm`, `margin-bawah-mm`, `margin-dalam-mm`, `margin-luar-mm`, `kolom`, `gutter-mm`.

## WARNA

Fixed swatch names; only hex changes per project.

| swatch | hex |
|---|---|
| Primary | #xxxxxx |
| Secondary | |
| Accent 1 | |
| Accent 2 | |
| Neutral Dark | |
| Neutral Light | |
| Background | |
| Highlight | |
| Terang | #FFFFFF |
| Terang 2 | slightly darker than white |

Nothing else may become a swatch; use tints only.

## FONT

`font-utama`, `font-angka` (tabular lining if available), `ukuran-dasar-pt`, `leading-dasar-pt`.

## REGULASI

`profil-regulasi` (name of a profile in `catalogs/profiles/`), `gri.versi` (`pra-2027`: GRI 302/305 valid, GRI 101 valid from 2026-01-01, 304 replaced; `2027`: GRI 101/102/103 replace 304/305-1..5/201-2/302), `pernyataan-penggunaan` (`in accordance with` or `with reference to`), `tanggal-terbit` (YYYY-MM-DD).

## OMISI

Table `kode | alasan.id | alasan.en` for GRI, `omisi-ojk` for OJK, `omisi-seojk` for SEOJK. Every omission has a reason.

## BAB

Table `no | slug | id | en | halaman-awal`. Chapter order and starting page.

## TOPIK

Material topics. Table `id | nama.id | nama.en | gri`, ids `T01..Tnn`. Each topic must have a 3-3 page.

## KONTAK

`email`, `telepon`, `alamat.id`, `alamat.en` (dummy for template), `web`.

## FORMAT

`format-angka-tabel` (`id` or `en`), `satuan-ribuan`, `satuan-desimal`.

Everything in the template is fictional and flagged `dummy: ya` in the config header.
