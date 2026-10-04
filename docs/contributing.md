---
layout: default
title: Contributing
nav_order: 6
---

# Contribute
{: .no_toc}


Contributions are much welcome for the documentation and for defects. Defects means here both behavior not conforming the specification and missing but desirable features. The following two sections describes the process that I use for code development and documentation writing.

1. TOC
{:toc}

* * *

## Contribution for the Python Package

The code and development happens in this GitHub [repository](http://github.com/mattijn/topojson). 

For contributions, use the following guidelines:

1. Fork the project on GitHub, clone the fork to your Operating System and open the repository as folder/workspace in your favorite IDE. _I use VSCode + Python extension._

2. Any change applied to the source code should be tested against the multiple tests included within the repository.

3. Once satisfied, push your changes as a new branch to your fork and create a Pull Request to the original repository.

4. A Pull Request triggers the Continuous Integration tests on the main GitHub repository and only after passing these tests a PR can be merged into main by the maintainer.

<div class="code-example mx-1 bg-example">
<div class="example-label" markdown="1">
Note to self 📝
{: .label .label-blue-000 }
</div>
<div class="example-text" markdown="1">
From a clone of the repository, an environment with [uv](https://docs.astral.sh/uv/) including the optional dependencies and the test tools:

```bash
uv venv --python 3.13
uv pip install -e ".[dev]" pytest
uv run pytest tests
```

The code is linted and formatted with [ruff](https://docs.astral.sh/ruff/), as configured in `pyproject.toml`; CI checks both:

```bash
uvx ruff check
uvx ruff format
```

The public API (`Topology`) is typed, and CI checks the types with mypy, also from the side of a user (`tests/typing_api.py`):

```bash
uv run --with mypy mypy topojson tests/typing_api.py
```

Or install the package including optional dependencies directly from the GitHub repository using:

```bash
pip install "topojson[dev] @ git+https://github.com/mattijn/topojson.git"
```

Or partly using conda:
```bash
conda create -n topo_dev
conda activate topo_dev
conda install flit codecov pytest ruff
conda install numpy shapely geojson pyshp fiona geopandas altair ipywidgets
pip install simplification
```

</div>
</div>


* * * 

## Contribution for the Documentation

The documentation page is build upon Github Pages. To build the documentation page locally, make sure you have installed:
1. Ruby 
- On MacOS this can be done using `brew install ruby`.
- On Windows you should follow instructions on [https://rubyinstaller.org/downloads/](https://rubyinstaller.org/downloads/). 

2. Dependencies GitHub Pages
- Enter the `docs` directory from this repository on cmd and run `bundle install` to install all required (sub)dependencies that are mentioned in the `Gemfile`.

Afterwards and consequently run the following command from within the `docs` folder:

```bash
PAGES_REPO_NWO=mattijn/topojson bundle exec jekyll serve --baseurl ''
```

`PAGES_REPO_NWO` names the repository, which the theme needs outside GitHub. If `bundle install` fails, the `github-pages` gem may not support the newest Ruby yet; use an earlier Ruby.

**Note:** On Windows, a Windows Defender Firewall dialog can popup. Click allow access to give permission.


The server address is shown in cmd. Any changes you make in the Markdown documentation is directly reflected on this website.

The _API reference_ documentation is created using `pydocmd`. The created markdown is subsequently changed to align with the style of this page. 

All of this happens from the Jupyter Notebook available in the `generate` folder. PydocMd should be [installed](https://github.com/NiklasRosenstein/pydoc-markdown) (using version `2.X`) and available from cmd to run all cells in the notebook successfully.

The charts on the example pages are Vega-Lite specifications in `docs/json`. They are created by running the examples of these pages; to update them, run from the root of the repository:

```bash
python generate/make-docs-charts.py
```

The lens on the overview page draws the arcs of Africa with the weight of each vertex, from `docs/json/lens_africa.json`; to update it:

```bash
python generate/make-docs-lens.py
```

The figures of the steps on the page How it works draw what each step gives for the toy example, from `docs/json/steps.json`; to update it:

```bash
python generate/make-docs-steps.py
```

The other figures drawn this way, on the pages Example usage, Types of input data, Settings and tuning, Retrieval data types, Incremental updates and Quantization, come from `docs/json/fig_*.json`; to update them:

```bash
python generate/make-docs-figures.py
```
