#target indesign
/*
 * build_report.jsx - ARSR build engine (ExtendScript ES3, ASCII only).
 * Reads build_plan.json (made by: python engine/run.py plan <project>) and builds the InDesign document:
 * swatches, tints, styles (GREP tag system), layers, master, pages, native tables, TOC and indexes.
 * It holds NO project data. Log: Desktop/ARSR_Build_Log.txt.
 * STATUS: written without access to a real InDesign. Run, read the log, fix. See skills/arsr-build-test.
 */
(function () {
    var VERSION = '0.1.0';
    var HIGHLIGHT_DUMMY = true;      // wrap dummy text in <dum>...</dum>
    var BR = '\n';   // forced line break (Shift+Enter); probeBreak() picks the character that really breaks a line
    var TAB = '\t';
    var LOG = [];
    var NERR = 0, NWARN = 0;

    // ------------------------------------------------------------------ helpers
    function log(level, where, msg) {
        if (level === 'ERROR') { NERR++; } else if (level === 'WARN') { NWARN++; }
        LOG.push(level + ' | ' + where + ' | ' + msg);
    }
    function safe(where, fn) {
        try { return fn(); } catch (e) { log('ERROR', where, String(e.message || e) + ' (line ' + e.line + ')'); return null; }
    }
    function each(arr, fn) { var i; for (i = 0; i < arr.length; i++) { fn(arr[i], i); } }
    function has(arr, v) { var i; for (i = 0; i < arr.length; i++) { if (arr[i] === v) { return true; } } return false; }
    function readText(f) {
        f.encoding = 'UTF-8';
        if (!f.open('r')) { throw new Error('cannot open ' + f.fsName); }
        var t = f.read();
        f.close();
        return t;
    }
    function writeLog() {
        var f = new File(Folder.desktop.fsName + '/ARSR_Build_Log.txt');
        f.encoding = 'UTF-8';
        if (f.open('w')) {
            f.write('ERROR ' + NERR + ' | WARN ' + NWARN + ' | build_report.jsx ' + VERSION + '\n' + LOG.join('\n') + '\n');
            f.close();
        }
    }
    // No alert(): a modal dialog blocks automation and made agents re-run the build. Status goes to files.
    function writeDone() {
        var f = new File(Folder.desktop.fsName + '/ARSR_Build_Done.txt');
        f.encoding = 'UTF-8';
        if (f.open('w')) {
            f.write((NERR ? 'DONE WITH ERRORS' : 'DONE OK') + ' | ERROR ' + NERR + ' | WARN ' + NWARN + '\nBuild finished. Do not run the build again; read ARSR_Build_Log.txt.\n');
            f.close();
        }
    }
    function alreadyBuilt() {
        var i, d;
        for (i = 0; i < app.documents.length; i++) {
            d = app.documents[i];
            try { if (d.extractLabel('ARSR_BUILD') === 'yes') { return d.name; } } catch (e) { }
        }
        return null;
    }
    function findPlan() {
        if ($.global.ARSR_PLAN_PATH) { return new File($.global.ARSR_PLAN_PATH); }
        var ptr = new File(Folder.userData.fsName + '/ARSR/last_plan.txt');
        if (ptr.exists) {
            var p = readText(ptr).replace(/[\r\n]+$/, '');
            var f = new File(p);
            if (f.exists) { return f; }
            log('WARN', 'plan', 'pointer file points to a missing plan: ' + p);
        }
        return File.openDialog('Select build_plan.json');
    }
    function probeBreak(d) {
        var cands = ['\n', String.fromCharCode(8232), String.fromCharCode(11)], i, t, ok;
        for (i = 0; i < cands.length; i++) {
            ok = false;
            try {
                t = d.pages[0].textFrames.add({ geometricBounds: [0, 0, 20, 120] });
                t.contents = 'a' + cands[i] + 'b';
                ok = (t.paragraphs.length === 1 && t.lines.length === 2);
                t.remove();
            } catch (e) { ok = false; try { t.remove(); } catch (e2) { } }
            if (ok) { log('INFO', 'break', 'forced line break = char code ' + cands[i].charCodeAt(0)); return cands[i]; }
        }
        log('ERROR', 'break', 'no character produced a forced line break; ID and EN will share one line');
        return '\n';
    }
    function paraJoin(parts) { return parts.join('\r'); }
    function biText(idText, enText, tagEn) {
        return idText + BR + '<' + (tagEn || 'e') + '>' + enText + '</' + (tagEn || 'e') + '>';
    }
    function dum(text, on) { return (on && HIGHLIGHT_DUMMY) ? '<dum>' + text + '</dum>' : text; }

    // ------------------------------------------------------------------ globals set in run()
    var app_ = app, doc, plan, L = {}, SW = {}, PS = {}, CS = {}, W, H, M, TEXTW;
    var NUMRX = /^\(?[\-\u2212+]?\(?[A-Za-z$]{0,3}\s?[0-9][0-9.,]*\s?%?\)?$/;

    // ------------------------------------------------------------------ swatches and tints
    function swatch(name) { return doc.swatches.itemByName(name); }
    function makeSwatches() {
        var k;
        for (k in plan.colors) {
            if (plan.colors.hasOwnProperty(k)) {
                (function (name, rgb) {
                    safe('swatch ' + name, function () {
                        doc.colors.add({ name: name, model: ColorModel.PROCESS, space: ColorSpace.RGB, colorValue: rgb });
                        SW[name] = doc.colors.itemByName(name);
                    });
                })(k, plan.colors[k]);
            }
        }
    }
    function tint(base, pct) {
        var name = base + ' ' + pct;
        if (SW[name]) { return SW[name]; }
        var t = null;
        try {
            t = doc.tints.add({ name: name, baseColor: SW[base], tintValue: pct });
        } catch (e) {
            log('WARN', 'tint ' + name, 'tint failed, base color used: ' + e.message);
            t = SW[base];
        }
        SW[name] = t;
        return t;
    }
    function color(ref) {   // 'Primary' or 'Primary@45'
        var p = String(ref).split('@');
        if (!SW[p[0]]) { log('ERROR', 'color', 'unknown swatch ' + p[0]); return null; }
        return p.length > 1 ? tint(p[0], Number(p[1])) : SW[p[0]];
    }
    // Numbers written to these properties are read in the SCRIPT unit (mm here), so a 34 pt title became 34 mm.
    // Pass them as "N pt" strings. Everything else in this script is millimetres.
    var PT_KEYS = ['pointSize', 'leading', 'ruleBelowLineWeight', 'ruleBelowOffset', 'underlineWeight', 'underlineOffset',
        'topEdgeStrokeWeight', 'bottomEdgeStrokeWeight', 'leftEdgeStrokeWeight', 'rightEdgeStrokeWeight',
        'topBorderStrokeWeight', 'bottomBorderStrokeWeight', 'leftBorderStrokeWeight', 'rightBorderStrokeWeight'];
    function applyProps(obj, props, where) {
        var k, v;
        for (k in props) {
            if (props.hasOwnProperty(k)) {
                v = props[k];
                try {
                    if (typeof v === 'string' && v.charAt(0) === '$') { v = color(v.substr(1)); }
                    else if (typeof v === 'number' && has(PT_KEYS, k)) { v = v + ' pt'; }
                    obj[k] = v;
                } catch (e) {
                    log('WARN', where, 'property ' + k + ' not applied: ' + e.message);
                }
            }
        }
    }

    // ------------------------------------------------------------------ styles
    var FAMILY_OF = {};   // paragraph style name -> family
    function group(kind, name) {
        var coll = kind === 'p' ? doc.paragraphStyleGroups : doc.characterStyleGroups;
        var g = coll.itemByName(name);
        if (!g.isValid) { g = coll.add({ name: name }); }
        return g;
    }
    function mkCS(grp, name, props) {
        return safe('character style ' + name, function () {
            var g = grp ? group('c', grp) : doc;
            var s = g.characterStyles.add({ name: name });
            applyProps(s, props || {}, 'character style ' + name);
            CS[name] = s;
            return s;
        });
    }
    function mkPS(grp, name, props, basedOn) {
        return safe('paragraph style ' + name, function () {
            var g = group('p', grp);
            var s = g.paragraphStyles.add({ name: name });
            var base = {
                appliedFont: plan.fonts.main, fontStyle: 'Regular', pointSize: plan.fonts.size, leading: plan.fonts.leading,
                tracking: 10, hyphenation: false, justification: Justification.LEFT_ALIGN, fillColor: '$Primary',
                spaceBefore: 0, spaceAfter: 0, leftIndent: 0, rightIndent: 0, firstLineIndent: 0
            };
            if (basedOn && PS[basedOn]) { s.basedOn = PS[basedOn]; base = {}; }
            applyProps(s, base, 'paragraph style ' + name);
            applyProps(s, props || {}, 'paragraph style ' + name);
            PS[name] = s;
            FAMILY_OF[name] = grp;
            return s;
        });
    }
    function makeCharStyles() {
        var P = plan.fonts.main;
        mkCS(null, 'Hide_Tags', { pointSize: 0.1, fillColor: doc.swatches.itemByName('None') });
        mkCS('Bahasa', 'en', { fontStyle: 'Regular', fillColor: '$Primary@45' });
        mkCS('Bahasa', 'enb', { fontStyle: 'Bold', fillColor: '$Primary@45' });
        mkCS('Bahasa', 'id', { fontStyle: 'Bold', fillColor: '$Primary' });
        mkCS('Bahasa', 'en.tabel', { fontStyle: 'Regular', pointSize: 7, fillColor: '$Primary@45' });
        mkCS('Bahasa', 'j.tabel.id', { fontStyle: 'Bold', pointSize: 9, fillColor: '$Primary' });
        mkCS('Latar Gelap', 'hid', { fillColor: '$Terang' });
        mkCS('Latar Gelap', 'hen', { fontStyle: 'Regular', fillColor: '$Terang 2' });
        mkCS('Latar Gelap', 'jid', { fontStyle: 'Bold', fillColor: '$Terang' });
        mkCS('Latar Gelap', 'jen', { fontStyle: 'Bold', fillColor: '$Terang 2' });
        mkCS('Latar Gelap', 'qid', { fillColor: '$Terang' });
        mkCS('Latar Gelap', 'qen', { fontStyle: 'Regular', fillColor: '$Terang 2' });
        mkCS('Format', 'b', { fontStyle: 'Bold' });
        mkCS('Format', 'i', { fontStyle: 'Italic' });
        mkCS('Format', 'big', { pointSize: 26 });
        mkCS('Format', 'acc', { fillColor: '$Accent 1' });
        mkCS('Format', 'mut', { fillColor: '$Primary@45' });
        mkCS('Format', 'sup', { position: Position.SUPERSCRIPT });
        mkCS('Format', 'sub', { position: Position.SUBSCRIPT });
        mkCS('Format', 'ref', { fontStyle: 'Bold', fillColor: '$Accent 2', pointSize: 6.5, capitalization: Capitalization.ALL_CAPS });
        mkCS('Format', 'dum', { underline: true, underlineColor: '$Highlight', underlineWeight: 6, underlineOffset: -1 });
        // English language on the EN styles (best effort)
        safe('language en', function () {
            var lang = app.languagesWithVendors.itemByName('English: USA');
            each(['en', 'enb', 'en.tabel', 'hen', 'jen', 'qen'], function (n) {
                if (CS[n]) { try { CS[n].appliedLanguage = lang; } catch (e) { log('WARN', 'language ' + n, e.message); } }
            });
        });
        for (var n in CS) { if (CS.hasOwnProperty(n) && !CS[n]) { log('ERROR', 'style', 'missing character style ' + n); } }
    }
    // tag -> character style per family. One table; no per-style duplication.
    var TAGS = [
        ['e', 'en', { Tabel: 'en.tabel' }], ['en', 'en', { Tabel: 'en.tabel' }], ['enb', 'enb', {}],
        ['id', 'id', { Tabel: 'j.tabel.id' }], ['b', 'b', {}], ['i', 'i', {}], ['big', 'big', {}], ['acc', 'acc', {}],
        ['mut', 'mut', {}], ['sup', 'sup', {}], ['sub', 'sub', {}], ['ref', 'ref', {}], ['dum', 'dum', {}],
        ['hid', 'hid', {}], ['hen', 'hen', {}], ['jid', 'jid', {}], ['jen', 'jen', {}], ['qid', 'qid', {}], ['qen', 'qen', {}]
    ];
    function addTagGreps(style, family) {
        var i, t, csName;
        for (i = 0; i < TAGS.length; i++) {
            t = TAGS[i];
            csName = t[2][family] || t[1];
            if (!CS[csName]) { continue; }
            try {
                style.nestedGrepStyles.add({ grepExpression: '(?<=<' + t[0] + '>).+?(?=</' + t[0] + '>)', appliedCharacterStyle: CS[csName] });
            } catch (e) { log('ERROR', 'grep ' + style.name + ' ' + t[0], e.message); }
        }
        try {
            style.nestedGrepStyles.add({ grepExpression: '</?[a-z]+>', appliedCharacterStyle: CS['Hide_Tags'] });
        } catch (e2) { log('ERROR', 'grep hide ' + style.name, e2.message); }
    }
    function makePStyles() {
        var P = 'Paragraf', T = 'Tabel', O = 'TOC', D = 'Divider', X = 'Tambahan';
        mkPS(P, 'Heading 1', { fontStyle: 'Bold', pointSize: 18, leading: 22, spaceAfter: 4 });
        mkPS(P, 'Heading 2', { fontStyle: 'Bold', pointSize: 11, leading: 14, fillColor: '$Accent 1', spaceAfter: 2 });
        mkPS(P, 'paragraf', { spaceAfter: 3 });
        mkPS(P, 'paragraf.pendek', { leading: 10, spaceAfter: 0 });
        mkPS(P, 'paragraf.tengah', { leading: 10, justification: Justification.CENTER_ALIGN });
        mkPS(P, 'penomoran.l1', { leftIndent: 6, firstLineIndent: -6 });
        mkPS(P, 'penomoran.l2', { leftIndent: 12, firstLineIndent: -6 });
        mkPS(P, 'penomoran.l3', { leftIndent: 18, firstLineIndent: -6 });
        mkPS(P, 'butir.l1', { leftIndent: 5, firstLineIndent: -5 });
        mkPS(P, 'butir.l2', { leftIndent: 10, firstLineIndent: -5 });
        mkPS(T, 'paragraf.tabel', { leading: 11, leftIndent: 2, rightIndent: 2, spaceBefore: 1 });
        mkPS(T, 'paragraf.tabel.angka', { justification: Justification.RIGHT_ALIGN, rightIndent: 4 }, 'paragraf.tabel');
        mkPS(T, 'paragraf.tabel.periode', { pointSize: 12, leading: 14, fontStyle: 'Bold', fillColor: '$Terang', justification: Justification.CENTER_ALIGN }, 'paragraf.tabel');
        mkPS(T, 'paragraf.tabel.indeks', { pointSize: 7.5, leading: 9, spaceBefore: 0.5 }, 'paragraf.tabel');
        mkPS(T, 'judul.tabel', { fontStyle: 'Bold', pointSize: 9, leading: 12, spaceAfter: 2 });
        mkPS(O, 'toc.bab', { fontStyle: 'Bold', pointSize: 9, leading: 11, spaceBefore: 3 });
        mkPS(O, 'toc.sub', { pointSize: 7.5, leading: 8.5, leftIndent: 4 });
        mkPS(D, 'divider.nomor', { fontStyle: 'Light', pointSize: 110, leading: 110, fillColor: '$Terang' });
        mkPS(D, 'divider.judul', { fontStyle: 'Bold', pointSize: 26, leading: 30, fillColor: '$Terang', spaceAfter: 4 });
        mkPS(D, 'divider.sub', { pointSize: 12, leading: 15, fillColor: '$Terang 2' });
        mkPS(X, 'stat.angka', {
            fontStyle: 'Light', pointSize: 26, leading: 28, justification: Justification.CENTER_ALIGN,
            ruleBelow: true, ruleBelowColor: '$Primary', ruleBelowLineWeight: 0.5, ruleBelowOffset: 2, ruleBelowLeftIndent: 8, ruleBelowRightIndent: 8, spaceAfter: 4
        });
        mkPS(X, 'stat.label', { leading: 10, justification: Justification.CENTER_ALIGN });
        mkPS(X, 'caption', { pointSize: 7, leading: 9 });
        mkPS(X, 'sumber', { pointSize: 6.5, leading: 8, fillColor: '$Primary@45', spaceBefore: 2 });
        mkPS(X, 'kutipan', { pointSize: 15, leading: 20, fontStyle: 'Light', fillColor: '$Terang' });
        mkPS(X, 'kutipan.nama', { fontStyle: 'Bold', pointSize: 9, leading: 12, fillColor: '$Terang', spaceBefore: 6 });
        mkPS(X, 'folio', { pointSize: 7, leading: 9, fontStyle: 'Bold' });
        mkPS(X, 'header.running', { pointSize: 6.5, leading: 8, fillColor: '$Primary@45' });
        mkPS(X, 'nav', { pointSize: 6, leading: 8, fillColor: '$Primary@45' });
        mkPS(X, 'nav.aktif', { pointSize: 6, leading: 8, fontStyle: 'Bold', fillColor: '$Primary' }, 'nav');
        mkPS(X, 'cover.judul', { fontStyle: 'Bold', pointSize: 34, leading: 38, fillColor: '$Terang' });
        mkPS(X, 'cover.sub', { pointSize: 14, leading: 18, fillColor: '$Terang 2' });
        // Tab stop for TOC
        safe('toc tabs', function () {
            each(['toc.bab', 'toc.sub'], function (n) {
                var w = (TEXTW - 4) / 2 - (n === 'toc.sub' ? 4 : 0);
                PS[n].tabStops.add({ alignment: TabStopAlignment.RIGHT_ALIGN, position: w, leader: '.' });
            });
        });
        // Numbering list (one named list, three levels)
        safe('numbering', function () {
            doc.numberingLists.add({ name: 'penomoran' });
            each([['penomoran.l1', NumberingStyle.ARABIC, 1], ['penomoran.l2', NumberingStyle.LOWER_LETTERS, 2], ['penomoran.l3', NumberingStyle.LOWER_ROMAN, 3]], function (r) {
                var s = PS[r[0]];
                s.bulletsAndNumberingListType = ListType.NUMBERED_LIST;
                s.numberingFormat = r[1];
                s.numberingLevel = r[2];
                s.appliedNumberingList = doc.numberingLists.itemByName('penomoran');
            });
        });
        for (var n in PS) {
            if (PS.hasOwnProperty(n) && PS[n]) { addTagGreps(PS[n], FAMILY_OF[n]); }
        }
    }
    function makeTableStyles() {
        var CELL = {};
        function mk(name, fill, bottomW, extra) {
            return safe('cell style ' + name, function () {
                var c = doc.cellStyles.add({ name: name });
                var props = {
                    topInset: 1, bottomInset: 1, leftInset: 0, rightInset: 0, verticalJustification: VerticalJustification.CENTER_ALIGN,
                    topEdgeStrokeWeight: 0, leftEdgeStrokeWeight: 0, rightEdgeStrokeWeight: 0,
                    bottomEdgeStrokeWeight: bottomW, bottomEdgeStrokeColor: '$Primary'
                };
                if (fill) { props.fillColor = fill; props.fillTint = 100; } else { props.fillColor = doc.swatches.itemByName('None'); }
                applyProps(c, props, 'cell style ' + name);
                if (extra) { applyProps(c, extra, 'cell style ' + name); }
                CELL[name] = c;
                return c;
            });
        }
        mk('sel.header.teks', null, 1, { bottomEdgeStrokeColor: '$Accent 2' });
        mk('sel.header.periode', null, 1, { bottomEdgeStrokeColor: '$Accent 2' });       // fill drawn by rounded rect (Tabel Dekor)
        mk('sel.header.berjalan', null, 1, { bottomEdgeStrokeColor: '$Accent 2' });
        mk('sel.isi', null, 0.25);
        mk('sel.isi.berjalan', '$Accent 1@15', 0.25);
        mk('sel.akhir', null, 2);
        mk('sel.akhir.berjalan', '$Accent 1@15', 2);
        safe('table style', function () {
            var t = doc.tableStyles.add({ name: 'tabel.dasar' });
            applyProps(t, { topBorderStrokeWeight: 0, leftBorderStrokeWeight: 0, rightBorderStrokeWeight: 0, bottomBorderStrokeWeight: 0 }, 'table style');
            try { t.headerRegionCellStyle = CELL['sel.header.teks']; t.bodyRegionCellStyle = CELL['sel.isi']; } catch (e) { log('WARN', 'table style', e.message); }
        });
        return CELL;
    }
    var CELLS = {};

    // ------------------------------------------------------------------ layers, master
    function makeLayers() {
        var names = ['Latar', 'Teks', 'Tabel Dekor', 'Header'];   // bottom to top is set by order below
        var order = ['Latar', 'Tabel Dekor', 'Teks', 'Header'];
        var base = doc.layers[0];
        base.name = 'Latar';
        L['Latar'] = base;
        each(order, function (n) {
            if (n !== 'Latar') { L[n] = doc.layers.add({ name: n }); }
        });
    }
    function pageArea(page) {
        // Ruler origin is PAGE_ORIGIN, so every coordinate is relative to the page the item sits on.
        // page.bounds returns spread-based numbers for right-hand pages and pushed items off the page: never use it.
        var right = (page.side !== PageSideOptions.LEFT_HAND);
        var x1 = right ? M.inside : M.outside;
        return { x0: 0, y0: 0, x1: x1, x2: x1 + TEXTW, top: M.top, bottom: H - M.bottom, right: right, pw: W };
    }
    function setupMaster() {
        safe('master', function () {
            var ms = doc.masterSpreads[0];
            ms.namePrefix = 'A';
            each([0, 1], function (i) {
                var pg = ms.pages[i];
                var mp = pg.marginPreferences;
                mp.top = M.top; mp.bottom = M.bottom; mp.columnCount = plan.doc.columns; mp.columnGutter = plan.doc.gutter;
                if (i === 0) { mp.left = M.outside; mp.right = M.inside; } else { mp.left = M.inside; mp.right = M.outside; }
                var a = pageArea(pg);
                var f1 = pg.textFrames.add({ itemLayer: L['Header'], geometricBounds: [a.y0 + 8, a.x1, a.y0 + 12, a.x2] });
                f1.contents = plan.meta.short + '  |  ' + plan.meta.year;
                f1.paragraphs[0].appliedParagraphStyle = PS['header.running'];
                f1.paragraphs[0].justification = i === 0 ? Justification.LEFT_ALIGN : Justification.RIGHT_ALIGN;
                var f2 = pg.textFrames.add({ itemLayer: L['Header'], geometricBounds: [a.bottom + 6, a.x1, a.bottom + 11, a.x2] });
                f2.contents = SpecialCharacters.AUTO_PAGE_NUMBER;
                f2.paragraphs[0].appliedParagraphStyle = PS['folio'];
                f2.paragraphs[0].justification = i === 0 ? Justification.LEFT_ALIGN : Justification.RIGHT_ALIGN;
            });
        });
    }

    // ------------------------------------------------------------------ frame helpers
    function tf(page, a, x1, y1, x2, y2, layer) {
        return page.textFrames.add({ itemLayer: layer || L['Teks'], geometricBounds: [y1, x1, y2, x2] });
    }
    function rect(page, x1, y1, x2, y2, fill, layer) {
        var r = page.rectangles.add({ itemLayer: layer || L['Latar'], geometricBounds: [y1, x1, y2, x2] });
        r.strokeWeight = 0;
        try { r.strokeColor = doc.swatches.itemByName('None'); } catch (e) { }
        if (fill) { r.fillColor = color(fill); }
        return r;
    }
    function fillText(frame, text, style, where) {
        frame.contents = text;
        frame.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS[style];
        if (frame.overflows) { log('WARN', where, 'text overflows frame'); }
    }
    function setStyleByParagraphs(frame, styles) {
        var i, n = frame.parentStory.paragraphs.length;
        for (i = 0; i < n; i++) { frame.parentStory.paragraphs[i].appliedParagraphStyle = PS[styles[i] || styles[styles.length - 1]]; }
    }
    function title(page, a, p, y) {
        var f = tf(page, a, a.x1, y, a.x2, y + 24);
        var s = biText(p.title.id, p.title.en);
        f.contents = s;
        f.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS['Heading 1'];
        return y + 26;
    }
    function nav(page, a, chapterNo) {
        var n = plan.chapters.length, w = TEXTW / n, i, f;
        for (i = 0; i < n; i++) {
            f = tf(page, a, a.x1 + i * w, a.y0 + 13, a.x1 + (i + 1) * w - 1, a.y0 + 18, L['Header']);
            f.contents = plan.chapters[i].id;
            f.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS[plan.chapters[i].no === chapterNo ? 'nav.aktif' : 'nav'];
            if (plan.chapters[i].no === chapterNo) {
                var u = rect(page, a.x1 + i * w, a.y0 + 18, a.x1 + (i + 1) * w - 1, a.y0 + 18.6, 'Accent 1', L['Header']);
            }
        }
    }
    function bleedRect(page, fill) {
        var right = (page.side !== PageSideOptions.LEFT_HAND), bl = plan.doc.bleed;
        var r = page.rectangles.add({ itemLayer: L['Latar'], geometricBounds: [-bl, right ? 0 : -bl, H + bl, right ? W + bl : W] });
        r.fillColor = color(fill); r.strokeWeight = 0;
        return r;
    }
    function placeholder(page, x1, y1, x2, y2) { return rect(page, x1, y1, x2, y2, 'Primary@10', L['Latar']); }

    // ------------------------------------------------------------------ tables
    function colWidths(t) {
        var cols = t.cols, n = cols.length, w = [], i, sum = 0, ratio;
        if (t.widths && t.widths.length === n) {
            for (i = 0; i < n; i++) { sum += t.widths[i]; }
            for (i = 0; i < n; i++) { w.push(t.widths[i] * TEXTW / sum); }
            return w;
        }
        var np = 0, nt = 0;
        for (i = 0; i < n; i++) { if (cols[i].kind === 'num') { np++; } else { nt++; } }
        var fixed = 0;
        for (i = 0; i < n; i++) { if (cols[i].kind !== 'num') { w.push(i === 0 ? 59 : 28); fixed += w[i]; } else { w.push(0); } }
        if (np) { for (i = 0; i < n; i++) { if (cols[i].kind === 'num') { w[i] = (TEXTW - fixed) / np; } } }
        else { ratio = TEXTW / fixed; for (i = 0; i < n; i++) { w[i] = w[i] * ratio; } }
        return w;
    }
    function buildTable(page, a, t, y, maxBottom, dummyRows, pageNo) {
        var ncol = t.cols.length, nrow = t.rows.length + 1, i, j, c, row, cell, txt, st, widths = colWidths(t);
        var frame = tf(page, a, a.x1, y, a.x2, maxBottom);
        var tb = frame.insertionPoints[0].tables.add({ headerRowCount: 1, bodyRowCount: nrow - 1, columnCount: ncol });
        try { tb.appliedTableStyle = doc.tableStyles.itemByName('tabel.dasar'); } catch (e0) { log('WARN', 'table', e0.message); }
        for (j = 0; j < ncol; j++) { safe('col width', function () { tb.columns[j].width = widths[j]; }); }
        var first = t.berjalan ? ncol - 1 : -1;
        var perStart = -1;
        for (j = 0; j < ncol; j++) { if (t.cols[j].kind === 'num' && perStart < 0) { perStart = j; } }
        // header
        for (j = 0; j < ncol; j++) {
            (function (jj) {
                safe('table p' + pageNo + ' header ' + jj, function () {
                    var col = t.cols[jj], cl = tb.rows[0].cells[jj];
                    if (col.kind === 'num') {
                        cl.contents = col.label;
                        cl.paragraphs.everyItem().appliedParagraphStyle = PS['paragraf.tabel.periode'];
                        cl.appliedCellStyle = CELLS[(t.berjalan && jj === ncol - 1) ? 'sel.header.berjalan' : 'sel.header.periode'];
                    } else {
                        cl.contents = '<id>' + col.id + '</id>' + BR + '<e>' + col.en + '</e>';
                        cl.paragraphs.everyItem().appliedParagraphStyle = PS['paragraf.tabel'];
                        cl.appliedCellStyle = CELLS['sel.header.teks'];
                    }
                });
            })(j);
        }
        try { tb.rows[0].autoGrow = false; tb.rows[0].height = 16.2; } catch (e1) { log('WARN', 'table p' + pageNo, 'header height: ' + e1.message); }
        // body
        for (i = 0; i < t.rows.length; i++) {
            var last = (i === t.rows.length - 1);
            var isDum = false, d;
            for (d = 0; d < dummyRows.length; d++) { if (dummyRows[d] === i) { isDum = true; } }
            for (j = 0; j < ncol; j++) {
                (function (ii, jj) {
                    safe('table p' + pageNo + ' r' + ii + 'c' + jj, function () {
                        var v = t.rows[ii][jj], cl = tb.rows[ii + 1].cells[jj], isRun = (t.berjalan && jj === ncol - 1);
                        var baseStyle = PS[t.index ? 'paragraf.tabel.indeks' : 'paragraf.tabel'];
                        if (t.cols[jj].kind === 'text' && typeof v !== 'string') {
                            txt = dum(t.cols[jj].inline ? (v[0] + ' <e>' + v[1] + '</e>') : biText(v[0], v[1]), isDum);
                            cl.contents = txt;
                            cl.paragraphs.everyItem().appliedParagraphStyle = baseStyle;
                        } else {
                            txt = String(v);
                            cl.contents = dum(txt, isDum);
                            cl.paragraphs.everyItem().appliedParagraphStyle = NUMRX.test(txt) && t.cols[jj].kind === 'num' ? PS['paragraf.tabel.angka'] : baseStyle;
                        }
                        cl.appliedCellStyle = CELLS[(last ? 'sel.akhir' : 'sel.isi') + (isRun ? '.berjalan' : '')];
                    });
                })(i, j);
            }
            safe('row height', function () { tb.rows[i + 1].minimumHeight = (t.minRow || 11.8); });
        }
        if (frame.overflows) { log('WARN', 'table p' + pageNo, 'table overflows its frame'); }
        // header decor: rounded rectangles behind period columns
        if (perStart >= 0) {
            var x = a.x1;
            for (j = 0; j < ncol; j++) {
                if (t.cols[j].kind === 'num') {
                    (function (jj, xx) {
                        var ok = safe('table decor p' + pageNo, function () {
                            var r = rect(page, xx, y, xx + widths[jj], y + 16.2, (t.berjalan && jj === ncol - 1) ? 'Accent 1' : 'Primary', L['Tabel Dekor']);
                            r.topLeftCornerOption = CornerOptions.ROUNDED_CORNER; r.topRightCornerOption = CornerOptions.ROUNDED_CORNER;
                            r.topLeftCornerRadius = 2.5; r.topRightCornerRadius = 2.5;
                            r.bottomLeftCornerOption = CornerOptions.NONE; r.bottomRightCornerOption = CornerOptions.NONE;
                            return r;
                        });
                        if (!ok) { log('WARN', 'table decor p' + pageNo, 'header stays square'); }
                    })(j, x);
                }
                x += widths[j];
            }
        }
        return frame;
    }

    // ------------------------------------------------------------------ page templates
    function cover(page, d, back) {
        page.appliedMaster = NothingEnum.NOTHING;
        var b = [0, 0, H, W];
        bleedRect(page, 'Primary');
        var a = pageArea(page);
        var f = tf(page, a, b[1] + 22, b[0] + 90, b[3] - 22, b[0] + 190);
        f.contents = '<jid>' + d.title.id + '</jid>' + BR + '<jen>' + d.title.en + '</jen>';
        f.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS['cover.judul'];
        if (d.subtitle) {
            var g = tf(page, a, b[1] + 22, b[0] + 195, b[3] - 22, b[0] + 225);
            g.contents = '<hid>' + d.subtitle.id + '</hid>' + BR + '<hen>' + d.subtitle.en + '</hen>';
            g.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS['cover.sub'];
        }
        var s = rect(page, b[1] + 22, b[0] + 80, b[1] + 62, b[0] + 81.5, 'Accent 1', L['Latar']);
    }
    function divider(page, d) {
        var b = [0, 0, H, W], a = pageArea(page);
        bleedRect(page, 'Primary');
        var no = String(d.chapter); if (no.length < 2) { no = '0' + no; }
        var f1 = tf(page, a, a.x1, a.top + 20, a.x2, a.top + 90);
        f1.contents = no; f1.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS['divider.nomor'];
        var f2 = tf(page, a, a.x1, a.top + 100, a.x2, a.top + 150);
        f2.contents = '<jid>' + d.title.id + '</jid>' + BR + '<jen>' + d.title.en + '</jen>';
        f2.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS['divider.judul'];
        if (d.subtitle) {
            var f3 = tf(page, a, a.x1, a.top + 155, a.x2, a.top + 185);
            f3.contents = '<hid>' + d.subtitle.id + '</hid>' + BR + '<hen>' + d.subtitle.en + '</hen>';
            f3.parentStory.paragraphs.everyItem().appliedParagraphStyle = PS['divider.sub'];
        }
        rect(page, a.x1, a.top + 94, a.x1 + 40, a.top + 95.5, 'Accent 1', L['Latar']);
    }
    function bodyParas(d) {
        var out = [], i, ids = d.text.id, ens = d.text.en, n = Math.max(ids.length, ens.length);
        for (i = 0; i < n; i++) {
            out.push(dum(biText(ids[i] || ens[i], ens[i] || ids[i]), d.dummy));
        }
        return out;
    }
    function textPage(page, d, a) {
        var y = title(page, a, d, a.top);
        placeholder(page, a.x1, y, a.x2, y + 45);
        y += 50;
        var f = tf(page, a, a.x1, y, a.x2, a.bottom);
        f.textFramePreferences.textColumnCount = 2;
        f.textFramePreferences.textColumnGutter = plan.doc.gutter;
        fillText(f, paraJoin(bodyParas(d)), 'paragraf', 'p' + d.n + ' text');
        if (d.source) { log('INFO', 'p' + d.n, 'source: ' + d.source); }
    }
    function cardPage(page, d, a) {
        var y = title(page, a, d, a.top), n = d.cards.length, cols = 3, gut = plan.doc.gutter, i;
        var cw = (TEXTW - gut * (cols - 1)) / cols, ch = 36;
        for (i = 0; i < n; i++) {
            (function (k) {
                var cx = a.x1 + (k % cols) * (cw + gut), cy = y + Math.floor(k / cols) * (ch + gut);
                rect(page, cx, cy, cx + cw, cy + ch, 'Primary@8', L['Latar']);
                var f = tf(page, a, cx + 2, cy + 3, cx + cw - 2, cy + ch - 2);
                f.contents = dum(d.cards[k].n, d.dummy) + '\r' + biText(d.cards[k].id, d.cards[k].en);
                f.parentStory.paragraphs[0].appliedParagraphStyle = PS['stat.angka'];
                f.parentStory.paragraphs[1].appliedParagraphStyle = PS['stat.label'];
                if (f.overflows) { log('WARN', 'p' + d.n, 'card ' + k + ' overflows'); }
            })(i);
        }
        y += Math.ceil(n / cols) * (ch + gut) + 2;
        if (d.text) {
            var f2 = tf(page, a, a.x1, y, a.x2, Math.min(a.bottom, y + 90));
            f2.textFramePreferences.textColumnCount = 2; f2.textFramePreferences.textColumnGutter = gut;
            fillText(f2, paraJoin(bodyParas(d)), 'paragraf', 'p' + d.n + ' text');
            y += 95;
        }
        if (a.bottom - y > 40) { placeholder(page, a.x1, y, a.x2, a.bottom); }
    }
    function quotePage(page, d, a) {
        var b = [0, 0, H, W];
        var y = a.top + 40;
        rect(page, a.x1, y, a.x2, y + 140, 'Primary', L['Latar']);
        var f = tf(page, a, a.x1 + 10, y + 12, a.x2 - 10, y + 128);
        var q = d.quote;
        f.contents = dum('<qid>' + q.id + '</qid>' + BR + '<qen>' + q.en + '</qen>', d.dummy) + '\r' + q.name + BR + '<hen>' + q.role + '</hen>';
        f.parentStory.paragraphs[0].appliedParagraphStyle = PS['kutipan'];
        f.parentStory.paragraphs[1].appliedParagraphStyle = PS['kutipan.nama'];
        if (f.overflows) { log('WARN', 'p' + d.n, 'quote overflows'); }
        placeholder(page, a.x1, y + 150, a.x2, a.bottom);
    }
    function tablePage(page, d, a) {
        var y = title(page, a, d, a.top);
        if (d.text) {
            var ft = tf(page, a, a.x1, y, a.x2, y + 30);
            ft.textFramePreferences.textColumnCount = 2; ft.textFramePreferences.textColumnGutter = plan.doc.gutter;
            fillText(ft, paraJoin(bodyParas(d)), 'paragraf.pendek', 'p' + d.n + ' intro');
            y += 32;
        }
        var fr = buildTable(page, a, d.table, y, a.bottom - 6, d.table.dummyRows || [], d.n);
        if (d.source) {
            var fs = tf(page, a, a.x1, a.bottom - 5, a.x2, a.bottom);
            fillText(fs, d.source, 'sumber', 'p' + d.n + ' source');
        }
    }
    function tocPage(page, d, a) {
        var y = title(page, a, d, a.top), parts = [], styles = [], i, e, gut = plan.doc.gutter;
        for (i = 0; i < d.toc.length; i++) {
            e = d.toc[i];
            parts.push(e.id + TAB + e.page + BR + '<e>' + e.en + '</e>');
            styles.push(e.level === 1 ? 'toc.bab' : 'toc.sub');
        }
        var f = tf(page, a, a.x1, y, a.x2, a.bottom);
        f.textFramePreferences.textColumnCount = 2; f.textFramePreferences.textColumnGutter = gut;
        f.contents = paraJoin(parts);
        setStyleByParagraphs(f, styles);
        if (f.overflows) { log('ERROR', 'p' + d.n, 'TOC overflows; add a daftar-isi page'); }
    }

    // ------------------------------------------------------------------ run
    function run() {
        var prior = alreadyBuilt();
        if (prior && !$.global.ARSR_FORCE) {
            log('WARN', 'build', 'document ' + prior + ' is already built in this InDesign session; nothing done. Close it, or set $.global.ARSR_FORCE = true, to build again.');
            return;
        }
        var planFile = findPlan();
        if (!planFile || !planFile.exists) { log('ERROR', 'plan', 'no build_plan.json (run: python engine/run.py plan <project>)'); return; }
        plan = eval('(' + readText(planFile) + ')');
        log('INFO', 'plan', planFile.fsName + ' schema ' + plan.schema + ' pages ' + plan.doc.pageCount);
        if (plan.schema !== 1) { log('ERROR', 'plan', 'unsupported plan schema ' + plan.schema); return; }
        var oldUnits = app.scriptPreferences.measurementUnit, oldLevel = app.scriptPreferences.userInteractionLevel;
        app.scriptPreferences.measurementUnit = MeasurementUnits.MILLIMETERS;
        app.scriptPreferences.userInteractionLevel = UserInteractionLevels.NEVER_INTERACT;
        try {
            M = plan.doc.margins; W = plan.doc.width; H = plan.doc.height; TEXTW = W - M.inside - M.outside;
            doc = app.documents.add();
            doc.insertLabel('ARSR_BUILD', 'yes');
            BR = probeBreak(doc);
            var dp = doc.documentPreferences;
            dp.pageWidth = W; dp.pageHeight = H; dp.facingPages = plan.doc.facing; dp.pagesPerDocument = plan.doc.pageCount;
            dp.documentBleedUniformSize = true; dp.documentBleedTopOffset = plan.doc.bleed;
            doc.viewPreferences.horizontalMeasurementUnits = MeasurementUnits.MILLIMETERS;
            doc.viewPreferences.verticalMeasurementUnits = MeasurementUnits.MILLIMETERS;
            doc.viewPreferences.textSizeMeasurementUnits = MeasurementUnits.POINTS;
            doc.viewPreferences.rulerOrigin = RulerOrigin.PAGE_ORIGIN;
            makeLayers();
            makeSwatches();
            makeCharStyles();
            makePStyles();
            CELLS = makeTableStyles();
            setupMaster();
            var total = plan.pages.length, i;
            for (i = 0; i < total; i++) {
                (function (d) {
                    safe('page ' + d.n, function () {
                        var page = doc.pages[d.n - 1];
                        var a = pageArea(page);
                        if (d.tipe === 'sampul') { cover(page, d); return; }
                        if (d.tipe === 'divider') { divider(page, d); } else {
                            nav(page, a, d.chapter);
                            if (d.tipe === 'teks') { textPage(page, d, a); }
                            else if (d.tipe === 'kartu') { cardPage(page, d, a); }
                            else if (d.tipe === 'kutipan') { quotePage(page, d, a); }
                            else if (d.tipe === 'daftar-isi') { tocPage(page, d, a); }
                            else if (d.table) { tablePage(page, d, a); }
                            else { log('ERROR', 'page ' + d.n, 'unknown page type ' + d.tipe); }
                        }
                    });
                })(plan.pages[i]);
            }
            // dummy register next to the plan
            safe('dummy register', function () {
                var f = new File(Folder.desktop.fsName + '/Dummy_Register.txt'), k;
                f.encoding = 'UTF-8';
                if (f.open('w')) {
                    for (k = 0; k < plan.dummyRegister.length; k++) { f.write(plan.dummyRegister[k].page + '\t' + plan.dummyRegister[k].what + '\n'); }
                    f.close();
                }
            });
            log('INFO', 'done', 'pages built ' + total);
            safe('save', function () {
                var f = new File(planFile.parent.fsName + '/report.indd');
                doc.save(f);
                log('INFO', 'saved', f.fsName);
            });
        } finally {
            app.scriptPreferences.measurementUnit = oldUnits;
            app.scriptPreferences.userInteractionLevel = oldLevel;
        }
    }

    try { run(); } catch (e) { log('ERROR', 'fatal', String(e.message || e) + ' (line ' + e.line + ')'); }
    writeLog();
    writeDone();
})();
