# -*- coding: utf-8 -*-
"""Arrange content pages into a physical page sequence and write the data files.

Shared by the dummy generator and the DOCX importer, so both obey the same rules:
- chapter 1 starts with the cover; every other chapter starts with a divider (one page, or two facing pages);
- with divider 2 the divider starts on a left (even) page, so a `catatan` page pads the previous chapter when needed;
- the table of contents gets as many pages as its entries need;
- the page count is a multiple of 4: `catatan` pages are inserted before the back cover (the last page).

A page is a dict: tipe, judul=(id,en), subjudul=(id,en), isi=(id,en) with paragraphs split by a blank line, tabel (rows),
kartu, kutipan, nama, jabatan, gri/ojk/seojk/topik lists, cek, periode, sumber, dummy (default True).
"""
import re

from . import plan as plan_mod

TITLE = {'LK': ('Laporan Keberlanjutan', 'Sustainability Report'),
         'LT': ('Laporan Tahunan', 'Annual Report'),
         'LT+LK': ('Laporan Tahunan dan Keberlanjutan', 'Annual and Sustainability Report')}

SUB = {
    'pendahuluan': ('Gambaran tahun ini', 'The year at a glance'),
    'ikhtisar': ('Gambaran tahun ini', 'The year at a glance'),
    'manajemen': ('Arah dan tanggung jawab', 'Direction and accountability'),
    'profil': ('Mengenal perusahaan', 'Getting to know the company'),
    'analisis': ('Membaca kinerja', 'Reading the results'),
    'tata-kelola': ('Landasan dan pengawasan', 'Foundations and oversight'),
    'ekonomi': ('Nilai yang dibagikan', 'Value shared'),
    'lingkungan': ('Menjaga bumi', 'Caring for the planet'),
    'sosial': ('Manusia dan masyarakat', 'People and communities'),
    'tjsl': ('Peduli sekitar', 'Caring for our surroundings'),
    'keberlanjutan': ('Ekonomi, lingkungan, sosial', 'Economic, environmental, social'),
    'keuangan': ('Angka dan lampiran', 'Figures and attachments'),
    'indeks': ('Rujukan dan penutup', 'References and closing'),
}
INTRO = {
    'pendahuluan': ('Bab ini merangkum cakupan laporan, topik material, dan ikhtisar kinerja tahun berjalan.',
                    'This chapter summarizes the report scope, material topics and the performance highlights of the year.'),
    'ikhtisar': ('Bab ini merangkum data keuangan penting, informasi saham, dan peristiwa utama tahun berjalan.',
                 'This chapter summarizes key financial data, share information and the main events of the year.'),
    'manajemen': ('Dewan Komisaris dan Direksi menyampaikan pandangan, arah, dan tanggung jawab atas laporan ini.',
                  'The Board of Commissioners and the Board of Directors share their views, direction and responsibility for this report.'),
    'profil': ('Bab ini memperkenalkan identitas, skala, wilayah operasi, dan rantai nilai perusahaan.',
               'This chapter introduces the identity, scale, areas of operation and value chain of the company.'),
    'analisis': ('Manajemen menguraikan kinerja keuangan, posisi keuangan, dan prospek usaha.',
                 'Management discusses financial performance, financial position and business prospects.'),
    'tata-kelola': ('Bab ini menjelaskan struktur tata kelola, pengelolaan risiko, etika, dan pelibatan pemangku kepentingan.',
                    'This chapter explains the governance structure, risk management, ethics and stakeholder engagement.'),
    'ekonomi': ('Bab ini melaporkan nilai ekonomi yang dihasilkan dan dibagikan kepada pemangku kepentingan.',
                'This chapter reports the economic value generated and shared with stakeholders.'),
    'lingkungan': ('Bab ini melaporkan energi, emisi, air, limbah, dan upaya menjaga keanekaragaman hayati.',
                   'This chapter reports energy, emissions, water, waste and efforts to protect biodiversity.'),
    'sosial': ('Bab ini melaporkan ketenagakerjaan, keselamatan kerja, pelatihan, dan hubungan dengan masyarakat.',
               'This chapter reports employment, work safety, training and relations with communities.'),
    'tjsl': ('Ringkasan tanggung jawab sosial dan lingkungan perusahaan pada tahun berjalan.',
             'A summary of the social and environmental responsibility of the company in the year.'),
    'keberlanjutan': ('Bab ini memuat strategi, topik material, serta kinerja ekonomi, lingkungan, dan sosial.',
                      'This chapter holds the strategy, material topics and the economic, environmental and social performance.'),
    'keuangan': ('Bab ini memuat ringkasan laporan keuangan dan penanda lampiran laporan yang telah diaudit.',
                 'This chapter holds a summary of the financial statements and the marker for the audited statements.'),
    'indeks': ('Bab ini memuat verifikasi, umpan balik, indeks rujukan regulasi, dan kontak.',
               'This chapter holds assurance, feedback, regulatory reference indexes and contacts.'),
}

NOTES = dict(tipe='catatan', judul=('Catatan', 'Notes'))


def toc_page_count(layout):
    entries = 0
    for _slug, pgs in layout:
        for pg in pgs:
            if pg['tipe'] not in plan_mod.SKIP_TOC_TYPES and 'judul' in pg:
                entries += 1
    need = entries * plan_mod.TOC_MM[2] + len(layout) * plan_mod.TOC_MM[1] + 20
    return int(need // (plan_mod.TOC_PAGE_MM * 0.9)) + 1


def arrange(layout, struct_rows, divider, intros=None, dummy=True):
    """layout = [(slug, [page dicts])]. Returns (chapters, {n: page}); chapters = [(no, slug, id, en, first_page)]."""
    srows = dict((r['slug'], r) for r in struct_rows)
    intros = intros or {}
    toc_pages = toc_page_count(layout)
    seq, bounds = [], []
    for idx, (slug, pgs) in enumerate(layout):
        row = srows[slug]
        if idx > 0 and divider == 2 and (len(seq) + 1) % 2 == 1:
            seq.append(dict(NOTES, dummy=dummy))
        bounds.append(len(seq) + 1)
        if idx > 0:
            seq.append(dict(tipe='divider', judul=(row['id'], row['en']), subjudul=SUB[slug], dummy=dummy))
            if divider == 2:
                if slug in intros:
                    seq.append(dict(tipe='divider-kanan', isi=intros[slug], dummy=False))
                else:
                    seq.append(dict(tipe='divider-kanan', isi=INTRO[slug], dummy=dummy))
        for pg in pgs:
            if pg['tipe'] == 'daftar-isi':
                for t in range(toc_pages):
                    q = dict(pg)
                    if t:
                        q['judul'] = ('Daftar Isi (lanjutan)', 'Table of Contents (continued)')
                    seq.append(q)
            else:
                seq.append(pg)
    while len(seq) % 4:
        seq.insert(len(seq) - 1, dict(NOTES, dummy=dummy))
    chapters = [(i + 1, slug, srows[slug]['id'], srows[slug]['en'], bounds[i]) for i, (slug, _p) in enumerate(layout)]
    return chapters, dict((i + 1, pg) for i, pg in enumerate(seq))


# ------------------------------------------------------------------ writing
def render_page(n, p, periods):
    head = '## HAL %d | tipe: %s' % (n, p['tipe'])
    for a in ('gri', 'ojk', 'seojk', 'topik'):
        if p.get(a):
            head += ' | %s: %s' % (a, ', '.join(p[a]))
    out = [head]
    if 'judul' in p:
        out += ['judul.id: ' + p['judul'][0], 'judul.en: ' + p['judul'][1]]
    if 'subjudul' in p:
        out += ['subjudul.id: ' + p['subjudul'][0], 'subjudul.en: ' + p['subjudul'][1]]
    if 'tahun' in p:
        out.append('tahun: ' + p['tahun'])
    if 'isi' in p:
        for lang, text in zip(('id', 'en'), p['isi']):
            paras = text.split('\n\n')
            out.append('isi.%s: %s' % (lang, paras[0]))
            for extra in paras[1:]:
                out += ['', '  ' + extra]
    if 'kutipan' in p:
        out += ['kutipan.id: ' + p['kutipan'][0], 'kutipan.en: ' + p['kutipan'][1],
                'nama: ' + p['nama'], 'jabatan: ' + p['jabatan']]
    if 'kartu' in p:
        out.append('kartu:')
        for a, li, le in p['kartu']:
            out.append('  - angka: %s | label.id: %s | label.en: %s' % (a, li, le))
    if 'tabel' in p:
        out.append('tabel:')
        for cells in p['tabel']:
            out.append('  | ' + ' | '.join(cells) + ' |')
        if p.get('cek'):
            out.append('cek: ' + p['cek'])
        per = p.get('periode') or (periods if p.get('numeric') else None)
        if per:
            out.append('berjalan: 1')
            out.append('periode: ' + ', '.join(str(x) for x in per))
    out.append('sumber: ' + p.get('sumber', 'dummy' if p.get('dummy', True) else 'auto'))
    if p.get('dummy', True):
        out.append('dummy: ya')
    out.append('')
    return '\n'.join(out)


def render_chapters(chapters, pages, periods):
    total = len(pages)
    res = []
    for i, (no, slug, cid, cen, start) in enumerate(chapters):
        end = chapters[i + 1][4] - 1 if i + 1 < len(chapters) else total
        lines = ['# BAB %02d | id: %s | en: %s' % (no, cid, cen), '']
        for n in range(start, end + 1):
            lines.append(render_page(n, pages[n], periods))
        res.append(('%02d_%s.md' % (no, slug), '\n'.join(lines).rstrip() + '\n'))
    return res


def set_kv(text, key, value, after=None):
    pat = re.compile(r'^%s:.*$' % re.escape(key), re.M)
    if pat.search(text):
        return pat.sub(lambda m: '%s: %s' % (key, value), text, count=1)
    if after:
        return re.sub(r'^(%s:.*)$' % re.escape(after), lambda m: m.group(1) + '\n%s: %s' % (key, value), text, count=1, flags=re.M)
    return text


def config_text(text, jenis, divider, chapters, total):
    """Return the config text with jenis, divider, jumlah-halaman and the BAB table set to this arrangement."""
    text = set_kv(text, 'jenis', jenis)
    text = set_kv(text, 'jumlah-halaman', str(total))
    text = set_kv(text, 'divider', str(divider), after='facing')
    table = ['## BAB', '', '| no | slug | id | en | halaman-awal |', '|---|---|---|---|---|']
    for no, slug, cid, cen, start in chapters:
        table.append('| %02d | %s | %s | %s | %d |' % (no, slug, cid, cen, start))
    block = '\n'.join(table) + '\n\n'
    text, n = re.subn(r'^## BAB\n.*?(?=^## )', lambda m: block, text, count=1, flags=re.M | re.S)
    if not n:
        raise ValueError('config has no ## BAB section')
    return text
