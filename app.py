"""
Adapted from: https://pydeck.gl/gallery/heatmap_layer.html


"""
import os
import json

import dash
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import dash_bootstrap_components as dbc
import json

import numpy as np
from shapely.affinity import affine_transform as T
from shapely.affinity import rotate as R


from dash.dependencies import Input, Output
from dash import dcc, html, Input, Output, callback
from dotenv import load_dotenv

load_dotenv()

mapbox_api_token = os.getenv("MAPBOX_ACCESS_TOKEN")

external_stylesheets = [
    dbc.themes.FLATLY,
    "https://fonts.googleapis.com/css2?family=Syne&display=swap"
]

_DATA_PATH = "data/"
colors = {
    "background": "#faf9f7",
    "dark": "#1c3052ff",
    "text-light": "#7AB3DC",
    "background-mid": "#4B4C51",
}

_ZONE_MAPPING = {"management-zone":{"figtype":"json_layer","file":"data/ssmu.geojson", 'color': "purple", 'opacity':0.3, 'fill':{'outlinecolor':'grey'}},
                 "protected-zone":{"figtype":"json_layer","file":"data/protected.json", 'color': "yellow", 'opacity':0.3, 'fill':{'outlinecolor':'grey'}},
                 "restricted-zone":{"figtype":"json_layer","file":"data/restricted.json", 'color': "red", 'opacity':0.3, 'fill':{'outlinecolor':'red'}},
                 "ecosystem-zone":{"figtype":"scatter","file":"data/vulnerable_marine_ecosystems.csv", }}

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY, "https://fonts.googleapis.com/css2?family=Syne&display=swap"])
app.css.config.serve_locally = True
server = app.server

app.layout = html.Div(
    className="page",
    children=[
        html.Div(
            className="header",
            children = [
                dbc.NavbarSimple(
                    children=[
                        dbc.NavItem(dbc.NavLink("Home", href="#")),
                        dbc.NavItem(dbc.NavLink("About", href="#")),
                        dbc.NavItem(dbc.NavLink("Contact", href="#")),
                    ],
                    brand="License to Krill",
                    brand_href="#",
                    color=colors["dark"],
                    dark=True,
                ),
                html.H3("Estimation of krill abundance in the Antarctic Peninsula"),
            ],
        ),
        html.Div(
            className="content",
            children=[
                html.Div(  # left pannel
                    className="left-pannel",
                    children=[
                        html.Div(
                            className="map-pickers",
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
                                                {"label": "Bathymetry", "value": "satellite"},
                                            ],
                                            value="satellite",
                                        ),
                                        html.Div(id="output"),
                                    ],
                                    className="radio-group",
                                ),
                                dcc.Dropdown(
                                    options=["1993","1995","1996","1997","1998", "1999", "2001", "2002", "2003", "2005", "2006", "2007", "2009", "2011",
                                             "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025",
                                             "2026", "2027", "2028", "2029", "2030"]
                                    ,
                                    value="2024",
                                    id="year",
                                    style={ "width": "6rem" },
                                    maxHeight=400,
                                    searchable=False,
                                    clearable=False,
                                ),
                                dcc.Dropdown(
                                    options=[
                                        {"label":"January", "value":"01"},
                                        {"label":"February", "value":"02"},
                                        {"label":"December", "value":"12"}],
                                    value="01",
                                    id="month",
                                    style={ "width": "6rem" },
                                    maxHeight=400,
                                    searchable=False,
                                    clearable=False,
                                ),

                            ]
                        ),
                        html.Div(
                            id = "krill-heatmap-container", children=[]
                        ),
                        html.Div(
                            id = "layer-pickers",
                            className="map-pickers",
                            children=[
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
                                          {"label": "Krill", "value": "Krill"},
                                          {"label": "Surface Temperature", "value": "SSTm"},
                                      ],
                                      value="all",
                                  ),
                              ],
                              className="radio-group",
                          ),
                                html.Div(
                                    children=[
                                        dbc.Checklist(
                                            id="zone-layer",
                                            className="btn-group",
                                            inputClassName="btn-check",
                                            labelClassName="btn btn-sm btn-outline-primary",
                                            labelCheckedClassName="active",
                                            options=[
                                                {"label": "Protected zones", "value": "protected-zone"},
                                                {"label": "Management zones", "value": "management-zone"},
                                                {"label": "Vulnerable marine ecosystems", "value": "ecosystem-zone"},
                                            ],
                                        ),
                                        html.Div(id="output-zones"),
                                    ],
                                    className="radio-group",
                                ),
                            ]
                        ),
                        
                    ],
                ), 
                html.Div(  # right pannel
                    className="right-pannel",
                    children=[
                        dcc.Tab(
                            html.Div(children=[
                                dbc.Card([
                                    dbc.CardBody([
                                        html.H4("Point Details", className="card-title"),
                                        dbc.Table(
                                            children=[
                                                html.Tbody([
                                                    html.Tr([html.Td("Sea Surface Temperature"), html.Td(id="SSTm-point", children=["-  g/m²"])]),
                                                    html.Tr([html.Td("Krill"), html.Td(id="krill-point", children=["- psu"])]),
                                                    html.Tr([html.Td("Sea Surface Salinity"), html.Td(id="SSSm-point", children=["- °C"])]),
                                                    html.Tr([html.Td("Sea surface height"), html.Td(id="ZOSm-point", children=["- m"])]),
                                                    html.Tr([html.Td("Chlorophyll"), html.Td(id="chlm-point", children=["-  mg/m³"])]),
                                                ])
                                            ],
                                            striped=True,
                                        )
                                    ]),
                                ]),
                            ]),
                            label="Hover",
                        ),
                    ],
                ),
            ],
        ),
        html.Footer(style={"background-color":colors["dark"]})
    ],
)


@callback(
    Output("krill-heatmap-container", "children"),
    Input("year", "value"),
    Input("month", "value"),
    Input("map-style", "value"),
    Input("map-layer", "value"),
    Input("zone-layer", "value"),
)
def update_map(year, month, mapbox_style, layer, zone_layers):
    
    krill_df = pd.read_csv("{}{year_val}-{month_val}.csv".format(_DATA_PATH, year_val=year, month_val=month), header=0)
    fig= px.scatter_mapbox(pd.DataFrame({"lat": [], "lon": []}), lat = "lat", lon="lon" )
    count = 0
    len_offset = { 1:0.375, 2:0.125, 3:0.125/3, 4:0 }
    if layer == "all":
        checklist = ["SSTm", "Krill"]
    else:
        checklist = [layer,]
    manual_colorscales = {"SSTm":"thermal", "Krill":"darkmint", "Speed":"redor", }
    for txt in checklist:
        n = len(checklist)
        figx = go.Densitymapbox(lat=krill_df.Latitud, lon=krill_df.Longitud, z=krill_df[txt], colorscale=manual_colorscales[txt],
                                radius=25, opacity=0.6,legendrank=1, hoverinfo="lon+lat", name=txt,
                                colorbar= dict(x=1,y= 0.875 - (count/n) - len_offset[n] , len = 1/n, title = txt, tickfont={"size":16})
                                , customdata=krill_df[["Krill", "SSSm", "SSTm", "ZOSm", "CHLm"]])
        count+=1    
        fig.add_trace(figx)

    krill_df["current_speed"] = np.sqrt(krill_df["Um"] *krill_df["Um"] + krill_df["Vm"]*krill_df["Vm"])
    krill_df["current_direction"] = np.arctan2(krill_df["Vm"],krill_df["Um"])
    map_layers = []
    if mapbox_style == "satellite":
        map_layers.append(
        {
                    "below": "traces",
                    "sourcetype": "raster",
                    "sourceattribution": "United States Geological Survey",
                    "source": [
                        "https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer/tile/{z}/{y}/{x}"
                    ]
                }
        )
        fig.update_layout(mapbox_style="white-bg")
    else:
        map_layers.append({
                    "below": "traces",})
        fig.update_layout(mapbox_style="outdoors")
    try:
      for z in zone_layers:
          info = _ZONE_MAPPING[z]
          if info["figtype"] == "json_layer":
            with open(info["file"]) as user_file:
                file_contents = user_file.read()      
            layer_json = json.loads(file_contents)
            map_layers.append({'source':layer_json,  'type': "fill", 'below': "traces", 'color': info["color"], 'opacity':info["opacity"], 'fill':info["fill"]})
          elif info["figtype"] == "scatter":
              marine_ecosystems = pd.read_csv(info["file"], sep=",")
              fig_me= go.Scattermapbox(mode="markers", lat = marine_ecosystems["Latitud"], lon=marine_ecosystems["Longitud"],
                                       marker={"size":15, "symbol":"star"}, name="ecosistema vulnerable")
              #fig_me=px.scatter_mapbox(lat=marine_ecosystems["Latitud"], lon=marine_ecosystems["Longitud"])
              #fig_me.update_traces(cluster=dict(enabled=True, size=[15, 20, 30,40], step=2))
              fig.add_trace(fig_me)
    except TypeError:
      pass

    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
        mapbox_center={"lat": -60.8416, "lon": -55.4433},
        mapbox_zoom=6,
        height=600,
        mapbox_bounds={"west": -100, "east": -18, "south": -70, "north": -40},
        mapbox_accesstoken=mapbox_api_token,
        mapbox_layers=map_layers
    )
    
    g = dcc.Graph(figure=fig, id="map_object")
    return g


@app.callback(
    [
        Output("krill-point", "children"),
        Output("SSSm-point", "children"),
        Output("SSTm-point", "children"),
        Output("ZOSm-point", "children"),
        Output("chlm-point", "children"),
    ],
    Input("map_object", "clickData"),
)
def display_popup(clickData):
    cd = ["Krill", "SSSm", "SSTm", "ZOSm", "CHLm"]
    units = [" g/m²", " psu", "°C", " m", " mg/m³"]
    ans = []
    for i, txt in enumerate(cd):
        ans.append(str(round(clickData["points"][0]["customdata"][i], 3))+units[i])
    return ans
    


if __name__ == "__main__":
    app.run_server(debug=False)
