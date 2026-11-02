---
name: arsr-style-system
description: The InDesign style system of the ARSR build - swatches, tints, paragraph/character style folders, the bilingual tag set (<e>, <id>, <hid>...) and GREP rules, table and cell styles, page templates. Use when changing design, adding a tag or style, or explaining why text is formatted a certain way.
---

# arsr-style-system

Design choices live in `data/00_config.md` (palette, fonts, margins). The engine `engine/jsx/build_report.jsx` holds the style system. Never hand-format text in InDesign pages; add a tag or style instead.

## Swatches
Exactly 10: Primary, Secondary, Accent 1, Accent 2, Neutral Dark, Neutral Light, Background, Highlight, Terang (white), Terang 2 (slightly darker). Other colors are tints made by `tint(base, pct)`, for example `Primary@45`. No new swatches.

## Text tags (one set for every paragraph style)
Line 1 Indonesian untagged, Shift+Enter, line 2 English in `<e>...</e>`. Tags open and close in the same paragraph. Tags stay in the text; a GREP style hides them (Hide_Tags, 0.1 pt, no fill, always last).

| Tag | Meaning |
|---|---|
| `<e>` `<en>` | English, upright Regular, lighter than ID |
| `<enb>` `<id>` | English bold; Indonesian bold Primary (in tables `<id>` -> `j.tabel.id`, 9 pt) |
| `<b>` `<i>` | Bold; italic for manual emphasis only |
| `<hid>` `<hen>` `<jid>` `<jen>` `<qid>` `<qen>` | Dark background: ID light, EN light 2, heading ID/EN, quote ID/EN |
| `<big>` `<acc>` `<mut>` `<sup>` `<sub>` | Big, Accent 1, muted, superscript, subscript |
| `<ref>` | Regulation code, Accent 2 bold small caps |
| `<dum>` | Dummy marker: Highlight underline band |

The tag -> character style map is the single `TAGS` table in `build_report.jsx`; families (Tabel) can override the target there.

## Style folders
- Paragraf: Heading 1, Heading 2, paragraf, paragraf.pendek, paragraf.tengah, penomoran.l1-3, butir.l1-2
- Tabel: paragraf.tabel, paragraf.tabel.angka, paragraf.tabel.periode, judul.tabel
- TOC: toc.bab, toc.sub. Divider: divider.nomor/judul/sub. Tambahan: stat.angka, stat.label, caption, sumber, kutipan, folio, header.running, nav, nav.aktif, cover.*
- Character folders: Bahasa, Latar Gelap, Format. One style = one dimension (color or size or weight) so tags stack.

## Tables
Native tables. Cell styles `sel.header.teks`, `sel.header.periode`, `sel.header.berjalan`, `sel.isi`, `sel.isi.berjalan`, `sel.akhir`, `sel.akhir.berjalan`; table style `tabel.dasar`. Hairline 0.25 pt Primary between rows, 2 pt under the last row, 1 pt Accent 2 under the header. Pure numbers use `paragraf.tabel.angka` (right aligned). Period header fill is a rounded rectangle on layer `Tabel Dekor` behind the table.

## Layers
Latar (backgrounds, placeholders), Tabel Dekor, Teks, Header (running header, nav). Covers use no master. Folio = physical page number; covers show none.

## How to change something
1. Colors, fonts, margins, sizes: edit `00_config.md`, rebuild.
2. New text condition: propose a new tag in `TAGS` plus a character style in `makeCharStyles()`. Update this file and `AGENTS.md`.
3. Page template change: edit the matching function in `build_report.jsx` (`textPage`, `cardPage`, ...). Run lint and tests.
