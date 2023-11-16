"""
Adapted from: https://pydeck.gl/gallery/heatmap_layer.html


"""
import os
import json

import dash
import pydeck as pdk
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output
from dash import dcc, html, Input, Output, callback
from dotenv import load_dotenv

load_dotenv()

mapbox_api_token = os.getenv("MAPBOX_ACCESS_TOKEN")

_DATA_PATH = "data/"
colors = {
    'background': '#faf9f7',
    'text-dark': '#101851',
    'text-light': '#7AB3DC',
    'background-mid': '#4B4C51',
}


app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

#TODO: add buttons for each variable that can be shown, and a default set
app.layout = html.Div(
    style={
        'backgroundColor': colors['background'],
        'font-family': 'Ubuntu',
        'padding': '1rem 2rem',
        "min-height": '100vh',
    },
    children=[
        html.H1(
            style={
                'textAlign': 'center',
                # 'color': colors['text-light'],
            },
            children='License to Krill',
        ),
        html.Div(
            style={
                'textAlign': 'center',
                # 'color': colors['text-light'],
                'padding-bottom': '1rem',
            },
            children='Estimación de la abundancia de Krill en la Antártica',
        ),
        html.Div(
            style={
                "display": "flex",
                "column-gap": "1rem",
            },
            children=[
                html.Div(  # left pannel
                    style={
                        "flex": "1 0",
                        "display": "flex",
                        "flex-direction": "column",
                        "row-gap": ".5rem",
                    },
                    children=[
                        html.Div(
                            style={
                                "display": "flex",
                                "column-gap": ".5rem",
                            },
                            children=[
                                html.Div(
                                    children=[
                                        dbc.RadioItems(
                                            id="map-style",
                                            className="btn-group",
                                            inputClassName="btn-check",
                                            labelClassName="btn btn-sm btn-outline-primary",
                                            labelCheckedClassName="active",
                                            options=[
                                                {"label": "Simple", "value": "simple"},
                                                {"label": "Satelital", "value": "satellite"},
                                            ],
                                            value="simple",
                                        ),
                                        html.Div(id="output"),
                                    ],
                                    className="radio-group",
                                ),
                                dcc.Dropdown(
                                    options=['1993','1995','1996','1997','1998', '1999', '2001', '2002', '2003', '2005', '2006', '2007', '2009', '2011'],
                                    value='2011',
                                    id="year",
                                    style={ 'width': '6rem' },
                                    maxHeight=400,
                                    searchable=False,
                                    clearable=False,
                                ),
                                dcc.Dropdown(
                                    options=['January','February','March'],
                                    value='February',
                                    id="month",
                                    style={ 'width': '6rem' },
                                    maxHeight=400,
                                    searchable=False,
                                    clearable=False,
                                ),
                            ]
                        ),
                        html.Div(
                            id = 'krill-heatmap-container', children=[]
                        ),
                        html.Div(  # layer selector
                            children=[
                                dbc.RadioItems(
                                    id="map-layer",
                                    className="btn-group",
                                    inputClassName="btn-check",
                                    labelClassName="btn btn-sm btn-outline-primary",
                                    labelCheckedClassName="active",
                                    options=[
                                        {"label": "All", "value": "all"},
                                        {"label": "Temperature", "value": "temp"},
                                        {"label": "Krill Denisty", "value": "krill"},
                                    ],
                                    value="all",
                                ),
                            ],
                            className="radio-group",
                        ),
                    ],
                ), 
                html.Div(  # right pannel
                    style={
                        "flex": "0 0 13rem",
                        "display": "flex",
                        "flex-direction": "column",
                        "row-gap": ".5rem",
                    },
                    children=[
                        dcc.Tab(
                            html.Div(children=[
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4("Point Details", className="card-title"),
                                        dbc.Table(
                                            children=[
                                                html.Tbody([
                                                    html.Tr([html.Td("Sea Surface Temperature"), html.Td("3.1")]),
                                                    html.Tr([html.Td("Krill"), html.Td("8")]),
                                                    html.Tr([html.Td("EKEm"), html.Td("1000000+")]),
                                                    html.Tr([html.Td("Clorofila"), html.Td("infty")]),
                                                ])
                                            ],
                                            striped=True,
                                         )
                                    ]),
                                ],
                                style={

                                }),
                            ]),
                            label="Hover",
                        ),
                    ],
                ),
            ],
        ),
    ],
)


@callback(
    Output('krill-heatmap-container', 'children'),
    Input('year', 'value'),
    Input("map-style", "value"),
    Input("map-layer", "value"),
)
def update_map(year, mapbox_style, layer):
    #TODO: add an input with the selected traces and display them
    
    krill_df = pd.read_csv("{}{year_val}-01-01.csv".format(_DATA_PATH, year_val=year), header=0)
    fig = go.Figure()

    trace_krill = go.Densitymapbox(lat=krill_df.Latitud, lon=krill_df.Longitud, z=krill_df.Krill, colorscale="viridis",
                                   radius=15, opacity=0.8,legendrank=1)
    
    trace_sstm = go.Densitymapbox(lat=krill_df.Latitud, lon=krill_df.Longitud, z=krill_df.SSTm, colorscale="RdBu",
                                 radius=19, opacity=0.7, name="Sea Surface Temperature",
                                 colorbar={'x':0.9,'y':1,'len':0.8,'thickness':25,'yanchor':'top','tickfont':{'size':8},'title':'Sea Surface Temp'},
                                reversescale=True)
    
    if layer == 'all' or layer == 'temp':
        fig.add_trace(trace_sstm)
    if layer == 'all' or layer == 'krill':
        fig.add_trace(trace_krill)
    
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
        mapbox_center={"lat": -60.8416, "lon": -55.4433},
        mapbox_zoom=6,
        height=600
    )
    #fig.update_layout(mapbox_bounds={"west": -180, "east": -50, "south": 20, "north": 90})
    if mapbox_style=='simple':
        fig.update_layout(mapbox_style="outdoors", mapbox_accesstoken=mapbox_api_token,)
    else:
        fig.update_layout(
            mapbox_style="white-bg",
            mapbox_accesstoken=mapbox_api_token,
            mapbox_layers=[
                {
                    "below": 'traces',
                    "sourcetype": "raster",
                    "sourceattribution": "United States Geological Survey",
                    "source": [
                        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                    ]
                }
            ]
        )

    g = dcc.Graph(figure=fig, id='map_object')
    return g


if __name__ == "__main__":
    app.run_server(debug=True)
