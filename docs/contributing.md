---
layout: default
title: Contributing
nav_order: 6
---

This is the contributing page

To build the documentation page locally, run the following command from the root-folder of the `docs`:

```bash
bundle exec jekyll serve
```

API-reference page is building using the following command:

Change docstring to PydocMd format is probable best solution for now as numpy/google style is not yet supported https://github.com/NiklasRosenstein/pydoc-markdown/issues/1

```bash
pydocmd simple topojson++ topojson.core.topology++ topojson.core.extract++ topojson.core.join++ topojson.core.cut++ topojson.core.dedup++ topojson.core.hashmap++ topojson.utils++ topojson.ops++ > docs.md
```

The content of this `docs.md` is copied into `api-reference.md` and the `docs.md` is removed again.
