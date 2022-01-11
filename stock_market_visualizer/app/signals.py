import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Output, Input, State
import json
from random import randrange

from stock_market.core import Sentiment
from stock_market.ext.indicator import Identity
from stock_market.ext.signal import MonthlySignalDetector,\
                                    BiMonthlySignalDetector,\
                                    GoldenCrossSignalDetector,\
                                    DeathCrossSignalDetector,\
                                    CrossoverSignalDetector
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.checkable_table import CheckableTableLayout
from stock_market_visualizer.app.dropdown_button import DropdownButton
from stock_market_visualizer.app.indicator import ModalIndicatorCreatorLayout, get_indicators_with_identity

logger = get_logger(__name__)


def get_api_supported_signal_detectors(client):
    return [sd["detector_name"] for sd in api.get_supported_signal_detectors(client)]


def get_supported_trivial_config_signal_detectors():
    return [MonthlySignalDetector, BiMonthlySignalDetector]


def get_supported_ticker_based_signal_detectors():
    return [GoldenCrossSignalDetector, DeathCrossSignalDetector]


def get_supported_signal_detectors():
    return get_supported_trivial_config_signal_detectors() +\
           get_supported_ticker_based_signal_detectors() +\
           [CrossoverSignalDetector]


class SignalDetectorConfigurationLayout:
    def __init__(self, name, children):
        self.name = name
        self.children = children
        self.config_name = f'config-{name}'
        self.layout = html.Div(id=self.config_name,
                                 children=self.children,
                                 hidden=True)

    def get_layout(self):
        return self.layout


class EmptyDetectorHandler:
    def __init__(self, client, detector_name):
        self.__client = client
        self.__detector_name = detector_name

    def name(self):
        return self.__detector_name

    def id(self):
        return self.name().replace(" ", "")

    def activate(self, engine_id):
        if engine_id is None:
            return None
        engine_id = api.add_signal_detector(engine_id,
                                            {"static_name" : self.name(),
                                             "config" : str(randrange(get_settings().max_id_generator))},
                                            self.__client)
        return engine_id

    def get_id(self, config):
        return config

class TrivialSignalDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, name):
        super().__init__(name, [])

    def get_handler(self, app, client):
        return EmptyDetectorHandler(client, self.name)


class TickerDropdownLayout:
    def __init__(self, name):
        self.dropdown_name = f'config-dropdown-ticker-{name}'
        self.layout = dcc.Dropdown(id=self.dropdown_name, options=[], placeholder='Ticker')
    
    def get_options(self):
        return self.dropdown_name, 'options'

    def get_value(self):
        return self.dropdown_name, 'value'

    def get_layout(self):
        return self.layout

class TickerBasedDetectorHandler:
    def __init__(self, app, client, detector_cls, engine_layout, signal_data_placeholder_layout, dropdown_layout):
        self.__app = app
        self.__client = client
        self.__detector_cls = detector_cls

        @self.__app.callback(
            Output(*dropdown_layout.get_options()),
            Output(*dropdown_layout.get_value()),
            Input(*engine_layout.get_id()),
            State(*dropdown_layout.get_value()))
        def update_dropdown_list(engine_id, value):
            options = self.__get_options(engine_id)
            if len(options) == 1:
                value = options[0]['value']
            return options, value

        @self.__app.callback(
            Input(*dropdown_layout.get_value()),
            State(*signal_data_placeholder_layout.get_data()),
            Output(*signal_data_placeholder_layout.get_data()))
        def update_active_ticker(ticker_value, data):
            data['ticker'] = ticker_value
            return data

    def name(self):
        return self.__detector_cls.NAME()

    def id(self):
        return self.name().replace(" ", "")

    def app(self):
        return self.__app

    def client(self):
        return self.__client

    def __get_options(self, engine_id):
        tickers = api.get_tickers(engine_id, self.__client)
        return [{'label': t, 'value': t} for t in tickers]

    def activate(self, engine_id):
        return engine_id

    def create(self, engine_id, data):
        new_engine_id = api.add_signal_detector(engine_id,
                                                {"static_name" : self.name(),
                                                 "config" : json.dumps({"id" : randrange(get_settings().max_id_generator),
                                                                        "ticker" : json.dumps(data['ticker'])})},
                                                self.__client)
        return new_engine_id

    def get_id(self, config):
        return json.loads(config)['id']


class TickerBasedDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, detector_cls, engine_layout, signal_data_placeholder_layout):
        self.detector_cls = detector_cls
        self.ticker_dropdown = TickerDropdownLayout(self.get_id())
        self.engine_layout = engine_layout
        self.signal_data_placeholder_layout = signal_data_placeholder_layout

        super().__init__(self.get_id(), self.ticker_dropdown.get_layout())

    def get_id(self):
        return self.detector_cls.NAME().replace(" ", "")

    def get_handler(self, app, client):
        return TickerBasedDetectorHandler(app,
                                          client,
                                          self.detector_cls,
                                          self.engine_layout,
                                          self.signal_data_placeholder_layout,
                                          self.ticker_dropdown)


class IndicatorGetterLayout:
    def __init__(self, name, include_identity):
        self.name = name
        self.include_identity = include_identity
        
        indicators = [ i.__name__ for i in get_indicators_with_identity() if include_identity or i != Identity]
        self.dropdown_button = DropdownButton(name, f'{name} Indicator', indicators, False)

        self.indicator_getter_id = f'{name}-info'
        self.indicator_getter_text = html.P(id=self.indicator_getter_id, className="d-inline")

        self.modal_layout = ModalIndicatorCreatorLayout(name)

        self.layout = [html.Div(children=[self.dropdown_button.get_layout(), self.indicator_getter_text],
                                 style={'margin-top' : 5, 'margin-bottom' : 5})] +\
                      self.modal_layout.get_layout()
                         

    def get_layout(self):
        return self.layout

    def get_info(self):
        return self.indicator_getter_id, 'children'

    def get_modal_layout(self):
        return self.modal_layout

    def get_dropdown_layout(self):
        return self.dropdown_button


class CrossoverDetectorHandler(TickerBasedDetectorHandler):
    def __init__(self,
                 app,
                 client,
                 crossover_layout):
        super().__init__(app,
                         client,
                         CrossoverSignalDetector,
                         crossover_layout.engine_layout,
                         crossover_layout.signal_data_placeholder_layout,
                         crossover_layout.ticker_dropdown)
        self.crossover_layout = crossover_layout

        indicators = get_indicators_with_identity()
        for indicator in api.get_supported_indicators(client):
            if indicator['indicator_name'] not in [i.__name__ for i in indicators.keys()]:
                logger.warning(f"{indicator} is not implemented in the stock market visualizer")

        for indicator in indicators.keys():
            if indicator.__name__ not in [i['indicator_name'] for i in api.get_supported_indicators(client)]:
                logger.warning(f"{indicator} is implemented in the stock market visualizer, but not supported by the engine")

        for indicator in indicators:
            self.__add_create_indicator_callbacks("Responsive",
                                                  indicator,
                                                  indicators[indicator],
                                                  crossover_layout.responsive_getter)
            if indicator != Identity:
                self.__add_create_indicator_callbacks("Unresponsive",
                                                      indicator,
                                                      indicators[indicator],
                                                      crossover_layout.unresponsive_getter)

        @app.callback(Input(*crossover_layout.custom_name_layout.get_name()),
                      State(*crossover_layout.signal_data_placeholder_layout.get_data()),
                      Output(*crossover_layout.signal_data_placeholder_layout.get_data()))
        def update_custom_name(custom_name, data):
            data['name'] = custom_name
            return data

        @app.callback(Input(*crossover_layout.sentiment_dropdown_layout.get_sentiment()),
                      State(*crossover_layout.signal_data_placeholder_layout.get_data()),
                      Output(*crossover_layout.signal_data_placeholder_layout.get_data()))
        def update_custom_name(sentiment, data):
            data['sentiment'] = sentiment
            return data        

    def __add_create_indicator_callbacks(self, name, indicator, arguments, getter):
        if indicator != Identity:
            modal = getter.get_modal_layout()

            @self.app().callback(Input(*getter.get_dropdown_layout().get_item_n_clicks(indicator.__name__)),
                                 Output(*modal.get_is_open(indicator)))
            def create_indicator_form(n_clicks):
                if n_clicks == 0 or None:
                    return False
                return True

    
            @self.app().callback(Input(*modal.get_add_n_clicks(indicator)),
                                 State(*self.crossover_layout.signal_data_placeholder_layout.get_data()),
                                 [State(*modal.get_argument_value(indicator, argument)) for argument in arguments],
                                 Output(*modal.get_is_open(indicator)),
                                 Output(*self.crossover_layout.signal_data_placeholder_layout.get_data()),
                                 Output(*getter.get_info()))
            def create_indicator(n_clicks, data, arguments):
                if n_clicks == 0 or None:
                    return dash.no_update, dash.no_update, dash.no_update
                if not isinstance(arguments, list):
                    arguments = [arguments]
                created_indicator = indicator(*arguments)
                data[name] = { 'name' : indicator.__name__,
                               'config' : created_indicator.to_json()}
                return False, data, str(created_indicator)
        else:
            @self.app().callback(Input(*getter.get_dropdown_layout().get_item_n_clicks(indicator.__name__)),
                                 State(*self.crossover_layout.signal_data_placeholder_layout.get_data()),
                                 Output(*self.crossover_layout.signal_data_placeholder_layout.get_data()),
                                 Output(*getter.get_info()))
            def create_indicator(n_clicks, data):
                if n_clicks == 0 or None:
                    return dash.no_update, dash.no_update
                created_indicator = indicator()
                data[name] = { 'name' : indicator.__name__,
                               'config' : created_indicator.to_json()}
                return data, str(created_indicator)

    def create(self, engine_id, data):
        if 'name' not in data:
            return engine_id
        if 'Responsive' not in data:
            return engine_id
        if 'Unresponsive' not in data:
            return engine_id
        if 'ticker' not in data or len(data['ticker']) == 0:
            return engine_id
        if 'sentiment' not in data:
            return engine_id
        new_engine_id = api.add_signal_detector(engine_id,
            {'static_name' : self.name(),
             'config' : json.dumps({'id' : randrange(get_settings().max_id_generator),
                                    'name' : data['name'],
                                    'ticker' : json.dumps(data['ticker']),
                                    'responsive_indicator_getter' : data['Responsive'],
                                    'unresponsive_indicator_getter' : data['Unresponsive'],
                                    'sentiment' : json.dumps(data['sentiment'])})},
            self.client())
        return new_engine_id

    def get_id(self, config):
        return json.loads(config)['id']

class CrossoverCustomNameLayout:
    def __init__(self, name):
        self.id = f'{name}-custom-name'
        self.layout = dcc.Input(id=self.id,
                                debounce=True,
                                placeholder='Name',
                                style={'margin-top' : 5, 'margin-bottom' : 5},
                                className='d-inline')

    def get_name(self):
        return self.id, 'value'

    def get_layout(self):
        return self.layout


class SentimentDropdownLayout:
    def __init__(self, name):
        self.id = f'{name}-sentiment'
        sentiment_values = [{'value' : s.value, 'label' : str(s.value).lower().capitalize()}
                            for s in Sentiment if s != Sentiment.NEUTRAL]
        self.layout = dcc.Dropdown(id=self.id,
                                   options=sentiment_values,
                                   placeholder='Sentiment')

    def get_sentiment(self):
        return self.id, 'value'

    def get_layout(self):
        return self.layout


class CrossoverDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, engine_layout, signal_data_placeholder_layout):
        self.engine_layout = engine_layout
        self.signal_data_placeholder_layout = signal_data_placeholder_layout
        
        name = CrossoverSignalDetector.NAME()
        self.custom_name_layout = CrossoverCustomNameLayout(name)
        self.sentiment_dropdown_layout = SentimentDropdownLayout(name)

        self.ticker_dropdown = TickerDropdownLayout(name)
        self.responsive_getter = IndicatorGetterLayout('Responsive', True)
        self.unresponsive_getter = IndicatorGetterLayout('Unresponsive', False)
        child_configs = [self.custom_name_layout.get_layout(), self.ticker_dropdown.get_layout()] +\
                        self.responsive_getter.get_layout() +\
                        self.unresponsive_getter.get_layout() +\
                        [self.sentiment_dropdown_layout.get_layout()]
        super().__init__(name, child_configs)

    def get_handler(self, app, client):
        return CrossoverDetectorHandler(app, client, self)


class SignalDataPlaceholderLayout:
    def __init__(self):
        self.id = 'signal-data-placeholder'
        self.layout = dcc.Store(id=self.id, data={})

    def get_data(self):
        return self.id, 'data'

    def get_layout(self):
        return self.layout

class SignalDetectorLayout:
    def __init__(self, engine_layout):
        self.engine_layout = engine_layout
        self.signal_detector_table = CheckableTableLayout('signal',
                                                          [sd.NAME() for sd in get_supported_signal_detectors()],
                                                          [],
                                                          False)
        self.legend_id = 'signal-edit-legend'
        self.legend = html.Legend(id=self.legend_id, children="", className='w-auto')
        self.signal_detector_data_layout = SignalDataPlaceholderLayout()

        self.trivial_config_layouts = [TrivialSignalDetectorConfigurationLayout(sd.NAME().replace(" ", ""))
                                       for sd in get_supported_trivial_config_signal_detectors()]
        self.ticker_based_config_layouts = [
             TickerBasedDetectorConfigurationLayout(sd, engine_layout, self.signal_detector_data_layout)
             for sd in get_supported_ticker_based_signal_detectors()]
        self.crossover_config_layout = CrossoverDetectorConfigurationLayout(engine_layout, self.signal_detector_data_layout)

        self.signal_edit_placeholder_id = 'signal-edit-placeholder'
        self.add_button_id = 'signal-add'
        self.signal_edit_fieldset_id = 'signal-edit-fieldset'

    def get_config_layouts(self):
        layouts = list(self.trivial_config_layouts)
        layouts.extend(self.ticker_based_config_layouts)
        layouts.append(self.crossover_config_layout)
        return layouts
    
    def get_layout(self):
        config_layouts = [self.legend, html.Br()] + [cl.get_layout() for cl in self.get_config_layouts()]
        return [
            dbc.Col(width=3, children=self.signal_detector_table.get_layout()),
            dbc.Col(html.Div(id=self.signal_edit_placeholder_id,
                             hidden=True,
                             children=[html.Fieldset(id=self.signal_edit_fieldset_id,
                                                     className='border p-2',
                                                     children=config_layouts + [self.signal_detector_data_layout.get_layout()]),
                                       dbc.Button("Add", id=self.add_button_id, n_clicks=0, style={'margin-top': 5})]))]


    def register_callbacks(self, app, client_getter):
        self.signal_detector_table.register_callbacks(app)
    
        client = client_getter()
        detector_handlers = {dh.name() : dh for dh in [cl.get_handler(app, client) for cl in self.get_config_layouts()]}
        
        @app.callback(
            Output(self.signal_edit_placeholder_id, 'hidden'),
            Input(self.signal_detector_table.collapse_table_id, 'is_open'),
            State(self.legend_id, 'children'))
        def hide_edit_fieldset(is_open, name):
            return not is_open or name in [h.name for h in self.trivial_config_layouts] or len(name) == 0
    
        @app.callback(
            Output(*self.signal_detector_table.get_table()),
            Input(*self.engine_layout.get_id()))
        def update_signal_table(engine_id):
            return [{'signal-col' : signal_detector['name'],
                     'name' : signal_detector['static_name'],
                     'config' : json.dumps(signal_detector['config'])}
                    for signal_detector in api.get_signal_detectors(engine_id, client)]
    
        @app.callback(
            Output(*self.engine_layout.get_id()),
            Output(self.signal_edit_placeholder_id, 'hidden'),
            Output(*self.signal_detector_table.get_table_selected()),
            Input(self.add_button_id, 'n_clicks'),
            State(*self.engine_layout.get_id()),
            State(self.legend_id, 'children'),
            State(*self.signal_detector_data_layout.get_data()),
            State(*self.signal_detector_table.get_table_selected()))
        def add_signal_detector(n_clicks, engine_id, handler_name, data, selected_signal_detectors):
            if n_clicks == 0:
                return dash.no_update, dash.no_update, dash.no_update
            handler = detector_handlers[handler_name]
    
            signal_detectors_before = api.get_signal_detectors(engine_id, client)
            new_engine_id = handler.create(engine_id, data)
            signal_detectors_after = api.get_signal_detectors(new_engine_id, client)
    
            if signal_detectors_before != signal_detectors_after:
                assert len(signal_detectors_after) - len(signal_detectors_before) == 1
                selected_signal_detectors.append(len(signal_detectors_before))
    
            return new_engine_id, new_engine_id != engine_id, selected_signal_detectors
    
        def register_dropdown_callback(handler):
            @app.callback(
                Output(*self.engine_layout.get_id()),
                Output(self.signal_edit_fieldset_id, 'children'),
                Output(self.signal_edit_placeholder_id, 'hidden'),
                Output(*self.signal_detector_table.get_table_selected()),
                Input(*self.signal_detector_table.get_dropdown().get_item_n_clicks(handler.id())),
                State(self.signal_edit_fieldset_id, 'children'),
                State(*self.engine_layout.get_id()),
                State(*self.signal_detector_table.get_table_selected()))
            def add_signal_detector(clicks, fieldset_children, engine_id, selected_signal_detectors):
                if clicks == 0:
                    return dash.no_update, dash.no_update, dash.no_update, dash.no_update
                signal_detectors_before = api.get_signal_detectors(engine_id, client)
                engine_id = handler.activate(engine_id)
                signal_detectors_after = api.get_signal_detectors(engine_id, client)
    
                hide_fieldset = False
                for child in fieldset_children:
                    child_props = child['props']
                    if 'id' not in child_props:
                        continue
                    name = child_props['id']
                    if 'signal-edit-legend' == name:
                        child_props['children'] = handler.name()
                    if 'config-' in name:
                        child_props['hidden'] = True
                    if handler.id() in name.replace('config-', ''):
                        if len(child_props['children']) != 0:
                            child_props['hidden'] = False
                        else:
                            hide_fieldset = True
    
                if signal_detectors_before != signal_detectors_after:
                    assert len(signal_detectors_after) - len(signal_detectors_before) == 1
                    selected_signal_detectors.append(len(signal_detectors_before))
                return engine_id, fieldset_children, hide_fieldset, selected_signal_detectors

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Input(self.signal_detector_table.table_id, 'data_timestamp'),
            State(self.signal_detector_table.table_id, 'data_previous'),
            State(*self.signal_detector_table.get_table()),
            State(*self.engine_layout.get_id()))
        def remove_signal_detector(timestamp, previous, current, engine_id):
            if engine_id is None:
                return dash.no_update
            
            removed_signal_detectors = [row for row in previous if row not in current]
            if not removed_signal_detectors:
                return dash.no_update
    
            assert len(removed_signal_detectors) == 1
            removed_sd = removed_signal_detectors[0]
            signal_detector_id = detector_handlers[removed_sd['name']].get_id(removed_sd['config'])
            new_engine_id = api.remove_signal_detector(engine_id, signal_detector_id, client)

            if new_engine_id is None:
                return dash.no_update
            return new_engine_id
    
        for sd in get_api_supported_signal_detectors(client):
            if sd not in detector_handlers.keys():
                logger.warning(f"{sd} signal detector is not implemented in the stock market visualizer")
    
        for sd in detector_handlers.keys():
            if sd not in get_api_supported_signal_detectors(client):
                logger.warning(f"{sd} signal detector is implemented in the stock market visualizer, but not supported by the engine")            
    
        for _, l in detector_handlers.items():
            register_dropdown_callback(l)