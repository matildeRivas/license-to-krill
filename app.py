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
import dash_bootstrap_components as dbc

from dash.dependencies import Input, Output
from dash import dcc, html, Input, Output, callback
from dotenv import load_dotenv

load_dotenv()

mapbox_api_token = os.getenv("MAPBOX_ACCESS_TOKEN")

_DATA_PATH = "data/"
colors = {
    'background': '#272830',
    'text-dark': '#101851',
    'text-light': '#7AB3DC',
    'background-mid': '#4B4C51',
}


styles = {
    "json-output": {
        "overflowY": "scroll",
        "height": "calc(50% - 25px)",
        "border": "thin lightgrey solid",
        "color": "white"
    },
    "tab": {"height": "calc(98vh - 115px)"},
}


#app = dash.Dash(__name__)
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

app.layout = html.Div(
    style={'backgroundColor': colors['background'], 'font-family': 'Ubuntu', 'padding':'30px'}, 
    children=[
        html.H1(
            children='License to Krill',
            style={
                'textAlign': 'center',
                'color': colors['text-light'],
            }
        ),
        html.Div(children='Estimación de la abundancia de Krill en la Antártica', style={
            'textAlign': 'center',
            'color': colors['text-light'],
        }),
        html.Div(children=[
            html.Div(style={
                "width": "72%",
                "height": "700px",
                "display": "inline-block",
                "position": "relative",
            },
            children=[
                html.Div(
                    [
                        dbc.RadioItems(
                            id="radios",
                            className="btn-group",
                            inputClassName="btn-check",
                            labelClassName="btn btn-outline-primary",
                            labelCheckedClassName="active",
                            options=[
                                {"label": "Vista simple", "value": "simple"},
                                {"label": "Satelital", "value": "satellite"},
                            ],
                            value="simple",
                        ),
                        html.Div(id="output"),
                    ],
                    className="radio-group",
                ),
                html.Div(
                    id = 'krill-heatmap-container', children=[])
            ]),   
            html.Div(
                [dcc.Dropdown(options=['1993','1995','1996','1997','1998', '1999', '2001', '2002', '2003', '2005', '2006', '2007', '2009', '2011'],
                              value='2011',
                              id="year",),
                dcc.Tab(
                    html.Div(
                        style=styles["tab"],
                        children=[
                            html.P("hoverInfo"),
                            html.Pre(id="hover-info-json-output", style=styles["json-output"],),
                        ],
                    ),
                    label="Hover",
                ),
                ],
                style={"width": "28%", "float": "right", "display": "inline-block",})
                #style={"display": "flex", "justify-content": "right",  "align-items": "center", })
        ],
        )#style={"display": "flex", "align-items": "center", "position":"relative", "top":"25px",  "bottom":"25px","backgroundColor":"background-mid"})
    ],
)


@callback(
    Output('krill-heatmap-container', 'children'),
    Input('year', 'value'),
    Input("radios", "value"))
def update_map(year, mapbox_style):
    
    krill_df = pd.read_csv("{}{year_val}-01-01.csv".format(_DATA_PATH, year_val=year), header=0)
    
    fig = px.density_mapbox(krill_df, lat='Latitud', lon='Longitud', z='Krill', radius=10,
                         zoom=4)
    if mapbox_style=='simple':
        fig.update_layout(mapbox_style="outdoors", mapbox_accesstoken=mapbox_api_token,)
    else:
         fig.update_layout(mapbox_style="white-bg", mapbox_accesstoken=mapbox_api_token,
                      mapbox_layers=[
        {
            "below": 'traces',
            "sourcetype": "raster",
            "sourceattribution": "United States Geological Survey",
            "source": [
                "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
            ]
        }]
    )

    g = dcc.Graph(figure=fig, id='map_object')

    return g


@app.callback(Output("hover-info-json-output", "children"), [Input("krill-heatmap", "clickInfo")])
def dump_json(data):
    print(data)
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    app.run_server(debug=True)
