# templates/dummy-company

Fictional starter project. Copy this folder, never edit it in place.

Only `data/00_config.md` is stored here. Chapter files `01_*.md` ... `07_*.md` (80 pages, bilingual, all `dummy: ya`) are generated from this config:

```
python engine/run.py dummy <out_dir>
```

The generator expects the 7 chapters and 14 topics (T01..T14) of this config. Change names, years, palette, fonts and margins freely; if you change chapters, topics or `jumlah-halaman`, adjust `engine/arsr/dummy.py` too.

The config uses `gri.versi: pra-2027` (GRI 302/305 valid) so every cited code exists in the catalog. Switch to `2027` only after adding GRI 101/102/103 disclosure numbers from the official text.
