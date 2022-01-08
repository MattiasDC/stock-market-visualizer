from dash import dash_table
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc

from stock_market.core import Sentiment
from stock_market.ext.indicator import Identity
from stock_market.ext.signal import CrossoverSignalDetector
from stock_market_visualizer.app.signals import get_supported_signal_detectors,\
                                                get_supported_trivial_config_signal_detectors,\
                                                get_supported_ticker_based_signal_detectors
import stock_market_visualizer.app.layouts.checkable_table_dropdown_layout as checkable_table_dropdown_layout
import stock_market_visualizer.app.layouts.dropdown_button_layout as dropdown_button_layout
from stock_market_visualizer.app.layouts.indicator_layout import get_create_indicator_modals_layout
from stock_market_visualizer.app.indicators import get_indicators_with_identity

def get_config_layout(name, children):
    return html.Div(id=f'config-{name}',
                    children=children,
                    hidden=True)

def get_ticker_dropdown_layout(name):
    return dcc.Dropdown(id=f'config-dropdown-ticker-{name}', options=[], placeholder='Ticker')

def get_ticker_based_config_layout(name):
    return get_config_layout(name, [get_ticker_dropdown_layout(name)])

def get_crossover_indicator_getter_layout(name, include_identity):
    indicators = [ i.__name__ for i in get_indicators_with_identity() if include_identity or i != Identity]
    getter_dropdown = dropdown_button_layout.get_layout(name, f'{name} Indicator', indicators, False)
    getter_text = html.P(id=f'{name}-info', className="d-inline")
    return [html.Div(children=[getter_dropdown, getter_text],
                     style={'margin-top' : 5, 'margin-bottom' : 5})] +\
           get_create_indicator_modals_layout(name)
    
def get_crossover_config_layout():
    name = CrossoverSignalDetector.NAME()
    custom_name_input = dcc.Input(id=f'{name}-custom-name',
                                  debounce=True,
                                  placeholder='Name',
                                  style={'margin-top' : 5, 'margin-bottom' : 5},
                                  className='d-inline')
    sentiment_values = [{'value' : s.value, 'label' : str(s.value).lower().capitalize()}
                        for s in Sentiment if s != Sentiment.NEUTRAL]
    return get_config_layout(name, [custom_name_input, get_ticker_dropdown_layout(name)] +
                                    get_crossover_indicator_getter_layout('Responsive', True) +
                                    get_crossover_indicator_getter_layout('Unresponsive', False) +
                                    [dcc.Dropdown(id=f'{name}-sentiment',
                                                  options=sentiment_values,
                                                  placeholder="Sentiment")])

def get_signal_detector_config_layouts():
    layouts = [get_ticker_based_config_layout(sd.NAME().replace(" ", "")) for sd in get_supported_ticker_based_signal_detectors()]
    layouts.extend([get_config_layout(sd.NAME().replace(" ", ""), []) for sd in get_supported_trivial_config_signal_detectors()])
    layouts.append(get_crossover_config_layout())
    return layouts

def get_signal_layout():
    config_layouts = [html.Legend(id='signal-edit-legend', children="", className='w-auto'), html.Br()] +\
                      get_signal_detector_config_layouts()
    return [
        dbc.Col(width=3, children=
            checkable_table_dropdown_layout.get_layout('signal',
            [sd.NAME() for sd in get_supported_signal_detectors()],
            [],
            False)),
        dbc.Col(html.Div(id='signal-edit-placeholder',
                         hidden=True,
                         children=[html.Fieldset(id='signal-edit-fieldset',
                                                 className='border p-2',
                                                 children=config_layouts + [dcc.Store(id='signal-data-placeholder', data={})]),
                                   dbc.Button("Add", id='signal-add', n_clicks=0, style={'margin-top': 5})]))]