# -*- coding: utf-8 -*-
"""Read DOCX and XLSX with the standard library only (both are ZIP files of XML). Read-only.

read_docx(path) -> (blocks, notes)
    blocks, in document order:
      ('p', style_name_lowercase, text, is_list)       text carries <b>..</b> for bold runs
      ('tbl', rows)                                    rows = [[cell, ...]], cell = [paragraph text, ...]
    notes: counts of things the importer cannot carry over (images, merged cells, nested tables, lists)
read_xlsx(path, style='id') -> {sheet name: rows}      rows as for 'tbl'; numbers formatted like the data files
"""
import re
import zipfile
import xml.etree.ElementTree as ET

from . import numfmt

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
S = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def _style_names(z):
    names = {}
    if 'word/styles.xml' not in z.namelist():
        return names
    root = ET.fromstring(z.read('word/styles.xml'))
    for st in root.iter(W + 'style'):
        n = st.find(W + 'name')
        if n is not None:
            names[st.get(W + 'styleId')] = n.get(W + 'val', '').lower()
    return names


def _runs(el, out, bold_ok):
    """Collect (text, bold) pieces of a paragraph, following hyperlinks and tracked insertions."""
    for ch in el:
        tag = ch.tag
        if tag == W + 'r':
            rpr = ch.find(W + 'rPr')
            bold = False
            if rpr is not None:
                b = rpr.find(W + 'b')
                bold = b is not None and b.get(W + 'val', '1') not in ('0', 'false')
            for x in ch:
                if x.tag == W + 't':
                    out.append((x.text or '', bold))
                elif x.tag == W + 'tab':
                    out.append((' ', bold))
                elif x.tag == W + 'br':
                    out.append(('\n', bold))
        elif tag in (W + 'hyperlink', W + 'ins', W + 'smartTag'):
            _runs(ch, out, bold_ok)


def _para(p, styles, notes):
    ppr = p.find(W + 'pPr')
    style = 'normal'
    is_list = False
    if ppr is not None:
        ps = ppr.find(W + 'pStyle')
        if ps is not None:
            style = styles.get(ps.get(W + 'val'), ps.get(W + 'val', '').lower())
        is_list = ppr.find(W + 'numPr') is not None
    if p.find('.//' + W + 'drawing') is not None or p.find('.//' + W + 'pict') is not None:
        notes['images'] = notes.get('images', 0) + 1
    pieces = []
    _runs(p, pieces, True)
    out, open_b = [], False
    for text, bold in pieces:
        if not text:
            continue
        if bold and not open_b:
            out.append('<b>')
            open_b = True
        elif not bold and open_b and text.strip():
            out.append('</b>')
            open_b = False
        out.append(text)
    if open_b:
        out.append('</b>')
    txt = ''.join(out)
    txt = re.sub(r'<b>(\s*)</b>', r'\1', txt)
    return style, txt, is_list


def _cell_paragraphs(tc, styles, notes):
    paras = []
    for ch in tc:
        if ch.tag == W + 'p':
            _st, txt, _l = _para(ch, styles, notes)
            for line in txt.split('\n'):          # a line break inside a cell also separates ID from EN
                if line.strip():
                    paras.append(re.sub(r'\s+', ' ', line).strip())
        elif ch.tag == W + 'tbl':
            notes['nested tables'] = notes.get('nested tables', 0) + 1
    return paras


def _table(tbl, styles, notes):
    rows = []
    for tr in tbl.findall(W + 'tr'):
        cells = []
        for tc in tr.findall(W + 'tc'):
            pr = tc.find(W + 'tcPr')
            if pr is not None and (pr.find(W + 'gridSpan') is not None or pr.find(W + 'vMerge') is not None):
                notes['merged cells'] = notes.get('merged cells', 0) + 1
            cells.append(_cell_paragraphs(tc, styles, notes))
        rows.append(cells)
    return rows


def _body(parent, styles, notes, blocks):
    for ch in parent:
        if ch.tag == W + 'p':
            style, txt, is_list = _para(ch, styles, notes)
            if is_list:
                notes['list items'] = notes.get('list items', 0) + 1
            blocks.append(('p', style, txt.replace('\n', ' '), is_list))
        elif ch.tag == W + 'tbl':
            blocks.append(('tbl', _table(ch, styles, notes)))
        elif ch.tag == W + 'sdt':
            c = ch.find(W + 'sdtContent')
            if c is not None:
                _body(c, styles, notes, blocks)


def read_docx(path):
    z = zipfile.ZipFile(path)
    try:
        styles = _style_names(z)
        root = ET.fromstring(z.read('word/document.xml'))
    finally:
        z.close()
    notes, blocks = {}, []
    body = root.find(W + 'body')
    _body(body, styles, notes, blocks)
    return blocks, notes


# ------------------------------------------------------------------ xlsx
BUILTIN_FMT = {1: '0', 2: '0.00', 3: '#,##0', 4: '#,##0.00', 9: '0%', 10: '0.00%'}


def _col(ref):
    n = 0
    for ch in re.match(r'[A-Z]+', ref).group(0):
        n = n * 26 + ord(ch) - 64
    return n - 1


def _decimals_of(code):
    code = re.sub(r'"[^"]*"', '', code or '').split(';')[0]
    m = re.search(r'\.(0+|#+)', code)
    return len(m.group(1)) if m else 0


def read_xlsx(path, style='id'):
    z = zipfile.ZipFile(path)
    try:
        names = z.namelist()
        shared = []
        if 'xl/sharedStrings.xml' in names:
            for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall(S + 'si'):
                shared.append(''.join(t.text or '' for t in si.iter(S + 't')))
        fmt_codes, xf_fmt = {}, []
        if 'xl/styles.xml' in names:
            sroot = ET.fromstring(z.read('xl/styles.xml'))
            for nf in sroot.iter(S + 'numFmt'):
                fmt_codes[int(nf.get('numFmtId'))] = nf.get('formatCode')
            cx = sroot.find(S + 'cellXfs')
            if cx is not None:
                for xf in cx.findall(S + 'xf'):
                    xf_fmt.append(int(xf.get('numFmtId', '0')))
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = dict((r.get('Id'), r.get('Target')) for r in rels)
        out = {}
        for sh in wb.iter(S + 'sheet'):
            t = target.get(sh.get(R + 'id'), '')
            t = t.lstrip('/')
            if not t.startswith('xl/'):
                t = 'xl/' + t
            root = ET.fromstring(z.read(t))
            rows = []
            for row in root.iter(S + 'row'):
                cells = {}
                for c in row.findall(S + 'c'):
                    ctype = c.get('t')
                    v = c.find(S + 'v')
                    if ctype == 'inlineStr':
                        text = ''.join(x.text or '' for x in c.iter(S + 't'))
                    elif v is None or v.text is None:
                        text = ''
                    elif ctype == 's':
                        text = shared[int(v.text)]
                    elif ctype in ('str', 'e'):
                        text = v.text
                    elif ctype == 'b':
                        text = 'TRUE' if v.text == '1' else 'FALSE'
                    else:
                        text = _num_text(float(v.text), c, xf_fmt, fmt_codes, style)
                    cells[_col(c.get('r'))] = text
                if cells:
                    width = max(cells) + 1
                    rows.append([[ln.strip() for ln in cells.get(i, '').split('\n') if ln.strip()] for i in range(width)])
            out[sh.get('name')] = rows
        return out
    finally:
        z.close()


def _num_text(val, c, xf_fmt, fmt_codes, style):
    sidx = int(c.get('s', '0') or 0)
    fid = xf_fmt[sidx] if sidx < len(xf_fmt) else 0
    code = fmt_codes.get(fid) or BUILTIN_FMT.get(fid)
    pct = bool(code) and '%' in code
    if code:
        dec = _decimals_of(code)
    else:
        txt = repr(val)
        dec = len(txt.split('.')[1]) if '.' in txt and not txt.endswith('.0') else 0
    if pct:
        return numfmt.fmt_num(val * 100.0, dec, style) + '%'
    return numfmt.fmt_num(val, dec, style)
