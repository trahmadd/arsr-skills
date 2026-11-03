# -*- coding: utf-8 -*-
"""Turn validated project data into build_plan.json for engine/jsx/build_report.jsx.

The plan holds resolved content and the registry (TOC, GRI/OJK/SEOJK indexes with physical page
numbers). It holds no styling. JSON is written with ASCII escapes so ExtendScript never meets an
encoding problem.
"""
import json
import os
import re

from . import mdparse, regrules, validate

SCHEMA = 1
# Rows one index page can hold (index row heights are fixed in build_report.jsx).
# Index pages are packed by ESTIMATED row height (mm) so that real InDesign tables do not overflow.
INDEX_MIN_ROW = 6.0        # minimum row height on index tables
INDEX_BUDGET_MM = 200.0    # table height available per index page (frame less header row, with safety)
LINE_MM = 3.2              # one 7.5 pt line at 9 pt leading (paragraf.tabel.indeks)
CHAR_MM = 1.45             # average character width at 7.5 pt, conservative
ROW_PAD_MM = 3.0           # space before + cell insets + slop


def est_lines(text, width_mm):
    cpl = max(1, int((width_mm - 4.0) / CHAR_MM))
    n = 0
    for part in str(text).split('\n'):
        n += max(1, -(-len(part) // cpl))
    return n


def est_row_mm(cells, cols, widths, min_row):
    mx = 1
    for c, col, w in zip(cells, cols, widths):
        if col['kind'] == 'text' and isinstance(c, (list, tuple)):
            n = est_lines(c[0] + ' ' + c[1], w) if col.get('inline') else est_lines(c[0], w) + est_lines(c[1], w)
        else:
            n = est_lines(c, w)
        mx = max(mx, n)
    return max(min_row, mx * LINE_MM + ROW_PAD_MM)


def pack_rows(rows, cols, widths, min_row):
    pages, cur, used = [], [], 0.0
    for r in rows:
        h = est_row_mm(r, cols, widths, min_row)
        if cur and used + h > INDEX_BUDGET_MM:
            pages.append(cur)
            cur, used = [], 0.0
        cur.append(r)
        used += h
    if cur:
        pages.append(cur)
    return pages
TOC_MM = {1: 11.0, 2: 6.0}   # entry heights used by build_report.jsx
TOC_PAGE_MM = 455.0         # two columns of the daftar-isi page
SKIP_TOC_TYPES = ('sampul', 'divider', 'daftar-isi', 'indeks-gri', 'indeks-ojk', 'indeks-seojk', 'kutipan')


class PlanError(Exception):
    def __init__(self, report):
        Exception.__init__(self, 'project has %d validation error(s); fix them first' % report.count('ERROR'))
        self.report = report


def hex_rgb(h):
    h = h.lstrip('#')
    return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]


def paragraphs(text):
    out = []
    for p in text.split('\n\n'):
        p = ' '.join(x.strip() for x in p.split('\n') if x.strip())
        if p:
            out.append(p)
    return out


def pair(page, key):
    return {'id': page.get(key + '.id'), 'en': page.get(key + '.en')}


def table_struct(page):
    t = mdparse.parse_table(page.keys['tabel'])
    hdr = t['headers']
    cols, i = [], 0
    while i < len(hdr):
        if hdr[i].startswith('id:'):
            cols.append({'kind': 'text', 'id': hdr[i][3:].strip(), 'en': hdr[i + 1][3:].strip()})
            i += 2
        else:
            cols.append({'kind': 'num', 'label': hdr[i]})
            i += 1
    rows = []
    for cells in t['rows']:
        j, row = 0, []
        for c in cols:
            if c['kind'] == 'text':
                row.append([cells[j], cells[j + 1]])
                j += 2
            else:
                row.append(cells[j])
                j += 1
        rows.append(row)
    nper = sum(1 for c in cols if c['kind'] == 'num')
    bj = page.get('berjalan').strip()
    berjalan = int(bj) if bj.isdigit() else (1 if nper else 0)
    widths = None
    if page.get('lebar').strip():
        widths = [float(x) for x in page.get('lebar').split(',')]
    return {'cols': cols, 'rows': rows, 'berjalan': berjalan, 'widths': widths,
            'dummyRows': [i for i, f in enumerate(t['dummy_rows']) if f]}


def pages_text(nums):
    """1, 2, 3, 5 -> '1-3, 5' (runs of three or more become ranges)."""
    ns = sorted(set(nums))
    out, i = [], 0
    while i < len(ns):
        j = i
        while j + 1 < len(ns) and ns[j + 1] == ns[j] + 1:
            j += 1
        if j - i >= 2:
            out.append('%d-%d' % (ns[i], ns[j]))
        else:
            out.extend(str(x) for x in ns[i:j + 1])
        i = j + 1
    return ', '.join(out)


def build(project_dir, repo_root=None):
    """Return (plan_dict, report). Raises PlanError when validation finds errors."""
    rep = validate.validate(project_dir, repo_root)
    if rep.count('ERROR'):
        raise PlanError(rep)
    ctx = rep.ctx
    cat, cfg = ctx.cat, ctx.cfg
    kv = ctx.kv
    y = int(kv('PROYEK', 'tahun-laporan'))

    # ---- chapters
    babs = sorted(ctx.rows('BAB'), key=lambda r: int(r['halaman-awal']))
    total = len(ctx.pages)
    chapters = []
    for i, r in enumerate(babs):
        start = int(r['halaman-awal'])
        end = int(babs[i + 1]['halaman-awal']) - 1 if i + 1 < len(babs) else total
        chapters.append({'no': int(r['no']), 'slug': r['slug'], 'id': r['id'], 'en': r['en'], 'start': start, 'end': end})

    def chapter_of(n):
        for c in chapters:
            if c['start'] <= n <= c['end']:
                return c['no']
        return 0

    # ---- pages
    pages, dummy_reg, toc = [], [], []
    for c in chapters:
        toc.append({'level': 1, 'id': c['id'], 'en': c['en'], 'page': c['start'], 'chapter': c['no']})
    for p in ctx.pages:
        d = {'n': p.n, 'tipe': p.tipe, 'chapter': chapter_of(p.n), 'dummy': p.is_dummy(),
             'gri': p.attr_list('gri'), 'ojk': p.attr_list('ojk'), 'seojk': p.attr_list('seojk'), 'topik': p.attr_list('topik')}
        if p.get('judul.id'):
            d['title'] = pair(p, 'judul')
        if p.get('subjudul.id'):
            d['subtitle'] = pair(p, 'subjudul')
        if p.get('sumber'):
            d['source'] = p.get('sumber')
        if p.get('tahun'):
            d['year'] = p.get('tahun')
        if p.get('isi.id'):
            d['text'] = {'id': paragraphs(p.get('isi.id')), 'en': paragraphs(p.get('isi.en'))}
        if p.get('kutipan.id'):
            d['quote'] = {'id': p.get('kutipan.id'), 'en': p.get('kutipan.en'), 'name': p.get('nama'), 'role': p.get('jabatan')}
        if 'kartu' in p.keys:
            cards, _ = mdparse.parse_cards(p.keys['kartu'])
            d['cards'] = [{'n': c['angka'], 'id': c['label.id'], 'en': c['label.en']} for c in cards]
        if 'tabel' in p.keys and p.keys['tabel'].has_content():
            d['table'] = table_struct(p)
        pages.append(d)
        if p.is_dummy():
            dummy_reg.append({'page': p.n, 'what': (d.get('title') or {}).get('id') or p.tipe})
        elif d.get('table'):
            for ri in d['table']['dummyRows']:
                dummy_reg.append({'page': p.n, 'what': 'table row %d' % (ri + 1)})
        if p.tipe not in SKIP_TOC_TYPES and d.get('title') and p.n != chapters[chapter_of(p.n) - 1]['start']:
            toc.append({'level': 2, 'id': d['title']['id'], 'en': d['title']['en'], 'page': p.n, 'chapter': d['chapter']})
    toc.sort(key=lambda e: (e['page'], e['level']))

    # ---- registry
    cited = {'gri': {}, 'ojk': {}, 'seojk': {}}
    for d in pages:
        for k in cited:
            for code in d[k]:
                cited[k].setdefault(code, []).append(d['n'])
    omit_gri = dict((r['kode'], r) for r in ctx.rows('OMISI'))
    omit_ojk = dict((r['kode'], r) for r in ctx.rows('OMISI', 'omisi-ojk'))
    omit_seojk = dict((r['kode'], r) for r in ctx.rows('OMISI', 'omisi-seojk'))

    def gri_sort(tok):
        m = re.match(r'^GRI (\d+)$', tok)
        if m:
            return (int(m.group(1)), -1)
        a, b = tok.split('-')
        return (int(a), int(b))

    gri_rows = []
    for tok in sorted(set(cited['gri']) | set(omit_gri), key=gri_sort):
        if tok.startswith('GRI '):
            srow = cat.gri_std.get(tok, {})
            std, title = tok, 'Standard (all disclosures): ' + srow.get('title', '')
        else:
            drow = cat.gri_dis.get(tok, {})
            sname = drow.get('standard', '')
            std = sname
            title = '%s %s' % (tok, drow.get('title', ''))
        om = omit_gri.get(tok)
        reason = [om['alasan.id'], om['alasan.en']] if om else '-'
        gri_rows.append({'std': std, 'disclosure': title, 'pages': pages_text(cited['gri'].get(tok, [])) or '-', 'reason': reason, 'code': tok})
    ojk_rows = []
    for code in sorted(cat.ojk, key=regrules.natkey):
        om = omit_ojk.get(code)
        ojk_rows.append({'code': code, 'id': cat.ojk[code]['title.id'], 'en': cat.ojk[code]['title.en'],
                         'pages': pages_text(cited['ojk'].get(code, [])) or '-',
                         'note': [om['alasan.id'], om['alasan.en']] if om else '-'})
    seojk_rows = []
    for code in sorted(cat.seojk, key=regrules.natkey):
        seojk_rows.append({'code': code, 'id': cat.seojk[code]['title.id'], 'en': cat.seojk[code]['title.en'],
                           'pages': pages_text(cited['seojk'].get(code, [])) or '-'})

    # ---- index tables, split across the index pages of each type
    errors = []
    for tipe, rows, make in (
            ('indeks-gri', gri_rows, lambda r: [r['std'], r['disclosure'], r['pages'], r['reason']]),
            ('indeks-ojk', ojk_rows, lambda r: [r['code'], [r['id'], r['en']], r['pages'], r['note']]),
            ('indeks-seojk', seojk_rows, lambda r: [r['code'], [r['id'], r['en']], r['pages']])):
        idx = [d for d in pages if d['tipe'] == tipe]
        if not idx:
            continue
        cols_n = None
        cols = {
            'indeks-gri': [{'kind': 'ref', 'id': 'Standar GRI', 'en': 'GRI Standard'}, {'kind': 'ref', 'id': 'Pengungkapan', 'en': 'Disclosure'},
                           {'kind': 'ref', 'id': 'Halaman', 'en': 'Page'}, {'kind': 'text', 'id': 'Alasan penghilangan', 'en': 'Reason for omission'}],
            'indeks-ojk': [{'kind': 'ref', 'id': 'Kode', 'en': 'Code'}, {'kind': 'text', 'id': 'Butir', 'en': 'Item', 'inline': True},
                           {'kind': 'ref', 'id': 'Halaman', 'en': 'Page'}, {'kind': 'text', 'id': 'Keterangan', 'en': 'Note'}],
            'indeks-seojk': [{'kind': 'ref', 'id': 'Kode', 'en': 'Code'}, {'kind': 'text', 'id': 'Butir', 'en': 'Item', 'inline': True},
                             {'kind': 'ref', 'id': 'Halaman', 'en': 'Page'}],
        }[tipe]
        widths = {'indeks-gri': [16, 100, 24, 30], 'indeks-ojk': [14, 100, 18, 38], 'indeks-seojk': [16, 116, 38]}[tipe]
        packed = pack_rows([make(r) for r in rows], cols, widths, INDEX_MIN_ROW)
        if len(packed) > len(idx):
            errors.append('PLN-01 | %s: needs %d page(s) by estimated row height but the data has %d; add %d index page(s) (total pages stay a multiple of 4)' % (
                tipe, len(packed), len(idx), len(packed) - len(idx)))
        for k, d in enumerate(idx):
            chunk = packed[k] if k < len(packed) else []
            d['table'] = {'cols': cols, 'rows': chunk, 'berjalan': 0, 'widths': widths, 'dummyRows': [], 'index': True, 'minRow': INDEX_MIN_ROW}

    # ---- TOC split across daftar-isi pages by height
    tp = [d for d in pages if d['tipe'] == 'daftar-isi']
    if tp:
        k, used = 0, 0.0
        for d in tp:
            d['toc'] = []
        for e in toc:
            h = TOC_MM[e['level']]
            if used + h > TOC_PAGE_MM:
                k += 1
                used = 0.0
            if k >= len(tp):
                errors.append('PLN-01 | daftar-isi: %d entries do not fit %d page(s); add a daftar-isi page' % (len(toc), len(tp)))
                break
            tp[k]['toc'].append(e)
            used += h
    if errors:
        for e in errors:
            rep.error(e.split(' | ')[0], 'plan', e.split(' | ', 1)[1])
        raise PlanError(rep)

    sw = dict((r['swatch'], hex_rgb(r['hex'])) for r in ctx.rows('WARNA'))
    plan = {
        'schema': SCHEMA,
        'meta': {'company': kv('PROYEK', 'nama-perusahaan'), 'short': kv('PROYEK', 'nama-singkat'), 'code': kv('PROYEK', 'kode-emiten'),
                 'year': y, 'pubYear': int(kv('PROYEK', 'tahun-terbit')), 'theme': {'id': kv('PROYEK', 'tema.id'), 'en': kv('PROYEK', 'tema.en')},
                 'jenis': kv('PROYEK', 'jenis'), 'griVersi': ctx.versi, 'statement': kv('REGULASI', 'pernyataan-penggunaan'),
                 'numberStyle': ctx.style, 'projectDir': os.path.abspath(str(project_dir))},
        'doc': {'pageCount': total, 'width': 210, 'height': 297, 'facing': kv('HALAMAN', 'facing') == 'ya',
                'bleed': float(kv('HALAMAN', 'bleed-mm')),
                'margins': {'top': float(kv('HALAMAN', 'margin-atas-mm')), 'bottom': float(kv('HALAMAN', 'margin-bawah-mm')),
                            'inside': float(kv('HALAMAN', 'margin-dalam-mm')), 'outside': float(kv('HALAMAN', 'margin-luar-mm'))},
                'columns': int(kv('HALAMAN', 'kolom')), 'gutter': float(kv('HALAMAN', 'gutter-mm'))},
        'colors': sw,
        'fonts': {'main': kv('FONT', 'font-utama'), 'num': kv('FONT', 'font-angka'),
                  'size': float(kv('FONT', 'ukuran-dasar-pt')), 'leading': float(kv('FONT', 'leading-dasar-pt'))},
        'chapters': chapters,
        'pages': pages,
        'registry': {'toc': toc, 'gri': gri_rows, 'ojk': ojk_rows, 'seojk': seojk_rows},
        'dummyRegister': dummy_reg,
    }
    return plan, rep


def write(project_dir, out_path=None, repo_root=None):
    plan, rep = build(project_dir, repo_root)
    out = out_path or os.path.join(str(project_dir), 'build', 'build_plan.json')
    d = os.path.dirname(os.path.abspath(out))
    if not os.path.isdir(d):
        os.makedirs(d)
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(plan, f, ensure_ascii=True, indent=1, sort_keys=True)
        f.write('\n')
    return out, plan, rep


def write_pointer(plan_path):
    """Tell the JSX where the newest plan is: %APPDATA%\\ARSR\\last_plan.txt (Windows). Returns path or None."""
    base = os.environ.get('APPDATA')
    if not base:
        return None
    d = os.path.join(base, 'ARSR')
    if not os.path.isdir(d):
        os.makedirs(d)
    p = os.path.join(d, 'last_plan.txt')
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(os.path.abspath(plan_path).replace('\\', '/') + '\n')
    return p
