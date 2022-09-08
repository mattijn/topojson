import fire
from pathlib import Path
import altair as alt
import pandas as pd
from okab.saver import OkabSaver

def stats_to_visz():

    versions = ['lastrelease', 'master', 'PR']
    df_list = []
    for version in versions:
        fp_version = Path(f'tests/timings_{version}.json').resolve()
        df_version = pd.read_json(fp_version)
        df_list.append(df_version)
    df = pd.concat(df_list)

    chart = alt.Chart(df, title='timing of files (s) across version', height=150).mark_circle().encode(
        x=alt.X('version:N', title=None),
        y=alt.Y('time:Q', title=None, scale=alt.Scale(type='log')),
        color='version:N', 
        column=alt.Column('file:N', title=None)
    ).resolve_scale(x='independent')

    chart.save("tests/benchmark_chart.png", method=OkabSaver, scale_factor=2)
    
if __name__ == '__main__':

    fire.Fire(stats_to_visz)