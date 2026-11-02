# -*- coding: utf-8 -*-
"""Read-only validator for arsr project data (Python side). Never modifies any file."""
import os
import re
from pathlib import Path

from . import catalog, mdparse, numfmt, regrules
from .report import Report

REQ_KV = {
    'PROYEK': ['nama-perusahaan', 'nama-singkat', 'kode-emiten', 'tahun-laporan', 'tahun-terbit', 'tema.id', 'tema.en', 'jenis'],
    'HALAMAN': ['ukuran', 'facing', 'bleed-mm', 'jumlah-halaman', 'margin-atas-mm', 'margin-bawah-mm',
                'margin-dalam-mm', 'margin-luar-mm', 'kolom', 'gutter-mm'],
    'FONT': ['font-utama', 'font-angka', 'ukuran-dasar-pt', 'leading-dasar-pt'],
    'REGULASI': ['profil-regulasi', 'gri.versi', 'pernyataan-penggunaan', 'tanggal-terbit'],
    'KONTAK': ['email', 'telepon', 'alamat.id', 'alamat.en', 'web'],
    'FORMAT': ['format-angka-tabel', 'satuan-ribuan', 'satuan-desimal'],
}
REQ_TABLES = {
    ('WARNA', 'tabel'): ['swatch', 'hex'],
    ('OMISI', 'tabel'): ['kode', 'alasan.id', 'alasan.en'],
    ('OMISI', 'omisi-ojk'): ['kode', 'alasan.id', 'alasan.en'],
    ('OMISI', 'omisi-seojk'): ['kode', 'alasan.id', 'alasan.en'],
    ('BAB', 'tabel'): ['no', 'slug', 'id', 'en', 'halaman-awal'],
    ('TOPIK', 'tabel'): ['id', 'nama.id', 'nama.en', 'gri'],
}
SWATCHES = ['Primary', 'Secondary', 'Accent 1', 'Accent 2', 'Neutral Dark', 'Neutral Light',
            'Background', 'Highlight', 'Terang', 'Terang 2']

REQ_PAGE = {
    'sampul': ['judul.id', 'judul.en', 'subjudul.id', 'subjudul.en', 'tahun'],
    'divider': ['judul.id', 'judul.en'],
    'teks': ['judul.id', 'judul.en', 'isi.id', 'isi.en'],
    'kartu': ['judul.id', 'judul.en', 'kartu'],
    'kutipan': ['kutipan.id', 'kutipan.en', 'nama', 'jabatan'],
    'tabel': ['judul.id', 'judul.en', 'tabel'],
    'daftar-isi': ['judul.id', 'judul.en'],
    'indeks-gri': ['judul.id', 'judul.en'],
    'indeks-ojk': ['judul.id', 'judul.en'],
    'indeks-seojk': ['judul.id', 'judul.en'],
}
KNOWN_KEYS = set(['judul.id', 'judul.en', 'subjudul.id', 'subjudul.en', 'tahun', 'isi.id', 'isi.en',
                  'kutipan.id', 'kutipan.en', 'nama', 'jabatan', 'gambar', 'kartu', 'tabel', 'cek',
                  'berjalan', 'lebar', 'periode', 'sumber', 'dummy'])
FORBIDDEN = [
    (re.compile(r'\[isi\]', re.I), '[isi]'),
    (re.compile(r'\[contoh\]', re.I), '[contoh]'),
    (re.compile(r'\bTBD\b'), 'TBD'),
    (re.compile(r'lorem ipsum', re.I), 'lorem ipsum'),
    (re.compile(r'</?[A-Za-z][A-Za-z0-9]*(\s[^<>]*)?/?>'), 'inline tag'),
]
CEK_OK = re.compile(r'^[0-9r+\-*/().\s]+$')


class Ctx(object):
    def __init__(self, cfg, rep, cat, project):
        self.cfg, self.rep, self.cat, self.project = cfg, rep, cat, Path(project)
        self.versi = self.kv('REGULASI', 'gri.versi')
        self.cutoff = catalog.CUTOFF.get(self.versi, catalog.CUTOFF['pra-2027'])
        self.replaced_std, self.replaced_codes = catalog.replaced_sets(cat, self.cutoff)
        self.pages = []
        self.topics = {}
        self.table_periods = {}
        self.rules = {}
        self.style = self.kv('FORMAT', 'format-angka-tabel') or 'id'

    def kv(self, section, key, default=''):
        return mdparse.cfg_kv(self.cfg, section, key, default)

    def rows(self, section, name='tabel'):
        return mdparse.cfg_rows(self.cfg, section, name)

    def rel(self, path):
        try:
            return str(Path(path).resolve().relative_to(self.project.resolve())).replace('\\', '/')
        except ValueError:
            return str(path)

    def where(self, page, line=None):
        return '%s:%d (HAL %d)' % (self.rel(page.file), line or page.line, page.n)


# ------------------------------------------------------------------ config

def check_config(ctx):
    rep, cfg = ctx.rep, ctx.cfg
    cf = 'data/00_config.md'
    for n, msg in cfg['problems']:
        rep.error('CFG-01', '%s:%d' % (cf, n), msg)
    for sec, keys in REQ_KV.items():
        if sec not in cfg['sections']:
            rep.error('CFG-01', cf, 'missing section ## %s' % sec)
            continue
        for k in keys:
            if not ctx.kv(sec, k):
                rep.error('CFG-01', cf, 'missing key %s in ## %s' % (k, sec))
    for (sec, name), cols in REQ_TABLES.items():
        s = cfg['sections'].get(sec)
        if s is None:
            if sec not in cfg['sections']:
                rep.error('CFG-01', cf, 'missing section ## %s' % sec)
            continue
        t = s['tables'].get(name)
        if t is None:
            rep.error('CFG-01', cf, 'missing table %s in ## %s' % (name, sec))
        elif t['headers'] != cols:
            rep.error('CFG-01', '%s:%d' % (cf, t['line']), 'table %s/%s header must be: %s' % (sec, name, ' | '.join(cols)))
    # values
    if ctx.kv('PROYEK', 'jenis') and ctx.kv('PROYEK', 'jenis') not in ('LK', 'LT', 'LT+LK'):
        rep.error('CFG-02', cf, 'jenis must be LK, LT or LT+LK')
    for k in ('tahun-laporan', 'tahun-terbit'):
        v = ctx.kv('PROYEK', k)
        if v and not re.fullmatch(r'\d{4}', v):
            rep.error('CFG-02', cf, '%s must be a 4-digit year' % k)
    jp = ctx.kv('HALAMAN', 'jumlah-halaman')
    if jp and (not jp.isdigit() or int(jp) % 4 != 0 or int(jp) == 0):
        rep.error('CFG-02', cf, 'jumlah-halaman must be a positive multiple of 4')
    if ctx.versi and ctx.versi not in catalog.CUTOFF:
        rep.error('CFG-02', cf, 'gri.versi must be one of: %s' % ', '.join(sorted(catalog.CUTOFF)))
    if ctx.kv('REGULASI', 'tanggal-terbit') and not catalog.parse_date(ctx.kv('REGULASI', 'tanggal-terbit')):
        rep.error('CFG-02', cf, 'tanggal-terbit must be YYYY-MM-DD')
    if ctx.kv('FORMAT', 'format-angka-tabel') and ctx.kv('FORMAT', 'format-angka-tabel') not in ('id', 'en'):
        rep.error('CFG-02', cf, 'format-angka-tabel must be id or en')
    sw = {r.get('swatch'): r.get('hex', '') for r in ctx.rows('WARNA')}
    for name in SWATCHES:
        if name not in sw:
            rep.error('CFG-02', cf, 'swatch %s missing in ## WARNA' % name)
        elif not re.fullmatch(r'#[0-9A-Fa-f]{6}', sw[name]):
            rep.error('CFG-02', cf, 'swatch %s hex must be #RRGGBB' % name)
    for name in sw:
        if name not in SWATCHES:
            rep.error('CFG-02', cf, 'unknown swatch %s (only tints are allowed beyond the 10 swatches)' % name)
    for r in ctx.rows('TOPIK'):
        tid = r.get('id', '')
        if not re.fullmatch(r'T\d{2}', tid):
            rep.error('CFG-02', '%s:%d' % (cf, r['_line']), 'topic id "%s" must look like T01' % tid)
        elif tid in ctx.topics:
            rep.error('CFG-02', '%s:%d' % (cf, r['_line']), 'duplicate topic id %s' % tid)
        ctx.topics[tid] = r
    if not ctx.rows('BAB'):
        rep.error('CFG-01', cf, 'BAB table has no rows')


# ------------------------------------------------------------------- pages

def analyse_table(ctx, page, key):
    rep = ctx.rep
    t = mdparse.parse_table(key)
    for n, msg in t['problems']:
        rep.error('STR-07', ctx.where(page, n), msg)
    hdr = t['headers']
    if not hdr:
        rep.error('STR-07', ctx.where(page, key.line), 'table has no header row')
        return None
    cols, i, ok = [], 0, True
    while i < len(hdr):
        c = hdr[i]
        if c.startswith('id:'):
            if i + 1 < len(hdr) and hdr[i + 1].startswith('en:'):
                cols.append(('text', c[3:].strip(), hdr[i + 1][3:].strip()))
                i += 2
                continue
            rep.error('STR-07', ctx.where(page, t['header_line']), 'header cell "%s" must be followed by an en: cell' % c)
            ok = False
        elif c.startswith('en:'):
            rep.error('STR-07', ctx.where(page, t['header_line']), 'header cell "%s" has no preceding id: cell' % c)
            ok = False
        else:
            if not c:
                rep.error('STR-06', ctx.where(page, t['header_line']), 'empty header cell')
            cols.append(('num', c))
        i += 1
    if not ok:
        return None
    seen_num = False
    for c in cols:
        if c[0] == 'num':
            seen_num = True
        elif seen_num:
            rep.error('STR-07', ctx.where(page, t['header_line']), 'text columns must come before period columns')
            break
    exp = sum(2 if c[0] == 'text' else 1 for c in cols)
    parsed = []
    for cells, ln in zip(t['rows'], t['row_lines']):
        if len(cells) != exp:
            rep.error('STR-07', ctx.where(page, ln), 'row has %d cells, header defines %d' % (len(cells), exp))
            parsed.append(None)
            continue
        j, row = 0, []
        for c in cols:
            if c[0] == 'text':
                row.append((cells[j], cells[j + 1]))
                j += 2
            else:
                row.append(cells[j])
                j += 1
        for cell in cells:
            if not cell:
                rep.error('STR-06', ctx.where(page, ln), 'empty table cell')
                break
        parsed.append(row)
    if not parsed:
        rep.error('STR-07', ctx.where(page, key.line), 'table has no data rows')
    labels = [c[1] for c in cols if c[0] == 'num']
    periods = len(labels)
    ctx.table_periods.setdefault(page.n, []).append(periods)
    # berjalan / periode / lebar
    bj = page.get('berjalan').strip()
    if periods == 0:
        if bj not in ('', '0'):
            rep.error('STR-08', ctx.where(page), 'berjalan set but table has no period columns')
    elif bj and (not bj.isdigit() or int(bj) > periods):
        rep.error('STR-08', ctx.where(page), 'berjalan must be 0..%d' % periods)
    per = page.get('periode').strip()
    if per:
        want = [x.strip() for x in per.split(',')]
        if want != labels:
            rep.error('STR-08', ctx.where(page), 'periode (%s) does not match header period columns (%s)' % (', '.join(want), ', '.join(labels)))
    if periods and re.fullmatch(r'\d{4}', labels[-1]) and labels[-1] != ctx.kv('PROYEK', 'tahun-laporan'):
        rep.warn('NUM-04', ctx.where(page), 'last period column is %s, tahun-laporan is %s' % (labels[-1], ctx.kv('PROYEK', 'tahun-laporan')))
    lb = page.get('lebar').strip()
    if lb:
        parts = [x.strip() for x in lb.split(',')]
        if len(parts) != len(cols) or not all(re.fullmatch(r'\d+(\.\d+)?', x) for x in parts):
            rep.error('STR-08', ctx.where(page), 'lebar needs %d numbers in mm (one per logical column)' % len(cols))
    # NUM-03 number format
    for ci, c in enumerate(cols):
        if c[0] != 'num':
            continue
        for ri, row in enumerate(parsed):
            if row is None:
                continue
            cell = row[ci]
            if cell in ('-', '–', ''):
                continue
            if numfmt.parse_number(cell, ctx.style) is None:
                rep.warn('NUM-03', ctx.where(page, t['row_lines'][ri]), 'cell "%s" is not a number in format-angka-tabel "%s"' % (cell, ctx.style))
    return {'cols': cols, 'rows': parsed, 'row_lines': t['row_lines'], 'dummy_rows': t['dummy_rows']}


def run_cek(ctx, page, key, info):
    rep = ctx.rep
    rows, cols = info['rows'], info['cols']
    numcols = [i for i, c in enumerate(cols) if c[0] == 'num']
    for formula in [f.strip() for f in key.text().replace('\n', ';').split(';') if f.strip()]:
        w = ctx.where(page, key.line)
        if '=' not in formula:
            rep.error('NUM-01', w, 'cek formula needs "=": %s' % formula)
            continue
        lhs, rhs = [x.strip() for x in formula.split('=', 1)]
        m = re.fullmatch(r'r(\d+)', lhs)
        if not m or not CEK_OK.match(rhs):
            rep.error('NUM-01', w, 'bad cek formula (use r3 = r1 + r2): %s' % formula)
            continue
        li = int(m.group(1))
        refs = set(int(x) for x in re.findall(r'r(\d+)', rhs)) | set([li])
        if any(r < 1 or r > len(rows) for r in refs):
            rep.error('NUM-01', w, 'cek refers to a row outside 1..%d: %s' % (len(rows), formula))
            continue
        for ci in numcols:
            vals, bad = {}, False
            for r in refs:
                row = rows[r - 1]
                pn = numfmt.parse_number(row[ci], ctx.style) if row is not None else None
                if pn is None:
                    bad = True
                    break
                vals[r] = pn
            label = cols[ci][1]
            if bad:
                rep.error('NUM-01', w, 'cannot verify "%s" in column %s: non-numeric cell' % (formula, label))
                continue
            expr = re.sub(r'r(\d+)', lambda mm: '(%r)' % vals[int(mm.group(1))][0], rhs)
            try:
                val = eval(expr, {'__builtins__': {}}, {})
            except Exception as e:  # noqa
                rep.error('NUM-01', w, 'cek "%s" failed in column %s: %s' % (formula, label, e))
                continue
            tol = 10 ** (-vals[li][1]) + 1e-9
            if abs(val - vals[li][0]) > tol:
                rep.error('NUM-01', w, 'cek "%s" fails in column %s: expected %s, data has %s' % (
                    formula, label, numfmt.fmt_num(val, vals[li][1], ctx.style), rows[li - 1][ci]))


def check_page(ctx, page, dummy_stats):
    rep = ctx.rep
    w = ctx.where(page)
    for n, msg in page.problems:
        rep.error('STR-12', ctx.where(page, n), msg)
    tipe = page.tipe
    if tipe not in REQ_PAGE:
        rep.error('STR-03', w, 'tipe "%s" is not a known page type (%s)' % (tipe, ', '.join(sorted(REQ_PAGE))))
        return
    for k in REQ_PAGE[tipe]:
        if k not in page.keys or not page.keys[k].has_content():
            rep.error('STR-04', w, 'type %s requires key %s' % (tipe, k))
    for name, key in page.keys.items():
        if name not in KNOWN_KEYS:
            rep.warn('STR-11', ctx.where(page, key.line), 'unknown key "%s" (see page-types.md)' % name)
        if not key.has_content():
            if name in REQ_PAGE[tipe]:
                continue  # already reported by STR-04
            rep.error('STR-06', ctx.where(page, key.line), 'key %s is empty' % name)
            continue
        for pat, label in FORBIDDEN:
            if pat.search(key.text()):
                rep.error('STR-06', ctx.where(page, key.line), 'forbidden text (%s) in key %s' % (label, name))
        if name.endswith('.id') and name[:-3] + '.en' not in page.keys:
            rep.error('STR-05', ctx.where(page, key.line), 'key %s has no %s.en' % (name, name[:-3]))
        if name.endswith('.en') and name[:-3] + '.id' not in page.keys:
            rep.error('STR-05', ctx.where(page, key.line), 'key %s has no %s.id' % (name, name[:-3]))
    for tid in page.attr_list('topik'):
        if tid not in ctx.topics:
            rep.error('STR-09', w, 'topik %s is not defined in config TOPIK' % tid)
    d = page.get('dummy').strip()
    if d and d.lower() != 'ya':
        rep.error('STR-04', w, 'dummy must be "ya"')
    if page.is_dummy():
        dummy_stats['pages'].append(page.n)
    if 'kartu' in page.keys and page.keys['kartu'].has_content():
        cards, probs = mdparse.parse_cards(page.keys['kartu'])
        for n, msg in probs:
            rep.error('STR-04', ctx.where(page, n), msg)
        if not 3 <= len(cards) <= 6:
            rep.error('STR-04', w, 'kartu needs 3 to 6 cards, found %d' % len(cards))
        for c in cards:
            for f in ('angka', 'label.id', 'label.en'):
                if not c.get(f):
                    rep.error('STR-04', ctx.where(page, c['_line']), 'card needs %s' % f)
            for f, v in c.items():
                for pat, label in FORBIDDEN:
                    if f != '_line' and pat.search(str(v)):
                        rep.error('STR-06', ctx.where(page, c['_line']), 'forbidden text (%s) in card' % label)
    if 'tabel' in page.keys and page.keys['tabel'].has_content():
        info = analyse_table(ctx, page, page.keys['tabel'])
        if info is not None:
            dummy_stats['rows'] += sum(1 for f in info['dummy_rows'] if f)
            for ri, row in enumerate(info['rows']):
                if row is None:
                    continue
                for cell in row:
                    for s in (cell if isinstance(cell, tuple) else (cell,)):
                        for pat, label in FORBIDDEN:
                            if pat.search(s):
                                rep.error('STR-06', ctx.where(page, info['row_lines'][ri]), 'forbidden text (%s) in table' % label)
            if 'cek' in page.keys and page.keys['cek'].has_content():
                run_cek(ctx, page, page.keys['cek'], info)
    elif 'cek' in page.keys:
        rep.error('NUM-01', w, 'cek given on a page without a table')


# ---------------------------------------------------------------- main

def validate(project_dir, repo_root=None):
    project = Path(project_dir)
    root = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    rep = Report(str(project))
    cfg_path = project / 'data' / '00_config.md'
    if not cfg_path.is_file():
        rep.error('CFG-01', str(cfg_path), 'data/00_config.md not found')
        return rep
    cfg = mdparse.parse_config(str(cfg_path))
    cat = catalog.load(str(root / 'catalogs'))
    ctx = Ctx(cfg, rep, cat, project)
    check_config(ctx)

    data = project / 'data'
    files = sorted(f for f in os.listdir(str(data)) if re.match(r'^\d{2}_.+\.md$', f) and not f.startswith('00_'))
    bab = ctx.rows('BAB')
    expected = {}
    for r in bab:
        expected['%s_%s.md' % (r.get('no', ''), r.get('slug', ''))] = r
    for fn in expected:
        if fn not in files:
            rep.error('STR-01', 'data/' + fn, 'chapter file listed in config BAB is missing')
    chapters = []
    for fn in files:
        if fn not in expected:
            rep.error('STR-01', 'data/' + fn, 'chapter file is not listed in config BAB')
            continue
        ch = mdparse.parse_chapter(str(data / fn))
        for n, msg in ch['problems']:
            rep.error('STR-12', 'data/%s:%d' % (fn, n), msg)
        if ch['no'] is None:
            rep.error('STR-01', 'data/' + fn, 'missing "# BAB nn | id: ... | en: ..." header')
        elif ch['no'] != fn[:2]:
            rep.error('STR-01', 'data/' + fn, 'header says BAB %s but file prefix is %s' % (ch['no'], fn[:2]))
        row = expected[fn]
        if ch['pages'] and str(ch['pages'][0].n) != row.get('halaman-awal', ''):
            rep.error('STR-01', 'data/' + fn, 'first page is %d but config BAB halaman-awal is %s' % (ch['pages'][0].n, row.get('halaman-awal')))
        if not ch['pages']:
            rep.error('STR-01', 'data/' + fn, 'chapter has no "## HAL n" page blocks')
        chapters.append(ch)
        ctx.pages.extend(ch['pages'])
    rep.pages = len(ctx.pages)

    # page numbering
    for idx, p in enumerate(ctx.pages, 1):
        if p.n != idx:
            rep.error('STR-02', ctx.where(p), 'page number is %d, expected %d (numbers must be continuous from 1)' % (p.n, idx))
            break
    jp = ctx.kv('HALAMAN', 'jumlah-halaman')
    if jp.isdigit() and int(jp) != len(ctx.pages):
        rep.error('STR-02', 'data', 'data has %d pages but config jumlah-halaman is %s' % (len(ctx.pages), jp))
    if len(ctx.pages) % 4:
        rep.error('STR-02', 'data', 'page count %d is not a multiple of 4' % len(ctx.pages))

    ds = {'pages': [], 'rows': 0}
    for p in ctx.pages:
        check_page(ctx, p, ds)
    rep.info('DUM-01', 'pages', '%d page(s) flagged dummy: ya; %d table row(s) flagged {dummy}' % (len(ds['pages']), ds['rows']))
    if ds['pages']:
        rep.info('DUM-01', 'pages', 'dummy pages: ' + ', '.join(str(n) for n in ds['pages']))

    prof = ctx.kv('REGULASI', 'profil-regulasi')
    rules = catalog.profile_rule_ids(cat, prof) if prof else None
    if rules is None:
        if prof:
            rep.error('CFG-02', 'data/00_config.md', 'profil-regulasi "%s" not found in catalogs/profiles/' % prof)
    else:
        ctx.rules = rules
        regrules.run(ctx)
    rep.meta = ['profile: %s | gri.versi: %s | jenis: %s | style: %s' % (prof, ctx.versi, ctx.kv('PROYEK', 'jenis'), ctx.style)]
    ctx.chapters = chapters
    rep.ctx = ctx
    return rep
