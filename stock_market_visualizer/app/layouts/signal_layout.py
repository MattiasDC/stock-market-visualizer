from dash import dash_table
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from stock_market_visualizer.app.signals import get_signal_detectors
from .checkable_table_dropdown_layout import get_checkable_table_dropdown_layout

def get_signal_layout(client):
	return [
        dbc.Col(width=3, children=
            get_checkable_table_dropdown_layout('signal',
            get_signal_detectors(client),
            [],
            False)),
        dbc.Col(dbc.Container(id='signal-edit-placeholder'))
        ]