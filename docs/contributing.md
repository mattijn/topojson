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
One can install the package including optional dependencies directly from the GitHub repository using:
  
```cmd
python -m pip install "topojson[dev] @ git+https://github.com/mattijn/topojson.git"
```

Or partly using conda:
```cmd
conda create -n topo_dev
conda activate topo_dev
conda install flit codecov pytest flake8
conda install numpy shapely geojson pyshp fiona geopandas altair ipywidgets
python -m pip install simplification
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
bundle exec jekyll serve --baseurl ''
```

**Note:** On Windows, a Windows Defender Firewall dialog can popup. Click allow access to give permission.


The server address is shown in cmd. Any changes you make in the Markdown documentation is directly reflected on this website.

The _API reference_ documentation is created using `pydocmd`. The created markdown is subsequently changed to align with the style of this page. 

All of this happens from the Jupyter Notebook available in the `generate` folder. PydocMd should be [installed](https://github.com/NiklasRosenstein/pydoc-markdown) (using version `2.X`) and available from cmd to run all cells in the notebook successfully.
