import dash
from dash_extensions.enrich import Output, Input, State
import datetime as dt

from utils.dateutils import from_sdate
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from .callback_helper import CallbackHelper

def register_graph_callbacks(app, client_getter):
    callback_helper = CallbackHelper(client_getter)

    @app.callback(
        Input('indicator-table', 'data'),
        Input('engine-id', 'data'),
        Output('stock-market-graph', 'figure'))
    def change(rows, engine_id):
        indicators = callback_helper.get_configured_indicators(rows)
        return callback_helper.get_traces_and_layout(engine_id, indicators)

    @app.callback(
        Output('stock-market-graph', 'figure'),
        Input('update-interval', 'n_intervals'),
        State('date-picker-end', 'date'),
        State('engine-id', 'data'),
        State('indicator-table', 'data'))
    def update_on_interval(n_intervals, end_date, engine_id, indicator_rows):
        end_date = from_sdate(end_date) 
        if end_date is None or end_date < dt.datetime.now().date():
            return dash.no_update
        
        logger.info("Interval callback triggered: updating engine")
        client = callback_helper.get_client()
        api.update_engine(engine_id, end_date, client)
        indicators = callback_helper.get_configured_indicators(indicator_rows)
        return callback_helper.get_traces_and_layout(engine_id, indicators)