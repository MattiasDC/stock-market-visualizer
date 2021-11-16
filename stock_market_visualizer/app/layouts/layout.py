from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

from .date_layout import get_start_date_layout, get_end_date_layout
from .indicator_layout import get_create_indicator_modals_layout, get_indicator_table_layout
from .ticker_layout import get_ticker_table_layout

def get_themes():
    return [dbc.themes.BOOTSTRAP]

def get_layout():
    return dbc.Container(children=[
        html.H1(children='Stock Market Engine'),
        dbc.Container(
            [
             dbc.Row(
                [
                dbc.Col(get_start_date_layout()),
                dbc.Col(get_end_date_layout()),
                dbc.Col(get_ticker_table_layout()),
                dbc.Col(get_indicator_table_layout())
                ])
        ]),
        dcc.Graph(id='stock-market-graph'),
        dcc.Store(id='engine-id')
    ] + get_create_indicator_modals_layout())