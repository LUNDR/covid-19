# for data managaement
import numpy as np
import pandas as pd
import time
from datetime import datetime, timedelta

# for charting
import plotly
import plotly.graph_objects as go

# colours
from palettable.colorbrewer.qualitative import Paired_12
from palettable.tableau import Tableau_20


# for dash app
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc


from figures import fig1, fig2, fig3, fig4, headline, map1


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], meta_tags=[
                {"name": "viewport", "content": "width=device-width, initial-scale=1"}])
application = app.server
app.title = 'COVID-19 Cases & Deaths Dashboard'


app.layout = html.Div(
    html.Div([
        html.Div([
            html.Div([
                html.H3(children='Covid-19 Data Dashboard',
                        style={
                            'text-align': 'left',
                            'display': 'inline-block',
                            'margin-top': '0.5%',
                            'margin-left': '1.5%'}
                        ),


                html.Div(children=['''
                                    Visualizations of data on cases and deaths from COVID-19 compiled by the 
                                    ''',html.A('European Centre for Disease Prevention and Control', href = 'https://www.ecdc.europa.eu/en')],
                                    style={'width': '74%',
                                                'display': 'inline-block',
                                                'margin-bottom': '1.5%',
                                                'margin-left': '1.5%'}
                         )

            ], className="container",
                style={'max-width': 'none',
                       'padding': 0,
                         'height': '3%',
                         'float': 'left'}
            ),

        ], className="header twelve columns"),




        html.Div([
            html.Div([
                dcc.Graph(
                    figure=headline,
                    responsive=False,

                )
            ],
                className="five columns",
                style={
                'display': 'inline-block',
                'margin-left': '1.5%',
                'margin-top': '1.5%'}
            ),



            html.Div([
                dcc.Graph(
                    figure=map1,
                    responsive=False,

                )
            ],
                className="five columns",
                style={
                'display': 'inline-block',
                'margin-left': '1.5%',
                'margin-top': '1.5%'}),


        ], className='row',
            style={}
        ),

        html.Div([
            html.Div([
                dcc.Graph(
                    figure=fig2,
                    responsive=False,
                )
            ],
                className="five columns",
                style={
                'display': 'inline-block',
                'margin-left': '1.5%',
                'margin-top': '1.5%'}
            ),

            html.Div([
                dcc.Graph(
                    figure=fig3,
                    responsive=False,
                )
            ],
                className="five columns",
                style={
                'display': 'inline-block',
                    'margin-left': '1.5%',
                    'margin-top': '1.5%'}
            ),

        ], className='row',
            style={}
        ),

        html.Div([
            html.Div([
                dcc.Graph(
                    figure=fig4,
                    responsive=False,

                )
            ],
                className="five columns",
                style={
                'display': 'inline-block',
                'margin-left': '1.5%',
                    'margin-top': '1.5%'}
            ),

            html.Div([
                dcc.Graph(
                    figure=fig1,
                    responsive=False,

                )
            ],
                className="five columns",
                style={
                'display': 'inline-block',
                    'margin-left': '1.5%',
                    'margin-top': '1.5%',
                    'margin-bottom': '1.5%'}
            ),
        ],
            className='row',
            style={}
        ),

        html.Div([
            html.Div(['Plotly Dash Application created by Rachel Lund (2020)',
                html.A([
                    html.Img(src = 'assets/github-logo.png',
                                                            style = {
                                                            'height' : 50,
                                                            'width' : 'auto',
                                                            'position' : 'center',
                                                            'float': 'center'})
                ], href = 'https://github.com/LUNDR')],
                    style={
                        'height' : '3%',
                        'margin-top': '0%',
                        'font-size': '1em',
                        'margin-left': '1.5%',
                        'margin-bottom': '0%',
                        'padding-top' : '2%',
                        'padding-bottom': '2%'}
                    ),
    


        ],
            className="footer",
            style={'background-color': 'black'}
        ),
    ],
        style={'background-color': '#f2f3f4'}
    )
)

if __name__ == '__main__':
    application.run(port=8080)


######
