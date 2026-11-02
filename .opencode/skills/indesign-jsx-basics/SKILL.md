---
name: indesign-jsx-basics
description: How to write and fix Adobe InDesign ExtendScript (.jsx, ES3) with few errors - DOM object model, units, styles, tables, GREP, layers, logging, common failures. Use before writing or editing any .jsx file or when InDesign reports a script error.
---

# indesign-jsx-basics

InDesign runs ExtendScript = JavaScript ES3 + an InDesign DOM. Python cannot run inside InDesign. JSX files live in `engine/jsx/`.

## Hard rules (a violation = script fails to load)

1. ES3 only: `var`, `function`, no `let`/`const`, no arrow functions, no template strings, no trailing commas, no `JSON`, no `forEach/map/filter/indexOf` on arrays, no `Object.keys`, no `String.trim`.
2. ASCII only in code and comments. Write non-ASCII as `²`. Read data files with `file.encoding = 'UTF-8'`.
3. Wrap each item in `try/catch` (use `safe(where, fn)`); one bad item must not stop the build. Log to Desktop.
4. Never edit the document in a QA script. Read only.
5. Run `python tools/jsx_lint.py engine/jsx` after every edit. Run `python -m unittest discover -s tests` (includes a Node mock build).

## Mental model

`app` > `documents` > `document` > `pages`, `layers`, `swatches`, `paragraphStyles`, `characterStyles`, `tables`...
Collections: `coll.add({props})`, `coll.itemByName('x')` (check `.isValid`), `coll[0]`, `coll.everyItem().prop = v`, `coll.length`.
Enumerations are constants, e.g. `Justification.LEFT_ALIGN`, `MeasurementUnits.MILLIMETERS`. A wrong enum name gives "undefined" or an error: confirm names in the InDesign scripting reference when unsure.

## Setup used by this repo

```
app.scriptPreferences.measurementUnit = MeasurementUnits.MILLIMETERS;  // restore in finally
doc.viewPreferences.textSizeMeasurementUnits = MeasurementUnits.POINTS;
doc.viewPreferences.rulerOrigin = RulerOrigin.PAGE_ORIGIN;
geometricBounds = [y1, x1, y2, x2]      // top, left, bottom, right
```
Facing pages: page coordinates differ per page. Always offset from `page.bounds` (see `pageArea()` in `build_report.jsx`).

## Patterns

| Task | Pattern |
|---|---|
| Swatch | `doc.colors.add({name, model: ColorModel.PROCESS, space: ColorSpace.RGB, colorValue: [r,g,b]})` |
| Tint | `doc.tints.add({name, baseColor, tintValue})` |
| Paragraph style | `doc.paragraphStyleGroups.add({name})` then `grp.paragraphStyles.add({name})` |
| GREP style | `style.nestedGrepStyles.add({grepExpression, appliedCharacterStyle})` |
| Text frame | `page.textFrames.add({geometricBounds, itemLayer})`; set `.contents`, then style paragraphs |
| Native table | `frame.insertionPoints[0].tables.add({headerRowCount:1, bodyRowCount:n, columnCount:c})` |
| Forced line break | `String.fromCharCode(8232)` |
| Auto folio | `frame.contents = SpecialCharacters.AUTO_PAGE_NUMBER` on the master |
| Log | `File(Folder.desktop.fsName + '/X.txt')`, `encoding='UTF-8'`, `open('w')`, `write`, `close` |

More detail and failure table: `references/pitfalls.md`.

## Error handling workflow

1. Run the script. Open the Desktop log. Take the FIRST ERROR line (rule | where | message).
2. Fix only that cause. Re-run lint + tests + InDesign. One change, one check.
3. If a property name or enum is rejected, search the InDesign scripting reference, change that one line, and note it in `references/pitfalls.md`.
