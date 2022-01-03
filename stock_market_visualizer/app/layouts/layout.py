from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

from .date_layout import get_start_date_layout, get_end_date_layout
from .header_layout import get_header_layout
from .indicator_layout import get_create_indicator_modals_layout, get_indicator_table_layout
from .interval_layout import get_interval_layout
from .ticker_layout import get_ticker_table_layout
from .signal_layout import get_signal_layout

def get_themes():
    return [dbc.themes.BOOTSTRAP]

def get_layout(client):
    return dbc.Container(children=
        [
        dcc.Location(id='url', refresh=False),
        dcc.Store(id='restoreable-state'),
        get_header_layout(),
        dbc.Container(
            [
             dbc.Row(
                [
                dbc.Col(get_start_date_layout()),
                dbc.Col(get_end_date_layout()),
                dbc.Col(get_ticker_table_layout()),
                dbc.Col(get_indicator_table_layout())
                ]),
             dbc.Row(
                dbc.Col(dcc.Graph(id='stock-market-graph')),
                ),
             dbc.Row(
                children=get_signal_layout(client)
                )
        ]),
        dcc.Store(id='engine-id'),
        get_interval_layout()
        ] + get_create_indicator_modals_layout())