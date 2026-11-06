# Writing in Word for the engine / Menulis di Word untuk mesin

For copywriters. You do not need Markdown. Write in Word with the styles below; the machine reads the file and builds the data files.
Untuk copywriter. Anda tidak perlu Markdown. Tulis di Word dengan style berikut; mesin membaca berkas dan membuat berkas data.

Start from `templates/contoh-word/Contoh_Laporan_LT-LK.docx`: replace the content, keep the pattern. / Mulailah dari berkas contoh itu: ganti isinya, pertahankan polanya.

## The six styles / Enam style

| Word style | Use | Contoh |
|---|---|---|
| Heading 1 | A chapter. `Indonesia \| English` | `Profil Perusahaan \| Company Profile` |
| Heading 2 | One section = one page (a long one continues on the next page). `Indonesia \| English` | `Identitas \| Identity` |
| Heading 3 | A sub heading inside a section. `Indonesia \| English` | `Visi \| Vision` |
| Normal | An Indonesian paragraph | |
| English | The English translation of the paragraph above it | |
| Meta | One line of attributes under a heading | `tipe: tabel \| gri: 2-1 \| ojk: C.2 \| dummy: ya` |

Word's own Heading 1/2/3 also build Word's table of contents, so the file stays normal to read. Bold, italic and colour are not carried over: the design decides them.

## Write in pairs / Tulis berpasangan

Indonesian paragraph, then its English paragraph. Every Indonesian paragraph needs an English one. The importer warns when the counts differ.

## Meta line / Baris Meta

Put it directly under a Heading 1 or Heading 2. Separate items with ` | ` (space, bar, space).

| Key | Under | Meaning |
|---|---|---|
| `slug: profil` | Heading 1 | Chapter name from `structures/*.md` (optional when the title matches or the order is the same) |
| `tipe: teks \| tabel \| kartu \| kutipan` | Heading 2 | Page type. Default: `tabel` when the section has a table, otherwise `teks` |
| `gri: 2-1, 2-2` `ojk: C.2` `seojk: LT.5` | Heading 2 | Regulation codes this section covers. They feed the GRI, POJK and SEOJK indexes. Codes must exist in `catalogs/` |
| `topik: T01` | Heading 2 | Material topic id from the config |
| `cek: r3 = r1 - r2` | Heading 2 | Check formula: row 3 equals row 1 minus row 2 (rows count from the first data row) |
| `nama: ... \| jabatan: ...` | Heading 2 of a quote | Name and position of the speaker |
| `tabel: File.xlsx#Sheet` | Heading 2 | Take the table from an Excel file in `source/` |
| `dummy: ya` | Heading 2 | Content is sample data: it is marked yellow and listed in `Dummy_Register.txt` |

## Tables / Tabel

- Row 1 is the header. A **text** column has **two lines** in the header cell (Indonesian, English). A **year** column has one line (`2025`).
- Text cells also have two lines. A code that is the same in both languages may be written once.
- Write numbers as you want them printed: `1.234,5` (Indonesian style). Keep the same number of decimals in a column.
- Rightmost year column = the current year (highlighted by the design).
- Keep checked tables within 14 data rows; longer tables continue on the next page.
- Merged cells, tables inside tables, pictures and bullet lists are not carried over. The importer warns; check those pages.

In Excel the same rules apply: use Alt+Enter for the second line of a text cell, and format numbers with the decimals you want shown.

## Number cards / Kartu angka

A section with `tipe: kartu` and a table of 3 to 6 rows, **no header row**: column 1 = the number, column 2 = the label (two lines: Indonesian, English).

## Quotes / Kutipan

`tipe: kutipan | nama: ... | jabatan: ...`, then the quote as an Indonesian paragraph and an English paragraph.

## Do not write / Jangan ditulis

Cover, table of contents, chapter dividers, GRI/POJK/SEOJK indexes, filler pages and the back cover. The engine makes them. A chapter's intro (the paragraphs between its Heading 1 and its first Heading 2) is used on the second divider page.

## File names / Nama berkas

One file for the whole report, or one per chapter named `NN_nama-bab.docx` (`01_pendahuluan.docx`). Files are read in name order. Put them, and any `.xlsx`, in the project's `source/` folder. Everything before the first Heading 1 is ignored: use that space for notes.

## What happens next / Setelah itu

```powershell
python engine\run.py import C:\work\smlg      # Word/Excel -> data\*.md  (old data kept in build\data_before_import)
python engine\run.py validate C:\work\smlg    # read logs\ARSR_Validate_Log.txt
python engine\run.py plan C:\work\smlg
```

Read `logs\ARSR_Import_Log.txt` first: its warnings tell you what the machine could not carry over.
