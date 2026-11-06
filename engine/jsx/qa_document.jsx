#target indesign
/*
 * qa_document.jsx - ARSR read-only QA of the ACTIVE InDesign document (ExtendScript ES3, ASCII only).
 * Changes nothing in the document. Writes only ARSR_QA_Log.txt (in the project logs folder; Desktop if unknown).
 * Checks (ids match references/validation-rules.md):
 *  DOC-01 visible tag <..>      DOC-02 empty text frame      DOC-03 overflow (frame or table)
 *  DOC-04 forbidden text        DOC-05 page count = plan     DOC-06 header cell without tag
 *  DOC-07 TOC / index page numbers match plan registry       DOC-08 missing swatch / style
 * STATUS: untested in real InDesign. Run, read the log, fix.
 */
(function () {
    var LOG = [], NERR = 0, NWARN = 0;
    function log(level, rule, where, msg) {
        if (level === 'ERROR') { NERR++; } else if (level === 'WARN') { NWARN++; }
        LOG.push(level + ' | ' + rule + ' | ' + where + ' | ' + msg);
    }
    function safe(where, fn) { try { return fn(); } catch (e) { log('ERROR', 'QA-00', where, String(e.message || e) + ' (line ' + e.line + ')'); return null; } }
    function readText(f) { f.encoding = 'UTF-8'; if (!f.open('r')) { throw new Error('cannot open ' + f.fsName); } var t = f.read(); f.close(); return t; }
    function findPlan() {
        if ($.global.ARSR_PLAN_PATH) { return new File($.global.ARSR_PLAN_PATH); }
        var ptr = new File(Folder.userData.fsName + '/ARSR/last_plan.txt');
        if (ptr.exists) { var f = new File(readText(ptr).replace(/[\r\n]+$/, '')); if (f.exists) { return f; } }
        return null;
    }
    function pageOfFrame(fr) { try { return fr.parentPage ? fr.parentPage.name : '?'; } catch (e) { return '?'; } }
    var FORBIDDEN = [/\[isi\]/i, /\[contoh\]/i, /\bTBD\b/, /lorem ipsum/i, /dolor sit amet/i];

    function run() {
        if (app.documents.length === 0) { log('ERROR', 'QA-00', 'doc', 'no open document'); return; }
        var doc = app.activeDocument, plan = null, pf = findPlan(), i, j, k;
        if (pf && pf.exists) { plan = eval('(' + readText(pf) + ')'); } else { log('WARN', 'QA-00', 'plan', 'no build_plan.json; DOC-05 and DOC-07 skipped'); }

        // DOC-08 required swatches and styles
        var needS = ['Primary', 'Secondary', 'Accent 1', 'Accent 2', 'Neutral Dark', 'Neutral Light', 'Background', 'Highlight', 'Terang', 'Terang 2'];
        for (i = 0; i < needS.length; i++) { if (!doc.swatches.itemByName(needS[i]).isValid) { log('ERROR', 'DOC-08', 'swatch', 'missing ' + needS[i]); } }
        var needP = ['Heading 1', 'Heading 2', 'paragraf', 'paragraf.tabel', 'paragraf.tabel.angka', 'paragraf.tabel.periode', 'stat.angka', 'toc.bab'];
        for (i = 0; i < needP.length; i++) {
            var found = false;
            for (j = 0; j < doc.allParagraphStyles.length; j++) { if (doc.allParagraphStyles[j].name === needP[i]) { found = true; } }
            if (!found) { log('ERROR', 'DOC-08', 'paragraph style', 'missing ' + needP[i]); }
        }

        // DOC-05 page count
        if (plan && doc.pages.length !== plan.doc.pageCount) {
            log('ERROR', 'DOC-05', 'document', 'pages in document ' + doc.pages.length + ' but plan has ' + plan.doc.pageCount);
        }

        // DOC-01 visible tags: tag text must carry Hide_Tags (0.1 pt)
        safe('DOC-01', function () {
            app.findGrepPreferences = NothingEnum.NOTHING;
            app.findGrepPreferences.findWhat = '</?[a-z]+>';
            var hits = doc.findGrep(), n = 0;
            for (k = 0; k < hits.length; k++) {
                var h = hits[k];
                if (h.pointSize > 0.2) {
                    n++;
                    if (n <= 30) { log('ERROR', 'DOC-01', 'page ' + (h.parentTextFrames && h.parentTextFrames.length ? pageOfFrame(h.parentTextFrames[0]) : '?'), 'visible tag ' + h.contents); }
                }
            }
            if (n > 30) { log('ERROR', 'DOC-01', 'document', (n - 30) + ' more visible tags not listed'); }
            app.findGrepPreferences = NothingEnum.NOTHING;
        });

        // DOC-02 / DOC-03 / DOC-04 per text frame
        var frames = doc.textFrames.everyItem().getElements();
        for (i = 0; i < frames.length; i++) {
            (function (f) {
                safe('frame ' + i, function () {
                    var pg = pageOfFrame(f), c = f.contents;
                    if (typeof c === 'string') {
                        if (c.replace(/\s+/g, '') === '' && f.tables.length === 0) { log('ERROR', 'DOC-02', 'page ' + pg, 'empty text frame'); }
                        for (var r = 0; r < FORBIDDEN.length; r++) { if (FORBIDDEN[r].test(c)) { log('ERROR', 'DOC-04', 'page ' + pg, 'forbidden text ' + FORBIDDEN[r]); } }
                    }
                    if (f.overflows) { log('ERROR', 'DOC-03', 'page ' + pg, 'text frame overflows'); }
                });
            })(frames[i]);
        }

        // DOC-06 header cells carry a tag or a period label
        var tables = doc.stories.everyItem().tables.everyItem().getElements();
        for (i = 0; i < tables.length; i++) {
            (function (t) {
                safe('table ' + i, function () {
                    var hdr = t.rows[0].cells, c, txt;
                    for (var m = 0; m < hdr.length; m++) {
                        c = hdr[m]; txt = c.contents;
                        if (txt === '' || /^\s*$/.test(txt)) { log('ERROR', 'DOC-06', 'table ' + i, 'empty header cell ' + m); continue; }
                        if (!/<id>/.test(txt) && !/^[0-9]{4}([\/\-][0-9]{2,4})?$/.test(txt) && c.paragraphs[0].appliedParagraphStyle.name !== 'paragraf.tabel.periode') {
                            log('ERROR', 'DOC-06', 'table ' + i, 'header cell ' + m + ' has no <id> tag');
                        }
                    }
                });
            })(tables[i]);
        }

        // DOC-07 TOC and indexes: every plan registry page number appears in the document text
        if (plan) {
            safe('DOC-07', function () {
                var tocPages = {}, d;
                for (i = 0; i < plan.pages.length; i++) {
                    d = plan.pages[i];
                    if (d.tipe !== 'daftar-isi') { continue; }
                    var pgObj = doc.pages[d.n - 1], text = '';
                    for (j = 0; j < pgObj.textFrames.length; j++) { text += '\n' + pgObj.textFrames[j].contents; }
                    for (k = 0; k < d.toc.length; k++) {
                        if (text.indexOf(d.toc[k].id + '\t' + d.toc[k].page) < 0) { log('ERROR', 'DOC-07', 'page ' + d.n, 'TOC entry missing or wrong page: ' + d.toc[k].id + ' -> ' + d.toc[k].page); }
                    }
                }
                for (k = 0; k < plan.registry.toc.length; k++) {
                    if (plan.registry.toc[k].page < 1 || plan.registry.toc[k].page > doc.pages.length) { log('ERROR', 'DOC-07', 'registry', 'page out of range ' + plan.registry.toc[k].page); }
                }
            });
        }
    }

    var oldFind = null;
    try { run(); } catch (e) { log('ERROR', 'QA-00', 'fatal', String(e.message || e) + ' (line ' + e.line + ')'); }
    var logDir = Folder.desktop.fsName;
    try {
        var lb = app.activeDocument.extractLabel('ARSR_LOGDIR');
        if (lb) { var lf = new Folder(lb); if (!lf.exists) { lf.create(); } if (lf.exists) { logDir = lf.fsName; } }
    } catch (eL) { }
    var f = new File(logDir + '/ARSR_QA_Log.txt');
    f.encoding = 'UTF-8';
    if (f.open('w')) { f.write('ERROR ' + NERR + ' | WARN ' + NWARN + ' | qa_document.jsx\n' + LOG.join('\n') + '\n'); f.close(); }
})();
