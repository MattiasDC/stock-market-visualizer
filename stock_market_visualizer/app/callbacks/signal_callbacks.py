import dash
from dash_extensions.enrich import Output, Input, State
from random import randrange

from stock_market.ext.signal import MonthlySignalDetector,\
                                    BiMonthlySignalDetector,\
                                    GoldenCrossSignalDetector,\
                                    DeathCrossSignalDetector
from utils.logging import get_logger

import stock_market_visualizer.app.callbacks.checkable_table_dropdown_callbacks as checkable_table
from stock_market_visualizer.app.callbacks.callback_helper import CallbackHelper
import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.signals import get_signal_detectors

logger = get_logger(__name__)

class EmptyDetectorHandler:
    def __init__(self, client, detector_cls):
        self.__client = client
        self.__detector_cls = detector_cls

    def name(self):
        return self.__detector_cls.NAME()

    def create(self, engine_id):
        if engine_id is None:
            return [], dash.no_update
        engine_id = api.add_signal_detector(engine_id, {"name" : self.name(),
                                                        "config" : str(randrange(10000000))}, self.__client)
        return [], engine_id

    def get_id(self, config):
        return config

def register_signal_callbacks(app, client_getter):
    callback_helper = CallbackHelper(client_getter)

    checkable_table.register_callbacks(app, 'signal')

    client = callback_helper.get_client()
    detector_handler = {l.name() : l for l in [EmptyDetectorHandler(client, MonthlySignalDetector),
                                               EmptyDetectorHandler(client, BiMonthlySignalDetector)]}

    @app.callback(
        Output('signal-table', 'data'),
        Input('engine-id', 'data'))
    def update_signal_table(engine_id):
        client = callback_helper.get_client()
        return [{'signal-col' : signal_detector['name'],
                 'config' : str(signal_detector['config'])}
                for signal_detector in api.get_signal_detectors(engine_id, client)]

    def register_dropdown_callback(layouter):
        @app.callback(
        	Output('signal-edit-placeholder', 'children'),
            Output('engine-id', 'data'),
            Input(f'dropdown-{layouter.name()}', 'n_clicks'),
            State(f'signal-table', 'data'),
            State(f'engine-id', 'data'),
            State('date-picker-end', 'date'))
        def add_signal_detector(clicks, table, engine_id, end_date):
            if clicks == 0:
                return dash.no_update, dash.no_update
            children, engine_id = layouter.create(engine_id)
            if engine_id is not None:
                api.update_engine(engine_id, end_date, client)
            return children, engine_id

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
            signal_detector_id = detector_handler[removed_sd['signal-col']].get_id(removed_sd['config'])
            client = callback_helper.get_client()
            engine_id = api.remove_signal_detector(engine_id, signal_detector_id, client)
            if engine_id is None:
                return dash.no_update
    
            return engine_id

    for sd in get_signal_detectors(client):
        if sd not in detector_handler.keys():
            logger.warning(f"{sd} signal detector is not implemented in the stock market visualizer")

    for _, l in detector_handler.items():
        register_dropdown_callback(l)