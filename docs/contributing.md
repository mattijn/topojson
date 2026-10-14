
# Contribute


Contributions are much welcome for the documentation and for defects. Defects means here both behavior not conforming the specification and missing but desirable features. The following two sections describes the process that I use for code development and documentation writing.

1. [Contribution for the Python Package](#contribution-for-the-python-package)
2. [Contribution for the Documentation](#contribution-for-the-documentation)

* * *

## Contribution for the Python Package

The code and development happens in this GitHub [repository](http://github.com/mattijn/topojson). 

For contributions, use the following guidelines:

1. Fork the project on GitHub, clone the fork to your Operating System and open the repository as folder/workspace in your favorite IDE. _I use VSCode + Python extension._

2. Any change applied to the source code should be tested against the multiple tests included within the repository.

3. Once satisfied, push your changes as a new branch to your fork and create a Pull Request to the original repository.

4. A Pull Request triggers the Continuous Integration tests on the main GitHub repository and only after passing these tests a PR can be merged into main by the maintainer.

!!! note "Note to self"

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




* * * 

## Contribution for the Documentation

The documentation is built with [Zensical](https://zensical.org) from the Markdown in the `docs` folder, as configured in `zensical.toml`, and published to GitHub Pages by the workflow `docs`. To build it locally, install the documentation tools (next to the optional dependencies, which the examples use) and serve it from the root of the repository:

```bash
uv pip install -e ".[dev,docs]"
zensical serve
```

The server address is shown in the terminal, and a change in the Markdown is shown directly.

The examples on the example pages and How it works run while the site is built ([markdown-exec](https://pawamoy.github.io/markdown-exec/)), so the output below them is that of the current code. Examples that write or read files, or draw in a notebook, are shown and not run.

The _API reference_ is created from the docstrings and type annotations in the code by [mkdocstrings](https://mkdocstrings.github.io/): a page such as `docs/api/topojson.core.topology.md` holds only `::: topojson.core.topology`.

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
