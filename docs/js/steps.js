// The steps of the computation as a stack of plates: a call passes the data down to
// core.extract and each step does its part on the way up. Each plate shows what its
// step gives for the toy example (generate/make-docs-steps.py); the top plate is the
// step of the section. Moving the pointer down picks a plate; the plates above fade.
//
// <figure class="steps" data-src="steps.json" data-step="cut"><svg></svg></figure>
(function () {
  const ORDER = ["extract", "join", "cut", "dedup", "hashmap", "topology"];
  const NS = "http://www.w3.org/2000/svg";
  const still = matchMedia("(prefers-reduced-motion: reduce)");
  const cache = {};

  // isometric projection of a point of the toy example (x 0..15, y 0..5) on a plate
  const S = 15, GAP = 30, W = 560, CX = 180;
  const P = (x, y, z) => [CX + (x - (5 - y)) * 0.866 * S, 64 + (x + (5 - y)) * 0.5 * S - z];
  const pts = (line, z) => line.map(([x, y]) => P(x, y, z).map(v => v.toFixed(1)).join(",")).join(" ");

  // keep the text at about 12px on screen, whatever the scale of the figure
  // (at most 1.45 times larger in the figure, so that the names still fit)
  function fit(svg, most = Infinity) {
    const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
    if (scale > 0) svg.style.setProperty("--steps-font", `${Math.min(12 / scale, most).toFixed(1)}px`);
  }

  function el(name, attrs, parent) {
    const e = document.createElementNS(NS, name);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    parent.appendChild(e);
    return e;
  }

  function trim(line, d) {
    const towards = (p, q) => {
      const l = Math.hypot(q[0] - p[0], q[1] - p[1]);
      return [p[0] + ((q[0] - p[0]) / l) * d, p[1] + ((q[1] - p[1]) / l) * d];
    };
    const out = line.slice();
    out[0] = towards(line[0], line[1]);
    out[out.length - 1] = towards(line[line.length - 1], line[line.length - 2]);
    return out;
  }

  // what a plate shows: lines, thick lines, dots and labels in toy coordinates
  function content(step, d) {
    const s = d[step], c = { lines: [], thick: [], dots: [], grid: [], labels: [] };
    if (step === "extract") c.lines = s.lines;
    if (step === "join") { c.lines = s.lines; c.dots = s.junctions; }
    if (step === "cut") c.lines = s.parts.map(p => trim(p, 0.45));
    if (step === "dedup") {
      s.arcs.forEach((a, i) => (s.shared.includes(i) ? c.thick : c.lines).push(a));
    }
    if (step === "hashmap" || step === "topology") {
      c.lines = s.arcs;
      // the number of each arc next to the middle of its middle segment
      s.arcs.forEach((a, i) => {
        const m = Math.floor((a.length - 1) / 2);
        c.labels.push([a[m], a[m + 1], String(i)]);
      });
    }
    return c;
  }

  function mount(figure) {
    const svg = figure.querySelector("svg");
    const top = ORDER.indexOf(figure.dataset.step);
    const plates = ORDER.slice(0, top + 1);
    const call = figure.dataset.step[0].toUpperCase() + figure.dataset.step.slice(1) + "()";
    svg.setAttribute("viewBox", `0 ${30 - GAP * top} ${W} ${222 + GAP * top}`);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", `The steps ${plates.join(", ")}: a call of ${call} passes the data down to core.extract, and each step does its part on the way up.`);

    let pick = top, ghost = plates.map(() => 0), frame = 0;
    const groups = plates.map(() => el("g", {}, svg));
    const path = el("g", {}, svg);

    function draw(d) {
      plates.forEach((step, i) => {
        const g = groups[i], z = i * GAP + ghost[i] * 18, on = i === pick, current = i === top;
        g.replaceChildren();
        g.setAttribute("opacity", (1 - 0.8 * ghost[i]).toFixed(2));
        const fill = ghost[i] > 0.5 ? "none" : current ? "var(--steps-accent)" : "var(--steps-plate)";
        const plate = [[-1.5, -1.5], [16.5, -1.5], [16.5, 6.5], [-1.5, 6.5], [-1.5, -1.5]];
        el("polygon", { points: pts(plate, z - 4), fill, stroke: "var(--steps-lo)", "stroke-width": 0.9 }, g);
        el("polygon", { points: pts(plate, z), fill, stroke: on ? "var(--steps-edge)" : "var(--steps-lo)", "stroke-width": 0.9 }, g);
        // a plate shows its content when it is on top or picked
        const shown = on || (current && pick === top);
        const c = shown ? content(step, d) : { lines: [], thick: [], dots: [], grid: [], labels: [] };
        const ink = on ? "var(--steps-hi)" : "var(--steps-mid)";
        c.grid.forEach(([x, y]) => { const [px, py] = P(x, y, z); el("circle", { cx: px, cy: py, r: 0.6, fill: "var(--steps-lo)" }, g); });
        c.lines.forEach(l => el("polyline", { points: pts(l, z), fill: "none", stroke: ink, "stroke-width": 0.9, "stroke-linejoin": "round", "stroke-linecap": "round" }, g));
        c.thick.forEach(l => el("polyline", { points: pts(l, z), fill: "none", stroke: ink, "stroke-width": 2.2, "stroke-linecap": "round" }, g));
        c.dots.forEach(([x, y]) => { const [px, py] = P(x, y, z); el("circle", { cx: px, cy: py, r: on ? 3 : 2.2, fill: fill === "none" ? "var(--steps-plate)" : fill, stroke: ink, "stroke-width": 0.9 }, g); });
        c.labels.forEach(([p, q, t]) => {
          // on the side of the segment away from the middle of the plate
          const [x0, y0] = P(...p, z), [x1, y1] = P(...q, z), [cx, cy] = P(7.5, 2.5, z);
          const mx = (x0 + x1) / 2, my = (y0 + y1) / 2, l = Math.hypot(x1 - x0, y1 - y0);
          let nx = (y0 - y1) / l, ny = (x1 - x0) / l;
          if (nx * (mx - cx) + ny * (my - cy) < 0) { nx = -nx; ny = -ny; }
          el("text", { x: mx + nx * 10, y: my + ny * 10, "text-anchor": "middle", "dominant-baseline": "central", class: "steps-label", fill: ink }, g).textContent = t;
        });
        const [lx, ly] = P(16.5, 6.5, z);
        el("text", { x: lx + 14, y: ly + 4, class: "steps-name", fill: on ? "var(--steps-hi)" : "var(--steps-mid)" }, g).textContent = `core.${step}`;
      });

      // the call: down along the stack, back up
      path.replaceChildren();
      const [x0, y0] = P(-1.5, -1.5, top * GAP), [, y1] = P(-1.5, -1.5, 0);
      const a = x0 - 22, b = x0 - 12, up = y0 - 34, low = y1 + 14;
      el("text", { x: a - 4, y: up - 10, "text-anchor": "start", class: "steps-name", fill: "var(--steps-hi)" }, path).textContent = call;
      el("path", { d: `M${a},${up} L${a},${low}`, fill: "none", stroke: "var(--steps-mid)", "stroke-width": 0.9, "stroke-dasharray": "2 3" }, path);
      el("path", { d: `M${a},${low} Q${a},${low + 10} ${(a + b) / 2},${low + 10} Q${b},${low + 10} ${b},${low} L${b},${up}`, fill: "none", stroke: "var(--steps-mid)", "stroke-width": 0.9 }, path);
      el("path", { d: `M${b - 3},${up + 5} L${b},${up} L${b + 3},${up + 5}`, fill: "none", stroke: "var(--steps-mid)", "stroke-width": 0.9 }, path);
      el("path", { d: `M${a - 3},${low - 5} L${a},${low} L${a + 3},${low - 5}`, fill: "none", stroke: "var(--steps-mid)", "stroke-width": 0.9 }, path);
    }

    function tick(d) {
      const k = still.matches ? 1 : 0.2;
      ghost = ghost.map((g, i) => g + ((i > pick ? 1 : 0) - g) * k);
      draw(d);
      const moving = ghost.some((g, i) => Math.abs((i > pick ? 1 : 0) - g) > 0.01);
      frame = moving ? requestAnimationFrame(() => tick(d)) : 0;
    }

    (cache[figure.dataset.src] ||= fetch(figure.dataset.src).then(r => r.json())).then(d => {
      draw(d);
      new ResizeObserver(() => fit(svg, 12 * 1.45)).observe(svg);
      const go = () => { if (!frame) frame = requestAnimationFrame(() => tick(d)); };
      // the pointer picks the plate whose name, at its right corner, is nearest in
      // height (at rest, so that it does not jump while the plates above fade)
      const corner = P(16.5, 6.5, 0)[1];
      svg.addEventListener("pointermove", e => {
        const y = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse()).y;
        const next = Math.min(top, Math.max(0, Math.round((corner - y) / GAP)));
        if (next !== pick) { pick = next; go(); }
      });
      svg.addEventListener("pointerleave", () => { pick = top; go(); });
    });
  }

  // Panels seen from above: lines (dark), the rest of the figure (faint), filled
  // rings with a label, and points. With data-step, the output of a step of the toy
  // example of How it works; else the panels of the file (generate/make-docs-figures.py).
  //
  // <figure class="parts" data-src="steps.json" data-step="cut"><svg></svg></figure>
  // <figure class="parts" data-src="fig_input_shapely.json"><svg></svg></figure>
  function panels(step, d) {
    const s = d[step], whole = d.extract.lines, junctions = d.join.junctions;
    if (step === "toy") return [{ lines: whole, arrows: true, numbers: true }];
    if (step === "extract") return s.lines.map((l, i) => ({ title: `line ${i}`, lines: [l], faint: whole, arrows: true }));
    if (step === "join") return s.lines.map((l, i) => ({ title: `line ${i}`, lines: [l], faint: whole, dots: junctions }));
    if (step === "cut") return s.parts.map((p, i) => ({ title: `part ${i}, of line ${s.line[i]}`, lines: [p], faint: whole, ends: true }));
    if (step === "dedup") return s.arcs.map((a, i) => ({ title: s.shared.includes(i) ? `arc ${i}, shared` : `arc ${i}`, lines: [a], faint: whole, ends: true, thick: s.shared.includes(i) }));
    return [{ lines: s.arcs, labels: true, ends: true }];
  }

  // all points of a panel, to find the extent of a figure
  function* points(p) {
    for (const l of [...(p.lines || []), ...(p.faint || [])]) yield* l;
    for (const polygon of p.fills || []) for (const ring of polygon) yield* ring;
    yield* p.dots || [];
    for (const [x, y] of p.texts || []) yield [x, y];
  }

  function mountParts(figure) {
    const svg = figure.querySelector("svg");
    (cache[figure.dataset.src] ||= fetch(figure.dataset.src).then(r => r.json())).then(d => {
      const list = figure.dataset.step ? panels(figure.dataset.step, d) : d.panels;
      const single = list.length === 1;
      let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
      for (const p of list) for (const [x, y] of points(p)) {
        x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
      }
      const bw = Math.max(x1 - x0, 1e-9), bh = Math.max(y1 - y0, 1e-9);
      const k = single ? Math.min(400 / bw, 280 / bh) : Math.min(150 / bw, 110 / bh);
      const pad = single ? 22 : 12, head = list.some(p => p.title) ? 18 : 0;
      // a panel is at least as wide as its title, the drawing in its middle
      const title = Math.max(0, ...list.map(p => (p.title || "").length)) * 6.6;
      const w = Math.max(bw * k + 2 * pad, title + 8), h = bh * k + 2 * pad + head;
      const box = { x0, y1, k, pad: pad + (w - bw * k - 2 * pad) / 2, top: pad, head, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
      let cols = 0;
      const layout = () => {
        // as many panels in a row as fit the width of the page, at their own size
        const room = figure.getBoundingClientRect().width || W;
        const fits = single ? 1 : Math.max(1, Math.min(list.length, Math.floor((room + 12) / (w + 12))));
        if (fits !== cols) { cols = fits; draw(list, single, box, w, h, cols); }
        fit(svg);
      };
      layout();
      new ResizeObserver(layout).observe(figure);
    });

    function draw(list, single, box, w, h, cols) {
      const { x0, y1, k, pad, top, head } = box;
      const rows = Math.ceil(list.length / cols), width = cols * (w + 12) - 12;
      svg.replaceChildren();
      svg.setAttribute("viewBox", `0 0 ${width} ${rows * (h + 12) - 12}`);
      svg.style.maxWidth = `${width}px`;
      svg.setAttribute("role", "img");
      svg.setAttribute("aria-label", figure.dataset.label || list.map(p => p.title).filter(Boolean).join(", ") || "A figure of the example");
      list.forEach((p, i) => {
        const g = el("g", { transform: `translate(${(i % cols) * (w + 12)},${Math.floor(i / cols) * (h + 12)})` }, svg);
        const Q = ([x, y]) => [pad + (x - x0) * k, head + top + (y1 - y) * k];
        const line = l => l.map(q => Q(q).map(v => v.toFixed(1)).join(",")).join(" ");
        const ring = r => "M" + r.map(q => Q(q).map(v => v.toFixed(1)).join(",")).join("L") + "Z";
        if (p.title) el("text", { x: 0, y: 11, class: "steps-label", fill: "var(--steps-edge)" }, g).textContent = p.title;
        el("rect", { x: 0.5, y: head + 0.5, width: w - 1, height: h - head - 1, rx: 4, fill: "var(--steps-plate)", stroke: "var(--steps-lo)", "stroke-width": 0.9 }, g);
        (p.fills || []).forEach((polygon, j) => el("path", { d: polygon.map(ring).join(""), "fill-rule": "evenodd", fill: j % 2 ? "var(--steps-fill-b)" : "var(--steps-fill-a)", stroke: "var(--steps-hi)", "stroke-width": 0.9, "stroke-linejoin": "round" }, g));
        (p.faint || []).forEach(l => el("polyline", { points: line(l), fill: "none", stroke: "var(--steps-lo)", "stroke-width": 0.9, "stroke-linejoin": "round" }, g));
        (p.lines || []).forEach(l => el("polyline", { points: line(l), fill: "none", stroke: "var(--steps-hi)", "stroke-width": p.thick ? 2.2 : 1.2, "stroke-linejoin": "round", "stroke-linecap": "round" }, g));
        const dot = (q, r) => { const [x, y] = Q(q); el("circle", { cx: x, cy: y, r, fill: "var(--steps-plate)", stroke: "var(--steps-hi)", "stroke-width": 0.9 }, g); };
        if (p.ends) (p.lines || []).forEach(l => { dot(l[0], 2); dot(l[l.length - 1], 2); });
        (p.dots || []).forEach(q => dot(q, 3));
        (p.texts || []).forEach(([x, y, s]) => { const [px, py] = Q([x, y]); el("text", { x: px, y: py, "text-anchor": "middle", "dominant-baseline": "central", class: "steps-label", fill: "var(--steps-hi)" }, g).textContent = s; });
        if (p.arrows) p.lines.forEach(l => {
          // an arrowhead at the end, along the last segment
          const [ax, ay] = Q(l[l.length - 2]), [bx, by] = Q(l[l.length - 1]), a = Math.atan2(by - ay, bx - ax), r = single ? 7 : 5;
          const tip = s => `${(bx - r * Math.cos(a + s)).toFixed(1)},${(by - r * Math.sin(a + s)).toFixed(1)}`;
          el("polyline", { points: `${tip(0.45)} ${bx},${by} ${tip(-0.45)}`, fill: "none", stroke: "var(--steps-hi)", "stroke-width": 1.2, "stroke-linejoin": "round" }, g);
        });
        // the number of each line next to its start, on the side away from the line
        if (p.numbers) p.lines.forEach((l, j) => {
          const [x, y] = Q(l[0]), [nx, ny] = Q(l[1]), dx = nx - x, n = Math.hypot(dx, ny - y);
          const left = dx / n > 0.5, label = el("text", { class: "steps-label", fill: "var(--steps-hi)", "dominant-baseline": "central" }, g);
          // along a horizontal start the label goes above it, else to its left
          label.setAttribute("x", left ? x : x - 8);
          label.setAttribute("y", left ? y - 12 : y - 6);
          label.setAttribute("text-anchor", left ? "start" : "end");
          label.textContent = `line ${j}`;
        });
        if (p.labels) p.lines.forEach((l, j) => {
          // next to the middle of the middle segment, away from the middle of the panel
          const m = Math.floor((l.length - 1) / 2), [ax, ay] = Q(l[m]), [bx, by] = Q(l[m + 1]), [cx, cy] = Q([box.cx, box.cy]);
          const mx = (ax + bx) / 2, my = (ay + by) / 2, n = Math.hypot(bx - ax, by - ay);
          let nx = (ay - by) / n, ny = (bx - ax) / n;
          if (nx * (mx - cx) + ny * (my - cy) < 0) { nx = -nx; ny = -ny; }
          el("text", { x: mx + nx * 12, y: my + ny * 12, "text-anchor": "middle", "dominant-baseline": "central", class: "steps-label", fill: "var(--steps-hi)" }, g).textContent = String(j);
        });
      });
    }
  }

  document.querySelectorAll("figure.steps").forEach(mount);
  document.querySelectorAll("figure.parts").forEach(mountParts);
})();
