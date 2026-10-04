// A map in thin lines with a lens that shows what topojson does: inside the lens the
// map is simplified and on a grid. Each vertex has a Douglas-Peucker weight
// (generate/make-docs-lens.py); in the lens a vertex is drawn where its weight is
// above the tolerance, and moved to the nearest point of a grid of whole degrees. Neighbours share
// their arcs, so the borders stay matched, inside the lens and across its edge.
//
// <figure class="lens" data-src="lens.json" data-intensity="0.6"><canvas></canvas></figure>
(function () {
  const still = matchMedia("(prefers-reduced-motion: reduce)");

  function mount(figure) {
    const canvas = figure.querySelector("canvas");
    const ctx = canvas.getContext("2d");
    const intensity = Math.min(1, Math.max(0, +figure.dataset.intensity || 0.6));
    let arcs = [], view = null, frame = 0;
    let lens = null, target = null, rest = null;

    fetch(figure.dataset.src).then(r => r.json()).then(data => {
      const [kx, ky] = data.transform.scale, [x0, y0] = data.transform.translate;
      arcs = data.arcs.map((flat, i) => {
        const w = data.weights[i].map(v => (v < 0 ? Infinity : v / 1000));
        const xs = [], ys = [];
        for (let j = 0, x = 0, y = 0; j < flat.length; j += 2) {
          x += flat[j]; y += flat[j + 1];
          xs.push(x0 + x * kx); ys.push(y0 + y * ky);
        }
        // a closed arc (an island) keeps at least a triangle
        const closed = xs.length > 3 && xs[0] === xs[xs.length - 1] && ys[0] === ys[ys.length - 1];
        if (closed) {
          const inner = w.slice(1, -1).map((v, k) => [v, k + 1]).sort((a, b) => b[0] - a[0]);
          inner.slice(0, 2).forEach(([, k]) => (w[k] = Infinity));
        }
        return { xs, ys, w, closed };
      });
      resize();
      new ResizeObserver(resize).observe(canvas);
    });

    function resize() {
      const rect = canvas.getBoundingClientRect(), dpr = devicePixelRatio || 1;
      if (!arcs.length || !rect.width) return;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (const a of arcs) for (let i = 0; i < a.xs.length; i++) {
        x0 = Math.min(x0, a.xs[i]); x1 = Math.max(x1, a.xs[i]);
        y0 = Math.min(y0, a.ys[i]); y1 = Math.max(y1, a.ys[i]);
      }
      const pad = 12, s = Math.min((rect.width - 2 * pad) / (x1 - x0), (rect.height - 2 * pad) / (y1 - y0));
      view = {
        s, w: rect.width, h: rect.height,
        ox: (rect.width - s * (x1 + x0)) / 2, oy: (rect.height + s * (y1 + y0)) / 2,
      };
      // at rest, the lens lies on the Great Lakes
      const r = 0.17 * rect.width;
      rest = { x: view.ox + s * 31, y: view.oy - s * -1, r };
      lens = target = { ...rest };
      draw();
    }

    function draw() {
      const css = getComputedStyle(figure);
      const tolerance = 0.05 + 1.6 * intensity;  // inside the lens, in degrees
      const cell = 1;                             // of the grid in the lens, in degrees
      const { x, y, r } = lens, { s, ox, oy } = view;
      ctx.clearRect(0, 0, view.w, view.h);

      // the lens: a fine grid, the grid the vertices in it snap to
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.clip();
      ctx.beginPath();
      for (let lon = Math.ceil((x - r - ox) / s / cell) * cell; ox + s * lon < x + r; lon += cell) {
        ctx.moveTo(ox + s * lon, y - r); ctx.lineTo(ox + s * lon, y + r);
      }
      for (let lat = Math.ceil((oy - y - r) / s / cell) * cell; oy - s * lat > y - r; lat += cell) {
        ctx.moveTo(x - r, oy - s * lat); ctx.lineTo(x + r, oy - s * lat);
      }
      ctx.strokeStyle = css.getPropertyValue("--lens-grid");
      ctx.lineWidth = 0.5;
      ctx.stroke();
      ctx.restore();
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.strokeStyle = css.getPropertyValue("--lens-ring");
      ctx.lineWidth = 0.9;
      ctx.stroke();

      // the map: simplified and on the grid inside the lens, in full detail outside
      ctx.lineJoin = ctx.lineCap = "round";
      ctx.strokeStyle = css.getPropertyValue("--lens-line");
      ctx.beginPath();
      for (const a of arcs) {
        const line = [];
        for (let i = 0; i < a.xs.length; i++) {
          const lon = a.xs[i], lat = a.ys[i];
          const d = Math.hypot(ox + s * lon - x, oy - s * lat - y) / r;
          const t = Math.min(1, Math.max(0, (1 - d) / 0.25)), k = t * t * (3 - 2 * t);
          if (a.w[i] <= tolerance * k) continue;
          // towards the nearest point of the grid, fully a little inside the edge
          const qx = lon + (Math.round(lon / cell) * cell - lon) * k;
          const qy = lat + (Math.round(lat / cell) * cell - lat) * k;
          line.push(ox + s * qx, oy - s * qy);
        }
        // an island without area on the grid is dropped, as topojson does
        if (a.closed) {
          let area = 0;
          for (let j = 2; j < line.length; j += 2) area += line[j - 2] * line[j + 1] - line[j] * line[j - 1];
          if (Math.abs(area) < 1) continue;
        }
        ctx.moveTo(line[0], line[1]);
        for (let j = 2; j < line.length; j += 2) ctx.lineTo(line[j], line[j + 1]);
      }
      ctx.stroke();
    }

    function tick() {
      const k = still.matches ? 1 : 0.22;
      lens = { x: lens.x + (target.x - lens.x) * k, y: lens.y + (target.y - lens.y) * k, r: lens.r + (target.r - lens.r) * k };
      draw();
      const moving = Math.abs(target.x - lens.x) + Math.abs(target.y - lens.y) + Math.abs(target.r - lens.r) > 0.5;
      frame = moving ? requestAnimationFrame(tick) : 0;
    }
    const go = () => { if (view && !frame) frame = requestAnimationFrame(tick); };

    // a mouse moves the lens and lets it go back to rest; a finger moves it by a tap
    // or a drag, and leaves it there
    const follow = e => {
      if (!rest) return;
      const rect = canvas.getBoundingClientRect();
      target = { x: e.clientX - rect.left, y: e.clientY - rect.top, r: rest.r };
      go();
    };
    canvas.addEventListener("pointermove", follow);
    canvas.addEventListener("pointerdown", follow);
    canvas.addEventListener("pointerleave", e => {
      if (rest && e.pointerType === "mouse") { target = { ...rest }; go(); }
    });
  }

  document.querySelectorAll("figure.lens").forEach(mount);
})();
