import fire
from pathlib import Path
import altair as alt
import pandas as pd


def stats_to_visz():
    # the following 3 versions are compared, namely the last released version on pypi
    # the version that is currently on main in github and the version in the PR being
    # processed.
    versions = ["last-released", "main", "PR"]

    # collect all timings and create a pandas dataframe
    list_df = []
    for version in versions:
        fp_version = Path(f"tests/timings_{version}.json").resolve()
        fp_version = fp_version.as_posix()
        df_version = pd.read_json(fp_version, orient="records")
        list_df.append(df_version)
    df = pd.concat(list_df)

    # parse to altair chart
    chart = (
        alt.Chart(df, title="timing of files (s) across version", height=150)
        .mark_circle()
        .encode(
            x=alt.X("version:N", title=None),
            y=alt.Y("time:Q", title=None, scale=alt.Scale(type="log")),
            color="version:N",
            column=alt.Column("file:N", title=None),
        )
        .resolve_scale(x="independent")
    )

    # save chart as png using okab as save method
    chart.save("tests/benchmark_chart.svg", scale_factor=1)


if __name__ == "__main__":
    fire.Fire(stats_to_visz)
