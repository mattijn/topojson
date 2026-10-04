// Run tests/pyodide/check.py in Pyodide, with the topojson of this repository.
// Run from the root of the repository: node tests/pyodide/check.mjs
import { loadPyodide } from "pyodide";
import { readFileSync } from "node:fs";

const py = await loadPyodide();
await py.loadPackage(["numpy", "shapely"], { messageCallback: () => {} });
py.FS.mkdir("/repo");
py.FS.mount(py.FS.filesystems.NODEFS, { root: process.cwd() }, "/repo");
py.runPython(`import os, sys; sys.path.insert(0, "/repo"); os.chdir("/repo")`);
py.runPython(readFileSync("tests/pyodide/check.py", "utf8"));
