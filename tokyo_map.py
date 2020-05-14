import plotly_express as px
import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
from datetime import datetime as dt

# Load data
adr = pd.read_pickle('data/adr.pkl')
tokyo = pd.read_pickle('data/tokyo.pkl')
target = [
    {'label':'全体', 'value':'全体'},
    {'label':'住人', 'value':'住人'},
    {'label':'来訪者', 'value':'来訪者'}
]
mapbox_access_token = open(".mapbox_token").read()

col_options = [dict(label=x, value=x) for x in adr.index]

# make Layout
line_layout = go.Layout(
    legend={"x":0.8, "y":0.1},
    paper_bgcolor="#1e1e1e",
    plot_bgcolor="#383838",
    font=dict(
        color='white'
    ),
    margin=dict(
        l=0,
        r=0,
        t=10,
        b=1
    )
)

map_layout = go.Layout(
    paper_bgcolor='#1E1E1E',
    font=dict(
        color='white'
    ),
    margin=dict(
    l=31,
    r=0,
    t=1,
    b=1
    ),
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style='dark',
        center=dict(
            lon=139.74,
            lat=35.7
        ),
        zoom=10
    )
)

app = dash.Dash()
#     __name__, external_stylesheets=["https://codepen.io/chriddyp/pen/bWLwgP.css"]
# )

app.config['suppress_callback_exceptions']=True

app.layout = html.Div(
    [
        html.H1("Visualization of Tokyo"),
        html.Div(
            [
                html.P(
                    "Date:"
                ), 
                dcc.DatePickerRange(
                    id='date_range',
                    min_date_allowed=dt(2020, 2, 1),
                    max_date_allowed=dt(2020, 4, 5),
                    initial_visible_month=dt(2020, 2, 1),
                    start_date=dt(2020, 2, 1).date(),
                    end_date=dt(2020, 4, 5).date(),
                ),
                html.P(
                    "TargetClass:"
                ),
                dcc.Dropdown(
                    id='class',
                    options=target,
                    value='全体',
                    style={
                        "color":'1E1E1E'
                    }
                ),
                html.P(
                    "Area:"
                ), 
                dcc.Dropdown(
                    id='area',
                    options=col_options,
                    multi=True,
                    value=['千代田区', '新宿区', '台東区']
                ),
            ],
            className='div-for-ctr',
            style={"width": "25%", "float": "left"}
        ),
        html.Div(
            [
                dcc.Graph(
                    id="graph_geo",
                    style={"width": "75%",
                        # "display": "inline-block"
                        },
                    config={
                        'displayModeBar':False
                    }
                ),
                dcc.Graph(
                    id="graph_line",
                    style={"width": "75%",
                        "display": "inline-block"
                        },
                    config={
                        'displayModeBar':False
                    }
                ),
            ],
            className='div-for-charts'
        )
        
    ],
    className='div-all'
)


@app.callback(Output("graph_geo", "figure"),
                [
                    Input("class", "value"),
                    Input("date_range", "start_date"),
                    Input("date_range", "end_date")
                ]
            )
def make_map_figure(value, start_date, end_date):
    px.set_mapbox_access_token(mapbox_access_token)
    
    date_range = (tokyo.columns >= start_date) & (tokyo.columns <= end_date)
    selected_columns = tokyo.columns[date_range]
    fil_tky = tokyo[selected_columns]

    fil_tky = fil_tky[fil_tky.index.get_level_values('対象分類')==value]
    fil_tky['人数'] = np.sum(fil_tky, axis=1)

    merged_df = pd.merge(fil_tky, adr, on='エリア')

    fig = px.scatter_mapbox(merged_df,
                        lat="latitude",
                        lon="longitude",
                        color="人数",
                        mapbox_style='dark',
                        size="人数",
                        size_max=20,
                        zoom=10,
                        color_continuous_scale=px.colors.sequential.Emrld,
                        hover_name=adr.index)
    
    fig['layout'] = map_layout

    return  fig


@app.callback(Output("graph_line", "figure"),
                [
                    Input("class", "value"),
                    Input("date_range", "start_date"),
                    Input("date_range", "end_date"),
                    Input("area", "value")
                ]
            )
def make_line_figure(value, start_date, end_date, area):
    if type(area) is not list:
        area = [area]

    tf = tokyo[tokyo.index.get_level_values('対象分類')==value].T
    tf = tf.reset_index().rename(columns={'index':'Date'})
    tf.columns = tf.columns.get_level_values('エリア')

    filtered_df = pd.DataFrame()
    for a in area:
        tmp_tf = tf[['Date', a]]
        tmp_tf['area'] = a
        tmp_tf = tmp_tf.rename(columns={a:'Number of People'})
        filtered_df = pd.concat([filtered_df, tmp_tf])

    fig = px.line(
        filtered_df,
        x='Date',
        y='Number of People',
        line_group='area',
        color='area',
        hover_name='area',
        color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
    fig['layout'] = line_layout
    # go.Scatter(x=filtered_df.index, y=filtered_df[i][value], name=i, color_continuous_scale='emrld') for i in area
    return  fig

if __name__ == '__main__':
    app.run_server(debug=True)