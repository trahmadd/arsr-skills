# -*- coding: utf-8 -*-
"""Number parsing and formatting for Indonesian (1.234,5) and English (1,234.5) styles."""
import re

_ID = re.compile(r'^(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$')
_EN = re.compile(r'^(\d{1,3}(,\d{3})+|\d+)(\.\d+)?$')


def parse_number(text, style):
    """Return (value, decimals) or None when text is not a number in `style`.

    Accepts a trailing %, a leading Rp, a leading minus and accounting
    parentheses for negatives.
    """
    t = (text or '').strip()
    if not t:
        return None
    neg = False
    if t.startswith('(') and t.endswith(')'):
        neg = True
        t = t[1:-1].strip()
    t = t.replace('%', '').replace('Rp', '').strip()
    if t.startswith('-'):
        neg = True
        t = t[1:].strip()
    if style == 'id':
        if not _ID.match(t):
            return None
        norm = t.replace('.', '').replace(',', '.')
        dec = len(t.split(',')[1]) if ',' in t else 0
    else:
        if not _EN.match(t):
            return None
        norm = t.replace(',', '')
        dec = len(t.split('.')[1]) if '.' in t else 0
    val = float(norm)
    return (-val if neg else val), dec


def fmt_num(value, decimals, style):
    """Format a number. style 'id' -> 1.234,5 ; 'en' -> 1,234.5"""
    s = '{:,.{d}f}'.format(value, d=decimals)
    if style == 'id':
        s = s.replace(',', '\x00').replace('.', ',').replace('\x00', '.')
    return s
