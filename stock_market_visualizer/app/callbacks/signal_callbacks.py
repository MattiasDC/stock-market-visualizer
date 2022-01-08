import dash
from dash import dcc
from dash import html
from dash_extensions.enrich import Output, Input, State
import json
from random import randrange

from utils.logging import get_logger
from stock_market.ext.indicator import Identity
from stock_market.ext.signal import CrossoverSignalDetector

import stock_market_visualizer.app.callbacks.checkable_table_dropdown_callbacks as checkable_table
from stock_market_visualizer.app.callbacks.callback_helper import CallbackHelper
from stock_market_visualizer.app.config import get_settings
import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.indicators import get_indicators_with_identity
from stock_market_visualizer.app.signals import get_signal_detectors,\
                                                get_supported_trivial_config_signal_detectors,\
                                                get_supported_ticker_based_signal_detectors

logger = get_logger(__name__)

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
        api.update_engine(engine_id, api.get_date(engine_id, self.__client), self.__client)
        return engine_id

    def get_id(self, config):
        return config

class TickerBasedDetectorHandler:
    def __init__(self, app, client, detector_cls):
        self.__app = app
        self.__client = client
        self.__detector_cls = detector_cls

        @self.__app.callback(
            Output(f'config-dropdown-ticker-{self.id()}', 'options'),
            Output(f'config-dropdown-ticker-{self.id()}', 'value'),
            Input('engine-id', 'data'),
            State(f'config-dropdown-ticker-{self.id()}', 'value'))
        def update_dropdown_list(engine_id, value):
            options = self.__get_options(engine_id)
            if len(options) == 1:
                value = options[0]['value']
            return options, value

        @self.__app.callback(
            Input(f'config-dropdown-ticker-{self.id()}', 'value'),
            State('signal-data-placeholder', 'data'),
            Output('signal-data-placeholder', 'data'))
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
        api.update_engine(new_engine_id, api.get_date(new_engine_id, self.__client), self.__client)
        return new_engine_id

    def get_id(self, config):
        return json.loads(config)['id']

class CrossoverDetectorHandler(TickerBasedDetectorHandler):
    def __init__(self, app, client):
        super().__init__(app, client, CrossoverSignalDetector)

        indicators = get_indicators_with_identity()
        for indicator in api.get_supported_indicators(client):
            if indicator['indicator_name'] not in [i.__name__ for i in indicators.keys()]:
                logger.warning(f"{indicator} is not implemented in the stock market visualizer")

        for indicator in indicators.keys():
            if indicator.__name__ not in [i['indicator_name'] for i in api.get_supported_indicators(client)]:
                logger.warning(f"{indicator} is implemented in the stock market visualizer, but not supported by the engine")

        for indicator in indicators:
            self.add_create_indicator_callbacks("Responsive", indicator, indicators[indicator])
            if indicator != Identity:
                self.add_create_indicator_callbacks("Unresponsive", indicator, indicators[indicator])

        @app.callback(Input(f'{self.name()}-custom-name', 'value'),
                      State('signal-data-placeholder', 'data'),
                      Output('signal-data-placeholder', 'data'))
        def update_custom_name(custom_name, data):
            data['name'] = custom_name
            return data

        @app.callback(Input(f'{self.name()}-sentiment', 'value'),
                      State('signal-data-placeholder', 'data'),
                      Output('signal-data-placeholder', 'data'))
        def update_custom_name(sentiment, data):
            data['sentiment'] = sentiment
            return data        

    def add_create_indicator_callbacks(self, name, indicator, arguments):
        if indicator != Identity:
            @self.app().callback(Input(f'dropdown-{name}-{indicator.__name__}', 'n_clicks'),
                                 Output(f'modal-{name}-{indicator.__name__}', 'is_open'))
            def create_indicator_form(n_clicks):
                if n_clicks == 0 or None:
                    return False
                return True
    
            @self.app().callback(Input(f'add-{name}-{indicator.__name__}', 'n_clicks'),
                                 State('signal-data-placeholder', 'data'),
                                 [State(f'{name}-{indicator.__name__}-{argument}-input', 'value') for argument in arguments],
                                 Output(f'modal-{name}-{indicator.__name__}', 'is_open'),
                                 Output('signal-data-placeholder', 'data'),
                                 Output(f'{name}-info', 'children'))
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
            @self.app().callback(Input(f'dropdown-{name}-{indicator.__name__}', 'n_clicks'),
                                 State('signal-data-placeholder', 'data'),
                                 Output('signal-data-placeholder', 'data'),
                                 Output(f'{name}-info', 'children'))
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
        api.update_engine(new_engine_id, api.get_date(new_engine_id, self.client()), self.client())
        return new_engine_id

    def get_id(self, config):
        return json.loads(config)['id']

def register_signal_callbacks(app, client_getter):
    callback_helper = CallbackHelper(client_getter)

    checkable_table.register_callbacks(app, 'signal')

    client = callback_helper.get_client()
    trivial_handlers = [EmptyDetectorHandler(client, sd.NAME()) for sd in get_supported_trivial_config_signal_detectors()]
    ticker_based_sds = [TickerBasedDetectorHandler(app, client, sd) for sd in get_supported_ticker_based_signal_detectors()]
    detector_handlers = {l.name() : l for l in trivial_handlers + ticker_based_sds}
    
    crossover_handler = CrossoverDetectorHandler(app, client)
    detector_handlers[crossover_handler.name()] = crossover_handler

    @app.callback(
        Output('signal-edit-placeholder', 'hidden'),
        Input(f'collapse-signal-table', 'is_open'),
        State('signal-edit-legend', 'children'))
    def hide_edit_fieldset(is_open, name):
        return not is_open or name in [h.name() for h in trivial_handlers] or len(name) == 0

    @app.callback(
        Output('signal-table', 'data'),
        Input('engine-id', 'data'))
    def update_signal_table(engine_id):
        client = callback_helper.get_client()
        return [{'signal-col' : signal_detector['name'],
                 'name' : signal_detector['static_name'],
                 'config' : json.dumps(signal_detector['config'])}
                for signal_detector in api.get_signal_detectors(engine_id, client)]

    @app.callback(
        Output('engine-id', 'data'),
        Output('signal-edit-placeholder', 'hidden'),
        Output('signal-table', 'selected_rows'),
        Input('signal-add', 'n_clicks'),
        State('engine-id', 'data'),
        State('signal-edit-legend', 'children'),
        State('signal-data-placeholder', 'data'),
        State('signal-table', 'selected_rows'))
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
            Output('engine-id', 'data'),
            Output('signal-edit-fieldset', 'children'),
            Output('signal-edit-placeholder', 'hidden'),
            Output('signal-table', 'selected_rows'),
            Input(f'dropdown-signal-{handler.id()}', 'n_clicks'),
            State('signal-edit-fieldset', 'children'),
            State('engine-id', 'data'),
            State('signal-table', 'selected_rows'))
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
            Output('engine-id', 'data'),
            Input('signal-table', 'data_timestamp'),
            State('signal-table', 'data_previous'),
            State('signal-table', 'data'),
            State('engine-id', 'data'))
        def remove_signal_detector(timestamp, previous, current, engine_id):
            if engine_id is None:
                return dash.no_update
        
            removed_signal_detectors = [row for row in previous if row not in current]
            if not removed_signal_detectors:
                return dash.no_update

            assert len(removed_signal_detectors) == 1
            removed_sd = removed_signal_detectors[0]
            signal_detector_id = detector_handlers[removed_sd['name']].get_id(removed_sd['config'])
            client = callback_helper.get_client()
            engine_id = api.remove_signal_detector(engine_id, signal_detector_id, client)
            if engine_id is None:
                return dash.no_update
    
            return engine_id

    for sd in get_signal_detectors(client):
        if sd not in detector_handlers.keys():
            logger.warning(f"{sd} signal detector is not implemented in the stock market visualizer")

    for sd in detector_handlers.keys():
        if sd not in get_signal_detectors(client):
            logger.warning(f"{sd} signal detector is implemented in the stock market visualizer, but not supported by the engine")            

    for _, l in detector_handlers.items():
        register_dropdown_callback(l)