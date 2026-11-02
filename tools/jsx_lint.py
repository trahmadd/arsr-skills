# -*- coding: utf-8 -*-
"""ES3 / ExtendScript linter for .jsx files. Read-only. Usage: python tools/jsx_lint.py <file.jsx|folder> ...
Exit 0 = clean, 1 = findings. Catches the usual mistakes of AI-written InDesign scripts."""
import os
import re
import sys

RULES = [
    ('ES3-01', r'\b(let|const)\s+[A-Za-z_$]', 'let/const are not ES3; use var'),
    ('ES3-02', r'=>', 'arrow functions are not ES3'),
    ('ES3-03', r'\.(forEach|map|filter|reduce|some|every)\s*\(', 'Array.prototype.%s is not in ExtendScript; use a for loop'),
    ('ES3-04', r'\b(JSON)\s*\.', 'no JSON object in ExtendScript; eval("(" + text + ")")'),
    ('ES3-05', r'`', 'template literals are not ES3'),
    ('ES3-06', r'\bObject\.(keys|create|assign|entries|values)\b|\bArray\.isArray\b', 'ES5+ static method'),
    ('ES3-07', r'\.(trim|padStart|padEnd|includes|startsWith|endsWith|repeat)\s*\(', 'ES5+/ES6 method missing in ExtendScript'),
    ('ES3-08', r',\s*[}\]]', 'trailing comma (breaks ExtendScript)'),
    ('ES3-09', r'["\']use strict["\']', 'no strict mode in ExtendScript'),
    ('ES3-10', r'\b(class|import|export|async|await)\s+[A-Za-z_$({]', 'ES6 syntax'),
    ('ES3-11', r'\bfor\s*\(\s*(var\s+)?\w+\s+of\s', 'for...of is not ES3'),
    ('ES3-12', r'\.\.\.\w', 'spread/rest is not ES3'),
    ('ES3-13', r'\bindexOf\s*\(', 'Array.indexOf is missing; fine for strings only (check the receiver)'),
]
WARN_ONLY = ('ES3-13',)


def strip(src):
    """Blank out comments and string contents (keeps line numbers and length)."""
    out, i, n, st = [], 0, len(src), None
    while i < n:
        c = src[i]
        nx = src[i + 1] if i + 1 < n else ''
        if st is None:
            if c == '/' and nx == '/':
                while i < n and src[i] != '\n':
                    out.append(' ')
                    i += 1
                continue
            if c == '/' and nx == '*':
                while i < n and not (src[i] == '*' and i + 1 < n and src[i + 1] == '/'):
                    out.append('\n' if src[i] == '\n' else ' ')
                    i += 1
                out.append('  ')
                i += 2
                continue
            if c in '"\'':
                st = c
                out.append(c)
            elif c == '/' and re.search(r'[=(,:;!&|?{}\[]\s*$', ''.join(out[-40:])):
                j = i + 1
                while j < n and src[j] != '\n' and src[j] != '/':
                    j += 2 if src[j] == '\\' else 1
                out.append('/' + ' ' * (j - i - 1) + '/')
                i = j + 1
                continue
            else:
                out.append(c)
        else:
            if c == '\\':
                out.append('  ')
                i += 2
                continue
            if c == st:
                st = None
                out.append(c)
            else:
                out.append('\n' if c == '\n' else ' ')
        i += 1
    return ''.join(out)


def lint(path):
    raw = open(path, 'rb').read()
    findings = []
    for ln, line in enumerate(raw.split(b'\n'), 1):
        if any(b > 127 for b in line):
            findings.append(('ASCII-01', ln, 'non-ASCII character in code or comment; use \\uXXXX escapes', 'ERROR'))
    text = strip(raw.decode('utf-8', 'replace'))
    for rid, rx, msg in RULES:
        for m in re.finditer(rx, text):
            ln = text.count('\n', 0, m.start()) + 1
            findings.append((rid, ln, msg % m.group(1) if '%s' in msg else msg, 'WARN' if rid in WARN_ONLY else 'ERROR'))
    depth = 0
    for ch in text:
        depth += (ch in '({[') - (ch in ')}]')
    if depth:
        findings.append(('SYN-01', 0, 'unbalanced brackets (net %d)' % depth, 'ERROR'))
    return sorted(findings, key=lambda f: f[1])


def main(argv):
    files = []
    for a in argv or ['.']:
        if os.path.isdir(a):
            for r, _, fs in os.walk(a):
                files += [os.path.join(r, f) for f in fs if f.endswith(('.jsx', '.js'))]
        else:
            files.append(a)
    bad = 0
    for f in sorted(files):
        res = lint(f)
        for rid, ln, msg, lv in res:
            print('%s:%d: %s [%s] %s' % (f, ln, lv, rid, msg))
            bad += lv == 'ERROR'
    print('jsx_lint: %d file(s), %d error(s)' % (len(files), bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
