# -*- coding: utf-8 -*-
"""Eval helper for testing skills on free models. Read-only except where stated.

  python tools/eval_check.py seed E2 <out_dir>        create a broken project (E2) or broken jsx (E3) to give the model
  python tools/eval_check.py snapshot                 save hashes of engine/ catalogs/ tools/ (before E1/E5)
  python tools/eval_check.py check E1 <project_dir>   grade the result; prints PASS/FAIL lines, exit 1 on any FAIL
Tasks: E1 new project  E2 fix data errors  E3 fix jsx lint errors  E5 design change via config only.
"""
import hashlib
import json
import os
import re
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from arsr import dummy, validate  # noqa: E402
import jsx_lint  # noqa: E402

SNAP = os.path.join(ROOT, 'evals', '.snapshot.json')
GUARDED = ('engine', 'catalogs', 'tools')
BAD_JSX = '''#target indesign
(function () {
    let names = ['Primary', 'Accent 1',];
    var total = 0;
    names.forEach(function (n) { total += n.length; });
    var f = (a) => a + 1;
    var label = "Laporan – 2025 ²";
    alert(`total ${total}`);
})();
'''


def rd(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def wr(p, t):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(t)


def hashes():
    out = {}
    for g in GUARDED:
        for r, _, fs in os.walk(os.path.join(ROOT, g)):
            if '__pycache__' in r:
                continue
            for n in fs:
                p = os.path.join(r, n)
                out[os.path.relpath(p, ROOT)] = hashlib.sha1(open(p, 'rb').read()).hexdigest()
    return out


def seed(task, out):
    if task == 'E2':
        dummy.generate(os.path.join(ROOT, 'templates', 'dummy-company'), out)
        f = os.path.join(out, 'data', '06_keberlanjutan.md')
        t = rd(f)
        t = t.replace('gri: ', 'gri: 999-9, ', 1)                 # unknown GRI code
        t = re.sub(r'(?m)^(isi\.en: ).*$', r'\1[isi]', t, count=1)   # forbidden placeholder
        wr(f, t)
        f = os.path.join(out, 'data', '00_config.md')
        wr(f, rd(f).replace('gri.versi: pra-2027', 'gri.versi: banana'))
        print('seeded 3 faults in %s; goal: validate shows ERROR 0' % out)
    elif task == 'E3':
        os.makedirs(out, exist_ok=True)
        wr(os.path.join(out, 'broken.jsx'), BAD_JSX)
        print('wrote %s; goal: python tools/jsx_lint.py <file> shows 0 errors and the script still does the same thing' % os.path.join(out, 'broken.jsx'))
    else:
        print('seed supports E2 and E3')
        return 2
    return 0


def check(task, target):
    res = []

    def ok(name, cond, why=''):
        res.append((bool(cond), name, why))
    if task in ('E1', 'E2', 'E5'):
        rep = validate.validate(target)
        ok('validate has 0 errors', rep.count('ERROR') == 0, '; '.join('%s %s' % (i[1], i[3][:60]) for i in rep.items if i[0] == 'ERROR')[:300])
        ok('no [isi]/TBD/lorem left', not any(re.search(r'\[isi\]|\[contoh\]|\bTBD\b|lorem ipsum', rd(os.path.join(target, 'data', f)), re.I)
                                              for f in os.listdir(os.path.join(target, 'data')) if f.endswith('.md')))
    if task in ('E1', 'E5'):
        if os.path.exists(SNAP):
            before = json.load(open(SNAP))
            changed = [k for k, v in hashes().items() if before.get(k) != v]
            ok('engine/catalogs/tools untouched', not changed, ', '.join(changed[:5]))
        else:
            ok('snapshot exists (run snapshot first)', False)
    if task == 'E1':
        cfg = rd(os.path.join(target, 'data', '00_config.md'))
        ok('company name changed from the dummy', 'Nusantara Contoh' not in cfg)
        ok('dummy flag kept on generated pages', 'dummy: ya' in ''.join(rd(os.path.join(target, 'data', f)) for f in os.listdir(os.path.join(target, 'data')) if f.endswith('.md')))
    if task == 'E5':
        cfg = rd(os.path.join(target, 'data', '00_config.md'))
        ok('palette changed in config', re.search(r'(?m)^\|\s*Primary\s*\|\s*#?([0-9A-Fa-f]{6})', cfg) is not None and '108282' not in cfg)
    if task == 'E3':
        p = target if target.endswith('.jsx') else os.path.join(target, 'broken.jsx')
        errs = [f for f in jsx_lint.lint(p) if f[3] == 'ERROR']
        ok('jsx_lint 0 errors', not errs, '; '.join('%s@%d' % (e[0], e[1]) for e in errs[:6]))
        t = rd(p)
        ok('still builds the name list and alert', 'Primary' in t and 'alert(' in t)
    for good, name, why in res:
        print('%s  %s%s' % ('PASS' if good else 'FAIL', name, '  (' + why + ')' if why and not good else ''))
    return 0 if all(r[0] for r in res) else 1


def main(a):
    if len(a) >= 1 and a[0] == 'snapshot':
        json.dump(hashes(), open(SNAP, 'w'), indent=0)
        print('snapshot saved: %s' % SNAP)
        return 0
    if len(a) == 3 and a[0] == 'seed':
        return seed(a[1], a[2])
    if len(a) == 3 and a[0] == 'check':
        return check(a[1], a[2])
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
