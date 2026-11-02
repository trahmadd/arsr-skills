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

Items marked UNVERIFIED in the log came from a mock only; confirm them in real InDesign and record the result here.
