# -*- coding: utf-8 -*-
"""Tests for the arsr engine. Run: python -m unittest discover -s tests -v   (from the repo root)"""
import os
import re
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'engine'))

from arsr import catalog, dummy, mdparse, numfmt, plan, validate  # noqa: E402

TEMPLATE = os.path.join(ROOT, 'templates', 'dummy-company')


def run_cli(argv):
    import io
    import contextlib
    import run as runmod
    with contextlib.redirect_stdout(io.StringIO()):
        return runmod.main(argv)


def rd(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def wr(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='arsr_test_')
        cls.base = os.path.join(cls.tmp, 'base')
        dummy.generate(TEMPLATE, cls.base, jenis='LT+LK', divider='1')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def fresh(self):
        d = tempfile.mkdtemp(dir=self.tmp)
        p = os.path.join(d, 'p')
        shutil.copytree(self.base, p)
        return p

    def mutate(self, fname, old, new, count=1):
        p = self.fresh()
        f = os.path.join(p, 'data', fname)
        text = rd(f)
        self.assertIn(old, text, 'mutation anchor not found: %r' % old)
        wr(f, text.replace(old, new, count))
        return validate.validate(p)

    def assertRule(self, rep, rule, level='ERROR'):
        self.assertTrue(rep.has(rule, level), '%s %s not reported; got %s' % (level, rule, [(i[0], i[1], i[3][:80]) for i in rep.items if i[0] != 'INFO']))


class TestNumbers(unittest.TestCase):
    def test_parse_id(self):
        self.assertEqual(numfmt.parse_number('1.234,5', 'id'), (1234.5, 1))
        self.assertEqual(numfmt.parse_number('31,3%', 'id'), (31.3, 1))
        self.assertEqual(numfmt.parse_number('(12,0)', 'id'), (-12.0, 1))
        self.assertIsNone(numfmt.parse_number('1,234.5', 'id'))

    def test_parse_en(self):
        self.assertEqual(numfmt.parse_number('1,234.5', 'en'), (1234.5, 1))
        self.assertIsNone(numfmt.parse_number('1.234,5', 'en'))

    def test_roundtrip(self):
        self.assertEqual(numfmt.fmt_num(1234567.891, 2, 'id'), '1.234.567,89')
        self.assertEqual(numfmt.fmt_num(1234567.891, 2, 'en'), '1,234,567.89')


class TestParser(unittest.TestCase):
    def test_page_and_table(self):
        d = tempfile.mkdtemp()
        try:
            f = os.path.join(d, '01_x.md')
            wr(f, '# BAB 01 | id: A | en: B\n\n## HAL 1 | tipe: tabel | gri: 2-1, 3-3 | topik: T01\n'
                  'judul.id: J\njudul.en: K\nisi.id: p1\n\n  p2\nisi.en: q\n'
                  'tabel:\n  | id: A | en: B | 2024 |\n  | x {dummy} | y | 1 |\n')
            ch = mdparse.parse_chapter(f)
            self.assertEqual(ch['no'], '01')
            p = ch['pages'][0]
            self.assertEqual(p.attrs['gri'], ['2-1', '3-3'])
            self.assertEqual(p.get('isi.id'), 'p1\n\np2')
            t = mdparse.parse_table(p.keys['tabel'])
            self.assertEqual(t['headers'], ['id: A', 'en: B', '2024'])
            self.assertEqual(t['rows'][0][0], 'x')
            self.assertEqual(t['dummy_rows'], [True])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_catalog_counts(self):
        cat = catalog.load(os.path.join(ROOT, 'catalogs'))
        self.assertEqual(len(cat.ojk), 50)
        self.assertEqual(len(cat.seojk), 10)
        self.assertIn('F.21', cat.ojk)
        self.assertIn('2-27', cat.gri_dis)
        std, codes = catalog.replaced_sets(cat, catalog.CUTOFF['2027'])
        self.assertTrue({'304', '302'} <= std)
        self.assertIn('305-1', codes)


class TestDummy(Base):
    def test_clean(self):
        rep = validate.validate(self.base)
        self.assertEqual(rep.count('ERROR'), 0, [i for i in rep.items if i[0] == 'ERROR'])
        self.assertEqual(rep.pages, 88)
        self.assertEqual(rep.rules('WARN'), ['GRI-02'])

    def test_validator_does_not_modify_data(self):
        def snap(p):
            out = {}
            for d, _, fs in os.walk(p):
                for fn in fs:
                    fp = os.path.join(d, fn)
                    out[fp] = rd(fp)
            return out
        p = self.fresh()
        before = snap(p)
        validate.validate(p)
        self.assertEqual(before, snap(p))

    def test_log_written_only_to_log_dir(self):
        p = self.fresh()
        logdir = os.path.join(self.tmp, 'logs')
        rep = validate.validate(p)
        path = rep.write(logdir)
        self.assertTrue(os.path.isfile(str(path)))
        self.assertTrue(rd(str(path)).startswith('ERROR 0 | WARN 1 | pages 88'))
        self.assertEqual(os.listdir(logdir), ['ARSR_Validate_Log.txt'])


class TestPlan(Base):
    def test_plan_ok(self):
        import json
        p = self.fresh()
        out, pl, rep = plan.write(p)
        raw = rd(out)
        self.assertTrue(all(ord(c) < 128 for c in raw), 'plan must be ASCII')
        pl = json.loads(raw)
        self.assertEqual(len(pl['pages']), pl['doc']['pageCount'])
        self.assertEqual(len(pl['registry']['ojk']), 50)
        self.assertEqual(pl['pages'][0]['tipe'], 'sampul')
        for k in ('Primary', 'Accent 1', 'Terang 2'):
            self.assertIn(k, pl['colors'])
        rows = sum(len(d['table']['rows']) for d in pl['pages'] if d['tipe'] == 'indeks-gri')
        self.assertEqual(rows, len(pl['registry']['gri']))

    def test_plan_refuses_errors(self):
        p = self.fresh()
        f = os.path.join(p, 'data', '06_keberlanjutan.md')
        wr(f, rd(f).replace('gri: ', 'gri: 999-9, ', 1))
        with self.assertRaises(plan.PlanError):
            plan.build(p)

    def test_plan_capacity(self):
        p = self.fresh()
        f = os.path.join(p, 'data', '08_indeks.md')
        text = rd(f)
        n = text.count('tipe: indeks-gri')
        self.assertGreater(n, 1)
        wr(f, text.replace('tipe: indeks-gri', 'tipe: teks', 1))
        # converting an index page to teks needs content keys; capacity error or validation error both refuse
        with self.assertRaises(plan.PlanError):
            plan.build(p)


class TestJsx(Base):
    def test_lint_clean(self):
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import jsx_lint
        jdir = os.path.join(ROOT, 'engine', 'jsx')
        for fn in sorted(os.listdir(jdir)):
            errs = [f for f in jsx_lint.lint(os.path.join(jdir, fn)) if f[3] == 'ERROR']
            self.assertEqual(errs, [], fn)

    def test_mock_build(self):
        import json
        import subprocess
        node = shutil.which('node') or ('/opt/node22/bin/node' if os.path.exists('/opt/node22/bin/node') else None)
        if not node:
            self.skipTest('node not available')
        p = self.fresh()
        out, pl, rep = plan.write(p)
        o = os.path.join(self.tmp, 'mockout')
        r = subprocess.run([node, os.path.join(ROOT, 'tests', 'mock_indesign.js'), os.path.join(ROOT, 'engine', 'jsx', 'build_report.jsx'), out, o],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        logs = os.path.join(p, 'logs')
        self.assertFalse(os.path.exists(os.path.join(o, 'ARSR_Build_Log.txt')), 'build log must not go to Desktop')
        first = rd(os.path.join(logs, 'ARSR_Build_Log.txt')).split('\n')[0]
        self.assertTrue(first.startswith('ERROR 0 |'), first)
        st = json.load(open(os.path.join(o, 'mock_stats.json')))
        self.assertEqual(st['unbalanced'], [])
        self.assertEqual(st['outOfPage'], [], 'items placed outside their page')
        self.assertEqual(st['badUnits'], [], 'point sizes must be written as "N pt" strings')
        self.assertTrue(os.path.exists(os.path.join(logs, 'ARSR_Build_Done.txt')))
        self.assertIn('forced line break = char code', rd(os.path.join(logs, 'ARSR_Build_Log.txt')))
        self.assertNotIn('alert', rd(os.path.join(ROOT, 'engine', 'jsx', 'build_report.jsx')).replace('No alert()', ''))
        tables = sum(v for k, v in st['adds'].items() if k.endswith('.tables'))
        self.assertEqual(tables, sum(1 for d in pl['pages'] if d.get('table')))
        # QA script: the mock has no real content, so only check that the script itself does not crash
        o2 = os.path.join(self.tmp, 'qaout')
        r = subprocess.run([node, os.path.join(ROOT, 'tests', 'mock_indesign.js'), os.path.join(ROOT, 'engine', 'jsx', 'qa_document.jsx'), out, o2],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('QA-00', rd(os.path.join(o2, 'ARSR_QA_Log.txt')))


class TestJenis(unittest.TestCase):
    """Report types (LK, LT, LT+LK), one or two-page dividers, project folders and launchers."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='arsr_jenis_')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def make(self, jenis, divider):
        p = os.path.join(self.tmp, '%s-%s' % (jenis.replace('+', ''), divider))
        if not os.path.isdir(p):
            dummy.generate(TEMPLATE, p, jenis=jenis, divider=divider)
        return p

    def test_all_combinations_validate(self):
        for jenis in ('LK', 'LT', 'LT+LK'):
            for div in ('1', '2'):
                p = self.make(jenis, div)
                rep = validate.validate(p)
                self.assertEqual(rep.count('ERROR'), 0, '%s divider %s: %s' % (jenis, div, [i for i in rep.items if i[0] == 'ERROR'][:3]))
                self.assertEqual(rep.pages % 4, 0)

    def test_two_page_dividers_face_each_other(self):
        p = self.make('LT+LK', '2')
        out, pl, rep = plan.write(p)
        pages = pl['pages']
        for i, d in enumerate(pages):
            if d['tipe'] == 'divider':
                self.assertEqual(d['n'] % 2, 0, 'divider must start on a left page')
                self.assertEqual(pages[i + 1]['tipe'], 'divider-kanan')
                self.assertTrue(pages[i + 1]['sections'], 'right divider lists the chapter sections')
        self.assertEqual(pl['doc']['divider'], 2)

    def test_one_page_mode_has_no_right_divider(self):
        p = self.make('LK', '1')
        out, pl, rep = plan.write(p)
        self.assertNotIn('divider-kanan', [d['tipe'] for d in pl['pages']])

    def test_lt_skips_gri_and_ojk(self):
        rep = validate.validate(self.make('LT', '1'))
        self.assertFalse(any(i[1].startswith('GRI-') for i in rep.items if i[0] != 'INFO'))
        self.assertEqual(rep.count('ERROR'), 0)

    def test_covers_follow_jenis(self):
        out, pl, rep = plan.write(self.make('LK', '1'))
        self.assertIn('Laporan Keberlanjutan', pl['pages'][0]['title']['id'])
        self.assertNotIn('Tahunan', pl['pages'][0]['title']['id'])

    def test_structure_errors(self):
        p = self.make('LK', '1')
        q = os.path.join(self.tmp, 'bad-struct')
        shutil.copytree(p, q)
        cfg = os.path.join(q, 'data', '00_config.md')
        text = rd(cfg)
        wr(cfg, re.sub(r'(?m)^\| 05 \| ekonomi .*\n', '', text))
        os.remove(os.path.join(q, 'data', '05_ekonomi.md'))
        self.assertTrue(validate.validate(q).has('STR-20', 'ERROR'))
        q2 = os.path.join(self.tmp, 'bad-index')
        shutil.copytree(p, q2)
        f = os.path.join(q2, 'data', '08_indeks.md')
        wr(f, rd(f).replace('tipe: indeks-gri', 'tipe: indeks-seojk'))
        self.assertTrue(validate.validate(q2).has('STR-21', 'ERROR'))

    def test_divider_rules(self):
        p = self.make('LT+LK', '2')
        q = os.path.join(self.tmp, 'bad-div')
        shutil.copytree(p, q)
        cfg = os.path.join(q, 'data', '00_config.md')
        wr(cfg, rd(cfg).replace('divider: 2', 'divider: 1'))
        self.assertTrue(validate.validate(q).has('STR-13', 'ERROR'))

    def test_project_folders_and_launchers(self):
        p = self.make('LT+LK', '2')
        out, pl, rep = plan.write(p)
        for name in ('data', 'source', 'build', 'logs'):
            self.assertTrue(os.path.isdir(os.path.join(p, name)), name)
        self.assertTrue(os.path.exists(os.path.join(p, 'source', 'README.txt')))
        launcher = rd(os.path.join(p, 'build', 'run_build.jsx'))
        self.assertIn('ARSR_PLAN_PATH', launcher)
        self.assertIn('#include', launcher)
        self.assertIn('build_report.jsx', launcher)
        self.assertIn('qa_document.jsx', rd(os.path.join(p, 'build', 'run_qa.jsx')))
        self.assertTrue(pl['doc']['logDir'].endswith('/logs'))

    def test_mock_build_two_page_divider(self):
        import json
        import subprocess
        node = shutil.which('node') or ('/opt/node22/bin/node' if os.path.exists('/opt/node22/bin/node') else None)
        if not node:
            self.skipTest('node not available')
        for jenis in ('LK', 'LT'):
            p = self.make(jenis, '2')
            out, pl, rep = plan.write(p)
            o = os.path.join(self.tmp, 'mock-' + jenis.replace('+', ''))
            r = subprocess.run([node, os.path.join(ROOT, 'tests', 'mock_indesign.js'), os.path.join(ROOT, 'engine', 'jsx', 'build_report.jsx'), out, o],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            first = rd(os.path.join(p, 'logs', 'ARSR_Build_Log.txt')).split('\n')[0]
            self.assertTrue(first.startswith('ERROR 0 |'), first)
            with open(os.path.join(o, 'mock_stats.json')) as fh:
                st = json.load(fh)
            self.assertEqual(st['unbalanced'], [])
            self.assertEqual(st['outOfPage'], [])

    def test_validate_cli_writes_into_project_logs(self):
        p = self.make('LK', '1')
        shutil.rmtree(os.path.join(p, 'source'), ignore_errors=True)
        r = run_cli(['validate', p])
        self.assertEqual(r, 0)
        self.assertTrue(os.path.exists(os.path.join(p, 'logs', 'ARSR_Validate_Log.txt')))
        self.assertTrue(os.path.isdir(os.path.join(p, 'source')))


def mini_docx(path, blocks):
    """Write a tiny .docx with the standard library. blocks: ('Style', 'text') or ('table', [[ [lines], ...], ...])."""
    import zipfile
    ns = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

    def esc(t):
        return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def para(style, text):
        return '<w:p><w:pPr><w:pStyle w:val="%s"/></w:pPr><w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>' % (style, esc(text))

    body = []
    for b in blocks:
        if b[0] == 'table':
            rows = ''.join('<w:tr>%s</w:tr>' % ''.join('<w:tc>%s</w:tc>' % ''.join(para('Normal', ln) for ln in c) for c in r) for r in b[1])
            body.append('<w:tbl>%s</w:tbl>' % rows)
        else:
            body.append(para(b[0].replace(' ', ''), b[1]))
    names = {'Heading1': 'heading 1', 'Heading2': 'heading 2', 'Heading3': 'heading 3', 'Normal': 'Normal', 'English': 'English', 'Meta': 'Meta'}
    styles = ''.join('<w:style w:type="paragraph" w:styleId="%s"><w:name w:val="%s"/></w:style>' % (k, v) for k, v in names.items())
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"/>')
        z.writestr('word/document.xml', '<?xml version="1.0" encoding="UTF-8"?><w:document %s><w:body>%s</w:body></w:document>' % (ns, ''.join(body)))
        z.writestr('word/styles.xml', '<?xml version="1.0" encoding="UTF-8"?><w:styles %s>%s</w:styles>' % (ns, styles))


class TestImport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='arsr_import_')

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def project(self, name, jenis='LK', divider='1'):
        p = os.path.join(self.tmp, name)
        dummy.generate(TEMPLATE, p, jenis=jenis, divider=divider)
        os.makedirs(os.path.join(p, 'source'), exist_ok=True)
        return p

    def test_no_source_is_an_error(self):
        from arsr import importer
        p = self.project('nosrc')
        log, info = importer.run(p)
        self.assertIsNone(info)
        self.assertEqual(log.count('ERROR'), 1)

    def test_unmappable_heading_and_bad_table(self):
        from arsr import importer
        p = self.project('bad')
        mini_docx(os.path.join(p, 'source', 'a.docx'), [
            ('Heading 1', 'Bab Aneh | Strange chapter'), ('Meta', 'slug: tidak-ada'),
            ('Heading 2', 'Satu | One'), ('Normal', 'Isi.'), ('English', 'Body.')])
        log, info = importer.run(p)
        self.assertIsNone(info)
        self.assertTrue(any('slug "tidak-ada"' in r[2] for r in log.rows if r[0] == 'ERROR'))
        mini_docx(os.path.join(p, 'source', 'a.docx'), [
            ('Heading 1', 'Pendahuluan | Introduction'),
            ('Heading 2', 'Tabel | Table'), ('Meta', 'tipe: tabel'),
            ('table', [[['Deskripsi', 'Description'], ['2024']], [['A', 'A'], ['1'], ['extra']]])])
        log, info = importer.run(p)
        self.assertIsNone(info)
        self.assertTrue(any('cells' in r[2] for r in log.rows if r[0] == 'ERROR'))

    def test_minimal_import_keeps_old_data_and_pairs_languages(self):
        from arsr import importer
        p = self.project('mini')
        mini_docx(os.path.join(p, 'source', 'a.docx'), [
            ('Normal', 'Catatan penulis yang diabaikan.'),
            ('Heading 1', 'Pendahuluan | Introduction'), ('Meta', 'slug: pendahuluan'),
            ('Normal', 'Pengantar bab.'), ('English', 'Chapter intro.'),
            ('Heading 2', 'Tentang Laporan | About This Report'),
            ('Meta', 'gri: 2-2, 2-3 | dummy: ya'),
            ('Normal', 'Paragraf satu.'), ('English', 'Paragraph one.'),
            ('Normal', 'Paragraf dua.'), ('English', 'Paragraph two.')])
        log, info = importer.run(p)
        self.assertIsNotNone(info, log.render())
        text = rd(os.path.join(p, 'data', '01_pendahuluan.md'))
        self.assertIn('judul.id: Tentang Laporan', text)
        self.assertIn('isi.id: Paragraf satu.', text)
        self.assertIn('isi.en: Paragraph one.', text)
        self.assertIn('gri: 2-2, 2-3', text)
        self.assertTrue(os.path.isdir(os.path.join(p, 'build', 'data_before_import')))
        self.assertTrue(any('not found in the Word files' in r[2] for r in log.rows), 'missing chapters get a warning and a placeholder')
        rep = validate.validate(p)
        self.assertFalse(rep.has('STR-01', 'ERROR'), [i for i in rep.items if i[0] == 'ERROR'][:3])
        self.assertFalse(rep.has('STR-13', 'ERROR'))

    def test_roundtrip_example_validates(self):
        try:
            import docx  # noqa: F401
            import openpyxl  # noqa: F401
        except ImportError:
            self.skipTest('python-docx / openpyxl not installed')
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import make_word_example
        from arsr import importer
        for jenis, div in (('LT+LK', '2'), ('LK', '1'), ('LT', '2')):
            p = self.project('rt-%s-%s' % (jenis.replace('+', ''), div), jenis, div)
            make_word_example.build(os.path.join(p, 'source'), jenis)
            log, info = importer.run(p)
            self.assertIsNotNone(info, log.render())
            self.assertEqual(log.count('ERROR'), 0)
            rep = validate.validate(p)
            self.assertEqual(rep.count('ERROR'), 0, '%s: %s' % (jenis, [i for i in rep.items if i[0] == 'ERROR'][:3]))
            out, pl, _ = plan.write(p)
            self.assertEqual(len(pl['pages']) % 4, 0)

    def test_xlsx_number_formats(self):
        try:
            import openpyxl
        except ImportError:
            self.skipTest('openpyxl not installed')
        from arsr import docxread
        path = os.path.join(self.tmp, 't.xlsx')
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'S'
        ws.append(['A\nB', 1234.5, 0.311])
        ws['B1'].number_format = '#,##0.0'
        ws['C1'].number_format = '0.0%'
        wb.save(path)
        rows = docxread.read_xlsx(path, 'id')['S']
        self.assertEqual(rows[0][0], ['A', 'B'])
        self.assertEqual(rows[0][1], ['1.234,5'])
        self.assertEqual(rows[0][2], ['31,1%'])


class TestSkills(unittest.TestCase):
    def test_skill_frontmatter(self):
        base = os.path.join(ROOT, '.opencode', 'skills')
        ids = sorted(os.listdir(base))
        self.assertGreaterEqual(len(ids), 6)
        for d in ids:
            text = rd(os.path.join(base, d, 'SKILL.md'))
            m = re.match(r'^---\nname: (.+)\ndescription: (.+)\n---\n', text)
            self.assertTrue(m, d)
            self.assertEqual(m.group(1), d)
            self.assertRegex(d, r'^[a-z0-9]+(-[a-z0-9]+)*$')
            self.assertLessEqual(len(m.group(2)), 1024)
            self.assertLess(len(text.splitlines()), 120, d + ' too long for weak models; move detail to references/')


class TestEvals(Base):
    def test_seeded_faults_fail_and_graders_work(self):
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import eval_check
        o = os.path.join(self.tmp, 'e2')
        eval_check.seed('E2', o)
        self.assertEqual(eval_check.check('E2', o), 1)
        o3 = os.path.join(self.tmp, 'e3')
        eval_check.seed('E3', o3)
        self.assertEqual(eval_check.check('E3', o3), 1)


class TestDummyConfig(Base):
    def test_config_year_flows_into_tables(self):
        cfg = rd(os.path.join(TEMPLATE, 'data', '00_config.md'))
        cfg = cfg.replace('tahun-laporan: 2025', 'tahun-laporan: 2026').replace('Nusantara Contoh', 'Contoh Laporan')
        f = os.path.join(self.tmp, 'cfg2026.md')
        wr(f, cfg)
        out = os.path.join(self.tmp, 'p2026')
        dummy.generate(TEMPLATE, out, f)
        rep = validate.validate(out)
        self.assertEqual(rep.count('ERROR'), 0, rep.render()[:600])
        self.assertFalse(rep.has('NUM-04'), 'year columns must follow tahun-laporan')


class TestNegative(Base):
    def test_unknown_gri_code(self):
        self.assertRule(self.mutate('03_profil.md', 'gri: 2-1 |', 'gri: 2-1, 999-9 |'), 'GRI-01')

    def test_replaced_standard_under_version(self):
        self.assertRule(self.mutate('06_keberlanjutan.md', 'gri: GRI 101', 'gri: 304-1'), 'GRI-03')

    def test_unknown_ojk(self):
        self.assertRule(self.mutate('03_profil.md', 'ojk: C.2', 'ojk: C.2, Z.9'), 'OJK-01')

    def test_unknown_seojk(self):
        self.assertRule(self.mutate('02_manajemen.md', 'seojk: LT.3', 'seojk: LT.3, LT.99'), 'OJK-02')

    def test_missing_ojk_coverage(self):
        self.assertRule(self.mutate('05_tata-kelola.md', 'ojk: E.5', 'ojk: '.rstrip()), 'OJK-03')

    def test_missing_english(self):
        rep = self.mutate('03_profil.md', 'judul.en: Company Identity\n', '')
        self.assertRule(rep, 'STR-05')

    def test_forbidden_text(self):
        self.assertRule(self.mutate('03_profil.md', 'Visi: menjadi', 'TBD Visi: menjadi'), 'STR-06')

    def test_inline_tag(self):
        self.assertRule(self.mutate('03_profil.md', 'Visi: menjadi', '<e>Visi</e>: menjadi'), 'STR-06')

    def test_bad_cek(self):
        # table row on page 11: revenue 1.610,5 -> 1.699,5 breaks r3 = r1 - r2
        rep = self.mutate('01_pendahuluan.md', '| Pendapatan | Revenue | Miliar Rp | IDR billion | 1.450,2 | 1.523,8 | 1.610,5 |', '| Pendapatan | Revenue | Miliar Rp | IDR billion | 1.450,2 | 1.523,8 | 1.699,5 |')
        self.assertRule(rep, 'NUM-01')

    def test_wrong_number_format(self):
        self.assertRule(self.mutate('01_pendahuluan.md', '| Pendapatan | Revenue | Miliar Rp | IDR billion | 1.450,2 | 1.523,8 | 1.610,5 |', '| Pendapatan | Revenue | Miliar Rp | IDR billion | 1.450,2 | 1.523,8 | 1,610.5 |'), 'NUM-03', 'WARN')

    def test_page_gap(self):
        p = self.fresh()
        f = os.path.join(p, 'data', '03_profil.md')
        text = rd(f)
        text = re.sub(r'## HAL 15 ', '## HAL 16 ', text, count=1)
        wr(f, text)
        self.assertRule(validate.validate(p), 'STR-02')

    def test_unknown_page_type(self):
        self.assertRule(self.mutate('03_profil.md', 'tipe: teks | gri: 2-1', 'tipe: galeri | gri: 2-1'), 'STR-03')

    def test_missing_required_key(self):
        self.assertRule(self.mutate('06_keberlanjutan.md', 'tipe: teks', 'tipe: kutipan', 1), 'STR-04')

    def test_missing_33_for_topic(self):
        rep = self.mutate('06_keberlanjutan.md', 'gri: 3-3, 401-1', 'gri: 401-1')
        self.assertRule(rep, 'GRI-05')

    def test_unknown_topic_ref(self):
        self.assertRule(self.mutate('06_keberlanjutan.md', 'topik: T08', 'topik: T99'), 'STR-09')

    def test_omission_without_reason(self):
        p = self.fresh()
        f = os.path.join(p, 'data', '00_config.md')
        text = rd(f)
        text = text.replace('| 305-6 | Perusahaan tidak menggunakan zat perusak ozon | The company does not use ozone-depleting substances |',
                            '| 305-6 |  | The company does not use ozone-depleting substances |')
        wr(f, text)
        self.assertRule(validate.validate(p), 'GRI-07')

    def test_gri2_coverage(self):
        rep = self.mutate('05_tata-kelola.md', 'gri: 2-30', 'gri: 2-29')
        self.assertRule(rep, 'GRI-04')

    def test_missing_index_page_type(self):
        self.assertRule(self.mutate('08_indeks.md', 'tipe: indeks-ojk', 'tipe: indeks-gri', 2), 'OJK-05')

    def test_bad_config(self):
        p = self.fresh()
        f = os.path.join(p, 'data', '00_config.md')
        wr(f, rd(f).replace('gri.versi: pra-2027', 'gri.versi: banana'))
        self.assertRule(validate.validate(p), 'CFG-02')

    def test_missing_chapter_file(self):
        p = self.fresh()
        os.remove(os.path.join(p, 'data', '04_analisis.md'))
        self.assertRule(validate.validate(p), 'STR-01')


if __name__ == '__main__':
    unittest.main()
