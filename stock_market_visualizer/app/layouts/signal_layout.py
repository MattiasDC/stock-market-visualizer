from dash import dash_table
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from stock_market_visualizer.app.signals import get_signal_detectors,\
                                                get_supported_trivial_config_signal_detectors,\
                                                get_supported_ticker_based_signal_detectors
from .checkable_table_dropdown_layout import get_checkable_table_dropdown_layout

def get_config_layout(name, children):
    return html.Div(id=f'config-{name}',
                    children=children,
                    hidden=True)

def get_ticker_based_config_layout(name):
    return get_config_layout(name, [dcc.Dropdown(id=f'config-dropdown-ticker-{name}', options=[])])

def get_signal_detector_config_layouts():
    layouts = [get_ticker_based_config_layout(sd.NAME()) for sd in get_supported_ticker_based_signal_detectors()]
    layouts.extend([get_config_layout(sd.NAME(), []) for sd in get_supported_trivial_config_signal_detectors()])
    return layouts

def get_signal_layout(client):
    config_layouts = get_signal_detector_config_layouts()
    config_layouts.insert(0, html.Legend(id='signal-edit-legend',
                                         children="",
                                         className='w-auto'))
    return [
        dbc.Col(width=3, children=
            get_checkable_table_dropdown_layout('signal',
            get_signal_detectors(client),
            [],
            False)),
        dbc.Col(html.Form(id='signal-edit-placeholder',
                          hidden=True,
                          children=[html.Fieldset(id='signal-edit-fieldset',
        					                      className='border p-2',
        					                      children=config_layouts),
                                    dbc.Button("Add", style={'margin-top': 5})]))
        ]