# MANUAL: perintah dan prompt untuk validator / Manual for testers

Untuk siapa pun (manusia atau agen AI) yang memakai atau menguji repo `arsr-skills`. Semua perintah dijalankan dari **folder utama repo**, Python 3.8+, tanpa library tambahan. Contoh memakai PowerShell di Windows 11.
For anyone (human or AI agent) who uses or tests this repo. Run every command from the **repo root**; Python 3.8+, no extra libraries.

> **Aturan emas / Golden rules**
> 1. Validator dan QA hanya membaca. Satu-satunya yang dibuat: folder kosong `source/ build/ logs/` dan berkas log.
> 2. Semua log ada di `<proyek>\logs\`. Baca **baris pertama** log dulu, lalu **ERROR pertama**.
> 3. Build InDesign dijalankan **satu kali**. Jangan diulang hanya untuk "memeriksa".
> 4. Jangan mengarang kode GRI / OJK / SEOJK. Baris `verified: no` di `catalogs/` hanya menghasilkan peringatan.
> 5. Letakkan folder proyek **di luar repo** (mis. `C:\work\smlg`).

---

## 1. Perintah / Commands

| Tujuan | Perintah | Hasil |
|---|---|---|
| Buat proyek baru (data dummy) | `python engine\run.py new C:\work\smlg --jenis LT+LK --divider 2 --config C:\work\smlg.md` | `data\ source\ build\ logs\` + berkas bab. `dummy` = nama lama, sama saja |
| Impor Word/Excel | `python engine\run.py import C:\work\smlg` | `source\*.docx` menjadi `data\*.md`; data lama ke `build\data_before_import`; log impor |
| Validasi data (baca-saja) | `python engine\run.py validate C:\work\smlg` | `logs\ARSR_Validate_Log.txt`; keluar 0 = tanpa error, 1 = ada error, 2 = salah pakai |
| Rencana build | `python engine\run.py plan C:\work\smlg` | `build\build_plan.json`, `build\run_build.jsx`, `build\run_qa.jsx` |
| Build di InDesign | jalankan `C:\work\smlg\build\run_build.jsx` **sekali** (File > Scripts > Scripts Panel, klik ganda) | dokumen baru; `logs\ARSR_Build_Log.txt`, `ARSR_Build_Done.txt`, `Dummy_Register.txt`; `build\report.indd` |
| QA dokumen (baca-saja) | jalankan `C:\work\smlg\build\run_qa.jsx` pada dokumen yang terbuka | `logs\ARSR_QA_Log.txt` |
| Cek gaya kode JSX | `python tools\jsx_lint.py engine\jsx` | `0 error(s)` |
| Semua tes otomatis | `python -m unittest discover -s tests` | `Ran 51 tests ... OK` (tes mock butuh Node 18+, dilewati bila tidak ada) |
| Buat contoh Word untuk copywriter | `python tools\make_word_example.py C:\work\contoh --jenis LT+LK` | `.docx` + `Contoh_Tabel.xlsx` (butuh `python-docx` dan `openpyxl`) |
| Uji skill pada model gratis | `python tools\eval_check.py seed E2 C:\work\e2` / `snapshot` / `check E1 C:\work\p1` | PASS/FAIL per butir (lihat `evals\README.md`) |

Opsi:
- `new` / `dummy`: `--jenis LK|LT|LT+LK`, `--divider 1|2` (default 2), `--config <00_config.md>`, `--force` (timpa folder yang ada).
- `validate` / `plan`: `--log-dir <folder>` mengganti lokasi log (bawaan `<proyek>\logs`). `plan --no-pointer` tidak menulis `%APPDATA%\ARSR\last_plan.txt`.
- `import`: `--gri-pages N` (bawaan 4), `--ojk-pages N` (bawaan 2) bila `plan` melapor PLN-01.

Jenis laporan: **LT** Laporan Tahunan, **LK** Laporan Keberlanjutan, **LT+LK** terintegrasi. Bab tiap jenis: `structures\lk.md`, `lt.md`, `lt-lk.md`.

## 2. Alur kerja baku / Standard flow

```powershell
python engine\run.py new C:\work\smlg --jenis LT+LK --divider 2
python engine\run.py validate C:\work\smlg
python engine\run.py plan C:\work\smlg
# InDesign: build\run_build.jsx (sekali), lalu build\run_qa.jsx
```

Dari Word: taruh `*.docx` (dan `*.xlsx`) di `C:\work\smlg\source\`, jalankan `import`, lalu `validate` dan `plan`. Panduan penulisan: `docs\penulisan-word.md`; contoh: `templates\contoh-word\`.

## 3. Membaca log / Reading logs

| Berkas di `<proyek>\logs\` | Isi | Baris pertama |
|---|---|---|
| `ARSR_Validate_Log.txt` | temuan validator | `ERROR n \| WARN n \| pages n` |
| `ARSR_Import_Log.txt` | catatan impor Word/Excel | `ERROR n \| WARN n \| import \| pages n` |
| `ARSR_Build_Log.txt` | log build InDesign | `ERROR n \| WARN n \| build_report.jsx ...` |
| `ARSR_Build_Done.txt` | status akhir build | `DONE OK` atau `DONE WITH ERRORS` |
| `ARSR_QA_Log.txt` | QA dokumen | `ERROR n \| WARN n \| qa_document.jsx` |
| `Dummy_Register.txt` | halaman dan bagian berdata dummy | tab: halaman, bagian |

Format baris: `[ATURAN] lokasi | pesan` (validator) atau `LEVEL | tempat | pesan` (build). Perbaiki **ERROR paling atas**, jalankan ulang, ulangi sampai `ERROR 0`. WARN ditinjau, tidak diabaikan.

## 4. Kode aturan / Rule ids

Daftar lengkap: `.opencode\skills\arsr-data-spec\references\validation-rules.md`. Ringkasan:

| Awalan | Arti | Contoh tindakan |
|---|---|---|
| `CFG-` | `00_config.md` salah (bagian, kunci, nilai) | samakan dengan `templates\dummy-company\data\00_config.md` |
| `STR-01..12` | struktur berkas bab, halaman, kunci, tabel | lihat `page-types.md` |
| `STR-13` | divider 2 halaman: harus mulai di halaman kiri, disusul `divider-kanan` | tambah/kurangi satu halaman sebelum divider (halaman `catatan` boleh) |
| `STR-20` / `STR-21` | bab wajib / halaman wajib sesuai `jenis` | tambah bab atau halaman indeks yang diminta |
| `NUM-01..04` | rumus `cek`, format angka, label tahun | betulkan angka atau `periode` |
| `GRI-` / `OJK-` | kode regulasi dan cakupan | pakai kode dari `catalogs\`; catat alasan di `OMISI` bila tidak berlaku |
| `PLN-01` | baris indeks/daftar isi tidak muat | tambah halaman indeks (`--gri-pages`, `--ojk-pages`) atau halaman `daftar-isi` |
| `DOC-01..08` | QA dokumen InDesign | lihat `arsr-validate-qa` |

Catatan jenis: untuk `LT` aturan GRI dan POJK 51 dilewati; untuk `LK` aturan SEOJK dilewati.

## 5. Daftar uji untuk validator / Tester checklist

Jalankan berurutan; catat hasil tiap butir.

| # | Uji | Perintah | Hasil yang diharapkan |
|---|---|---|---|
| 1 | Tes otomatis | `python -m unittest discover -s tests` | `OK`, 51 tes |
| 2 | Linter | `python tools\jsx_lint.py engine\jsx` | `0 error(s)` |
| 3 | Enam kombinasi | `new C:\work\t\LK-1 --jenis LK --divider 1` dan seterusnya untuk LT, LT+LK, divider 1 dan 2; lalu `validate` | `ERROR 0` semua. Jumlah halaman: LK 80/92, LT 52/64, LT+LK 88/100 (divider 1/2) |
| 4 | Peringatan GRI | `validate` pada LK atau LT+LK | tepat satu WARN `GRI-02` (85 kode `verified: no`); LT tanpa WARN |
| 5 | Kesalahan sengaja | ganti satu kode di berkas bab menjadi `gri: 999-9` | `ERROR GRI-01` (kode tidak ada di katalog); `plan` menolak dengan pesan "project has 1 validation error(s)" |
| 6 | Impor | `new ... --jenis LT+LK --divider 2`, salin contoh Word dan Excel ke `source\`, `import`, `validate` | `import` 100 halaman, `validate` `ERROR 0` |
| 7 | Log di folder proyek | setelah `validate` | berkas ada di `<proyek>\logs\`, **tidak** di Desktop |
| 8 | Folder otomatis | hapus `source\`, jalankan `validate` | `source\` terbuat kembali |
| 9 | Launcher | buka `build\run_build.jsx` | berisi `ARSR_PLAN_PATH` dan `#include` ke `engine\jsx\build_report.jsx` |
| 10 | Build InDesign | `run_build.jsx` sekali | `DONE OK`, `ERROR 0`; tidak ada popup; dokumen tersimpan di `build\report.indd` |
| 11 | Pemeriksaan visual | buka dokumen hasil | semua item di dalam halaman; divider 2 halaman berhadapan (kiri bernomor, kanan berisi daftar bagian dan kotak foto); tabel pendek dan kutipan terisi kotak placeholder |
| 12 | QA | `run_qa.jsx` | `ERROR 0` |

Bila butir 10-12 gagal: salin **satu baris ERROR pertama**, ubah satu tempat saja di `engine\jsx\build_report.jsx`, jalankan lint dan tes, lalu build ulang setelah menutup dokumen lama. Catat nama API InDesign yang dikoreksi di `.opencode\skills\indesign-jsx-basics\references\pitfalls.md`.

## 6. Prompt siap pakai untuk agen (OpenCode) / Ready prompts

Sebut skill, tugas, dan batas. Tambahkan: `Jawab maksimal 5 baris. Jangan menempel isi skrip ke chat.`

```text
Pakai skill arsr-start. Proyek baru C:\work\smlg jenis LK, divider 2, dari config C:\work\smlg.md. Jalankan validate dan plan. Laporkan hanya ERROR pertama dan hasil akhir.
Pakai skill arsr-validate-qa. Perbaiki ERROR pertama di log validasi, jalankan ulang, ulangi sampai 0 ERROR. Jangan baca berkas bab yang tidak disebut log.
Pakai skill arsr-import-word. Berkas Word ada di C:\work\smlg\source. Jalankan import lalu validate. Laporkan peringatan impor dan ERROR pertama.
Pakai skill arsr-build-test. Jalankan run_build.jsx SEKALI untuk C:\work\smlg. Baca ARSR_Build_Done.txt dan ERROR pertama di ARSR_Build_Log.txt. Jangan ulangi build.
Pakai skill arsr-validate-qa. Jalankan run_qa.jsx pada dokumen terbuka dan ringkas ERROR di ARSR_QA_Log.txt per aturan DOC-xx.
Pakai skill indesign-jsx-basics. ERROR pertama dari log build: <tempel>. Ubah satu tempat saja, jalankan lint dan tes.
Ubah hanya data\00_config.md: Primary #0B3C5D, font Inter. Jangan menyentuh engine.
Pakai skill arsr-data-spec. Ganti jenis proyek C:\work\smlg menjadi LT+LK dengan divider 1. Validasi dan laporkan jumlah halaman.
```

## 7. Pemecahan masalah / Troubleshooting

| Gejala | Penyebab umum | Tindakan |
|---|---|---|
| `not a folder` (kode 2) | jalur proyek salah | periksa jalur; proyek harus punya `data\00_config.md` |
| `no .docx file in source/` | Word belum ditaruh | salin berkas ke `<proyek>\source\` |
| `cannot map Heading 1` | judul bab tidak dikenal | tambah baris Meta `slug: nama-bab` di bawahnya |
| `NUM-04` | tahun di config berubah setelah data dibuat | buat ulang proyek (`new ... --force`) atau samakan kolom tahun |
| `STR-13` | divider mulai di halaman kanan | tambah/kurangi satu halaman di bab sebelumnya |
| `PLN-01` | indeks atau daftar isi tidak muat | `import --gri-pages N` / tambah halaman `daftar-isi` |
| Build dilewati: "already built" | dokumen hasil build masih terbuka | tutup dokumen, atau `$.global.ARSR_FORCE = true` |
| Log muncul di Desktop | plan lama tanpa `logDir` | jalankan ulang `plan` |
| Folder tujuan read-only | atribut Windows | `attrib -r <folder>` |
| Tes mock dilewati | Node tidak terpasang | pasang Node 18+ |

## 8. Yang belum terbukti / Known limits

- JSX hanya teruji lewat mock Node dan uji nyata di InDesign; nama API baru bisa memunculkan ERROR pada build pertama.
- Pemecahan halaman hasil impor memakai estimasi karakter dan baris; periksa peringatan overflow.
- Judul GRI Topic Standard `verified: no`; data OJK/SEOJK dari salinan pihak ketiga yang tidak lengkap; nomor GRI 101/102/103 belum ada.
- DOC-09 belum diimplementasikan. PDF tidak diimpor.
- Katalog regulasi membantu validasi, bukan nasihat hukum.
