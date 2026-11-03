(function (root) {
  function ewma(a, span) { var al = 2 / (span + 1), o = [a[0]]; for (var i = 1; i < a.length; i++) o.push(al * a[i] + (1 - al) * o[i - 1]); return o; }
  function residuals(v) { var m = ewma(v, 10), r = [0]; for (var i = 1; i < v.length; i++) r.push(Math.abs(v[i] - m[i - 1])); return r; }
  function seqs(mask) { var o = [], s = -1; for (var i = 0; i < mask.length; i++) { if (mask[i] && s < 0) s = i; else if (!mask[i] && s >= 0) { o.push([s, i - 1]); s = -1; } } if (s >= 0) o.push([s, mask.length - 1]); return o; }
  function mean(a) { return a.reduce(function (x, y) { return x + y; }, 0) / (a.length || 1); }
  function std(a) { var m = mean(a); return Math.sqrt(mean(a.map(function (x) { return (x - m) * (x - m); }))); }
  function pick(es, zmin, zmax) {
    var mu = mean(es), sd = std(es), bt = mu + zmin * sd, best = -Infinity; if (!sd || !mu) return bt;
    for (var z = zmin; z <= zmax + 1e-9; z += 0.5) {
      var t = mu + z * sd, below = es.filter(function (x) { return x <= t; }), ab = es.map(function (x) { return x > t; }), n = ab.filter(Boolean).length;
      if (below.length < 2 || !n) continue;
      var sc = ((mu - mean(below)) / mu + (sd - std(below)) / sd) / (n + Math.pow(seqs(ab).length, 2));
      if (sc > best) { best = sc; bt = t; }
    } return bt;
  }
  function prune(es, sq, p) {
    if (!sq.length) return []; var inS = es.map(function () { return false; });
    sq.forEach(function (s) { for (var i = s[0]; i <= s[1]; i++) inS[i] = true; });
    var rest = es.filter(function (_, i) { return !inS[i]; }), floor = rest.length ? Math.max.apply(null, rest) : 0;
    var rk = sq.map(function (s) { return [Math.max.apply(null, es.slice(s[0], s[1] + 1)), s]; }).sort(function (a, b) { return b[0] - a[0]; });
    var vals = rk.map(function (r) { return r[0]; }).concat([floor]), cut = -1;
    for (var i = 0; i < vals.length - 1; i++) if (vals[i] > 0 && (vals[i] - vals[i + 1]) / vals[i] >= p) cut = i;
    return rk.slice(0, cut + 1).map(function (r) { return r[1]; }).sort(function (a, b) { return a[0] - b[0]; });
  }
  function detect(values, o) {
    o = o || {}; var r = residuals(values), es = ewma(r, o.span || 30), t = pick(es, o.zmin || 2.5, o.zmax || 10);
    return { residual: r, smoothed: es, threshold: t, events: prune(es, seqs(es.map(function (x) { return x > t; })), o.p || 0.13) };
  }
  var api = { ewma: ewma, residuals: residuals, detect: detect };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.TH = api;
})(this);
