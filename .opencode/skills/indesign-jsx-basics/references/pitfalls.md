# Common InDesign scripting failures

| Symptom | Likely cause | Fix |
|---|---|---|
| "Syntax error" at load, no line useful | ES5+ syntax, trailing comma, non-ASCII char | `python tools/jsx_lint.py engine/jsx` |
| "undefined is not an object" | Misspelled property or enum, or item not found | Check `.isValid`; check the enum name in the reference |
| Text appears in the wrong place on right pages | Coordinates relative to spread, not page | Offset by `page.bounds` |
| Style not found | Names are per group; `itemByName` on the wrong collection | Keep a map name -> style object when creating |
| Tint call fails | Wrong property names | `baseColor`, `tintValue`; log WARN and fall back to the base color |
| Frame shows overflow mark | Too much text for the frame | Resize or split; QA reports DOC-03 |
| Table cell text in wrong style | Style applied to the cell before contents | Set `contents` first, then `paragraphs.everyItem().appliedParagraphStyle` |
| Tags `<e>` visible | GREP styles missing on that paragraph style | Add the tag set through `addTagGreps()`; never hand-format |
| Rounded corners fail | Property names differ by version | Log WARN, keep square header (spec allows) |
| Script runs but nothing happens | Ran from the wrong menu or no plan found | Run `python engine/run.py plan <project>` first; check `%APPDATA%\ARSR\last_plan.txt` |
| Slow build | Per-cell formatting on huge tables | Acceptable; do not add `redraw` hacks. Keep `userInteractionLevel` NEVER_INTERACT |
| `UserInteractionLevels.NEVER_INTERACT_WITH_USER` not found | InDesign enum is `NEVER_INTERACT` | Use `UserInteractionLevels.NEVER_INTERACT` |
| `doc.lists` not found | Numbering lists collection is `numberingLists` | Use `doc.numberingLists.add` and `doc.numberingLists.itemByName` |
| `paragraphStyle.numberingList` not found | Property is `appliedNumberingList` | Use `style.appliedNumberingList = doc.numberingLists.itemByName(...)` |
| `masterSpread.name` read-only | Master spread name is set via `namePrefix` | Use `ms.namePrefix = 'A'` (or remove) |
| `NumberingStyle.LOWERCASE_LETTERS` / `LOWERCASE_ROMAN` not found | InDesign uses `LOWER_LETTERS` / `LOWER_ROMAN` | Use `NumberingStyle.LOWER_LETTERS` and `LOWER_ROMAN` |
| Fonts look ~3x too big, text overset everywhere (hundreds of preflight errors) | Numbers written to `pointSize`, `leading`, stroke weights are read in the script unit (mm) | Write them as `"34 pt"` strings (`PT_KEYS` in `applyProps`) |
| Items on right-hand pages sit outside the page | `page.bounds` returns spread-based numbers; with ruler origin PAGE_ORIGIN coordinates are page-relative | Use 0..W, 0..H; never add `page.bounds` to coordinates |
| Build runs again and again, new Untitled-N documents | `alert()` blocks automation and the agent re-runs the script | No `alert()`; read `ARSR_Build_Done.txt` / `ARSR_Build_Log.txt`; the script skips if a built document is open |
| ID and EN text on one line | `String.fromCharCode(8232)` is not a forced line break when written to `contents` | `probeBreak()` tests `'\n'`, U+2028, U+000B on a temp frame and keeps the one that gives 2 lines in 1 paragraph |
| Colored cover/divider bleeds into the neighbouring page | Bleed rectangle extended past the spine | Use `bleedRect(page, fill)`: bleed only on outer sides |
| Index table overflows its frame | Fixed rows-per-page guess | `plan.py` packs index rows by estimated height (`pack_rows`); PLN-01 says how many pages are needed |

Items marked UNVERIFIED in the log came from a mock only; confirm them in real InDesign and record the result here.
