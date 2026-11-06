# templates/dummy-company

Fictional starter project. Copy this folder, never edit it in place.

Only `data/00_config.md` is stored here. Chapter files (bilingual, all `dummy: ya`) are generated from this config for the report type you choose:

```
python engine/run.py new <out_dir> --jenis LT+LK --divider 2
```

`--jenis` LK, LT or LT+LK picks the chapters (`structures/`); `--divider` 1 or 2 picks one-page or two facing-page chapter dividers. `new` also writes the chapter table and page count into the project's config. The generator expects the 14 topics (T01..T14) of this config. Change names, years, palette, fonts and margins freely; if you change the topics, adjust `engine/arsr/dummy.py` too.

The config uses `gri.versi: pra-2027` (GRI 302/305 valid) so every cited code exists in the catalog. Switch to `2027` only after adding GRI 101/102/103 disclosure numbers from the official text.
