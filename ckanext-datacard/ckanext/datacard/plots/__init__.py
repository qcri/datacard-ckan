import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# data: dataframe with metrics as columns
# groups: categories in data, if None no grouping is done
# html: whether to return HTML object
def generate_datacard_plot(data, groups=None, html=True):

    assert data is not None
    if groups is not None: 
        assert len(data)==len(groups)

    if groups is None:
        return generate_datacard_plot_single(data, html)

    fig=go.Figure()

    # creating bar plot for each column in each dataframe
    for group in groups:
        subdata = data[group]
        for col in subdata.iloc[:, subdata.columns != 'package']:
            fig.add_trace( go.Bar(x=subdata.iloc[:, 'package'], y=subdata[1], visible=True) )

    # update layout with dropdown for each group making only the relevant bar plots visible

def generate_datacard_plot_single(data, html=True):
    pass
