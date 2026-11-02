# -*- coding: utf-8 -*-
"""arsr command line.

  python engine/run.py validate <project_dir> [--log-dir DIR]
  python engine/run.py plan <project_dir>
  python engine/run.py dummy <out_dir> [--template DIR]

validate is read-only: it writes one log file (default: your Desktop) and nothing else.
Exit code 0 = no errors, 1 = errors, 2 = bad usage.
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from arsr import dummy, plan, validate  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog='run.py', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    v = sub.add_parser('validate', help='validate a project folder (read-only)')
    v.add_argument('project')
    v.add_argument('--log-dir', default=None, help='where to write the log (default: Desktop)')
    pl = sub.add_parser('plan', help='validate, then write build/build_plan.json for build_report.jsx')
    pl.add_argument('project')
    pl.add_argument('--log-dir', default=None)
    pl.add_argument('--no-pointer', action='store_true', help='do not write %%APPDATA%%\\ARSR\\last_plan.txt')
    d = sub.add_parser('dummy', help='create a dummy project from the template config')
    d.add_argument('out')
    d.add_argument('--template', default=os.path.join(HERE, '..', 'templates', 'dummy-company'))
    d.add_argument('--force', action='store_true', help='overwrite an existing out folder')
    a = ap.parse_args(argv)
    if a.cmd == 'validate':
        if not os.path.isdir(a.project):
            print('not a folder: %s' % a.project)
            return 2
        rep = validate.validate(a.project)
        p = rep.write(a.log_dir)
        print('ERROR %d | WARN %d | pages %d' % (rep.count('ERROR'), rep.count('WARN'), rep.pages))
        print('log: %s' % p)
        return 1 if rep.count('ERROR') else 0
    if a.cmd == 'plan':
        try:
            out, pl_, rep = plan.write(a.project)
        except plan.PlanError as e:
            e.report.write(a.log_dir)
            print(str(e))
            print('log: see ARSR_Validate_Log.txt')
            return 1
        print('plan: %s (%d pages)' % (out, len(pl_['pages'])))
        if not a.no_pointer:
            ptr = plan.write_pointer(out)
            if ptr:
                print('pointer: %s' % ptr)
        return 0
    if a.cmd == 'dummy':
        if os.path.exists(a.out):
            if not a.force:
                print('%s exists; use --force to overwrite' % a.out)
                return 2
            shutil.rmtree(a.out)
        n = dummy.generate(a.template, a.out)
        print('wrote %d chapter files + config to %s' % (n, os.path.join(a.out, 'data')))
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
