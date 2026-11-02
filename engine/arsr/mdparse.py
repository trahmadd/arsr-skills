# -*- coding: utf-8 -*-
"""Parse arsr Markdown data: 00_config.md and chapter files. Read-only, stdlib only."""
import re

KV = re.compile(r'^([a-z][a-z0-9.\-]*):[ \t]*(.*)$')
HEAD = re.compile(r'^# BAB (\d{2}) \| id: (.+?) \| en: (.+?)\s*$')
PAGE = re.compile(r'^## HAL (\d+)\s*(.*)$')
LIST_ATTRS = ('gri', 'ojk', 'seojk', 'topik')


def read_text(path):
    with open(path, encoding='utf-8-sig') as f:
        return f.read()


def split_row(line):
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    return [c.strip() for c in s.split('|')]


def is_sep(cells):
    return bool(cells) and all(re.match(r'^:?-{3,}:?$', c) for c in cells)


# --------------------------------------------------------------- config

def parse_config(path):
    """Return {'file','header','sections':{NAME:{'kv':{},'tables':{name:{headers,rows,line}}}},'problems':[]}"""
    cfg = {'file': path, 'header': '', 'sections': {}, 'problems': []}
    sec = None
    pending = None
    table = None

    def close():
        nonlocal table
        if table is not None and sec is not None:
            sec['tables'][table['name']] = table
        table = None

    for n, raw in enumerate(read_text(path).splitlines(), 1):
        line = raw.rstrip()
        if line.startswith('|'):
            cells = split_row(line)
            if table is None:
                table = {'name': pending or 'tabel', 'headers': cells, 'rows': [], 'line': n}
                pending = None
            elif is_sep(cells):
                pass
            elif len(cells) != len(table['headers']):
                cfg['problems'].append((n, 'table row has %d cells, header has %d' % (len(cells), len(table['headers']))))
            else:
                row = dict(zip(table['headers'], cells))
                row['_line'] = n
                table['rows'].append(row)
            continue
        close()
        if not line.strip():
            continue
        if line.startswith('## '):
            sec = {'kv': {}, 'tables': {}, 'line': n}
            cfg['sections'][line[3:].strip()] = sec
            pending = None
            continue
        if line.startswith('# '):
            cfg['header'] = line[2:].strip()
            continue
        m = KV.match(line)
        if m and sec is not None:
            if m.group(2) == '':
                pending = m.group(1)
            else:
                if m.group(1) in sec['kv']:
                    cfg['problems'].append((n, 'duplicate key %s' % m.group(1)))
                sec['kv'][m.group(1)] = m.group(2).strip()
            continue
        if sec is None:
            continue  # free text between the header and the first section is a comment
        if not m:
            cfg['problems'].append((n, 'cannot parse line: %s' % line[:60]))
    close()
    return cfg


def cfg_kv(cfg, section, key, default=''):
    return cfg['sections'].get(section, {}).get('kv', {}).get(key, default)


def cfg_rows(cfg, section, name='tabel'):
    t = cfg['sections'].get(section, {}).get('tables', {}).get(name)
    return t['rows'] if t else []


# -------------------------------------------------------------- chapters

class Key(object):
    def __init__(self, name, value, line):
        self.name = name
        self.value = value
        self.line = line
        self.block = []  # list of (lineno, text)

    def text(self):
        parts = ([self.value] if self.value else []) + [t for _, t in self.block]
        while parts and not parts[0].strip():
            parts.pop(0)
        while parts and not parts[-1].strip():
            parts.pop()
        return '\n'.join(parts)

    def has_content(self):
        return bool(self.text().strip())


class Page(object):
    def __init__(self, n, line):
        self.n = n
        self.line = line
        self.attrs = {}
        self.keys = {}
        self.problems = []
        self.file = ''

    def get(self, name):
        k = self.keys.get(name)
        return k.text() if k else ''

    @property
    def tipe(self):
        return self.attrs.get('tipe', '')

    def attr_list(self, name):
        v = self.attrs.get(name, [])
        return v if isinstance(v, list) else [v]

    def is_dummy(self):
        return self.get('dummy').strip().lower() == 'ya'


def _parse_attrs(rest, page):
    for part in rest.split('|'):
        part = part.strip()
        if not part:
            continue
        if ':' not in part:
            page.problems.append((page.line, 'attribute without colon: %s' % part))
            continue
        k, v = part.split(':', 1)
        k, v = k.strip(), v.strip()
        if k in LIST_ATTRS:
            page.attrs[k] = [x.strip() for x in v.split(',') if x.strip()]
        else:
            page.attrs[k] = v


def parse_chapter(path):
    """Return {'file','no','id','en','pages':[Page],'problems':[(line,msg)]}"""
    ch = {'file': path, 'no': None, 'id': '', 'en': '', 'pages': [], 'problems': []}
    page = None
    cur = None
    seen_head = False
    for n, raw in enumerate(read_text(path).splitlines(), 1):
        line = raw.rstrip()
        if line.startswith('# '):
            m = HEAD.match(line)
            if not m:
                ch['problems'].append((n, 'bad chapter header: %s' % line[:70]))
            elif seen_head:
                ch['problems'].append((n, 'second chapter header'))
            else:
                ch['no'], ch['id'], ch['en'] = m.group(1), m.group(2), m.group(3)
            seen_head = True
            cur = None
            continue
        if line.startswith('## '):
            m = PAGE.match(line)
            if not m:
                ch['problems'].append((n, 'bad page heading: %s' % line[:70]))
                page = None
                cur = None
                continue
            page = Page(int(m.group(1)), n)
            page.file = path
            _parse_attrs(m.group(2), page)
            ch['pages'].append(page)
            cur = None
            continue
        if page is None:
            if line.strip():
                ch['problems'].append((n, 'text before first page block: %s' % line[:50]))
            continue
        if not line.strip():
            if cur is not None:
                cur.block.append((n, ''))
            continue
        if line[0] in ' \t':
            if cur is None:
                page.problems.append((n, 'indented line without a key'))
            else:
                cur.block.append((n, line.strip()))
            continue
        m = KV.match(line)
        if not m:
            page.problems.append((n, 'cannot parse line: %s' % line[:60]))
            cur = None
            continue
        key = Key(m.group(1), m.group(2).strip(), n)
        if key.name in page.keys:
            page.problems.append((n, 'duplicate key %s' % key.name))
        page.keys[key.name] = key
        cur = key
    return ch


def parse_table(key):
    """Parse a `tabel:` block. Returns dict(headers, rows, row_lines, dummy_rows, problems)."""
    out = {'headers': None, 'rows': [], 'row_lines': [], 'dummy_rows': [], 'problems': [], 'line': key.line}
    for n, t in key.block:
        if not t.strip():
            continue
        if not t.startswith('|'):
            out['problems'].append((n, 'table line does not start with |'))
            continue
        cells = split_row(t)
        if is_sep(cells):
            continue
        if out['headers'] is None:
            out['headers'] = cells
            out['header_line'] = n
            continue
        flag = False
        if cells and cells[0].endswith('{dummy}'):
            cells[0] = cells[0][:-len('{dummy}')].strip()
            flag = True
        out['rows'].append(cells)
        out['row_lines'].append(n)
        out['dummy_rows'].append(flag)
    return out


def parse_cards(key):
    """Parse `kartu:` block lines '- angka: x | label.id: y | label.en: z'."""
    cards = []
    problems = []
    for n, t in key.block:
        if not t.strip():
            continue
        if not t.startswith('- '):
            problems.append((n, 'card line must start with "- "'))
            continue
        card = {'_line': n}
        for part in t[2:].split(' | '):
            if ':' not in part:
                problems.append((n, 'card field without colon: %s' % part))
                continue
            k, v = part.split(':', 1)
            card[k.strip()] = v.strip()
        cards.append(card)
    return cards, problems
