import benchmarker

if __name__ == "__main__":
    benchmarker.run_benchmarks(modules=["benchmarks_topojson"])

    # Only run specific benchmark function(s)
    # benchmarker.run_benchmarks(modules=["benchmarks_topojson"], functions=["topology_agriparcels_16000"])
