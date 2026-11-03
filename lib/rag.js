(function (root) {
  var KB = [
    ['SMAP-P1', 'Gradual thermal sensor drift: slow monotonic offset, no command correlation. Recalibrate, cross-check redundant sensor.'],
    ['MSL-M6', 'Power rail transient: abrupt voltage dip on bus after payload command. Isolate load, check battery state of charge.'],
    ['SMAP-A4', 'Gyro noise burst: high variance spikes, attitude jitter. Reaction wheel desaturation and filter reset.'],
    ['MSL-T2', 'Radio link dropout: telemetry gaps and stale values. Switch antenna, retry downlink window.'],
    ['MSL-P3', 'Solar array current drop: gradual decline in charge current, temperature correlated. Verify sun angle, review array degradation trend.'],
    ['SMAP-R2', 'Reaction wheel friction rise: motor current creeping up with stable speed. Schedule lubrication check, reduce wheel duty.'],
    ['MSL-C5', 'Memory bit-flip burst: EDAC counters jump, sporadic bad values. Scrub memory, reboot subsystem, log radiation event.']
  ].map(function (d) { return { id: d[0], text: d[1] }; });
  function vec(t) { var m = {}; (String(t).toLowerCase().match(/[a-z0-9]+/g) || []).forEach(function (w) { m[w] = (m[w] || 0) + 1; }); return m; }
  function cos(a, b) { var d = 0, x = 0, y = 0, k; for (k in a) { x += a[k] * a[k]; if (b[k]) d += a[k] * b[k]; } for (k in b) y += b[k] * b[k]; return d / (Math.sqrt(x * y) || 1); }
  function retrieve(q, k) {
    var v = vec(q);
    return KB.map(function (d) { return { id: d.id, text: d.text, score: cos(v, vec(d.id + ' ' + d.text)) }; })
      .sort(function (a, b) { return b.score - a.score; }).slice(0, k || 2);
  }
  var api = { KB: KB, retrieve: retrieve };
  if (typeof module !== 'undefined' && module.exports) module.exports = api; else root.RAG = api;
})(this);
