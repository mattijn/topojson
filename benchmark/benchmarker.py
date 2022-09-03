# -*- coding: utf-8 -*-
"""
Module for benchmarking.
"""

import datetime
import importlib
import inspect
import logging
from pathlib import Path
import sys
import tempfile
from typing import List, Optional

import pandas as pd

# Add path so the benchmark packages are found
sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporter  # noqa: E402

################################################################################
# Some init
################################################################################

logger = logging.getLogger(__name__)

################################################################################
# The real work
################################################################################


class RunResult:
    """The result of a benchmark run."""

    def __init__(
        self,
        package: str,
        package_version: str,
        operation: str,
        operation_descr: str,
        secs_taken: float,
        run_details: Optional[dict] = None,
    ):
        """
        Constructor for a RunResult.

        Args:
            package (str): Package being benchmarked.
            package_version (str): Version of the package.
            operation (str): Operation name.
            operation_descr (str): Description of the operation.
            secs_taken (float): Seconds the operation took.
            run_details (dict, optional): (Important) details of this specific
                run with impact on performance. Eg. # CPU's used,...
        """
        self.run_datetime = datetime.datetime.now()
        self.package = package
        self.package_version = package_version
        self.operation = operation
        self.operation_descr = operation_descr
        self.secs_taken = secs_taken
        self.run_details = run_details

    def __repr__(self):
        return f"{self.__class__}({self.__dict__})"


def run_benchmarks(
    benchmarks_subdir: str = "benchmarks",
    results_subdir: str = "results",
    results_filename: str = "benchmark_results.csv",
    modules: Optional[List[str]] = None,
    functions: Optional[List[str]] = None,
):

    # Init logging
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d|%(levelname)s|%(name)s|%(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )

    # Discover and run all benchmark implementations
    tmp_dir = Path(tempfile.gettempdir()) / "benchmark"
    logger.info(f"tmpdir: {tmp_dir}")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    benchmarks_dir = Path(__file__).parent / benchmarks_subdir
    results = []
    for file in benchmarks_dir.glob("benchmarks_*.py"):
        module_name = file.stem
        if (not module_name.startswith("_")) and (module_name not in globals()):
            if modules is not None and module_name not in modules:
                # Benchmark whitelist specified, and this one isn't in it
                logger.info(
                    f"skip module {module_name}: not in modules: {modules}"
                )
                continue

            benchmark_implementation = importlib.import_module(
                f"{benchmarks_subdir}.{module_name}", __package__
            )

            # Run the functions in this benchmark
            available_functions = inspect.getmembers(
                benchmark_implementation, inspect.isfunction
            )
            for function_name, function in available_functions:
                if function_name.startswith("_"):
                    continue
                if functions is not None and function_name not in functions:
                    # Function whitelist specified, and this one isn't in it
                    logger.info(
                        f"skip function {function_name}: not in functions: {functions}"
                    )
                    continue

                # Run the benchmark function
                logger.info(f"{benchmarks_subdir}.{module_name}.{function_name} start")
                function_results = function(tmp_dir=tmp_dir)
                if isinstance(function_results, List) is False:
                    function_results = [function_results]
                for function_result in function_results:
                    if isinstance(function_result, RunResult) is True:
                        logger.info(
                            f"{benchmarks_subdir}.{module_name}.{function_name} "
                            f"ready in {function_result.secs_taken:.2f} s"
                        )
                        results.append(function_result)
                    else:
                        logger.warning(
                            f"{benchmarks_subdir}.{module_name}.{function_name} "
                            "ignored: instead of a RunResult it returned "
                            f"{function_result}"
                        )

    # Add results to csv file
    if len(results) > 0:
        results_dir = Path(__file__).resolve().parent / results_subdir
        results_dir.mkdir(parents=True, exist_ok=True)
        results_path = results_dir / results_filename
        results_dictlist = [vars(result) for result in results]
        results_df = pd.DataFrame(results_dictlist)
        if not results_path.exists():
            results_df.to_csv(results_path, index=False)
        else:
            results_df.to_csv(results_path, index=False, mode="a", header=False)

        # Generate reports
        reporter.generate_reports(results_path, output_dir=results_dir)


if __name__ == "__main__":
    run_benchmarks()
