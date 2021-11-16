from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

from .indicator_layout import get_create_indicator_modals_layout, get_indicator_table_layout
from .ticker_layout import get_ticker_table_layout

def get_themes():
    return [dbc.themes.BOOTSTRAP]

def get_layout():
    earliest_start = dt.date(1990, 1, 1)

    return dbc.Container(children=[
        html.H1(children='Stock Market Engine'),
        dbc.Container(
            [
             dbc.Row(
                [
                dbc.Col(
                    [
                    html.P("Start"),
                    dcc.DatePickerSingle(
                        id='date-picker-start',
                        min_date_allowed=earliest_start,
                        max_date_allowed=dt.datetime.now().date() - dt.timedelta(days=1),
                        placeholder='Start Date',
                        display_format='D-M-Y')
                    ]),
                dbc.Col(
                    [
                    html.P("End"),
                    dcc.DatePickerSingle(
                        id='date-picker-end',
                        min_date_allowed=earliest_start + dt.timedelta(days=1),
                        placeholder='End Date',
                        display_format='D-M-Y')
                    ]),
                dbc.Col(get_ticker_table_layout()),
                dbc.Col(get_indicator_table_layout())
                ])
        ]),
        dcc.Graph(id='stock-market-graph'),
        dcc.Store(id='engine-id')
    ] + get_create_indicator_modals_layout())