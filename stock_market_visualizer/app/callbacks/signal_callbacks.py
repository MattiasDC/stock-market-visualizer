import dash
from dash import dcc
from dash import html
from dash_extensions.enrich import Output, Input, State
import json
from random import randrange

from utils.logging import get_logger

import stock_market_visualizer.app.callbacks.checkable_table_dropdown_callbacks as checkable_table
from stock_market_visualizer.app.callbacks.callback_helper import CallbackHelper
from stock_market_visualizer.app.config import get_settings
import stock_market_visualizer.app.sme_api_helper as api
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
        self.__active_ticker = None

        @self.__app.callback(
            Output(f'config-dropdown-ticker-{self.name()}', 'options'),
            Output(f'config-dropdown-ticker-{self.name()}', 'value'),
            Input('engine-id', 'data'),
            State(f'config-dropdown-ticker-{self.name()}', 'value'))
        def update_dropdown_list(engine_id, value):
            options = self.__get_options(engine_id)
            if len(options) == 1:
                value = options[0]['value']
            return options, value

        @self.__app.callback(
            Input(f'config-dropdown-ticker-{self.name()}', 'value'),
            Output('signal-data-placeholder', 'data'))
        def update_active_ticker(ticker_value):
            return ticker_value

    def name(self):
        return self.__detector_cls.NAME()

    def __get_options(self, engine_id):
        tickers = api.get_tickers(engine_id, self.__client)
        return [{'label': t, 'value': t} for t in tickers]

    def activate(self, engine_id):
        if engine_id is None:
            return None
        return engine_id

    def create(self, engine_id, data):
        new_engine_id = api.add_signal_detector(engine_id,
                                            {"static_name" : self.name(),
                                             "config" : json.dumps({"id" : randrange(get_settings().max_id_generator),
                                                                    "ticker" : json.dumps(data)})},
                                            self.__client)
        api.update_engine(new_engine_id, api.get_date(new_engine_id, self.__client), self.__client)
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

    @app.callback(
        Output('signal-edit-placeholder', 'hidden'),
        Input(f'collapse-signal-table', 'is_open'),
        State('signal-edit-legend', 'children'))
    def hide_edit_fieldset(is_open, name):
        return not is_open or name in [h.name() for h in trivial_handlers]

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
            Input(f'dropdown-{handler.name()}', 'n_clicks'),
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
                name = child_props['id']
                if 'signal-edit-legend' == name:
                    child_props['children'] = handler.name()
                if 'config-' in name:
                    child_props['hidden'] = True
                if handler.name() in name.replace('config-', ''):
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

    for _, l in detector_handlers.items():
        register_dropdown_callback(l)