# -*- coding: utf-8 -*-
"""arsr command line.

  python engine/run.py validate <project_dir> [--log-dir DIR]
  python engine/run.py plan <project_dir>
  python engine/run.py new <project_dir> [--jenis LK|LT|LT+LK] [--divider 1|2] [--config my_00_config.md]
  python engine/run.py import <project_dir>            (DOCX/XLSX in <project>/source -> Markdown drafts in <project>/data)
  python engine/run.py dummy <out_dir> [...]           (same as new; kept for older instructions)

validate is read-only: it writes one log file (default: <project>/logs) and creates the empty folders
source/, build/, logs/ when they are missing. It never edits data or documents.
Exit code 0 = no errors, 1 = errors, 2 = bad usage.
"""
import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from arsr import dummy, importer, plan, project, validate  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog='run.py', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')
    v = sub.add_parser('validate', help='validate a project folder (read-only)')
    v.add_argument('project')
    v.add_argument('--log-dir', default=None, help='where to write the log (default: <project>/logs)')
    pl = sub.add_parser('plan', help='validate, then write build/build_plan.json for build_report.jsx')
    pl.add_argument('project')
    pl.add_argument('--log-dir', default=None)
    pl.add_argument('--no-pointer', action='store_true', help='do not write %%APPDATA%%\\ARSR\\last_plan.txt')
    im = sub.add_parser('import', help='read the Word/Excel files in <project>/source and write Markdown data to <project>/data')
    im.add_argument('project')
    im.add_argument('--gri-pages', type=int, default=4, help='pages reserved for the GRI content index (default 4)')
    im.add_argument('--ojk-pages', type=int, default=2, help='pages reserved for the POJK index (default 2)')
    for name, hlp in (('new', 'create a project folder (data, source, build, logs) with dummy data'),
                      ('dummy', 'same as new (older name)')):
        d = sub.add_parser(name, help=hlp)
        d.add_argument('out')
        d.add_argument('--template', default=os.path.join(HERE, '..', 'templates', 'dummy-company'))
        d.add_argument('--config', default=None, help='use this 00_config.md (company, year, palette) instead of the template one')
        d.add_argument('--jenis', default=None, choices=['LK', 'LT', 'LT+LK'], help='report type (default: the config value)')
        d.add_argument('--divider', default=None, choices=['1', '2'], help='chapter divider: 1 page or 2 facing pages (default: config, else 2)')
        d.add_argument('--force', action='store_true', help='overwrite an existing out folder')
    a = ap.parse_args(argv)
    if a.cmd == 'validate':
        if not os.path.isdir(a.project):
            print('not a folder: %s' % a.project)
            return 2
        project.ensure_skeleton(a.project, with_data=False)
        rep = validate.validate(a.project)
        p = rep.write(a.log_dir or os.path.join(a.project, 'logs'))
        print('ERROR %d | WARN %d | pages %d' % (rep.count('ERROR'), rep.count('WARN'), rep.pages))
        print('log: %s' % p)
        return 1 if rep.count('ERROR') else 0
    if a.cmd == 'plan':
        try:
            out, pl_, rep = plan.write(a.project)
        except plan.PlanError as e:
            e.report.write(a.log_dir or os.path.join(a.project, 'logs'))
            print(str(e))
            print('log: see ARSR_Validate_Log.txt')
            return 1
        print('plan: %s (%d pages)' % (out, len(pl_['pages'])))
        if not a.no_pointer:
            ptr = plan.write_pointer(out)
            if ptr:
                print('pointer: %s' % ptr)
        return 0
    if a.cmd == 'import':
        if not os.path.isdir(a.project):
            print('not a folder: %s' % a.project)
            return 2
        project.ensure_skeleton(a.project, with_data=False)
        return importer.main_cli(a.project, a.gri_pages, a.ojk_pages)
    if a.cmd in ('dummy', 'new'):
        if os.path.exists(a.out):
            if not a.force:
                print('%s exists; use --force to overwrite' % a.out)
                return 2
            shutil.rmtree(a.out)
        n = dummy.generate(a.template, a.out, a.config, jenis=a.jenis, divider=a.divider)
        project.ensure_skeleton(a.out)
        print('wrote %d chapter files + config to %s' % (n, os.path.join(a.out, 'data')))
        print('folders: data, source, build, logs')
        return 0
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
