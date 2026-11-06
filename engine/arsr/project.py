# -*- coding: utf-8 -*-
"""Project folder layout and the InDesign launchers.

<project>/
  data/     Markdown data (00_config.md + one file per chapter)
  source/   original DOCX / XLSX from the copywriter (input of import_docx.py)
  build/    build_plan.json, run_build.jsx, run_qa.jsx, report.indd
  logs/     every log and summary (validate, plan, build, QA, import)
"""
import os

FOLDERS = ('data', 'source', 'build', 'logs')

SOURCE_README = """Put the copywriter's original files here (DOCX, XLSX).
Then run:  python engine/run.py import <project>
The importer only reads this folder; it writes Markdown drafts to ../data and a report to ../logs.
Naming:  NN_chapter-name.docx  (for example 01_pendahuluan.docx) or one file for the whole report.
Letakkan berkas asli dari copywriter di sini (DOCX, XLSX). Importer hanya membaca folder ini.
"""


def ensure_skeleton(project_dir, with_data=True):
    """Create the missing folders (empty ones only). The one thing validate/plan write besides logs."""
    made = []
    for name in FOLDERS:
        if name == 'data' and not with_data:
            continue
        d = os.path.join(str(project_dir), name)
        if not os.path.isdir(d):
            os.makedirs(d)
            made.append(name)
    readme = os.path.join(str(project_dir), 'source', 'README.txt')
    if not os.path.exists(readme):
        with open(readme, 'w', encoding='utf-8', newline='\n') as f:
            f.write(SOURCE_README)
    return made


def _js_path(p):
    return os.path.abspath(p).replace('\\', '/').replace('"', '')


def write_launchers(project_dir, plan_path, engine_dir):
    """build/run_build.jsx and build/run_qa.jsx: one double-click per project, no pointer file needed."""
    out = []
    for name, script, what in (('run_build.jsx', 'build_report.jsx', 'build the report (run ONCE)'),
                               ('run_qa.jsx', 'qa_document.jsx', 'read-only QA of the open report')):
        body = ('#target indesign\n'
                '// ARSR launcher for this project: %s.\n'
                '// InDesign: File > Scripts > Scripts Panel > double-click this file. No dialog appears; read ../logs.\n'
                '$.global.ARSR_PLAN_PATH = "%s";\n'
                '#include "%s"\n') % (what, _js_path(plan_path), _js_path(os.path.join(engine_dir, 'jsx', script)))
        p = os.path.join(os.path.dirname(os.path.abspath(plan_path)), name)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(body)
        out.append(p)
    return out
