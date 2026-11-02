// Mock of the InDesign DOM to flow-test build_report.jsx in Node. It proves the script's own logic
// (variables, plan handling, tag balance, call counts). It does NOT prove InDesign API names - only real InDesign does.
// usage: node tests/mock_indesign.js <script.jsx> <plan.json> <out_dir>
var fs = require('fs'), vm = require('vm'), path = require('path');
var script = process.argv[2], planPath = process.argv[3], outDir = process.argv[4];
var stats = { adds: {}, contents: [], pageItems: {} };
var enumNames = {};
(fs.readFileSync(script, 'utf8').match(/\b[A-Z][A-Za-z]+(?=\.[A-Z][A-Z_0-9]+)/g) || []).forEach(function (n) { enumNames[n] = 1; });

function node(p, extra) {
  var store = extra || {};
  var f = function () { return node(p + '()'); };
  return new Proxy(f, {
    get: function (t, k) {
      if (typeof k === 'symbol') { return undefined; }
      if (k in store) { return store[k]; }
      if (k === 'length') { return 3; }
      if (k === 'isValid') { return true; }
      if (k === 'overflows') { return false; }
      if (k === 'name') { return p; }
      if (k === 'bounds') { return [0, 0, 297, 210]; }
      if (k === 'side') { return 'RIGHT_HAND'; }
      if (k === 'toString' || k === 'valueOf') { return function () { return p; }; }
      if (/^\d+$/.test(k)) { return node(p + '[' + k + ']'); }
      if (k === 'add') {
        return function (props) {
          stats.adds[p] = (stats.adds[p] || 0) + 1;
          if (props && props.contents !== undefined) { stats.contents.push(String(props.contents)); }
          return node(p + '.add');
        };
      }
      var n = node(p + '.' + k);
      store[k] = n;
      return n;
    },
    set: function (t, k, v) {
      if (k === 'contents' && typeof v === 'string') { stats.contents.push(v); }
      store[k] = v;
      return true;
    },
    apply: function () { return node(p + '()'); }
  });
}
function MockFile(p) {
  this.fsName = p; this.exists = fs.existsSync(p); this.encoding = '';
  this._mode = null; this._buf = [];
}
MockFile.prototype.open = function (m) { this._mode = m; return m === 'w' ? true : this.exists; };
MockFile.prototype.read = function () { return fs.readFileSync(this.fsName, 'utf8'); };
MockFile.prototype.write = function (s) { this._buf.push(s); };
MockFile.prototype.close = function () { if (this._mode === 'w') { fs.writeFileSync(this.fsName, this._buf.join('')); } };
MockFile.openDialog = function () { return new MockFile(planPath); };
var sb = {
  File: MockFile, Folder: { desktop: { fsName: outDir }, userData: { fsName: path.join(outDir, 'appdata') } },
  $: { global: {} }, alert: function () { }, String: String, Math: Math, Number: Number, eval: eval,
  SpecialCharacters: { AUTO_PAGE_NUMBER: '#PN#' }
};
sb.$.global.ARSR_PLAN_PATH = planPath;
Object.keys(enumNames).forEach(function (n) {
  if (!sb[n]) { sb[n] = new Proxy({}, { get: function (t, k) { return typeof k === 'string' ? n + '.' + k : undefined; } }); }
});
sb.app = node('app');
var doc = node('doc');
sb.app.documents = { add: function () { return doc; } };
fs.mkdirSync(outDir, { recursive: true });
vm.createContext(sb);
vm.runInContext(fs.readFileSync(script, 'utf8').replace(/^#target.*$/m, ''), sb, { filename: script });
// tag balance in every composed string, per paragraph
var bad = [];
stats.contents.forEach(function (s) {
  s.split(/\r/).forEach(function (para) {
    var st = [], m, rx = /<(\/?)([a-z]+)>/g;
    while ((m = rx.exec(para))) {
      if (!m[1]) { st.push(m[2]); } else if (st.pop() !== m[2]) { bad.push(para.slice(0, 80)); st = []; break; }
    }
    if (st.length) { bad.push(para.slice(0, 80)); }
  });
});
fs.writeFileSync(path.join(outDir, 'mock_stats.json'), JSON.stringify({ adds: stats.adds, strings: stats.contents.length, unbalanced: bad }));
