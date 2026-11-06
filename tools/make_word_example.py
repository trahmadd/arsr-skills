# -*- coding: utf-8 -*-
"""Build the example Word file (and its Excel table) that shows copywriters how to write for the engine.

  python tools/make_word_example.py <out_dir> [--jenis LT+LK|LK|LT]

The content is the fictional dummy report, written the way a copywriter should write it, so the file imports
cleanly: python engine/run.py import <project> turns it back into data files that validate with 0 errors.
Needs python-docx and openpyxl (tools only; the engine itself uses the standard library).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'engine'))

from arsr import arrange, dummy, mdparse  # noqa: E402

try:
    import docx
    from docx.enum.style import WD_STYLE_TYPE
    from docx.shared import Pt, RGBColor
    import openpyxl
except ImportError:
    docx = None

GUIDE = [
    ('Cara memakai berkas ini / How to use this file', None),
    ('Berkas ini contoh penulisan yang benar. Hapus isinya dan tulis laporan Anda dengan pola yang sama. '
     'Semua yang ada sebelum Heading 1 pertama diabaikan mesin.',
     'This file is an example of correct writing. Replace the content and write your report with the same pattern. '
     'Everything before the first Heading 1 is ignored by the machine.'),
    ('1. Heading 1 = bab. Tulis "Indonesia | English". Baris Meta di bawahnya: slug: nama-bab.',
     '1. Heading 1 = chapter. Write "Indonesian | English". The Meta line under it: slug: chapter-name.'),
    ('2. Heading 2 = satu bagian (satu halaman, atau lebih bila panjang). Tulis "Indonesia | English".',
     '2. Heading 2 = one section (one page, or more when long). Write "Indonesian | English".'),
    ('3. Paragraf Normal = bahasa Indonesia. Paragraf bergaya English = terjemahannya. Tulis berpasangan: Indonesia, lalu English.',
     '3. Normal paragraph = Indonesian. Paragraph in style English = its translation. Write in pairs: Indonesian, then English.'),
    ('4. Meta = satu baris atribut: tipe, gri, ojk, seojk, topik, cek, dummy, nama, jabatan, tabel.',
     '4. Meta = one attribute line: tipe, gri, ojk, seojk, topik, cek, dummy, nama, jabatan, tabel.'),
    ('5. Tabel Word: sel judul kolom teks berisi dua baris (Indonesia, English); kolom tahun satu baris. Angka ditulis 1.234,5.',
     '5. Word table: a text column header has two lines (Indonesian, English); a year column one line. Write numbers as 1.234,5.'),
    ('6. Kartu angka: tabel tanpa baris judul; tiap baris = angka | label (dua baris). Kutipan: Meta tipe: kutipan | nama | jabatan.',
     '6. Number cards: a table without a header row; each row = number | label (two lines). Quote: Meta tipe: kutipan | nama | jabatan.'),
    ('7. Sampul, daftar isi, pembatas bab, indeks, dan sampul belakang dibuat otomatis. Jangan ditulis.',
     '7. Cover, table of contents, chapter dividers, indexes and back cover are generated. Do not write them.'),
    ('8. Tabel besar boleh dari Excel: Meta "tabel: NamaBerkas.xlsx#NamaSheet" dan tanpa tabel Word.',
     '8. A big table may come from Excel: Meta "tabel: FileName.xlsx#SheetName" and no Word table.'),
]


def setup_styles(d):
    st = d.styles
    for name in ('English', 'Meta'):
        try:
            st[name]
        except KeyError:
            s = st.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            s.base_style = st['Normal']
    st['English'].font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    st['Meta'].font.name = 'Consolas'
    st['Meta'].font.size = Pt(9)
    st['Meta'].font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)


def bi(a, b):
    return '%s | %s' % (a, b)


def meta_line(d, parts):
    d.add_paragraph(' | '.join(parts), style='Meta')


def add_cell_lines(cell, lines, english_second=True):
    cell.paragraphs[0].text = lines[0]
    for ln in lines[1:]:
        cell.add_paragraph(ln, style='English')


def table_from_rows(d, rows):
    """rows: dummy table rows (first = header with 'id:'/'en:' cells)."""
    head = rows[0]
    cols, i = [], 0
    while i < len(head):
        if head[i].startswith('id:'):
            cols.append(('text', i))
            i += 2
        else:
            cols.append(('num', i))
            i += 1
    t = d.add_table(rows=len(rows), cols=len(cols))
    t.style = 'Table Grid'
    for ri, row in enumerate(rows):
        for ci, (kind, at) in enumerate(cols):
            cell = t.cell(ri, ci)
            if kind == 'text':
                a = row[at].split(': ', 1)[1] if ri == 0 else row[at]
                b = row[at + 1].split(': ', 1)[1] if ri == 0 else row[at + 1]
                add_cell_lines(cell, [a, b])
            else:
                cell.paragraphs[0].text = row[at]
    return t


def write_section(d, k, pg, xlsx_ref=None):
    tipe = pg['tipe']
    if tipe == 'kutipan':
        title = {4: bi('Pesan Presiden Komisaris', 'Message from the President Commissioner'),
                 5: bi('Pesan Presiden Direktur', 'Message from the President Director')}[k]
    else:
        title = bi(*pg['judul'])
    d.add_heading(title, level=2)
    parts = ['tipe: ' + tipe]
    if tipe == 'tabel' and not pg.get('isi') and False:
        pass
    for a in ('gri', 'ojk', 'seojk', 'topik'):
        if pg.get(a):
            parts.append('%s: %s' % (a, ', '.join(pg[a])))
    if pg.get('cek'):
        parts.append('cek: ' + pg['cek'])
    if tipe == 'kutipan':
        parts += ['nama: ' + pg['nama'], 'jabatan: ' + pg['jabatan']]
    if xlsx_ref:
        parts.append('tabel: ' + xlsx_ref)
    parts.append('dummy: ya')
    meta_line(d, parts)
    if tipe == 'kutipan':
        d.add_paragraph(pg['kutipan'][0])
        d.add_paragraph(pg['kutipan'][1], style='English')
        return
    if tipe == 'kartu':
        t = d.add_table(rows=len(pg['kartu']), cols=2)
        t.style = 'Table Grid'
        for i, (a, li, le) in enumerate(pg['kartu']):
            t.cell(i, 0).paragraphs[0].text = a
            add_cell_lines(t.cell(i, 1), [li, le])
        return
    if pg.get('isi'):
        ids, ens = pg['isi'][0].split('\n\n'), pg['isi'][1].split('\n\n')
        for i in range(max(len(ids), len(ens))):
            if i < len(ids):
                d.add_paragraph(ids[i])
            if i < len(ens):
                d.add_paragraph(ens[i], style='English')
    if tipe == 'tabel' and not xlsx_ref:
        table_from_rows(d, pg['tabel'])


def make_xlsx(path, pg, Y):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Saham'
    head = pg['tabel'][0]
    ws.append(['Deskripsi\nDescription', 'Satuan\nUnit'] + [int(x) for x in Y])
    for row in pg['tabel'][1:]:
        vals = [float(c.replace('.', '').replace(',', '.')) for c in row[4:]]
        ws.append([row[0] + '\n' + row[1], row[2] + '\n' + row[3]] + vals)
    for c in ws[1][2:]:
        c.value = str(c.value)
    for r in range(2, ws.max_row + 1):
        for c in range(3, ws.max_column + 1):
            ws.cell(r, c).number_format = '#,##0'
    wb.save(path)


def build(out_dir, jenis='LT+LK', xlsx_name='Contoh_Tabel.xlsx'):
    if docx is None:
        raise RuntimeError('python-docx and openpyxl are needed: pip install python-docx openpyxl')
    os.makedirs(out_dir, exist_ok=True)
    cfg = mdparse.parse_config(os.path.join(HERE, '..', 'templates', 'dummy-company', 'data', '00_config.md'))
    g = dummy.Gen(cfg, jenis, 1)
    g.plan()
    srows = dict((r['slug'], r) for r in g.struct)
    d = docx.Document()
    setup_styles(d)
    d.add_heading(GUIDE[0][0], level=0)
    for a, b in GUIDE[1:]:
        d.add_paragraph(a)
        d.add_paragraph(b, style='English')
    xlsx_pg = None
    for slug, ids in dummy.LAYOUT[jenis]:
        row = srows[slug]
        d.add_heading(bi(row['id'], row['en']), level=1)
        meta_line(d, ['slug: ' + slug])
        intro = arrange.INTRO[slug]
        d.add_paragraph(intro[0])
        d.add_paragraph(intro[1], style='English')
        for k in ids:
            pg = g._tweak(k, dict(g.pages[k]))
            if pg['tipe'] in ('sampul', 'daftar-isi') or pg['tipe'].startswith('indeks'):
                continue
            ref = None
            if k == 12:   # Share information: shown with the Excel route
                ref = xlsx_name + '#Saham'
                xlsx_pg = pg
            write_section(d, k, pg, ref)
    d.save(os.path.join(out_dir, 'Contoh_Laporan_%s.docx' % jenis.replace('+', '-')))
    if xlsx_pg is not None:
        make_xlsx(os.path.join(out_dir, xlsx_name), xlsx_pg, g.Y)
    return out_dir


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--jenis', default='LT+LK', choices=['LK', 'LT', 'LT+LK'])
    a = ap.parse_args()
    print(build(a.out, a.jenis))
