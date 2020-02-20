window.addEventListener("DOMContentLoaded", event => {
  var opt = {
    mode: "vega-lite",
    renderer: "svg",
    actions: false
  };

  var spec_topology = "/example/tuning_topology.vl.json";
  vegaEmbed("#embed_tuning_topology", spec_topology, opt).catch(console.err);

  // var spec_topology = "/example/tuning_prequantize.vl.json";
  // vegaEmbed("#embed_tuning_prequantize", spec_topology, opt).catch(console.err);

  // var spec_topology = "/example/tuning_topoquantize.vl.json";
  // vegaEmbed("#embed_tuning_topoquantize", spec_topology, opt).catch(
  //   console.err
  // );
});
