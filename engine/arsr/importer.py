# -*- coding: utf-8 -*-
"""Import the copywriter's DOCX (and XLSX) from <project>/source into Markdown data files in <project>/data.

Word convention (see docs/penulisan-word.md):
  Heading 1  = chapter      "Profil Perusahaan | Company Profile"   (Indonesian | English)
  Heading 2  = one section  "Identitas | Identity"                  (one page, or more when it is long)
  Heading 3  = sub heading inside a section
  Normal     = Indonesian paragraph        style "English" = English paragraph
  Meta       = one line of attributes      "tipe: tabel | gri: 2-1 | ojk: C.2 | cek: r3 = r1 - r2"
  Table      = Word table; a header cell with two lines (ID, EN) is a text column, one line is a period column.
Cover, table of contents, dividers, index pages, padding pages and the back cover are generated, not written.
The importer reads source/ and writes data/ (the previous data is copied to build/data_before_import first).
"""
import os
import re
import shutil
import sys

from . import arrange, docxread, mdparse
from .arrange import INTRO

TEXT_BUDGET = 3600        # characters (Indonesian + English) per text page
INTRO_BUDGET = 800        # intro text above a table
TABLE_ROWS = 14           # body rows per table page
IGNORE_STYLES = ('title', 'subtitle', 'toc heading', 'header', 'footer', 'comment text', 'table of figures')
ATTR_LISTS = ('gri', 'ojk', 'seojk', 'topik')
META_KEYS = set(ATTR_LISTS + ('tipe', 'cek', 'dummy', 'nama', 'jabatan', 'slug', 'tabel', 'sumber', 'lebar'))
PAGE_TIPE = ('teks', 'tabel', 'kartu', 'kutipan')


class Log(object):
    def __init__(self):
        self.rows = []

    def add(self, level, where, msg):
        self.rows.append((level, where, msg))

    def count(self, level):
        return sum(1 for r in self.rows if r[0] == level)

    def render(self, extra=''):
        head = 'ERROR %d | WARN %d | import%s' % (self.count('ERROR'), self.count('WARN'), extra)
        order = {'ERROR': 0, 'WARN': 1, 'INFO': 2}
        body = ['%s | %s | %s' % r for r in sorted(self.rows, key=lambda r: order[r[0]])]
        return head + '\n' + '\n'.join(body) + '\n'


def strip_bold(blk):
    """The data files are plain text; bold formatting from Word is dropped here."""
    rb = re.compile(r'</?b>')
    if blk[0] == 'p':
        return ('p', blk[1], rb.sub('', blk[2]), blk[3])
    return ('tbl', [[[rb.sub('', ln) for ln in cell] for cell in row] for row in blk[1]])


def split_bi(text, log, where):
    parts = [t.strip() for t in re.split(r'\s+\|\s+', re.sub(r'</?b>', '', text))]
    if len(parts) >= 2:
        return parts[0], ' | '.join(parts[1:]) if len(parts) > 2 else parts[1]
    log.add('WARN', where, 'heading "%s" has no " | English" part; the Indonesian text is used for both' % text)
    return parts[0], parts[0]


def parse_meta(text, log, where):
    out = {}
    for part in re.split(r'\s+\|\s+', text.strip()):
        if ':' not in part:
            if part.strip():
                log.add('WARN', where, 'Meta part "%s" ignored (use key: value)' % part.strip())
            continue
        k, v = part.split(':', 1)
        k, v = k.strip().lower(), v.strip()
        if k not in META_KEYS:
            log.add('WARN', where, 'unknown Meta key "%s" ignored' % k)
            continue
        out[k] = v
    return out


def clean_text(t, log, where):
    """Data values are plain text (the build adds the tags): bold marks are dropped, a stray < is replaced."""
    t = re.sub(r'</?b>', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    if '<' in t or '>' in t:
        log.add('WARN', where, 'text contains < or >: replaced by ( and ) to avoid a visible tag')
        t = t.replace('<', '(').replace('>', ')')
    return t


# ------------------------------------------------------------------ parse blocks into chapters
def build_model(blocks, log):
    chapters, ch, sec = [], None, None
    pre = 0
    for src, blk in blocks:
        kind = blk[0]
        where = src
        if kind == 'p':
            _k, style, text, _lst = blk
            text = text.strip()
            if style in IGNORE_STYLES or not text:
                continue
            if style == 'heading 1':
                if '<b>' in text:
                    text = re.sub(r'</?b>', '', text)
                ch = {'title': split_bi(text, log, where + ' H1'), 'meta': {}, 'intro': {'id': [], 'en': []}, 'sections': [], 'src': src}
                chapters.append(ch)
                sec = None
            elif ch is None:
                pre += 1
            elif style == 'heading 2':
                sec = {'title': split_bi(text, log, where + ' H2'), 'meta': {}, 'items': [], 'src': src}
                ch['sections'].append(sec)
            elif style == 'meta':
                (sec or ch)['meta'].update(parse_meta(text, log, where + ' Meta'))
            elif style == 'heading 3':
                if sec is None:
                    a, b = split_bi(text, log, where + ' H3')
                    ch['intro']['id'].append(a)
                    ch['intro']['en'].append(b)
                    continue
                a, b = split_bi(text, log, where + ' H3')
                sec['items'].append(('h3', a, b))
            elif style.startswith('heading'):
                log.add('WARN', where, 'style "%s" is not used by the engine; paragraph kept as text' % style)
                if sec is None:
                    ch['intro']['id'].append(text)
                else:
                    sec['items'].append(('para', 'id', text))
            else:
                lang = 'en' if style == 'english' else 'id'
                if sec is None:
                    ch['intro'][lang].append(text)
                else:
                    sec['items'].append(('para', lang, text))
        else:
            if ch is None:
                pre += 1
                continue
            if sec is None:
                log.add('WARN', where, 'table before the first Heading 2 of a chapter is ignored')
                continue
            sec['items'].append(('table', blk[1]))
    if pre:
        log.add('INFO', 'source', '%d paragraph(s) before the first Heading 1 ignored (cover note, author, etc.)' % pre)
    return chapters


def map_chapters(chapters, struct, log):
    """chapter -> structure row: Meta slug, then title match, then order."""
    by_slug = dict((r['slug'], r) for r in struct)
    used = set()
    for i, ch in enumerate(chapters):
        row = None
        slug = ch['meta'].get('slug')
        if slug:
            row = by_slug.get(slug)
            if row is None:
                log.add('ERROR', ch['src'], 'Meta slug "%s" is not a chapter of this report type (%s)' % (slug, ', '.join(sorted(by_slug))))
        else:
            t = [x.casefold() for x in ch['title']]
            for r in struct:
                if r['slug'] not in used and (r['id'].casefold() in t or r['en'].casefold() in t):
                    row = r
                    break
            if row is None and i < len(struct) and struct[i]['slug'] not in used:
                row = struct[i]
                log.add('WARN', ch['src'], 'Heading 1 "%s" matched to chapter "%s" by order; add Meta "slug: %s" under it to be explicit' % (ch['title'][0], row['slug'], row['slug']))
            if row is None:
                log.add('ERROR', ch['src'], 'cannot map Heading 1 "%s" to a chapter; add Meta "slug: ..."' % ch['title'][0])
        if row is not None:
            if row['slug'] in used:
                log.add('ERROR', ch['src'], 'chapter "%s" appears twice' % row['slug'])
            used.add(row['slug'])
        ch['row'] = row
    return used


# ------------------------------------------------------------------ pages
def lists(meta):
    d = {}
    for a in ATTR_LISTS:
        if meta.get(a):
            d[a] = [x.strip() for x in meta[a].split(',') if x.strip()]
    return d


def convert_table(rows, meta, log, where, style):
    """rows = [[cell paragraphs]] -> (md rows, periods). Header cell with 2+ lines = text column, 1 line = period column."""
    if len(rows) < 2:
        log.add('ERROR', where, 'table needs a header row and at least one data row')
        return None, None
    head = rows[0]
    kinds = ['text' if len(c) >= 2 else 'num' for c in head]
    if kinds[0] != 'text':
        log.add('WARN', where, 'first table column should be a text column with two header lines (Indonesian, English)')
    md, periods = [], []
    hdr = []
    for c, k in zip(head, kinds):
        if k == 'text':
            hdr += ['id: ' + c[0], 'en: ' + c[1]]
        else:
            hdr.append(c[0] if c else '')
            periods.append(c[0] if c else '')
    md.append(hdr)
    for ri, row in enumerate(rows[1:], 2):
        if len(row) != len(head):
            log.add('ERROR', where, 'table row %d has %d cells, header has %d' % (ri, len(row), len(head)))
            return None, None
        cells = []
        for c, k in zip(row, kinds):
            if k == 'text':
                a = c[0] if c else '-'
                b = c[1] if len(c) > 1 else a
                cells += [a.replace('|', '/'), b.replace('|', '/')]
            else:
                cells.append(' '.join(c).replace('|', '/') if c else '-')
        md.append(cells)
    return md, periods


def xlsx_rows(ref, xl_cache, source_dir, style, log, where):
    fname, _h, sheet = ref.partition('#')
    path = os.path.join(source_dir, fname.strip())
    if not os.path.isfile(path):
        log.add('ERROR', where, 'Meta tabel: file "%s" not found in source/' % fname)
        return None
    if path not in xl_cache:
        try:
            xl_cache[path] = docxread.read_xlsx(path, style)
        except Exception as e:  # corrupt or unsupported workbook
            log.add('ERROR', where, 'cannot read %s: %s' % (fname, e))
            return None
    sheets = xl_cache[path]
    name = sheet.strip() or list(sheets)[0]
    if name not in sheets:
        log.add('ERROR', where, 'sheet "%s" not found in %s (sheets: %s)' % (name, fname, ', '.join(sheets)))
        return None
    return sheets[name]


def title_pair(sec_title, n):
    a, b = sec_title
    if n:
        return (a + ' (lanjutan)', b + ' (continued)')
    return (a, b)


def chunk_text(ids, ens, budget):
    """Split paired paragraph lists into groups under the character budget."""
    n = max(len(ids), len(ens))
    groups, cur, used = [], ([], []), 0
    for i in range(n):
        a = ids[i] if i < len(ids) else ''
        b = ens[i] if i < len(ens) else ''
        size = len(a) + len(b)
        if cur[0] and used + size > budget:
            groups.append(cur)
            cur, used = ([], []), 0
        cur[0].append(a)
        cur[1].append(b)
        used += size
    if cur[0]:
        groups.append(cur)
    return groups


def text_pair(group):
    return ('\n\n'.join(x for x in group[0] if x), '\n\n'.join(x for x in group[1] if x))


def section_pages(sec, log, source_dir, xl_cache, style):
    where = '%s | %s' % (sec['src'], sec['title'][0])
    meta = sec['meta']
    ids, ens, tables = [], [], []
    for it in sec['items']:
        if it[0] == 'para':
            (ids if it[1] == 'id' else ens).append(clean_text(it[2], log, where))
        elif it[0] == 'h3':
            ids.append(clean_text(it[1], log, where))
            ens.append(clean_text(it[2], log, where))
        else:
            tables.append(it[1])
    if meta.get('tabel'):
        rows = xlsx_rows(meta['tabel'], xl_cache, source_dir, style, log, where)
        if rows is not None:
            tables.append(rows)
    if len(ids) != len(ens):
        log.add('WARN', where, '%d Indonesian and %d English paragraph(s); each Indonesian paragraph should have an English one' % (len(ids), len(ens)))
    tipe = meta.get('tipe') or ('tabel' if tables else 'teks')
    if tipe not in PAGE_TIPE:
        log.add('ERROR', where, 'Meta tipe "%s" must be one of %s' % (tipe, ', '.join(PAGE_TIPE)))
        return []
    base = {'sumber': 'docx: ' + sec['src']}
    if meta.get('dummy', '').lower() == 'ya':
        base['dummy'] = True
    else:
        base['dummy'] = False
    if meta.get('sumber'):
        base['sumber'] = meta['sumber']
    attrs = lists(meta)
    if tipe == 'kutipan':
        if not (meta.get('nama') and meta.get('jabatan')):
            log.add('ERROR', where, 'a kutipan section needs Meta "nama: ... | jabatan: ..."')
            return []
        pg = dict(base, tipe='kutipan', nama=meta['nama'], jabatan=meta['jabatan'], kutipan=(' '.join(ids), ' '.join(ens)))
        pg.update(attrs)
        return [pg]
    if tipe == 'kartu':
        if not tables:
            log.add('ERROR', where, 'a kartu section needs a table: one row per card (number | label with ID line and EN line)')
            return []
        cards = []
        for r in tables[0]:
            if len(r) < 2 or not r[0]:
                log.add('ERROR', where, 'card row needs a number cell and a label cell')
                return []
            lab = r[1]
            cards.append((r[0][0], lab[0], lab[1] if len(lab) > 1 else lab[0]))
        if len(cards) > 6:
            log.add('WARN', where, '%d cards; only 3 to 6 fit a page' % len(cards))
        pg = dict(base, tipe='kartu', judul=title_pair(sec['title'], 0), kartu=cards)
        if ids:
            pg['isi'] = text_pair((ids, ens))
        pg.update(attrs)
        return [pg]
    pages = []
    n = 0
    if tipe == 'teks' or not tables:
        for g in chunk_text(ids, ens, TEXT_BUDGET):
            pg = dict(base, tipe='teks', judul=title_pair(sec['title'], n), isi=text_pair(g))
            if n == 0:
                pg.update(attrs)
            pages.append(pg)
            n += 1
        if not pages:
            log.add('ERROR', where, 'section has no text and no table')
        return pages
    # tabel
    intro_len = sum(len(x) for x in ids) + sum(len(x) for x in ens)
    intro = None
    if ids or ens:
        if intro_len <= INTRO_BUDGET:
            intro = text_pair((ids, ens))
        else:
            for g in chunk_text(ids, ens, TEXT_BUDGET):
                pg = dict(base, tipe='teks', judul=title_pair(sec['title'], n), isi=text_pair(g))
                if n == 0:
                    pg.update(attrs)
                pages.append(pg)
                n += 1
    first = True
    for t in tables:
        md, periods = convert_table(t, meta, log, where, style)
        if md is None:
            return []
        head, body = md[0], md[1:]
        for k in range(0, len(body), TABLE_ROWS):
            pg = dict(base, tipe='tabel', judul=title_pair(sec['title'], n), tabel=[head] + body[k:k + TABLE_ROWS])
            if periods:
                pg['periode'] = periods
            if meta.get('cek') and len(body) <= TABLE_ROWS:
                pg['cek'] = meta['cek']
            if meta.get('lebar'):
                pg['lebar'] = meta['lebar']
            if first and intro:
                pg['isi'] = intro
            if n == 0 or (first and not pages):
                pg.update(attrs)
            pages.append(pg)
            n += 1
            first = False
        if meta.get('cek') and len(body) > TABLE_ROWS:
            log.add('WARN', where, 'cek formula ignored: the table was split over several pages; keep checked tables within %d rows' % TABLE_ROWS)
    return pages


def index_pages(jenis, gri_pages, ojk_pages):
    pg = []
    if jenis in ('LK', 'LT+LK'):
        for i in range(gri_pages):
            pg.append({'tipe': 'indeks-gri', 'judul': ('Indeks Konten GRI' + (' (lanjutan)' if i else ''), 'GRI Content Index' + (' (continued)' if i else '')),
                       'dummy': False, 'sumber': 'auto'})
        for i in range(ojk_pages):
            d = {'tipe': 'indeks-ojk', 'judul': ('Daftar Pengungkapan POJK 51/POJK.03/2017' + (' (lanjutan)' if i else ''),
                                                 'POJK 51/POJK.03/2017 Disclosure Index' + (' (continued)' if i else '')),
                 'dummy': False, 'sumber': 'auto'}
            if i == 0:
                d['ojk'] = ['G.4']
            pg.append(d)
    if jenis in ('LT', 'LT+LK'):
        pg.append({'tipe': 'indeks-seojk', 'judul': ('Indeks Silang SEOJK 16/SEOJK.04/2021', 'SEOJK 16/SEOJK.04/2021 Cross Index'),
                   'dummy': False, 'sumber': 'auto'})
    return pg


# ------------------------------------------------------------------ run
def run(project_dir, repo_root=None, gri_pages=4, ojk_pages=2):
    log = Log()
    project = os.path.abspath(str(project_dir))
    root = os.path.abspath(repo_root or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
    data, source = os.path.join(project, 'data'), os.path.join(project, 'source')
    cfg_path = os.path.join(data, '00_config.md')
    if not os.path.isfile(cfg_path):
        log.add('ERROR', 'data/00_config.md', 'not found; create the project first: python engine/run.py new <folder> --jenis ...')
        return log, None
    cfg = mdparse.parse_config(cfg_path)
    kv = lambda s, k: mdparse.cfg_kv(cfg, s, k)  # noqa: E731
    jenis = kv('PROYEK', 'jenis')
    sf = {'LK': 'lk.md', 'LT': 'lt.md', 'LT+LK': 'lt-lk.md'}.get(jenis)
    if not sf:
        log.add('ERROR', 'data/00_config.md', 'jenis must be LK, LT or LT+LK')
        return log, None
    divider = int(kv('HALAMAN', 'divider') or 1)
    style = kv('FORMAT', 'format-angka-tabel') or 'id'
    struct = mdparse.cfg_rows(mdparse.parse_config(os.path.join(root, 'structures', sf)), 'BAB')
    files = sorted(f for f in os.listdir(source) if f.lower().endswith('.docx') and not f.startswith('~$')) if os.path.isdir(source) else []
    if not files:
        log.add('ERROR', 'source', 'no .docx file in source/. Put the copywriter files there (see docs/penulisan-word.md)')
        return log, None
    blocks = []
    for f in files:
        try:
            bl, notes = docxread.read_docx(os.path.join(source, f))
        except Exception as e:
            log.add('ERROR', f, 'cannot read this file (%s). Save it again as .docx from Word' % e)
            continue
        blocks += [(f, strip_bold(b)) for b in bl]
        for k, v in sorted(notes.items()):
            log.add('WARN' if k != 'images' else 'INFO', f, '%d %s found; %s' % (v, k, 'images are placeholders in the layout, place them in InDesign' if k == 'images' else 'not carried over, check the result'))
    if log.count('ERROR'):
        return log, None
    chapters = build_model(blocks, log)
    if not chapters:
        log.add('ERROR', 'source', 'no Heading 1 found: every chapter starts with a Heading 1 paragraph')
        return log, None
    map_chapters(chapters, struct, log)
    by_slug = dict((c['row']['slug'], c) for c in chapters if c['row'] is not None)
    xl_cache = {}
    layout, intros, rows_out = [], {}, []
    year = kv('PROYEK', 'tahun-laporan')
    for idx, r in enumerate(struct):
        ch = by_slug.get(r['slug'])
        row = dict(r)
        pages = []
        if ch is not None:
            row['id'], row['en'] = ch['title']
            if ch['intro']['id'] or ch['intro']['en']:
                ci = [clean_text(x, log, ch['src']) for x in ch['intro']['id']]
                ce = [clean_text(x, log, ch['src']) for x in ch['intro']['en']]
                intros[r['slug']] = text_pair((ci, ce))
            for sec in ch['sections']:
                pages += section_pages(sec, log, source, xl_cache, style)
        elif r['slug'] != 'indeks':
            log.add('WARN', 'chapter ' + r['slug'], 'not found in the Word files; one dummy placeholder page was generated (flagged dummy: ya)')
        if not pages and r['slug'] != 'indeks':
            pages = [{'tipe': 'teks', 'judul': (row['id'], row['en']), 'isi': INTRO[r['slug']], 'dummy': True, 'sumber': 'placeholder'}]
        if idx == 0:
            cover = {'tipe': 'sampul', 'judul': (arrange.TITLE[jenis][0] + ' ' + year, arrange.TITLE[jenis][1] + ' ' + year),
                     'subjudul': (kv('PROYEK', 'tema.id'), kv('PROYEK', 'tema.en')), 'tahun': year, 'dummy': False, 'sumber': 'config'}
            toc = {'tipe': 'daftar-isi', 'judul': ('Daftar Isi', 'Table of Contents'), 'dummy': False, 'sumber': 'auto'}
            pages = [cover, toc] + pages
        if r['slug'] == 'indeks':
            pages += index_pages(jenis, gri_pages, ojk_pages)
            co = kv('PROYEK', 'nama-perusahaan')
            pages.append({'tipe': 'sampul', 'judul': (co, co), 'subjudul': (kv('PROYEK', 'tema.id'), kv('PROYEK', 'tema.en')),
                          'tahun': year, 'dummy': False, 'sumber': 'config'})
        layout.append((r['slug'], pages))
        rows_out.append(row)
    if log.count('ERROR'):
        return log, None
    chapters_out, pages_out = arrange.arrange(layout, rows_out, divider, intros=intros, dummy=False)
    for p in pages_out.values():
        if p['tipe'] == 'catatan':
            p['sumber'] = 'auto'
    n_pad = sum(1 for p in pages_out.values() if p['tipe'] == 'catatan')
    if n_pad:
        log.add('INFO', 'layout', '%d catatan (note) page(s) were added so two-page dividers start on a left page and the total is a multiple of 4' % n_pad)
    # write: back up the old data first
    backup = os.path.join(project, 'build', 'data_before_import')
    if os.path.isdir(backup):
        shutil.rmtree(backup)
    os.makedirs(os.path.dirname(backup), exist_ok=True)
    shutil.copytree(data, backup)
    for f in os.listdir(data):
        if re.match(r'^\d{2}_.+\.md$', f) and not f.startswith('00_'):
            os.remove(os.path.join(data, f))
    for fname, body in arrange.render_chapters(chapters_out, pages_out, []):
        with open(os.path.join(data, fname), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(body)
    text = arrange.config_text(mdparse.read_text(cfg_path), jenis, divider, chapters_out, len(pages_out))
    with open(cfg_path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    log.add('INFO', 'import', '%d Word file(s), %d chapters, %d pages written to data/; previous data kept in build/data_before_import' % (len(files), len(chapters_out), len(pages_out)))
    return log, {'pages': len(pages_out), 'chapters': len(chapters_out)}


def write_log(log, project_dir, info):
    d = os.path.join(str(project_dir), 'logs')
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, 'ARSR_Import_Log.txt')
    extra = ' | pages %d' % info['pages'] if info else ' | nothing written'
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(log.render(extra))
    return p


def main_cli(project, gri_pages, ojk_pages):
    log, info = run(project, gri_pages=gri_pages, ojk_pages=ojk_pages)
    p = write_log(log, project, info)
    print('ERROR %d | WARN %d | %s' % (log.count('ERROR'), log.count('WARN'), ('pages %d' % info['pages']) if info else 'nothing written'))
    print('log: %s' % p)
    return 1 if log.count('ERROR') else 0


if __name__ == '__main__':
    sys.exit(main_cli(sys.argv[1], 4, 2))
