---
layout: default
title: Overview
nav_order: 1
---

# Encode spatial data as topology in Python!

<figure class="lens" data-src="{{site.baseurl}}/json/lens_africa.json" data-intensity="0.6">
  <canvas role="img" aria-label="A map of Africa in thin lines: sharp around the pointer, simplified further away, and without seams between the countries"></canvas>
</figure>
<script src="{{site.baseurl}}/js/lens.js" defer></script>

Topojson is a library that is capable of creating a topojson encoded format of merely any spatial object in Python.

With topojson it is possible to reduce the size of your spatial data. Mostly by orders of magnitude. It is able to do so through:

- Eliminating redundancy through computation of a topology
- Fixed-precision integer encoding of coordinates and
- Simplification and quantization of arcs

## Getting Started

- [Installation](installation)
- [Example usage](example-usage)
    - [Types of input data](example/input-types.html)
    - [Settings and tuning](example/settings-tuning.html)
    - [Retrieval data types](example/output-types.html)
    - [Incremental updates](example/incremental-updates.html)

## User Guide

- [How it works](how-it-works)
- [API-reference](api-reference)

## Bug Reports & Questions

- [Contributing](contributing)

Topojson is BSD-licensed and the source is available on GitHub. If any questions or issues come up as you use topojson, please get in touch via Github Issues: [Python TopoJSON on GitHub](https://github.com/mattijn/topojson).
