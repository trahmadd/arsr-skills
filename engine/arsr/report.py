# -*- coding: utf-8 -*-
"""Validation report: collects findings, writes ONE plain-text log (default: Desktop)."""
import os
from pathlib import Path


def desktop_dir():
    """Best guess of the user's Desktop (OneDrive-redirected Desktop first). Falls back to cwd."""
    home = Path.home()
    cands = []
    for env in ('OneDrive', 'OneDriveConsumer', 'OneDriveCommercial'):
        v = os.environ.get(env)
        if v:
            cands.append(Path(v) / 'Desktop')
    cands.append(home / 'Desktop')
    for c in cands:
        if c.is_dir():
            return c
    return Path.cwd()


class Report(object):
    def __init__(self, project, title='ARSR validation'):
        self.project = project
        self.title = title
        self.items = []   # (level, rule, where, message)
        self.pages = 0
        self.meta = []
        self.ctx = None

    def add(self, level, rule, where, msg):
        self.items.append((level, rule, where, msg))

    def error(self, rule, where, msg):
        self.add('ERROR', rule, where, msg)

    def warn(self, rule, where, msg):
        self.add('WARN', rule, where, msg)

    def info(self, rule, where, msg):
        self.add('INFO', rule, where, msg)

    def count(self, level):
        return sum(1 for i in self.items if i[0] == level)

    def has(self, rule, level=None):
        return any(i[1] == rule and (level is None or i[0] == level) for i in self.items)

    def rules(self, level=None):
        return sorted(set(i[1] for i in self.items if level is None or i[0] == level))

    def render(self):
        out = ['ERROR %d | WARN %d | pages %d' % (self.count('ERROR'), self.count('WARN'), self.pages),
               '%s | project: %s' % (self.title, self.project)]
        out.extend(self.meta)
        for level in ('ERROR', 'WARN', 'INFO'):
            rows = [i for i in self.items if i[0] == level]
            out.append('')
            out.append('--- %s (%d)' % (level, len(rows)))
            for _, rule, where, msg in rows:
                out.append('[%s] %s | %s' % (rule, where, msg))
        return '\n'.join(out) + '\n'

    def write(self, log_dir=None, name='ARSR_Validate_Log.txt'):
        d = Path(log_dir) if log_dir else desktop_dir()
        d.mkdir(parents=True, exist_ok=True)
        p = d / name
        with open(str(p), 'w', encoding='utf-8') as f:
            f.write(self.render())
        return p
