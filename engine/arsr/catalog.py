# -*- coding: utf-8 -*-
"""Load regulation catalogs (catalogs/*.md) and profiles (catalogs/profiles/*.md)."""
import os
import re
from datetime import date

from . import mdparse

CUTOFF = {'pra-2027': date(2026, 12, 31), '2027': date(2027, 12, 31)}


def read_tables(path):
    """Return list of tables: [{'headers': [...], 'rows': [dict]}] for every contiguous pipe table."""
    tables, cur = [], None
    for raw in mdparse.read_text(path).splitlines():
        if raw.startswith('|'):
            cells = mdparse.split_row(raw)
            if cur is None:
                cur = {'headers': cells, 'rows': []}
            elif mdparse.is_sep(cells):
                continue
            else:
                cur['rows'].append(dict(zip(cur['headers'], cells)))
        elif cur is not None:
            tables.append(cur)
            cur = None
    if cur is not None:
        tables.append(cur)
    return tables


def parse_date(s):
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', (s or '').strip())
    return date(int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def parse_replaces(text):
    """'GRI 304' / 'GRI 305-1..305-5, GRI 201-2' -> (set of standard numbers, set of codes)."""
    std, codes = set(), set()
    for tok in (text or '').split(','):
        tok = tok.strip()
        if not tok.startswith('GRI '):
            continue
        body = tok[4:].strip()
        m = re.fullmatch(r'(\d+)-(\d+)\.\.(\d+)-(\d+)', body)
        if m and m.group(1) == m.group(3):
            for i in range(int(m.group(2)), int(m.group(4)) + 1):
                codes.add('%s-%d' % (m.group(1), i))
        elif re.fullmatch(r'\d+-\d+', body):
            codes.add(body)
        elif re.fullmatch(r'\d+', body):
            std.add(body)
    return std, codes


class Catalog(object):
    def __init__(self):
        self.gri_std = {}   # 'GRI 302' -> row
        self.gri_dis = {}   # '302-1' -> row
        self.ojk = {}
        self.seojk = {}
        self.mapping = {}   # 'F.6' -> row
        self.profiles = {}  # name -> dict


def load(catalog_dir):
    cat = Catalog()
    for t in read_tables(os.path.join(catalog_dir, 'gri.md')):
        h = t['headers']
        for r in t['rows']:
            if 'status' in h:
                cat.gri_std[r['code']] = r
            elif 'standard' in h:
                cat.gri_dis[r['code']] = r
    for r in _first(os.path.join(catalog_dir, 'ojk.md')):
        cat.ojk[r['code']] = r
    for r in _first(os.path.join(catalog_dir, 'seojk.md')):
        cat.seojk[r['code']] = r
    for r in _first(os.path.join(catalog_dir, 'mapping-ojk-gri.md')):
        cat.mapping[r['ojk']] = r
    pdir = os.path.join(catalog_dir, 'profiles')
    if os.path.isdir(pdir):
        for fn in sorted(os.listdir(pdir)):
            if fn.endswith('.md'):
                p = parse_profile(os.path.join(pdir, fn))
                if p.get('profil'):
                    cat.profiles[p['profil']] = p
    return cat


def _first(path):
    t = read_tables(path)
    return t[0]['rows'] if t else []


def parse_profile(path):
    text = mdparse.read_text(path)
    prof = {'file': path, 'rules': {}}
    m = re.search(r'```\n(.*?)```', text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                prof[k.strip()] = v.strip()
    for t in read_tables(path):
        if t['headers'][:1] == ['id']:
            for r in t['rows']:
                prof['rules'][r['id']] = r.get('level', '')
    return prof


def profile_rule_ids(cat, name):
    """Rule ids of a profile including inherited ones. Returns dict id -> level, or None if unknown."""
    p = cat.profiles.get(name)
    if p is None:
        return None
    rules = {}
    if p.get('turunan'):
        parent = profile_rule_ids(cat, p['turunan'])
        if parent:
            rules.update(parent)
    rules.update(p['rules'])
    return rules


def replaced_sets(cat, cutoff):
    """Standards/codes replaced by standards effective on or before cutoff."""
    std, codes = set(), set()
    for row in cat.gri_std.values():
        eff = parse_date(row.get('effective'))
        if eff and eff <= cutoff:
            s, c = parse_replaces(row.get('replaces', ''))
            std |= s
            codes |= c
    return std, codes
