---
layout: default
title: Contributing
nav_order: 6
---

# Contribute

To build the documentation page locally, run the following command from the root-folder of the `docs`:

```bash
bundle exec jekyll serve --baseurl ''
```

The API reference documentation is created using `pydocmd`. The created markdown is subsequently changed to align with the style of this page. 


All of this happens from the Jupyter Notebook available in the generate folder. PydocMd should be installed and available from cmd to run the notebook.

Still have to fix some issues regarding relative linking: https://stackoverflow.com/a/19173888