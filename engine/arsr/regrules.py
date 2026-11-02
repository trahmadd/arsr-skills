# -*- coding: utf-8 -*-
"""Regulation rules (GRI-xx, OJK-xx). Run only for rule ids present in the active profile.

`ctx` comes from validate.Ctx. Everything here is read-only.
"""
import re

from . import catalog

GRI_2_RANGE = ['2-%d' % i for i in range(1, 31)]


def natkey(code):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', code)]


def std_number(token):
    m = re.match(r'^GRI (\d+)$', token) or re.match(r'^(\d+)-\d+$', token)
    return m.group(1) if m else None


def gri_problem(ctx, tok):
    """Return None when `tok` is a valid GRI code for the project's gri.versi, else (rule, message)."""
    cat = ctx.cat
    if re.fullmatch(r'GRI \d+', tok):
        row = cat.gri_std.get(tok)
        if not row:
            return ('GRI-01', 'unknown GRI standard %s (not in catalogs/gri.md)' % tok)
        num = tok[4:]
    elif re.fullmatch(r'\d+-\d+', tok):
        row = cat.gri_dis.get(tok)
        if not row:
            return ('GRI-01', 'unknown GRI code %s (not in catalogs/gri.md)' % tok)
        num = tok.split('-')[0]
    else:
        return ('GRI-01', 'malformed GRI code "%s" (use 302-1 or "GRI 101")' % tok)
    std = cat.gri_std.get('GRI ' + num)
    if std is not None:
        if std.get('status') == 'withdrawn':
            return ('GRI-03', '%s belongs to GRI %s which is withdrawn (%s)' % (tok, num, std.get('replaces', '')))
        eff = catalog.parse_date(std.get('effective'))
        if eff and eff > ctx.cutoff:
            return ('GRI-03', '%s: GRI %s is not effective under gri.versi %s' % (tok, num, ctx.versi))
    if num in ctx.replaced_std or tok in ctx.replaced_codes:
        return ('GRI-03', '%s is replaced under gri.versi %s (see catalogs/README.md)' % (tok, ctx.versi))
    return None


def _check_token(ctx, tok, where):
    prob = gri_problem(ctx, tok)
    if prob:
        ctx.rep.error(prob[0], where, prob[1])
        return False
    return True


def run(ctx):
    rules = ctx.rules
    rep = ctx.rep
    cat = ctx.cat
    cfg = ctx.cfg

    # ---- collect GRI usage
    used = {}      # code -> [page numbers]
    for p in ctx.pages:
        for tok in p.attr_list('gri'):
            used.setdefault(tok, []).append(p.n)
    omitted_gri = {}
    for r in ctx.rows('OMISI'):
        omitted_gri[r.get('kode', '')] = r
    topic_gri = {}
    for t in ctx.topics.values():
        for tok in [x.strip() for x in t.get('gri', '').split(',') if x.strip()]:
            topic_gri.setdefault(tok, []).append(t.get('id', ''))

    # ---- GRI-01 / GRI-03 on pages, topics, omissions
    valid_used = set()
    if 'GRI-01' in rules or 'GRI-03' in rules:
        for p in ctx.pages:
            for tok in p.attr_list('gri'):
                if _check_token(ctx, tok, ctx.where(p)):
                    valid_used.add(tok)
        for tok in topic_gri:
            _check_token(ctx, tok, 'config TOPIK')
        for code in omitted_gri:
            _check_token(ctx, code, 'config OMISI')

    # ---- GRI-02 aggregate warning for unverified codes
    if 'GRI-02' in rules:
        unv = []
        for tok in sorted(valid_used, key=natkey):
            row = cat.gri_std.get(tok) if tok.startswith('GRI ') else cat.gri_dis.get(tok)
            if row and row.get('verified', '').strip() != 'yes':
                unv.append(tok)
        if unv:
            rep.warn('GRI-02', 'catalogs/gri.md', '%d cited GRI code(s) have verified:no; check the official text before printing' % len(unv))
            rep.info('GRI-02', 'catalogs/gri.md', 'unverified codes cited: ' + ', '.join(unv))

    # ---- GRI-08 statement of use
    if 'GRI-08' in rules:
        if ctx.kv('REGULASI', 'pernyataan-penggunaan') not in ('in accordance with', 'with reference to'):
            rep.error('GRI-08', 'config REGULASI', 'pernyataan-penggunaan must be "in accordance with" or "with reference to"')

    # ---- GRI-07 omission reasons
    if 'GRI-07' in rules:
        for code, r in omitted_gri.items():
            if not r.get('alasan.id', '').strip() or not r.get('alasan.en', '').strip():
                rep.error('GRI-07', 'config OMISI', 'omission %s needs alasan.id and alasan.en' % code)

    accordance = ctx.kv('REGULASI', 'pernyataan-penggunaan') == 'in accordance with'
    cover_level = 'ERROR' if accordance else 'WARN'

    # ---- GRI-04 GRI 2 coverage
    if 'GRI-04' in rules:
        for code in GRI_2_RANGE:
            if code in cat.gri_dis and code not in used and code not in omitted_gri:
                rep.add(cover_level, 'GRI-04', 'pages', 'GRI %s is not cited on any page and not listed in OMISI' % code)

    # ---- GRI-05 material topics
    if 'GRI-05' in rules:
        for code in ('3-1', '3-2'):
            if code not in used:
                rep.error('GRI-05', 'pages', 'GRI %s is not cited on any page' % code)
        for tid in ctx.topics:
            ok = any('3-3' in p.attr_list('gri') and tid in p.attr_list('topik') for p in ctx.pages)
            if not ok:
                rep.error('GRI-05', 'config TOPIK', 'topic %s has no page with gri 3-3 and topik %s' % (tid, tid))
        for p in ctx.pages:
            if '3-3' in p.attr_list('gri') and not p.attr_list('topik'):
                rep.warn('GRI-05', ctx.where(p), 'page cites 3-3 but has no topik attribute')

    # ---- GRI-06 / GRI-09 topic standards
    material_std = set()
    for tok in topic_gri:
        n = std_number(tok)
        if n:
            material_std.add(n)
    if 'GRI-06' in rules:
        for p in ctx.pages:
            for tok in p.attr_list('gri'):
                n = std_number(tok)
                if n and int(n) >= 200 and n not in material_std and gri_problem(ctx, tok) is None:
                    rep.warn('GRI-06', ctx.where(p), '%s belongs to GRI %s which is not a material topic standard in config TOPIK' % (tok, n))
    if 'GRI-09' in rules:
        for n in sorted(material_std, key=int):
            if int(n) < 200:
                continue
            for code in sorted((c for c in cat.gri_dis if c.startswith(n + '-')), key=natkey):
                if gri_problem(ctx, code) is not None:
                    continue
                if code not in used and code not in omitted_gri:
                    rep.warn('GRI-09', 'pages', 'material standard GRI %s: disclosure %s is neither cited nor omitted' % (n, code))

    # ---- OJK
    ojk_used = {}
    for p in ctx.pages:
        for tok in p.attr_list('ojk'):
            ojk_used.setdefault(tok, []).append(p)
    omit_ojk = {r.get('kode', '') for r in ctx.rows('OMISI', 'omisi-ojk')}
    omit_seojk = {r.get('kode', '') for r in ctx.rows('OMISI', 'omisi-seojk')}

    if 'OJK-01' in rules:
        for p in ctx.pages:
            for tok in p.attr_list('ojk'):
                if tok not in cat.ojk:
                    rep.error('OJK-01', ctx.where(p), 'unknown OJK code %s (not in catalogs/ojk.md)' % tok)
        for code in omit_ojk:
            if code not in cat.ojk:
                rep.error('OJK-01', 'config omisi-ojk', 'unknown OJK code %s' % code)
    if 'OJK-02' in rules:
        for p in ctx.pages:
            for tok in p.attr_list('seojk'):
                if tok not in cat.seojk:
                    rep.error('OJK-02', ctx.where(p), 'unknown SEOJK code %s (not in catalogs/seojk.md)' % tok)
        for code in omit_seojk:
            if code not in cat.seojk:
                rep.error('OJK-02', 'config omisi-seojk', 'unknown SEOJK code %s' % code)
    if 'OJK-03' in rules:
        for code in sorted(cat.ojk, key=natkey):
            if code not in ojk_used and code not in omit_ojk:
                rep.error('OJK-03', 'pages', 'OJK %s is on no page and not listed in omisi-ojk' % code)
        for table in ('omisi-ojk', 'omisi-seojk'):
            for r in ctx.rows('OMISI', table):
                if not r.get('alasan.id', '').strip() or not r.get('alasan.en', '').strip():
                    rep.error('GRI-07' if 'GRI-07' in rules else 'OJK-03', 'config ' + table,
                              'omission %s needs alasan.id and alasan.en' % r.get('kode', ''))
    if 'OJK-04' in rules:
        for code, plist in ojk_used.items():
            m = cat.mapping.get(code)
            if not m:
                continue
            sugg = [x.strip() for x in m.get('gri', '').split(',') if x.strip()]
            sugg = [x for x in sugg if gri_problem(ctx, x) is None]
            if not sugg:
                continue
            for p in plist:
                if not any(s in p.attr_list('gri') for s in sugg):
                    rep.warn('OJK-04', ctx.where(p), 'OJK %s cited but none of its suggested GRI codes (%s)' % (code, ', '.join(sugg)))
    if 'OJK-05' in rules:
        if not any(p.tipe == 'indeks-ojk' for p in ctx.pages):
            rep.error('OJK-05', 'pages', 'no page with tipe indeks-ojk (OJK G.4 disclosure index)')
    if 'OJK-06' in rules and 'LT' in ctx.kv('PROYEK', 'jenis'):
        seojk_used = {tok for p in ctx.pages for tok in p.attr_list('seojk')}
        for code in sorted(cat.seojk, key=natkey):
            if code not in seojk_used and code not in omit_seojk:
                rep.error('OJK-06', 'pages', 'SEOJK %s is on no page and not listed in omisi-seojk' % code)
    if 'OJK-08' in rules:
        since = ctx.kv('PROYEK', 'berdiri')
        try:
            long_ops = (int(ctx.kv('PROYEK', 'tahun-laporan')) - int(since)) > 3 if since else True
        except ValueError:
            long_ops = True
        if long_ops:
            for p in ctx.pages:
                codes = p.attr_list('ojk')
                needs = any(c in ('B.1', 'B.3', 'F.2', 'F.3') or (c.startswith('F.') and c[2:].isdigit() and int(c[2:]) >= 17) for c in codes)
                if needs:
                    for periods in ctx.table_periods.get(p.n, []):
                        if periods != 3:
                            rep.warn('OJK-08', ctx.where(p), 'economic/social table has %d period column(s); 3 expected for companies operating more than 3 years' % periods)
    if 'OJK-09' in rules:
        try:
            if int(ctx.kv('PROYEK', 'tahun-terbit')) != int(ctx.kv('PROYEK', 'tahun-laporan')) + 1:
                rep.warn('OJK-09', 'config PROYEK', 'tahun-terbit is not tahun-laporan + 1')
        except ValueError:
            pass
        d = catalog.parse_date(ctx.kv('REGULASI', 'tanggal-terbit'))
        if d and d > ctx.cutoff:
            rep.warn('OJK-09', 'config REGULASI', 'tanggal-terbit %s is after the effective cutoff of gri.versi %s' % (d, ctx.versi))
