# -*- coding: utf-8 -*-
"""Generate a fictional, internally consistent project (LK, LT or LT+LK, one or two-page dividers) from a template 00_config.md.

All content is invented and flagged `dummy: ya`. Numbers come from one fact table so the same
fact has the same value on every page. Table totals satisfy their own `cek` formulas.
"""
import os
import re

from . import mdparse, numfmt
from .arrange import INTRO, SUB, TITLE, arrange, config_text, render_chapters  # noqa: F401

STRUCT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'structures')
STRUCT_FILE = {'LK': 'lk.md', 'LT': 'lt.md', 'LT+LK': 'lt-lk.md'}

_PROFIL = [14, 15, 16, 17, 18, 19, 20, 21, 23, 24]
_GOV = [26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
_EKO = [38, 39, 40, 41, 42, 43, 44]
_ENV = list(range(46, 57))
_SOC = list(range(58, 69))
# source page numbers (the numbers used inside Gen.plan) per chapter, per report type
LAYOUT = {
    'LK': [('pendahuluan', [1, 2, 3, 6, 7, 8, 10]), ('manajemen', [4, 5, 36]), ('profil', _PROFIL),
           ('tata-kelola', [9] + _GOV[:]), ('ekonomi', _EKO), ('lingkungan', _ENV), ('sosial', _SOC),
           ('indeks', [70, 72, 73, 74, 75, 76, 77, 79, 80])],
    'LT': [('ikhtisar', [1, 2, 3, 6, 10, 11, 12]), ('manajemen', [4, 5, 36]), ('profil', _PROFIL),
           ('analisis', [22, 101, 103]), ('tata-kelola', _GOV), ('tjsl', [65, 55, 66]),
           ('keuangan', [102, 104, 71]), ('indeks', [70, 78, 79, 80])],
    'LT+LK': [('pendahuluan', [1, 2, 3, 6, 7, 8, 10, 11, 12]), ('manajemen', [4, 5, 36]), ('profil', _PROFIL),
              ('analisis', [22, 101, 103]), ('tata-kelola', [9] + _GOV), ('keberlanjutan', _EKO + _ENV + _SOC),
              ('keuangan', [102, 104, 71]), ('indeks', [70, 72, 73, 74, 75, 76, 77, 78, 79, 80])],
}
TOPIC_ABOUT = {
    'T01': ('nilai ekonomi yang dihasilkan dan didistribusikan', 'economic value generated and distributed'),
    'T02': ('belanja kepada pemasok di sekitar wilayah operasi', 'spending on suppliers near operating sites'),
    'T03': ('penggunaan bahan dan bahan input daur ulang', 'materials used and recycled inputs'),
    'T04': ('konsumsi dan efisiensi energi', 'energy consumption and efficiency'),
    'T05': ('pengambilan, pembuangan dan konsumsi air', 'water withdrawal, discharge and consumption'),
    'T06': ('emisi gas rumah kaca dan emisi udara lain', 'greenhouse gas and other air emissions'),
    'T07': ('timbulan, pengalihan dan pembuangan limbah', 'waste generation, diversion and disposal'),
    'T08': ('perekrutan, perputaran dan tunjangan karyawan', 'hiring, turnover and employee benefits'),
    'T09': ('keselamatan dan kesehatan kerja seluruh pekerja', 'occupational health and safety of all workers'),
    'T10': ('pelatihan dan pengembangan kemampuan karyawan', 'employee training and skills development'),
    'T11': ('keberagaman, kesetaraan dan nondiskriminasi', 'diversity, equality and non-discrimination'),
    'T12': ('upah layak serta pencegahan tenaga kerja anak dan paksa', 'fair wages and prevention of child and forced labor'),
    'T13': ('pelibatan dan dampak terhadap masyarakat sekitar', 'engagement with and impact on local communities'),
    'T14': ('keselamatan dan kualitas produk serta layanan', 'product and service safety and quality'),
}


def r1(x):
    return round(x + 1e-9, 1)


class Gen(object):
    def __init__(self, cfg, jenis=None, divider=None):
        self.cfg = cfg
        kv = lambda s, k: mdparse.cfg_kv(cfg, s, k)  # noqa: E731
        self.y = int(kv('PROYEK', 'tahun-laporan'))
        self.Y = [self.y - 2, self.y - 1, self.y]
        self.style = kv('FORMAT', 'format-angka-tabel') or 'id'
        self.co = kv('PROYEK', 'nama-perusahaan')
        self.short = kv('PROYEK', 'nama-singkat')
        self.code = kv('PROYEK', 'kode-emiten')
        self.since = kv('PROYEK', 'berdiri') or '1998'
        self.theme = (kv('PROYEK', 'tema.id'), kv('PROYEK', 'tema.en'))
        self.addr = (kv('KONTAK', 'alamat.id'), kv('KONTAK', 'alamat.en'))
        self.jenis = jenis or kv('PROYEK', 'jenis') or 'LT+LK'
        if self.jenis not in LAYOUT:
            raise ValueError('jenis must be LK, LT or LT+LK, got %s' % self.jenis)
        self.divider = int(divider or kv('HALAMAN', 'divider') or 2)
        scfg = mdparse.parse_config(os.path.join(STRUCT_DIR, STRUCT_FILE[self.jenis]))
        self.struct = mdparse.cfg_rows(scfg, 'BAB')
        self.topics = dict((r['id'], r) for r in mdparse.cfg_rows(cfg, 'TOPIK'))
        self.pages = {}
        self._facts()

    # ------------------------------------------------------------ facts
    def _facts(self):
        F = {}
        F['revenue'] = [1450.2, 1523.8, 1610.5]
        F['opex'] = [1180.4, 1235.1, 1297.7]
        F['wages'] = [286.4, 301.9, 318.2]
        F['supplier'] = [r1(a - b) for a, b in zip(F['opex'], F['wages'])]
        F['op'] = [r1(a - b) for a, b in zip(F['revenue'], F['opex'])]
        F['tax'] = [r1(x * 0.2) for x in F['op']]
        F['net'] = [r1(a - b) for a, b in zip(F['op'], F['tax'])]
        F['capital'] = [84.0, 91.5, 98.8]
        F['community_juta'] = [2100, 2400, 2900]
        F['community'] = [r1(x / 1000.0) for x in F['community_juta']]
        F['distributed'] = [r1(a + b + c + d + e) for a, b, c, d, e in
                            zip(F['supplier'], F['wages'], F['capital'], F['tax'], F['community'])]
        F['retained'] = [r1(a - b) for a, b in zip(F['revenue'], F['distributed'])]
        F['assets'] = [2350.6, 2478.3, 2615.9]
        F['liab'] = [1186.2, 1241.7, 1288.4]
        F['equity'] = [r1(a - b) for a, b in zip(F['assets'], F['liab'])]
        F['price'] = [1250, 1340, 1425]
        F['shares'] = [2400, 2400, 2400]
        F['mcap'] = [r1(a * b / 1000.0) for a, b in zip(F['price'], F['shares'])]
        F['emp'] = [118, 126, 134]
        F['women'] = [34, 38, 42]
        F['men'] = [a - b for a, b in zip(F['emp'], F['women'])]
        F['outs'] = [46, 50, 54]
        F['interns'] = [8, 9, 11]
        F['nonemp'] = [a + b for a, b in zip(F['outs'], F['interns'])]
        F['hires'] = [14, 15, 16]
        F['leavers'] = [8, 7, 8]
        F['sites'] = [7, 8, 9]
        F['fuel'] = [78200, 80150, 79480]
        F['elec'] = [31450, 32020, 33110]
        F['ren'] = [4100, 6350, 9870]
        F['energy'] = [a + b + c for a, b, c in zip(F['fuel'], F['elec'], F['ren'])]
        F['e_int'] = [r1(a / b) for a, b in zip(F['energy'], F['revenue'])]
        F['e_out'] = [12300, 12980, 13410]
        F['e_saved'] = [1250, 2100, 3050]
        F['s1'] = [41200, 41900, 40700]
        F['s2'] = [18600, 19100, 17400]
        F['s3'] = [9800, 10400, 10900]
        F['ghg'] = [a + b + c for a, b, c in zip(F['s1'], F['s2'], F['s3'])]
        F['g_int'] = [r1(a / b) for a, b in zip(F['ghg'], F['revenue'])]
        F['g_red'] = [1100, 1900, 2800]
        F['nox'] = [32.4, 31.1, 29.8]
        F['sox'] = [18.7, 18.0, 17.2]
        F['w_surf'] = [182.4, 176.9, 171.3]
        F['w_gnd'] = [64.2, 61.8, 59.5]
        F['w_mun'] = [31.7, 33.0, 34.6]
        F['w_tot'] = [r1(a + b + c) for a, b, c in zip(F['w_surf'], F['w_gnd'], F['w_mun'])]
        F['w_dis'] = [208.0, 203.4, 199.7]
        F['w_con'] = [r1(a - b) for a, b in zip(F['w_tot'], F['w_dis'])]
        F['nb3'] = [1240, 1215, 1190]
        F['b3'] = [186, 181, 174]
        F['waste'] = [a + b for a, b in zip(F['nb3'], F['b3'])]
        F['divert'] = [812, 845, 903]
        F['dispose'] = [a - b for a, b in zip(F['waste'], F['divert'])]
        F['m_rec'] = [640, 780, 930]
        F['m_new'] = [5420, 5310, 5180]
        F['m_tot'] = [a + b for a, b in zip(F['m_rec'], F['m_new'])]
        F['m_pct'] = [r1(a / b * 100) for a, b in zip(F['m_rec'], F['m_tot'])]
        F['m_recl'] = [120, 150, 205]
        F['c_waste'] = [3.2, 3.5, 3.9]
        F['c_mon'] = [1.1, 1.2, 1.4]
        F['c_green'] = [0.8, 1.0, 1.3]
        F['c_tot'] = [r1(a + b + c) for a, b, c in zip(F['c_waste'], F['c_mon'], F['c_green'])]
        F['ec_rec'] = [5, 4, 3]
        F['ec_res'] = [4, 4, 3]
        F['cc_rec'] = [9, 7, 6]
        F['cc_res'] = [8, 7, 6]
        F['inj_min'] = [3, 2, 2]
        F['inj_sev'] = [1, 1, 0]
        F['inj_fat'] = [0, 0, 0]
        F['inj_tot'] = [a + b + c for a, b, c in zip(F['inj_min'], F['inj_sev'], F['inj_fat'])]
        F['ill'] = [0, 1, 0]
        F['hours'] = [4130, 4620, 5360]
        F['avg_h'] = [r1(a / b) for a, b in zip(F['hours'], F['emp'])]
        F['programs'] = [12, 14, 17]
        F['entry'] = [1.18, 1.21, 1.24]
        F['local_sm'] = [62.5, 64.3, 66.7]
        F['pl_took'] = [6, 7, 9]
        F['pl_back'] = [6, 7, 8]
        F['pay_ratio'] = [0.96, 0.97, 0.98]
        F['gov_c'] = [4, 4, 5]
        F['gov_d'] = [5, 5, 5]
        F['gov_t'] = [a + b for a, b in zip(F['gov_c'], F['gov_d'])]
        F['gov_ind'] = [2, 2, 2]
        F['gov_w'] = [2, 2, 3]
        F['pkb'] = [94, 101, 112]
        F['ratio_ceo'] = [6.8, 6.5, 6.4]
        F['ratio_inc'] = [1.2, 1.1, 1.0]
        F['pension'] = [42.5, 44.8, 47.2]
        F['t_rev'] = [1420.0, 1500.0, 1600.0]
        F['t_net'] = [205.0, 225.0, 245.0]
        F['local_spend'] = [536.0, 579.5, 688.2]
        F['comm_prog'] = [6, 7, 9]
        F['comm_ben'] = [1850, 2240, 2960]
        F['comm_ops'] = [6, 7, 8]
        F['cat_tot'] = [10, 10, 12]
        F['cat_eval'] = [10, 10, 12]
        self.F = F

    # ---------------------------------------------------------- helpers
    def f(self, v, d=0):
        return numfmt.fmt_num(v, d, self.style)

    def pct(self, a, b):
        return r1(a * 100.0 / b)

    def row(self, id_, en, uid, uen, vals, d=0):
        return [id_, en, uid, uen] + [self.f(v, d) for v in vals]

    def numtable(self, rows):
        hdr = ['id: Deskripsi', 'en: Description', 'id: Satuan', 'en: Unit'] + [str(x) for x in self.Y]
        return [hdr] + rows

    def page(self, n, tipe, **kw):
        if n in self.pages:
            raise ValueError('page %d defined twice' % n)
        kw['tipe'] = tipe
        self.pages[n] = kw

    def approach(self, tid, extra_id='', extra_en=''):
        a_id, a_en = TOPIC_ABOUT[tid]
        nm = self.topics[tid]
        return (
            'Pendekatan manajemen untuk topik %s (%s): perusahaan menetapkan kebijakan dan target tahunan, '
            'menunjuk penanggung jawab, memantau dampak aktual dan potensial, serta meninjau efektivitas tindakan '
            'bersama pemangku kepentingan terkait. %s' % (nm['nama.id'].lower(), a_id, extra_id)).strip(), (
            'Management approach for %s (%s): the company sets policies and annual targets, assigns an accountable '
            'owner, monitors actual and potential impacts, and reviews the effectiveness of actions with relevant '
            'stakeholders. %s' % (nm['nama.en'].lower(), a_en, extra_en)).strip()

    def topic_page(self, n, tid, gri, rows, cek, ojk=(), extra=('', ''), seojk=()):
        i, e = self.approach(tid, extra[0], extra[1])
        self.page(n, 'tabel', judul=(self.topics[tid]['nama.id'], self.topics[tid]['nama.en']), isi=(i, e),
                  gri=['3-3'] + list(gri), ojk=list(ojk), seojk=list(seojk), topik=[tid],
                  tabel=self.numtable(rows), cek=cek, numeric=True)

    # ------------------------------------------------------------- plan
    def plan(self):
        F, Y, y = self.F, self.Y, self.y
        co, sh = self.co, self.short
        f, pct = self.f, self.pct

        # ---------------- bab 01
        self.page(1, 'sampul', judul=('%s %d' % (TITLE[self.jenis][0], y), '%s %d' % (TITLE[self.jenis][1], y)),
                  subjudul=self.theme, tahun=str(y))
        self.page(2, 'daftar-isi', judul=('Daftar Isi', 'Table of Contents'))
        self.page(3, 'teks', judul=('Tentang Laporan', 'About This Report'),
                  gri=['2-2', '2-3', '2-4', '3-1'], seojk=['LT.8'],
                  isi=('Laporan ini mencakup periode 1 Januari sampai 31 Desember %d dan diterbitkan setiap tahun. Cakupan meliputi '
                       'seluruh entitas dalam laporan keuangan konsolidasian %s. Laporan disusun sesuai (in accordance with) GRI Standards. '
                       'Penyajian kembali informasi dicatat pada tabel terkait.\n\n'
                       'Proses penentuan topik material melibatkan manajemen dan perwakilan pemangku kepentingan. Standar PSPK 1 dan 2 '
                       '(efektif 1 Januari 2027) disebutkan sebagai informasi.' % (y, sh),
                       'This report covers 1 January to 31 December %d and is published annually. It covers all entities in the consolidated '
                       'financial statements of %s. It is prepared in accordance with the GRI Standards. Restatements are noted on the '
                       'relevant tables.\n\n'
                       'The material topic process involved management and stakeholder representatives. PSPK 1 and 2 (effective '
                       '1 January 2027) are mentioned for information only.' % (y, sh)))
        self.page(4, 'kutipan', gri=['2-22', '2-14'], ojk=['D.1'], seojk=['LT.3'],
                  kutipan=('Keberlanjutan adalah cara kami menjaga pertumbuhan tetap bermakna bagi seluruh pemangku kepentingan.',
                           'Sustainability is how we keep growth meaningful for all of our stakeholders.'),
                  nama='Andika Contohan', jabatan='Direktur Utama / President Director')
        self.page(5, 'kutipan', seojk=['LT.4'],
                  kutipan=('Dewan Komisaris memastikan tata kelola yang baik berjalan seiring dengan target keberlanjutan perusahaan.',
                           'The Board of Commissioners ensures good governance goes hand in hand with the sustainability targets.'),
                  nama='Sekar Contohwati', jabatan='Komisaris Utama / President Commissioner')
        self.page(6, 'kartu', judul=('Ikhtisar Kinerja Ekonomi', 'Economic Performance Highlights'),
                  gri=['201-1'], ojk=['B.1'], seojk=['LT.8'], topik=['T01'],
                  kartu=[(f(F['revenue'][2], 1), 'Pendapatan (miliar Rp)', 'Revenue (IDR billion)'),
                         (f(F['net'][2], 1), 'Laba bersih (miliar Rp)', 'Net profit (IDR billion)'),
                         (f(F['assets'][2], 1), 'Total aset (miliar Rp)', 'Total assets (IDR billion)'),
                         (f(F['retained'][2], 1), 'Nilai ekonomi ditahan (miliar Rp)', 'Economic value retained (IDR billion)')])
        self.page(7, 'kartu', judul=('Ikhtisar Kinerja Lingkungan', 'Environmental Performance Highlights'),
                  gri=['302-1', '305-1'], ojk=['B.2'], seojk=['LT.8'], topik=['T04', 'T06'],
                  kartu=[(f(F['energy'][2]), 'Konsumsi energi (GJ)', 'Energy consumption (GJ)'),
                         (f(F['ghg'][2]), 'Emisi GRK (tCO2e)', 'GHG emissions (tCO2e)'),
                         (f(F['waste'][2]), 'Limbah dihasilkan (ton)', 'Waste generated (tonnes)'),
                         (f(F['w_tot'][2], 1), 'Pengambilan air (ribu m3)', 'Water withdrawal (thousand m3)')])
        self.page(8, 'kartu', judul=('Ikhtisar Kinerja Sosial', 'Social Performance Highlights'),
                  gri=['2-7', '401-1', '403-9', '413-1'], ojk=['B.3'], seojk=['LT.8'], topik=['T08', 'T09', 'T13'],
                  kartu=[(f(F['emp'][2]), 'Karyawan (orang)', 'Employees (persons)'),
                         (f(pct(F['women'][2], F['emp'][2]), 1) + '%', 'Karyawan perempuan', 'Women employees'),
                         (f(F['avg_h'][2], 1), 'Jam pelatihan per karyawan', 'Training hours per employee'),
                         (f(F['inj_fat'][2]), 'Kecelakaan fatal (kasus)', 'Fatal accidents (cases)')])
        self.page(9, 'teks', judul=('Strategi Keberlanjutan', 'Sustainability Strategy'), gri=['2-22', '2-23'],
                  ojk=['A.1'], seojk=['LT.8'],
                  isi=('Strategi keberlanjutan %s bertumpu pada tiga pilar: pertumbuhan ekonomi yang bertanggung jawab, efisiensi '
                       'penggunaan sumber daya, dan pengembangan manusia serta masyarakat sekitar. Setiap pilar memiliki target tahunan '
                       'yang ditinjau Direksi.' % sh,
                       'The sustainability strategy of %s rests on three pillars: responsible economic growth, resource efficiency, and '
                       'the development of people and surrounding communities. Each pillar has annual targets reviewed by the Board of Directors.' % sh))
        rows = []
        for tid, t in sorted(self.topics.items()):
            stds = []
            for tok in [x.strip() for x in t['gri'].split(',')]:
                s = 'GRI ' + tok.split('-')[0]
                if s not in stds:
                    stds.append(s)
            rows.append([t['nama.id'], t['nama.en'], ', '.join(stds), ', '.join(stds)])
        self.page(10, 'tabel', judul=('Topik Material', 'Material Topics'), gri=['3-1', '3-2'], seojk=['LT.8'],
                  isi=('Topik material ditetapkan melalui penilaian dampak dan masukan pemangku kepentingan, lalu dipetakan ke Standar Topik GRI.',
                       'Material topics were set through impact assessment and stakeholder input, then mapped to the GRI Topic Standards.'),
                  tabel=[['id: Topik material', 'en: Material topic', 'id: Standar GRI', 'en: GRI Standard']] + rows)
        self.page(11, 'tabel', judul=('Ikhtisar Data Keuangan Penting', 'Key Financial Highlights'), seojk=['LT.1'],
                  tabel=self.numtable([
                      self.row('Pendapatan', 'Revenue', 'Miliar Rp', 'IDR billion', F['revenue'], 1),
                      self.row('Beban usaha', 'Operating expenses', 'Miliar Rp', 'IDR billion', F['opex'], 1),
                      self.row('Laba usaha', 'Operating profit', 'Miliar Rp', 'IDR billion', F['op'], 1),
                      self.row('Laba bersih', 'Net profit', 'Miliar Rp', 'IDR billion', F['net'], 1),
                      self.row('Total aset', 'Total assets', 'Miliar Rp', 'IDR billion', F['assets'], 1),
                      self.row('Total liabilitas', 'Total liabilities', 'Miliar Rp', 'IDR billion', F['liab'], 1),
                      self.row('Ekuitas', 'Equity', 'Miliar Rp', 'IDR billion', F['equity'], 1)]),
                  cek='r3 = r1 - r2; r4 = r3 * 0.8; r7 = r5 - r6', numeric=True)
        self.page(12, 'tabel', judul=('Informasi Saham', 'Share Information'), seojk=['LT.2'],
                  tabel=self.numtable([
                      self.row('Harga penutupan', 'Closing price', 'Rp per saham', 'IDR per share', F['price']),
                      self.row('Saham beredar', 'Shares outstanding', 'Juta lembar', 'Million shares', F['shares']),
                      self.row('Kapitalisasi pasar', 'Market capitalization', 'Miliar Rp', 'IDR billion', F['mcap'], 1)]),
                  cek='r3 = r1 * r2 / 1000', numeric=True)

        # ---------------- bab 02
        self.page(14, 'teks', judul=('Identitas Perusahaan', 'Company Identity'), gri=['2-1'], ojk=['C.2'], seojk=['LT.5'],
                  isi=('%s (kode saham %s) didirikan pada tahun %s dan berkedudukan di %s. Bentuk badan hukum adalah perseroan terbatas terbuka.' % (
                      co, self.code, self.since, self.addr[0]),
                       '%s (ticker %s) was established in %s and is domiciled at %s. Its legal form is a public limited company.' % (
                           co, self.code, self.since, self.addr[1])))
        self.page(15, 'teks', judul=('Visi, Misi, dan Nilai Keberlanjutan', 'Vision, Mission and Sustainability Values'),
                  gri=['2-23'], ojk=['C.1'],
                  isi=('Visi: menjadi mitra energi yang tepercaya dan berkelanjutan. Misi: menyediakan energi andal, mengelola dampak dengan '
                       'bertanggung jawab, dan tumbuh bersama masyarakat. Nilai: integritas, kolaborasi, keunggulan, kepedulian.',
                       'Vision: to be a trusted and sustainable energy partner. Mission: to provide reliable energy, manage impacts responsibly, '
                       'and grow together with communities. Values: integrity, collaboration, excellence, care.'))
        self.page(16, 'tabel', judul=('Skala Usaha', 'Scale of the Organization'), gri=['2-7'], ojk=['C.3'], seojk=['LT.5'],
                  tabel=self.numtable([
                      self.row('Total aset', 'Total assets', 'Miliar Rp', 'IDR billion', F['assets'], 1),
                      self.row('Jumlah karyawan', 'Number of employees', 'Orang', 'Persons', F['emp']),
                      self.row('Karyawan perempuan', 'Women employees', 'Orang', 'Persons', F['women']),
                      self.row('Karyawan laki-laki', 'Men employees', 'Orang', 'Persons', F['men']),
                      self.row('Lokasi operasi', 'Operating sites', 'Lokasi', 'Sites', F['sites'])]),
                  cek='r2 = r3 + r4', numeric=True)
        self.page(17, 'teks', judul=('Produk, Layanan, dan Kegiatan Usaha', 'Products, Services and Business Activities'),
                  gri=['2-6'], ojk=['C.4'], seojk=['LT.5'],
                  isi=('Kegiatan usaha meliputi pembangkitan listrik skala menengah, distribusi energi ke pelanggan industri, dan layanan '
                       'efisiensi energi. Rantai nilai mencakup pemasok bahan bakar, mitra konstruksi, dan pelanggan.',
                       'Business activities cover mid-scale power generation, energy distribution to industrial customers, and energy efficiency '
                       'services. The value chain includes fuel suppliers, construction partners and customers.'))
        self.page(18, 'tabel', judul=('Keanggotaan pada Asosiasi', 'Association Memberships'), gri=['2-28'], ojk=['C.5'],
                  tabel=[['id: Asosiasi', 'en: Association', 'id: Peran', 'en: Role'],
                         ['Asosiasi Energi Contoh', 'Contoh Energy Association', 'Anggota', 'Member'],
                         ['Forum Keberlanjutan Contoh', 'Contoh Sustainability Forum', 'Anggota aktif', 'Active member'],
                         ['Kamar Dagang Contoh', 'Contoh Chamber of Commerce', 'Anggota', 'Member']])
        self.page(19, 'teks', judul=('Perubahan Signifikan', 'Significant Changes'), gri=['2-4'], ojk=['C.6'],
                  isi=('Pada tahun %d perusahaan menambah satu lokasi operasi dan memperbarui metode perhitungan intensitas energi. Angka '
                       'pembanding tahun sebelumnya telah disajikan kembali sesuai metode baru.' % y,
                       'In %d the company added one operating site and updated its energy intensity method. Prior-year comparatives have been '
                       'restated using the new method.' % y))
        self.page(20, 'teks', judul=('Rantai Nilai', 'Value Chain'), gri=['2-6'],
                  isi=('Hulu: pemasok bahan bakar dan peralatan. Tengah: pembangkitan dan distribusi. Hilir: pelanggan industri dan komersial. '
                       'Perusahaan menilai risiko keberlanjutan pada pemasok utama setiap tahun.',
                       'Upstream: fuel and equipment suppliers. Midstream: generation and distribution. Downstream: industrial and commercial '
                       'customers. The company assesses sustainability risks of key suppliers every year.'))
        self.page(21, 'tabel', judul=('Pekerja Bukan Karyawan', 'Workers Who Are Not Employees'), gri=['2-8'],
                  tabel=self.numtable([
                      self.row('Tenaga alih daya', 'Outsourced workers', 'Orang', 'Persons', F['outs']),
                      self.row('Peserta magang', 'Interns', 'Orang', 'Persons', F['interns']),
                      self.row('Total pekerja bukan karyawan', 'Total non-employee workers', 'Orang', 'Persons', F['nonemp'])]),
                  cek='r3 = r1 + r2', numeric=True)
        self.page(22, 'teks', judul=('Analisis dan Pembahasan Manajemen', 'Management Discussion and Analysis'), seojk=['LT.6'],
                  isi=('Pendapatan tumbuh %s%% dibandingkan tahun sebelumnya, didorong volume distribusi dan layanan efisiensi energi. '
                       'Beban usaha naik lebih lambat daripada pendapatan sehingga margin laba usaha membaik.' % (
                           f(r1((F['revenue'][2] / F['revenue'][1] - 1) * 100), 1)),
                       'Revenue grew %s%% year on year, driven by distribution volume and energy efficiency services. Operating expenses rose '
                       'more slowly than revenue, improving the operating margin.' % (
                           f(r1((F['revenue'][2] / F['revenue'][1] - 1) * 100), 1))))
        self.page(23, 'kartu', judul=('Wilayah Operasi', 'Areas of Operation'),
                  kartu=[(f(F['sites'][2]), 'Lokasi operasi', 'Operating sites'),
                         (f(F['emp'][2]), 'Karyawan', 'Employees'),
                         (f(F['comm_ben'][2]), 'Penerima manfaat TJSL', 'CSR beneficiaries'),
                         (f(pct(F['local_spend'][2], F['supplier'][2]), 1) + '%', 'Belanja pemasok lokal', 'Local supplier spend')])
        self.page(24, 'teks', judul=('Sejarah Singkat', 'Brief History'),
                  isi=('Perusahaan berawal sebagai usaha distribusi energi regional, lalu berkembang menjadi penyedia energi terpadu dan '
                       'mencatatkan sahamnya di bursa.',
                       'The company began as a regional energy distributor, grew into an integrated energy provider and listed its shares on the exchange.'))

        # ---------------- bab 03
        self.page(26, 'teks', judul=('Tata Kelola Keberlanjutan', 'Sustainability Governance'),
                  gri=['2-9', '2-12', '2-13', '2-14'], ojk=['E.1'], seojk=['LT.7', 'LT.8'],
                  isi=('Dewan Komisaris mengawasi pengelolaan dampak, Direksi menetapkan strategi, dan Komite Keberlanjutan mengoordinasikan '
                       'pelaksanaan. Direksi meninjau dan menyetujui laporan ini sebelum diterbitkan.',
                       'The Board of Commissioners oversees impact management, the Board of Directors sets the strategy, and the Sustainability '
                       'Committee coordinates implementation. The Board of Directors reviews and approves this report before publication.'))
        self.page(27, 'tabel', judul=('Komposisi Badan Tata Kelola', 'Governance Body Composition'), gri=['2-10', '2-11'], seojk=['LT.7'],
                  isi=('Anggota dicalonkan dan dipilih melalui Rapat Umum Pemegang Saham. Ketua Dewan Komisaris tidak merangkap jabatan eksekutif.',
                       'Members are nominated and selected at the General Meeting of Shareholders. The Chair of the Board of Commissioners holds no executive role.'),
                  tabel=self.numtable([
                      self.row('Anggota Dewan Komisaris', 'Board of Commissioners members', 'Orang', 'Persons', F['gov_c']),
                      self.row('Anggota Direksi', 'Board of Directors members', 'Orang', 'Persons', F['gov_d']),
                      self.row('Total anggota', 'Total members', 'Orang', 'Persons', F['gov_t']),
                      self.row('Komisaris independen', 'Independent commissioners', 'Orang', 'Persons', F['gov_ind'])]),
                  cek='r3 = r1 + r2', numeric=True)
        self.page(28, 'teks', judul=('Kompetensi dan Konflik Kepentingan', 'Competence and Conflicts of Interest'),
                  gri=['2-15', '2-17', '2-18'], ojk=['E.2'],
                  isi=('Anggota Direksi dan Dewan Komisaris mengikuti program pengembangan kompetensi keberlanjutan setiap tahun. Konflik '
                       'kepentingan diungkapkan dan dikelola sesuai kebijakan benturan kepentingan. Kinerja badan tata kelola dievaluasi setiap tahun.',
                       'Directors and commissioners attend sustainability competence programs every year. Conflicts of interest are disclosed and '
                       'managed under the conflict of interest policy. Governance body performance is evaluated annually.'))
        self.page(29, 'tabel', judul=('Kebijakan Remunerasi', 'Remuneration Policy'), gri=['2-19', '2-20', '2-21'], seojk=['LT.7'],
                  isi=('Remunerasi ditetapkan berdasarkan kinerja dan pencapaian target keberlanjutan, melalui usulan Komite Nominasi dan Remunerasi.',
                       'Remuneration is set on performance and the achievement of sustainability targets, upon recommendation of the Nomination and Remuneration Committee.'),
                  tabel=self.numtable([
                      self.row('Rasio kompensasi tertinggi terhadap median', 'Highest-paid to median compensation ratio', 'Kali', 'Times', F['ratio_ceo'], 1),
                      self.row('Rasio kenaikan kompensasi', 'Compensation increase ratio', 'Kali', 'Times', F['ratio_inc'], 1)]),
                  numeric=True)
        self.page(30, 'teks', judul=('Penilaian Risiko Keberlanjutan', 'Sustainability Risk Assessment'), gri=['2-25'], ojk=['E.3'],
                  isi=('Risiko keberlanjutan dinilai setiap semester dan dimasukkan ke dalam profil risiko perusahaan. Dampak negatif yang '
                       'teridentifikasi ditangani melalui rencana pemulihan dengan penanggung jawab yang jelas.',
                       'Sustainability risks are assessed every semester and included in the company risk profile. Identified negative impacts are '
                       'addressed through remediation plans with clear owners.'))
        self.page(31, 'tabel', judul=('Pelibatan Pemangku Kepentingan', 'Stakeholder Engagement'), gri=['2-29', '3-1'], ojk=['E.4'],
                  tabel=[['id: Pemangku kepentingan', 'en: Stakeholder', 'id: Metode pelibatan', 'en: Engagement method',
                          'id: Frekuensi', 'en: Frequency'],
                         ['Karyawan', 'Employees', 'Forum dua arah', 'Two-way forum', 'Triwulanan', 'Quarterly'],
                         ['Pelanggan', 'Customers', 'Survei kepuasan', 'Satisfaction survey', 'Tahunan', 'Annual'],
                         ['Masyarakat sekitar', 'Local communities', 'Dialog warga', 'Community dialogue', 'Semesteran', 'Semi-annual'],
                         ['Pemegang saham', 'Shareholders', 'Rapat umum', 'General meeting', 'Tahunan', 'Annual'],
                         ['Pemerintah', 'Government', 'Pelaporan resmi', 'Official reporting', 'Sesuai ketentuan', 'As required']])
        self.page(32, 'teks', judul=('Permasalahan dan Kepatuhan', 'Issues and Compliance'),
                  gri=['2-16', '2-26', '2-27'], ojk=['E.5'],
                  isi=('Hal kritis dikomunikasikan kepada Dewan Komisaris melalui saluran pelaporan pelanggaran. Pada tahun %d tidak terdapat '
                       'sanksi material atas ketidakpatuhan terhadap hukum dan peraturan.' % y,
                       'Critical concerns are communicated to the Board of Commissioners through the whistleblowing channel. In %d there were no '
                       'material sanctions for non-compliance with laws and regulations.' % y))
        self.page(33, 'teks', judul=('Komitmen Kebijakan', 'Policy Commitments'), gri=['2-23', '2-24'],
                  isi=('Komitmen kebijakan mencakup etika bisnis, hak asasi manusia, lingkungan, serta keselamatan kerja. Kebijakan diterapkan '
                       'melalui prosedur, pelatihan, dan pemantauan kepatuhan.',
                       'Policy commitments cover business ethics, human rights, the environment and workplace safety. Policies are embedded through '
                       'procedures, training and compliance monitoring.'))
        self.page(34, 'tabel', judul=('Perjanjian Kerja Bersama', 'Collective Bargaining Agreements'), gri=['2-30'],
                  tabel=self.numtable([
                      self.row('Jumlah karyawan', 'Number of employees', 'Orang', 'Persons', F['emp']),
                      self.row('Karyawan tercakup PKB', 'Employees covered by CBA', 'Orang', 'Persons', F['pkb']),
                      self.row('Persentase tercakup', 'Coverage', '%', '%', [pct(a, b) for a, b in zip(F['pkb'], F['emp'])], 1)]),
                  cek='r3 = r2 / r1 * 100', numeric=True)
        self.page(35, 'teks', judul=('Membangun Budaya Keberlanjutan', 'Building a Sustainability Culture'),
                  gri=['2-24', '404-2'], ojk=['F.1'], topik=['T10'],
                  isi=('Budaya keberlanjutan dibangun melalui orientasi karyawan baru, kampanye internal, dan program duta keberlanjutan di setiap lokasi operasi.',
                       'The sustainability culture is built through onboarding, internal campaigns and sustainability ambassador programs at every operating site.'))
        self.page(36, 'teks', judul=('Surat Pernyataan Tanggung Jawab', 'Statement of Responsibility'), seojk=['LT.10'],
                  isi=('Seluruh anggota Direksi dan Dewan Komisaris menyatakan bertanggung jawab penuh atas kebenaran isi laporan ini.',
                       'All members of the Board of Directors and Board of Commissioners declare full responsibility for the accuracy of this report.'))

        # ---------------- bab 04
        self.topic_page(38, 'T01', ['201-1', '201-2', '201-3', '201-4'], [
            self.row('Nilai ekonomi dihasilkan', 'Economic value generated', 'Miliar Rp', 'IDR billion', F['revenue'], 1),
            self.row('Biaya kepada pemasok', 'Payments to suppliers', 'Miliar Rp', 'IDR billion', F['supplier'], 1),
            self.row('Gaji dan tunjangan', 'Wages and benefits', 'Miliar Rp', 'IDR billion', F['wages'], 1),
            self.row('Pembayaran kepada penyedia modal', 'Payments to capital providers', 'Miliar Rp', 'IDR billion', F['capital'], 1),
            self.row('Pajak kepada pemerintah', 'Taxes to government', 'Miliar Rp', 'IDR billion', F['tax'], 1),
            self.row('Investasi masyarakat', 'Community investment', 'Miliar Rp', 'IDR billion', F['community'], 1),
            self.row('Nilai ekonomi didistribusikan', 'Economic value distributed', 'Miliar Rp', 'IDR billion', F['distributed'], 1),
            self.row('Nilai ekonomi ditahan', 'Economic value retained', 'Miliar Rp', 'IDR billion', F['retained'], 1),
            self.row('Kewajiban program pensiun', 'Pension plan obligations', 'Miliar Rp', 'IDR billion', F['pension'], 1),
            self.row('Bantuan finansial pemerintah', 'Financial assistance from government', 'Miliar Rp', 'IDR billion', [0.0, 0.0, 0.0], 1)],
            'r7 = r2 + r3 + r4 + r5 + r6; r8 = r1 - r7', seojk=['LT.8'],
            extra=('Risiko dan peluang finansial terkait iklim dinilai setiap tahun dan dilaporkan kepada Direksi.',
                   'Financial risks and opportunities related to climate change are assessed yearly and reported to the Board of Directors.'))
        self.topic_page(39, 'T02', ['204-1'], [
            self.row('Total belanja pemasok', 'Total supplier spending', 'Miliar Rp', 'IDR billion', F['supplier'], 1),
            self.row('Belanja pemasok lokal', 'Local supplier spending', 'Miliar Rp', 'IDR billion', F['local_spend'], 1),
            self.row('Proporsi pemasok lokal', 'Share of local suppliers', '%', '%', [pct(a, b) for a, b in zip(F['local_spend'], F['supplier'])], 1)],
            'r3 = r2 / r1 * 100')
        self.page(40, 'tabel', judul=('Target dan Kinerja Ekonomi', 'Economic Targets and Performance'), gri=['201-1'], ojk=['F.2'], topik=['T01'],
                  tabel=self.numtable([
                      self.row('Target pendapatan', 'Revenue target', 'Miliar Rp', 'IDR billion', F['t_rev'], 1),
                      self.row('Realisasi pendapatan', 'Revenue actual', 'Miliar Rp', 'IDR billion', F['revenue'], 1),
                      self.row('Pencapaian pendapatan', 'Revenue achievement', '%', '%', [pct(a, b) for a, b in zip(F['revenue'], F['t_rev'])], 1),
                      self.row('Target laba bersih', 'Net profit target', 'Miliar Rp', 'IDR billion', F['t_net'], 1),
                      self.row('Realisasi laba bersih', 'Net profit actual', 'Miliar Rp', 'IDR billion', F['net'], 1),
                      self.row('Pencapaian laba bersih', 'Net profit achievement', '%', '%', [pct(a, b) for a, b in zip(F['net'], F['t_net'])], 1)]),
                  cek='r3 = r2 / r1 * 100; r6 = r5 / r4 * 100', numeric=True)
        self.page(41, 'teks', judul=('Inovasi Produk dan Layanan', 'Product and Service Innovation'), gri=['3-3'], ojk=['F.26'], topik=['T01'],
                  isi=('Perusahaan mengembangkan layanan efisiensi energi dan paket energi terbarukan bagi pelanggan industri. Pengembangan '
                       'dilakukan bersama pelanggan dan diuji pada lokasi percontohan sebelum diluncurkan.',
                       'The company develops energy efficiency services and renewable energy packages for industrial customers. Development is done '
                       'with customers and tested at pilot sites before launch.'))
        self.page(42, 'tabel', judul=('Keselamatan Produk dan Layanan', 'Product and Service Safety'), gri=['3-3', '416-1', '416-2'],
                  ojk=['F.27', 'F.28', 'F.29'], topik=['T14'],
                  isi=self.approach('T14'),
                  tabel=self.numtable([
                      self.row('Kategori produk dan layanan', 'Product and service categories', 'Kategori', 'Categories', F['cat_tot']),
                      self.row('Kategori yang dievaluasi', 'Categories assessed', 'Kategori', 'Categories', F['cat_eval']),
                      self.row('Persentase dievaluasi', 'Share assessed', '%', '%', [pct(a, b) for a, b in zip(F['cat_eval'], F['cat_tot'])], 1),
                      self.row('Insiden ketidakpatuhan', 'Non-compliance incidents', 'Kasus', 'Cases', [0, 0, 0]),
                      self.row('Produk ditarik kembali', 'Products recalled', 'Unit', 'Units', [0, 0, 0])]),
                  cek='r3 = r2 / r1 * 100', numeric=True)
        self.page(43, 'kartu', judul=('Kepuasan Pelanggan', 'Customer Satisfaction'), gri=['3-3'], ojk=['F.30'], topik=['T14'],
                  kartu=[('86,4' if self.style == 'id' else '86.4', 'Indeks kepuasan (skor 0-100)', 'Satisfaction index (score 0-100)'),
                         (f(1240), 'Responden survei', 'Survey respondents'),
                         (f(98.2, 1) + '%', 'Keluhan diselesaikan', 'Complaints resolved'),
                         (f(4.5, 1), 'Skor layanan (skala 5)', 'Service score (scale 5)')])
        self.page(44, 'teks', judul=('Kepatuhan terhadap Hukum dan Peraturan', 'Compliance with Laws and Regulations'), gri=['2-27'],
                  isi=('Perusahaan memantau kepatuhan melalui audit internal dan tinjauan hukum berkala. Tidak ada denda material yang tercatat pada tahun pelaporan.',
                       'The company monitors compliance through internal audits and regular legal reviews. No material fines were recorded in the reporting year.'))

        # ---------------- bab 05
        self.topic_page(46, 'T04', ['302-1', '302-2', '302-3', '302-4', '302-5'], [
            self.row('Bahan bakar tak terbarukan', 'Non-renewable fuel', 'GJ', 'GJ', F['fuel']),
            self.row('Listrik dibeli', 'Purchased electricity', 'GJ', 'GJ', F['elec']),
            self.row('Energi terbarukan', 'Renewable energy', 'GJ', 'GJ', F['ren']),
            self.row('Total konsumsi energi', 'Total energy consumption', 'GJ', 'GJ', F['energy']),
            self.row('Pendapatan', 'Revenue', 'Miliar Rp', 'IDR billion', F['revenue'], 1),
            self.row('Intensitas energi', 'Energy intensity', 'GJ per miliar Rp', 'GJ per IDR billion', F['e_int'], 1),
            self.row('Konsumsi di luar organisasi', 'Consumption outside the organization', 'GJ', 'GJ', F['e_out']),
            self.row('Pengurangan konsumsi energi', 'Reduction in energy consumption', 'GJ', 'GJ', F['e_saved'])],
            'r4 = r1 + r2 + r3; r6 = r4 / r5', ojk=['F.6', 'F.7'],
            extra=('Kebutuhan energi produk dan layanan dikurangi melalui layanan efisiensi bagi pelanggan.',
                   'Energy requirements of products and services are reduced through efficiency services for customers.'), seojk=['LT.8'])
        self.topic_page(47, 'T05', ['303-1', '303-2', '303-3', '303-4', '303-5'], [
            self.row('Total pengambilan air', 'Total water withdrawal', 'Ribu m3', 'Thousand m3', F['w_tot'], 1),
            self.row('Air permukaan', 'Surface water', 'Ribu m3', 'Thousand m3', F['w_surf'], 1),
            self.row('Air tanah', 'Groundwater', 'Ribu m3', 'Thousand m3', F['w_gnd'], 1),
            self.row('Air pihak ketiga', 'Third-party water', 'Ribu m3', 'Thousand m3', F['w_mun'], 1),
            self.row('Pembuangan air', 'Water discharge', 'Ribu m3', 'Thousand m3', F['w_dis'], 1),
            self.row('Konsumsi air', 'Water consumption', 'Ribu m3', 'Thousand m3', F['w_con'], 1)],
            'r1 = r2 + r3 + r4; r6 = r1 - r5', ojk=['F.8'])
        self.topic_page(48, 'T06', ['305-1', '305-2', '305-3', '305-4', '305-5', '305-7'], [
            self.row('Emisi Cakupan 1', 'Scope 1 emissions', 'tCO2e', 'tCO2e', F['s1']),
            self.row('Emisi Cakupan 2', 'Scope 2 emissions', 'tCO2e', 'tCO2e', F['s2']),
            self.row('Emisi Cakupan 3', 'Scope 3 emissions', 'tCO2e', 'tCO2e', F['s3']),
            self.row('Total emisi', 'Total emissions', 'tCO2e', 'tCO2e', F['ghg']),
            self.row('Pendapatan', 'Revenue', 'Miliar Rp', 'IDR billion', F['revenue'], 1),
            self.row('Intensitas emisi', 'Emissions intensity', 'tCO2e per miliar Rp', 'tCO2e per IDR billion', F['g_int'], 1),
            self.row('Pengurangan emisi', 'Emissions reduced', 'tCO2e', 'tCO2e', F['g_red']),
            self.row('Nitrogen oksida (NOx)', 'Nitrogen oxides (NOx)', 'Ton', 'Tonnes', F['nox'], 1),
            self.row('Sulfur oksida (SOx)', 'Sulfur oxides (SOx)', 'Ton', 'Tonnes', F['sox'], 1)],
            'r4 = r1 + r2 + r3; r6 = r4 / r5', ojk=['F.11', 'F.12'],
            extra=('Zat perusak ozon tidak digunakan sehingga 305-6 tidak dilaporkan.', 'Ozone-depleting substances are not used, so 305-6 is not reported.'))
        self.topic_page(49, 'T07', ['306-1', '306-2', '306-3', '306-4', '306-5'], [
            self.row('Total limbah dihasilkan', 'Total waste generated', 'Ton', 'Tonnes', F['waste']),
            self.row('Limbah non-B3', 'Non-hazardous waste', 'Ton', 'Tonnes', F['nb3']),
            self.row('Limbah B3', 'Hazardous waste', 'Ton', 'Tonnes', F['b3']),
            self.row('Limbah dialihkan dari pembuangan', 'Waste diverted from disposal', 'Ton', 'Tonnes', F['divert']),
            self.row('Limbah ke pembuangan akhir', 'Waste directed to disposal', 'Ton', 'Tonnes', F['dispose'])],
            'r1 = r2 + r3; r1 = r4 + r5', ojk=['F.13', 'F.14', 'F.15'],
            extra=('Tidak terdapat tumpahan signifikan pada tahun pelaporan.', 'There were no significant spills in the reporting year.'))
        self.page(50, 'tabel', judul=('Biaya Lingkungan Hidup', 'Environmental Costs'), gri=['3-3'], ojk=['F.4'], topik=['T06'],
                  tabel=self.numtable([
                      self.row('Pengelolaan limbah', 'Waste management', 'Miliar Rp', 'IDR billion', F['c_waste'], 1),
                      self.row('Pemantauan lingkungan', 'Environmental monitoring', 'Miliar Rp', 'IDR billion', F['c_mon'], 1),
                      self.row('Program penghijauan', 'Greening programs', 'Miliar Rp', 'IDR billion', F['c_green'], 1),
                      self.row('Total biaya lingkungan', 'Total environmental costs', 'Miliar Rp', 'IDR billion', F['c_tot'], 1)]),
                  cek='r4 = r1 + r2 + r3', numeric=True)
        self.topic_page(51, 'T03', ['301-1', '301-2', '301-3'], [
            self.row('Total bahan digunakan', 'Total materials used', 'Ton', 'Tonnes', F['m_tot']),
            self.row('Bahan baru', 'Virgin materials', 'Ton', 'Tonnes', F['m_new']),
            self.row('Bahan input daur ulang', 'Recycled input materials', 'Ton', 'Tonnes', F['m_rec']),
            self.row('Proporsi daur ulang', 'Recycled share', '%', '%', F['m_pct'], 1),
            self.row('Produk dan kemasan direklamasi', 'Reclaimed products and packaging', 'Ton', 'Tonnes', F['m_recl'])],
            'r1 = r2 + r3; r4 = r3 / r1 * 100', ojk=['F.5'])
        self.page(52, 'teks', judul=('Keanekaragaman Hayati', 'Biodiversity'), gri=['GRI 101'], ojk=['F.9', 'F.10'],
                  isi=('Tidak ada lokasi operasi yang berada di dalam kawasan konservasi. Perusahaan menilai dampak terhadap habitat di sekitar '
                       'lokasi dan menjalankan program penanaman pohon bersama masyarakat.',
                       'No operating site is located inside a conservation area. The company assesses impacts on surrounding habitats and runs tree '
                       'planting programs with communities.'))
        self.page(53, 'tabel', judul=('Pengaduan Lingkungan Hidup', 'Environmental Complaints'), gri=['2-25', '2-26'], ojk=['F.16'],
                  tabel=self.numtable([
                      self.row('Pengaduan diterima', 'Complaints received', 'Kasus', 'Cases', F['ec_rec']),
                      self.row('Pengaduan diselesaikan', 'Complaints resolved', 'Kasus', 'Cases', F['ec_res']),
                      self.row('Persentase diselesaikan', 'Share resolved', '%', '%', [pct(a, b) for a, b in zip(F['ec_res'], F['ec_rec'])], 1)]),
                  cek='r3 = r2 / r1 * 100', numeric=True)
        self.page(54, 'teks', judul=('Inisiatif Iklim', 'Climate Initiatives'),
                  isi=('Perusahaan menambah porsi energi terbarukan, memasang sistem pemantauan energi, dan menyiapkan peta jalan penurunan emisi.',
                       'The company is increasing its renewable energy share, installing energy monitoring systems and preparing an emissions reduction roadmap.'))
        self.page(55, 'kartu', judul=('Ringkasan Lingkungan', 'Environmental Summary'),
                  kartu=[(f(pct(F['ren'][2], F['energy'][2]), 1) + '%', 'Porsi energi terbarukan', 'Renewable energy share'),
                         (f(F['g_int'][2], 1), 'Intensitas emisi (tCO2e/miliar Rp)', 'Emissions intensity (tCO2e/IDR bn)'),
                         (f(F['m_pct'][2], 1) + '%', 'Bahan input daur ulang', 'Recycled input materials'),
                         (f(pct(F['divert'][2], F['waste'][2]), 1) + '%', 'Limbah dialihkan', 'Waste diverted')])
        self.page(56, 'teks', judul=('Tantangan Lingkungan', 'Environmental Challenges'),
                  isi=('Tantangan utama adalah ketergantungan pada bahan bakar tak terbarukan dan kebutuhan data emisi rantai pasok yang lebih lengkap.',
                       'Key challenges are dependence on non-renewable fuel and the need for more complete supply chain emissions data.'))

        # ---------------- bab 06
        self.topic_page(58, 'T08', ['401-1', '401-2', '401-3'], [
            self.row('Karyawan baru', 'New hires', 'Orang', 'Persons', F['hires']),
            self.row('Karyawan keluar', 'Leavers', 'Orang', 'Persons', F['leavers']),
            self.row('Karyawan akhir tahun', 'Employees at year end', 'Orang', 'Persons', F['emp']),
            self.row('Tingkat perputaran', 'Turnover rate', '%', '%', [pct(a, b) for a, b in zip(F['leavers'], F['emp'])], 1),
            self.row('Berhak cuti orang tua', 'Entitled to parental leave', 'Orang', 'Persons', F['emp']),
            self.row('Mengambil cuti orang tua', 'Took parental leave', 'Orang', 'Persons', F['pl_took']),
            self.row('Kembali bekerja', 'Returned to work', 'Orang', 'Persons', F['pl_back'])],
            'r4 = r2 / r3 * 100',
            extra=('Tunjangan karyawan tetap juga diberikan kepada karyawan kontrak.', 'Benefits for full-time employees are also provided to contract employees.'))
        self.topic_page(59, 'T11', ['405-1', '405-2', '406-1'], [
            self.row('Total karyawan', 'Total employees', 'Orang', 'Persons', F['emp']),
            self.row('Karyawan perempuan', 'Women employees', 'Orang', 'Persons', F['women']),
            self.row('Karyawan laki-laki', 'Men employees', 'Orang', 'Persons', F['men']),
            self.row('Persentase perempuan', 'Share of women', '%', '%', [pct(a, b) for a, b in zip(F['women'], F['emp'])], 1),
            self.row('Perempuan di badan tata kelola', 'Women in governance bodies', 'Orang', 'Persons', F['gov_w']),
            self.row('Total badan tata kelola', 'Total governance body members', 'Orang', 'Persons', F['gov_t']),
            self.row('Persentase perempuan di tata kelola', 'Share of women in governance', '%', '%', [pct(a, b) for a, b in zip(F['gov_w'], F['gov_t'])], 1),
            self.row('Rasio gaji pokok perempuan terhadap laki-laki', 'Ratio of basic salary women to men', 'Rasio', 'Ratio', F['pay_ratio'], 2),
            self.row('Insiden diskriminasi', 'Discrimination incidents', 'Kasus', 'Cases', [0, 0, 0])],
            'r1 = r2 + r3; r4 = r2 / r1 * 100; r7 = r5 / r6 * 100', ojk=['F.17', 'F.18'])
        self.topic_page(60, 'T09', ['403-1', '403-2', '403-3', '403-4', '403-5', '403-6', '403-7', '403-8', '403-9', '403-10'], [
            self.row('Karyawan', 'Employees', 'Orang', 'Persons', F['emp']),
            self.row('Pekerja bukan karyawan', 'Non-employee workers', 'Orang', 'Persons', F['nonemp']),
            self.row('Pekerja tercakup sistem K3', 'Workers covered by the OHS system', 'Orang', 'Persons', [a + b for a, b in zip(F['emp'], F['nonemp'])]),
            self.row('Cedera ringan', 'Minor injuries', 'Kasus', 'Cases', F['inj_min']),
            self.row('Cedera berat', 'Serious injuries', 'Kasus', 'Cases', F['inj_sev']),
            self.row('Kecelakaan fatal', 'Fatalities', 'Kasus', 'Cases', F['inj_fat']),
            self.row('Total kecelakaan kerja', 'Total work-related injuries', 'Kasus', 'Cases', F['inj_tot']),
            self.row('Penyakit akibat kerja', 'Work-related ill health', 'Kasus', 'Cases', F['ill'])],
            'r3 = r1 + r2; r7 = r4 + r5 + r6', ojk=['F.21'],
            extra=('Sistem manajemen K3 mencakup identifikasi bahaya, investigasi insiden, layanan kesehatan kerja, dan pelatihan.',
                   'The OHS management system covers hazard identification, incident investigation, occupational health services and training.'))
        self.topic_page(61, 'T10', ['404-1', '404-2', '404-3'], [
            self.row('Total jam pelatihan', 'Total training hours', 'Jam', 'Hours', F['hours']),
            self.row('Jumlah karyawan', 'Number of employees', 'Orang', 'Persons', F['emp']),
            self.row('Rata-rata jam pelatihan', 'Average training hours', 'Jam per karyawan', 'Hours per employee', F['avg_h'], 1),
            self.row('Karyawan dengan tinjauan kinerja', 'Employees with performance reviews', '%', '%', [100.0, 100.0, 100.0], 1),
            self.row('Program peningkatan keterampilan', 'Skills upgrading programs', 'Program', 'Programs', F['programs'])],
            'r3 = r1 / r2', ojk=['F.22'])
        self.topic_page(62, 'T12', ['202-1', '202-2', '408-1', '409-1'], [
            self.row('Operasi berisiko tenaga kerja anak', 'Operations at risk of child labor', 'Operasi', 'Operations', [0, 0, 0]),
            self.row('Operasi berisiko kerja paksa', 'Operations at risk of forced labor', 'Operasi', 'Operations', [0, 0, 0]),
            self.row('Rasio upah entry-level terhadap UMR', 'Entry-level wage to minimum wage ratio', 'Kali', 'Times', F['entry'], 2),
            self.row('Manajemen senior dari masyarakat lokal', 'Senior management from the local community', '%', '%', F['local_sm'], 1)],
            '', ojk=['F.19', 'F.20'])
        self.topic_page(63, 'T13', ['413-1', '413-2'], [
            self.row('Program pengembangan masyarakat', 'Community development programs', 'Program', 'Programs', F['comm_prog']),
            self.row('Penerima manfaat', 'Beneficiaries', 'Orang', 'Persons', F['comm_ben']),
            self.row('Anggaran TJSL', 'CSR budget', 'Juta Rp', 'IDR million', F['community_juta']),
            self.row('Lokasi dengan program pelibatan', 'Sites with engagement programs', 'Lokasi', 'Sites', F['comm_ops']),
            self.row('Total lokasi operasi', 'Total operating sites', 'Lokasi', 'Sites', F['sites']),
            self.row('Persentase lokasi dengan program', 'Share of sites with programs', '%', '%', [pct(a, b) for a, b in zip(F['comm_ops'], F['sites'])], 1),
            self.row('Operasi dengan dampak negatif signifikan', 'Operations with significant negative impact', 'Operasi', 'Operations', [0, 0, 0])],
            'r6 = r4 / r5 * 100', ojk=['F.23', 'F.25'])
        self.page(64, 'tabel', judul=('Pengaduan Masyarakat', 'Community Complaints'), gri=['2-25', '2-26'], ojk=['F.24'],
                  tabel=self.numtable([
                      self.row('Pengaduan diterima', 'Complaints received', 'Kasus', 'Cases', F['cc_rec']),
                      self.row('Pengaduan diselesaikan', 'Complaints resolved', 'Kasus', 'Cases', F['cc_res']),
                      self.row('Persentase diselesaikan', 'Share resolved', '%', '%', [pct(a, b) for a, b in zip(F['cc_res'], F['cc_rec'])], 1)]),
                  cek='r3 = r2 / r1 * 100', numeric=True)
        self.page(65, 'teks', judul=('Program Tanggung Jawab Sosial', 'Social Responsibility Programs'),
                  isi=('Program meliputi pelatihan kewirausahaan, beasiswa pendidikan, dan perbaikan fasilitas umum di sekitar lokasi operasi.',
                       'Programs include entrepreneurship training, education scholarships and improvements to public facilities around operating sites.'))
        self.page(66, 'kartu', judul=('Ringkasan Sosial', 'Social Summary'),
                  kartu=[(f(F['emp'][2]), 'Karyawan', 'Employees'),
                         (f(pct(F['leavers'][2], F['emp'][2]), 1) + '%', 'Tingkat perputaran', 'Turnover rate'),
                         (f(F['hours'][2]), 'Total jam pelatihan', 'Total training hours'),
                         (f(F['comm_ben'][2]), 'Penerima manfaat TJSL', 'CSR beneficiaries')])
        self.page(67, 'teks', judul=('Kegiatan Karyawan', 'Employee Activities'),
                  isi=('Kegiatan karyawan mencakup olahraga bersama, kerja bakti, dan forum berbagi pengetahuan lintas fungsi.',
                       'Employee activities include sports days, volunteer work and cross-functional knowledge sharing forums.'))
        self.page(68, 'teks', judul=('Kisah dari Masyarakat', 'Stories from Communities'),
                  isi=('Kelompok usaha warga binaan meningkatkan pendapatan melalui pelatihan dan akses pasar yang difasilitasi perusahaan.',
                       'Community enterprise groups raised their income through training and market access facilitated by the company.'))

        # ---------------- bab 07
        self.page(70, 'teks', judul=('Verifikasi, Umpan Balik, dan Tanggapan', 'Assurance, Feedback and Responses'),
                  gri=['2-5'], ojk=['G.1', 'G.2', 'G.3'],
                  isi=('Verifikasi independen: laporan ini belum memperoleh verifikasi tertulis dari pihak independen; perusahaan berencana '
                       'memulai asurans terbatas pada periode berikutnya.\n\n'
                       'Lembar umpan balik: kami menyambut masukan pembaca tentang kejelasan dan kelengkapan laporan melalui kontak pada halaman terakhir.\n\n'
                       'Tanggapan atas umpan balik tahun sebelumnya: pembaca meminta data tiga tahun dan penjelasan topik material yang lebih rinci; '
                       'keduanya telah diterapkan pada laporan ini.',
                       'Independent assurance: this report has not received written independent assurance; the company plans to start limited '
                       'assurance in the next period.\n\n'
                       'Feedback form: we welcome reader feedback on the clarity and completeness of this report through the contact on the last page.\n\n'
                       'Response to prior-year feedback: readers asked for three years of data and more detailed explanations of material topics; '
                       'both are reflected in this report.'))
        self.page(71, 'teks', judul=('Laporan Keuangan Tahunan yang Diaudit', 'Audited Annual Financial Statements'), seojk=['LT.9'],
                  isi=('Laporan keuangan tahunan yang telah diaudit dilampirkan sebagai bagian terpisah dari Laporan Tahunan ini.',
                       'The audited annual financial statements are attached as a separate part of this Annual Report.'))
        for n, part in ((72, ''), (73, ' (lanjutan)'), (74, ' (lanjutan)'), (75, ' (lanjutan)')):
            self.page(n, 'indeks-gri', judul=('Indeks Konten GRI' + part, 'GRI Content Index' + part.replace('lanjutan', 'continued')))
        self.page(76, 'indeks-ojk', judul=('Daftar Pengungkapan POJK 51/POJK.03/2017', 'POJK 51/POJK.03/2017 Disclosure Index'), ojk=['G.4'])
        self.page(77, 'indeks-ojk', judul=('Daftar Pengungkapan POJK 51/POJK.03/2017 (lanjutan)', 'POJK 51/POJK.03/2017 Disclosure Index (continued)'))
        self.page(78, 'indeks-seojk', judul=('Indeks Silang SEOJK 16/SEOJK.04/2021', 'SEOJK 16/SEOJK.04/2021 Cross Index'))
        self.page(79, 'teks', judul=('Glosarium dan Kontak', 'Glossary and Contact'),
                  isi=('GJ: gigajoule. tCO2e: ton setara karbon dioksida. K3: keselamatan dan kesehatan kerja. TJSL: tanggung jawab sosial dan lingkungan.\n\n'
                       '%s. Email: %s. Telepon: %s. Situs: %s.' % (self.addr[0], mdparse.cfg_kv(self.cfg, 'KONTAK', 'email'),
                                                                   mdparse.cfg_kv(self.cfg, 'KONTAK', 'telepon'), mdparse.cfg_kv(self.cfg, 'KONTAK', 'web')),
                       'GJ: gigajoule. tCO2e: tonnes of carbon dioxide equivalent. OHS: occupational health and safety. CSR: corporate social and environmental responsibility.\n\n'
                       '%s. Email: %s. Phone: %s. Website: %s.' % (self.addr[1], mdparse.cfg_kv(self.cfg, 'KONTAK', 'email'),
                                                                  mdparse.cfg_kv(self.cfg, 'KONTAK', 'telepon'), mdparse.cfg_kv(self.cfg, 'KONTAK', 'web'))))
        self.page(80, 'sampul', judul=(co, co), subjudul=self.theme, tahun=str(y))
        # ---------------- pages used by the annual-report chapters (numbers 101+ are not part of the old 80-page plan)
        self.page(101, 'tabel', judul=('Tinjauan Kinerja Keuangan', 'Financial Performance Review'), seojk=['LT.6'],
                  isi=('Laba usaha dan laba bersih meningkat seiring pertumbuhan pendapatan yang lebih cepat daripada beban usaha.',
                       'Operating profit and net profit increased as revenue grew faster than operating expenses.'),
                  tabel=self.numtable([
                      self.row('Pendapatan', 'Revenue', 'Miliar Rp', 'IDR billion', F['revenue'], 1),
                      self.row('Beban usaha', 'Operating expenses', 'Miliar Rp', 'IDR billion', F['opex'], 1),
                      self.row('Laba usaha', 'Operating profit', 'Miliar Rp', 'IDR billion', F['op'], 1),
                      self.row('Beban pajak', 'Income tax expense', 'Miliar Rp', 'IDR billion', F['tax'], 1),
                      self.row('Laba bersih', 'Net profit', 'Miliar Rp', 'IDR billion', F['net'], 1)]),
                  cek='r3 = r1 - r2; r5 = r3 - r4', numeric=True)
        self.page(102, 'tabel', judul=('Ringkasan Posisi Keuangan', 'Summary of Financial Position'),
                  tabel=self.numtable([
                      self.row('Total aset', 'Total assets', 'Miliar Rp', 'IDR billion', F['assets'], 1),
                      self.row('Total liabilitas', 'Total liabilities', 'Miliar Rp', 'IDR billion', F['liab'], 1),
                      self.row('Total ekuitas', 'Total equity', 'Miliar Rp', 'IDR billion', F['equity'], 1)]),
                  cek='r3 = r1 - r2', numeric=True)
        self.page(103, 'teks', judul=('Prospek Usaha', 'Business Prospects'),
                  isi=('Perusahaan memperkirakan permintaan layanan tetap stabil pada tahun berikutnya dan akan memprioritaskan efisiensi biaya, '
                       'penguatan modal kerja, dan investasi pada kapasitas yang sudah disetujui.',
                       'The company expects service demand to remain steady next year and will prioritize cost efficiency, working capital '
                       'strength and investment in already approved capacity.'))
        self.page(104, 'teks', judul=('Laporan Auditor Independen', 'Independent Auditor Report'),
                  isi=('Laporan auditor independen atas laporan keuangan konsolidasian dilampirkan pada bagian terpisah. Halaman ini adalah '
                       'penanda posisi lampiran dan memuat data contoh.',
                       'The independent auditor report on the consolidated financial statements is attached as a separate part. This page marks '
                       'the position of the attachment and holds sample data.'))
        return self.pages

    # ---------------------------------------------------------- assembly by report type
    def assemble(self):
        """Arrange the source pages into final physical pages for self.jenis and self.divider."""
        layout = [(slug, [self._tweak(k, dict(self.pages[k])) for k in ids]) for slug, ids in LAYOUT[self.jenis]]
        return arrange(layout, self.struct, self.divider, dummy=True)

    def _tweak(self, k, pg):
        if self.jenis == 'LT':
            for a in ('gri', 'ojk', 'topik'):
                pg.pop(a, None)
            if k == 3:
                i, e = pg['isi']
                pg['isi'] = (i.split(' Laporan disusun')[0] + ' Laporan disusun mengacu pada SEOJK 16/SEOJK.04/2021.',
                             e.split(' It is prepared')[0] + ' It is prepared with reference to SEOJK 16/SEOJK.04/2021.')
        if self.jenis == 'LK':
            pg.pop('seojk', None)
        return pg

    def chapters(self):
        chapters, pages = self.assemble()
        self.final = pages
        self.chapter_rows = chapters
        return render_chapters(chapters, pages, self.Y)


def generate(template_dir, out_dir, config=None, jenis=None, divider=None):
    """Write a project's data folder with dummy content for the chosen report type.
    config = a 00_config.md to start from (year, names, palette); jenis = LK | LT | LT+LK; divider = 1 | 2."""
    cfg_src = config or os.path.join(template_dir, 'data', '00_config.md')
    cfg = mdparse.parse_config(cfg_src)
    g = Gen(cfg, jenis, divider)
    g.plan()
    files = g.chapters()
    data = os.path.join(out_dir, 'data')
    os.makedirs(data)
    text = mdparse.read_text(cfg_src)
    text = config_text(text, g.jenis, g.divider, g.chapter_rows, len(g.final))
    with open(os.path.join(data, '00_config.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    for fname, body in files:
        with open(os.path.join(data, fname), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(body)
    return len(files)
