---
layout: default
title: Contributing
nav_order: 6
---

# Contribute

## Package

1. Fork the project on GitHub, clone the fork to your Operating System and open the repository as folder/workspace in your favorite IDE. _I use VSCode + Python extension._

2. Any change applied to the source code should be tested against the multiple tests included within the repository.

3. Once satisfied push the changes you've made as a new branch to your fork and create a Pull Request to the original repository.

4. A Pull Request triggers the tests again on the main GitHub repository and only after passing these tests a PR can be merged into master by the maintainer.

## Documentation

The documentation page is build upon Github Pages and this is done through Jekyll. To build the documentation page locally, make sure you have installed:
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

The server address is shown in the cmd. Now any changes made in the documentation is directly reflected on this website.

The _API reference_ documentation is created using `pydocmd`. The created markdown is subsequently changed to align with the style of this page. 

All of this happens from the Jupyter Notebook available in the `generate` folder. PydocMd should be [installed](https://github.com/NiklasRosenstein/pydoc-markdown) (using version `2.X`) and available from cmd to run all cells in the notebook successfully.