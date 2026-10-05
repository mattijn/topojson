// to_widget in the browser: topojson runs in Pyodide (Python in WebAssembly), and the
// sliders call toposimplify(keep=...) and topoquantize on the topology of Africa. With
// keep, Douglas-Peucker keeps a share of the vertices; the tolerance that gives the
// same result is shown with it. Until the button is pressed the map is the Africa of
// the lens, and nothing is loaded.
//
// <figure class="widget" data-src="lens_africa.json"><canvas></canvas></figure>
(function () {
  const PYODIDE = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.js";
  const PYTHON = `
import numpy as np
import topojson as tp

topo = tp.Topology(tp.utils.example_data_africa())
lines = tp.ops.arc_coordinates(topo.output["arcs"], topo.output["transform"])

def run(keep, quant):
    simple = topo.toposimplify(keep=keep).topoquantize(quant)
    arcs = tp.ops.arc_coordinates(simple.output["arcs"], simple.output["transform"])
    sizes = np.array([len(a) for a in arcs], dtype=np.int32)
    _, epsilon = tp.ops.simplify_keep(lines, keep)
    return np.concatenate(arcs).ravel(), sizes, float(epsilon)

run
`;
  // the topoquantize factor, a power of ten
  const quantText = e => `1e${e}`;

  function mount(figure) {
    const canvas = figure.querySelector("canvas");
    const ctx = canvas.getContext("2d");
    let lines = [], view = null, run = null, busy = false, again = false;
    const state = { keep: 0.1, quant: 5 };

    const el = (tag, cls, text) => {
      const e = document.createElement(tag);
      if (cls) e.className = cls;
      if (text !== undefined) e.textContent = text;
      return e;
    };
    const start = el("button", "widget-start", "Run in your browser");
    const note = el("span", "widget-note", "loads Python, NumPy, Shapely and topojson");
    const cover = el("div", "widget-cover");
    cover.append(start, note);
    canvas.after(cover);

    const controls = el("div", "widget-controls");
    const row = (label, min, max, step) => {
      const r = el("label", "widget-row");
      const input = el("input"), value = el("span", "widget-value");
      Object.assign(input, { type: "range", min, max, step });
      r.append(el("span", "widget-name", label), input, value);
      controls.append(r);
      return { input, value };
    };
    const keep = row("keep", 0, 1, 0.01);
    const quant = row("topoquantize", 1, 6, 1);
    const call = el("code", "widget-call");
    const status = el("div", "widget-status");
    controls.append(call, status);
    figure.append(controls);
    controls.querySelectorAll("input").forEach(c => (c.disabled = true));

    keep.input.addEventListener("input", () => { state.keep = +keep.input.value; sync(); update(); });
    quant.input.addEventListener("input", () => { state.quant = +quant.input.value; sync(); update(); });

    function sync() {
      keep.input.value = state.keep;
      keep.value.textContent = state.keep.toFixed(2);
      quant.input.value = state.quant;
      quant.value.textContent = quantText(state.quant);
      call.textContent = `topo.toposimplify(keep=${state.keep.toFixed(2)}).topoquantize(${quantText(state.quant)})`;
    }
    sync();

    // the poster: the arcs of the lens, in full detail
    fetch(figure.dataset.src).then(r => r.json()).then(data => {
      const [kx, ky] = data.transform.scale, [x0, y0] = data.transform.translate;
      lines = data.arcs.map(flat => {
        const xy = [];
        for (let j = 0, x = 0, y = 0; j < flat.length; j += 2) {
          x += flat[j]; y += flat[j + 1];
          xy.push(x0 + x * kx, y0 + y * ky);
        }
        return xy;
      });
      resize();
      new ResizeObserver(resize).observe(canvas);
    });

    function resize() {
      const rect = canvas.getBoundingClientRect(), dpr = devicePixelRatio || 1;
      if (!lines.length || !rect.width) return;
      canvas.width = Math.round(rect.width * dpr);
      canvas.height = Math.round(rect.height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      if (!view || !view.box) {
        let a = Infinity, b = -Infinity, c = Infinity, d = -Infinity;
        for (const xy of lines) for (let i = 0; i < xy.length; i += 2) {
          a = Math.min(a, xy[i]); b = Math.max(b, xy[i]);
          c = Math.min(c, xy[i + 1]); d = Math.max(d, xy[i + 1]);
        }
        view = { box: [a, b, c, d] };
      }
      const [a, b, c, d] = view.box, pad = 12;
      const s = Math.min((rect.width - 2 * pad) / (b - a), (rect.height - 2 * pad) / (d - c));
      Object.assign(view, { s, w: rect.width, h: rect.height, ox: (rect.width - s * (b + a)) / 2, oy: (rect.height + s * (d + c)) / 2 });
      draw();
    }

    function draw() {
      if (!view || !view.s) return;
      const { s, ox, oy } = view;
      ctx.clearRect(0, 0, view.w, view.h);
      ctx.lineJoin = ctx.lineCap = "round";
      ctx.lineWidth = 0.9;
      ctx.strokeStyle = getComputedStyle(figure).getPropertyValue(run ? "--widget-line" : "--widget-faint");
      ctx.beginPath();
      for (const xy of lines) {
        ctx.moveTo(ox + s * xy[0], oy - s * xy[1]);
        for (let i = 2; i < xy.length; i += 2) ctx.lineTo(ox + s * xy[i], oy - s * xy[i + 1]);
      }
      ctx.stroke();
    }

    // one call at a time; a slider that moves meanwhile is computed next, at its latest value
    function update() {
      if (!run) return;
      if (busy) { again = true; return; }
      busy = true;
      setTimeout(() => {
        const out = run(state.keep, 10 ** state.quant);
        const [xy, sizes, epsilon] = out.toJs();
        out.destroy();
        lines = [];
        for (let k = 0, i = 0; k < sizes.length; i += 2 * sizes[k++]) lines.push(xy.subarray(i, i + 2 * sizes[k]));
        draw();
        status.textContent = epsilon < 0 ? "every vertex" : `as epsilon ${Number(epsilon.toPrecision(3))}`;
        busy = false;
        if (again) { again = false; update(); }
      });
    }

    const script = src => new Promise((ok, fail) => {
      const s = Object.assign(document.createElement("script"), { src, onload: ok, onerror: fail });
      document.head.append(s);
    });

    start.addEventListener("click", async () => {
      start.disabled = true;
      const say = text => (note.textContent = text);
      try {
        say("loading Python…");
        if (!window.loadPyodide) await script(PYODIDE);
        const py = await window.loadPyodide();
        say("loading NumPy and Shapely…");
        await py.loadPackage(["numpy", "shapely", "micropip"], { messageCallback: () => {} });
        say("installing topojson from PyPI…");
        await py.pyimport("micropip").install("topojson");
        say("computing the topology of Africa…");
        await new Promise(ok => setTimeout(ok));
        run = py.runPython(PYTHON);
        const version = py.runPython("tp.__version__");
        cover.remove();
        controls.querySelectorAll("input").forEach(c => (c.disabled = false));
        figure.classList.add("live");
        figure.dataset.version = version;
        update();
      } catch (err) {
        say(`could not start: ${err.message || err}`);
        start.disabled = false;
      }
    });
  }

  document.querySelectorAll("figure.widget").forEach(mount);
})();
