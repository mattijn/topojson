# -*- coding: utf-8 -*-
"""
Module to generate reports for benchmarks.
"""

import ast
import math
import os
from pathlib import Path
from typing import Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pandas.api

A4_LONG_SIDE = 11.69
A4_SHORT_SIDE = 8.27


def generate_reports(results_path: Path, output_dir: Path):

    benchmark_df = pd.read_csv(results_path)

    def format_run_details(input: dict) -> str:
        if input is None or input == np.nan:
            return ""
        if isinstance(input, str):
            input = ast.literal_eval(input)
            result_list = [f"{key}:{input[key]}" for key in input]
            return ";".join(result_list)

        return ""

    # Detailed report per package and per operation
    for package in benchmark_df["package"].unique():
        reports_package_dir = output_dir / package
        reports_package_dir.mkdir(parents=True, exist_ok=True)

        package_df = benchmark_df.loc[benchmark_df["package"] == package]
        for operation in package_df["operation"].unique():
            package_operation_df = package_df.loc[
                benchmark_df["operation"] == operation
            ]
            operation_descr = package_operation_df[
                package_operation_df["run_datetime"]
                == package_operation_df["run_datetime"].max()
            ]["operation_descr"].item()
            package_operation_df = package_operation_df[
                ["package_version", "run_details", "secs_taken"]
            ]
            package_operation_df["run_details"] = package_operation_df[
                "run_details"
            ].apply(lambda x: format_run_details(x))
            package_operation_df = package_operation_df.set_index(
                ["package_version", "run_details"]
            )
            results_report_path = reports_package_dir / f"{package}_{operation}.png"
            save_chart(
                df=package_operation_df,
                title=f"{package}-{operation}\n({operation_descr})",
                size=(8, 6),
                label_points="above",
                y_value_formatter="{0:.2f}",
                output_path=results_report_path,
            )

    # General report for package + operation for comparison
    # Remark, to only keep one version, remove "package_version" from groupby!
    benchmark_to_keep_df = (
        benchmark_df[["package", "operation", "package_version"]]
        .sort_values(["package", "operation", "package_version"], ascending=False)
        .groupby(["package", "operation", "package_version"])
        .first()
        .reset_index()
        .set_index(["package", "operation", "package_version"])
    )
    benchmark_general_df = benchmark_df.set_index(
        ["package", "operation", "package_version"]
    )
    benchmark_general_df = (
        benchmark_general_df.loc[
            benchmark_general_df.index.isin(benchmark_to_keep_df.index)
        ].reset_index()
    )[["package", "package_version", "operation", "secs_taken"]]
    benchmark_general_df = benchmark_general_df.pivot_table(
        index="operation", columns=["package", "package_version"]
    )
    # Drop the "secs_taken" level to cleanup legend in chart
    benchmark_general_df = benchmark_general_df.droplevel(level=0, axis=1)
    results_report_path = output_dir / "benchmark.png"
    save_chart(
        df=benchmark_general_df,
        title="Comparison of libraries, time in sec",
        output_path=results_report_path,
        yscale="log",
        label_points="right",
        y_value_formatter="{0:.0f}",
        size=(8, 6),
        linestyle="None",
        gridlines="y",
    )


def save_chart(
    df: pd.DataFrame,
    title: str,
    output_path: Path,
    yscale: Optional[str] = None,
    y_value_formatter: Optional[str] = None,
    label_points: Optional[str] = None,
    open_output_file: bool = False,
    size: Tuple[float, float] = (8, 4),
    plot_kind: str = "line",
    gridlines: Optional[str] = None,
    linestyle: Optional[str] = None,
):
    """
    Render and save a chart.

    Args:
        df (pd.DataFrame): _description_
        title (str): _description_
        output_path (Path): _description_
        yscale (str): y scale to use.
        y_value_formatter (str, optional): a formatter for the y axes and
            labels. Examples:
              - {0:.2%} for a percentage.
              - {0:.2f} for a float with two decimals.
            Defaults to None.
        label_points (str, optional): _description_. Defaults to None.
        open_output_file (bool, optional): _description_. Defaults to False.
        size (Tuple[float, float], optional): _description_. Defaults to (8, 4).
        plot_kind (str, optional): _description_. Defaults to "line".
        gridlines (str, optional): where to draw grid lines:

                - 'x': draw grid lines on the x axis
                - 'y': draw grid lines on the x axis
                - 'both': draw grid lines on both axes
            If None, the default for the style used is used. Defaults to None.
        linestyle (Optional[str], optional): _description_. Defaults to None.

    Raises:
        Exception: _description_
    """

    # Init
    # Check input
    non_numeric_columns = [
        column
        for column in df.columns
        if not pandas.api.types.is_numeric_dtype(df[column])
    ]
    if len(non_numeric_columns) > 0:
        raise Exception(
            f"df has non-numeric columns, so cannot be plotted: {non_numeric_columns}"
        )

    # Init some things based on input
    rot = 90

    # Prepare plot figure and axes
    fig, axs = plt.subplots(figsize=(size))
    # Make sure all x axis values are shown
    axs.set_xticks(range(len(df)))
    if yscale is not None:
        plt.yscale(yscale)  # type: ignore

    # Plot
    df.plot(ax=axs, kind=plot_kind, rot=rot, title=title, linestyle=linestyle)

    # Show y axes as percentages is asked
    if y_value_formatter is not None:
        axs.yaxis.set_major_formatter(
            plt.FuncFormatter(y_value_formatter.format)  # type: ignore
        )
        axs.yaxis.set_minor_formatter(
            plt.FuncFormatter(y_value_formatter.format)  # type: ignore
        )

    # Show grid lines if specified
    if gridlines is not None:
        axs.grid(axis=gridlines, which="both")  # type: ignore

    # Set different markers + print labels
    # Set different markers for each line + get mn/max values + print labels
    markers = ("+", ".", "o", "*", "v", "^", "<", ">", "1", "2", "3", "4")
    max_y_value = None
    min_y_value = None

    xytext = (0, 0)
    horizontal_alignment = "center"
    vertical_alignment = "center"
    if label_points is not None:
        if label_points in ["alternate", "below"]:
            xytext = (0, -5)
            vertical_alignment = "top"
        elif label_points == "above":
            xytext = (0, 5)
            vertical_alignment = "bottom"
        elif label_points == "left":
            xytext = (-5, 0)
            horizontal_alignment = "right"
        elif label_points == "right":
            xytext = (5, 0)
            horizontal_alignment = "left"
        else:
            raise ValueError(
                f"Invalid value for labelpoints: {label_points}, should be one of "
                "alternate, below, above, left, right"
            )

    for i, line in enumerate(axs.get_lines()):
        line.set_marker(markers[i % len(markers)])

        for index, row in enumerate(df.itertuples()):
            for row_fieldname, row_fieldvalue in row._asdict().items():
                if row_fieldname != "Index":
                    if max_y_value is None or row_fieldvalue > max_y_value:
                        max_y_value = row_fieldvalue
                    if min_y_value is None or row_fieldvalue < min_y_value:
                        min_y_value = row_fieldvalue

                    if label_points is not None:
                        # Format label
                        if y_value_formatter is not None:
                            text = y_value_formatter.format(row_fieldvalue)
                        else:
                            text = str(row_fieldvalue)

                        # Label below or above line? + switch
                        if label_points == "alternate":
                            if xytext[1] > 0:
                                xytext = (0, -5)
                                vertical_alignment = "top"
                            else:
                                xytext = (0, 5)
                                vertical_alignment = "bottom"

                        axs.annotate(
                            text=text,  # type: ignore
                            # s=text,
                            # xy=(row.Index, row_fieldvalue),
                            xy=(index, row_fieldvalue),
                            xytext=xytext,
                            textcoords="offset points",
                            ha=horizontal_alignment,
                            va=vertical_alignment,
                            fontsize="small",
                            fontstyle="normal",
                        )

    # Set bottom and top values for y axis
    if max_y_value is not None:
        max_y_value *= 1.1
    if max_y_value is not None and math.isnan(max_y_value) is False:
        plt.ylim(bottom=0, top=max_y_value)
    else:
        plt.ylim(bottom=0)

    # Set legend to the right of the chart
    plt.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    plt.tight_layout()

    # Save and open if wanted
    fig.savefig(output_path)  # type: ignore
    if open_output_file is True:
        os.startfile(output_path)


if __name__ == "__main__":

    results_path = Path(__file__).resolve().parent / "results/benchmark_results.csv"
    output_dir = Path(__file__).resolve().parent / "results"
    generate_reports(results_path, output_dir)
