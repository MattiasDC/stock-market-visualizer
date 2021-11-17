import dash
from dash_extensions.enrich import Output, Input, State
import datetime as dt

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.common.utils import from_sdate
from .callback_helper import CallbackHelper

def register_date_callbacks(app, client_getter, redis_getter):
    callback_helper = CallbackHelper(client_getter, redis_getter)

    @app.callback(
        Output('date-picker-end', 'min_date_allowed'),
        Input('date-picker-start', 'date'))
    def update_min_date_allowed(start_date):
        if start_date is None:
            return dash.no_update
        return start_date

    @app.callback(
        Output('engine-id', 'data'),
        Output('date-picker-end', 'date'),
        Output('stock-market-graph', 'figure'),
        Input('date-picker-start', 'date'),
        Input('date-picker-end', 'date'),
        State('date-picker-end', 'min_date_allowed'),
        State('engine-id', 'data'),
        State('ticker-table', 'data'),
        State('indicator-table', 'data'))
    def update_engine(start_date, end_date, min_end_date, engine_id, ticker_rows, indicator_rows):
        start_date = from_sdate(start_date)
        min_end_date = from_sdate(min_end_date)
        end_date = from_sdate(end_date)
    
        if start_date is None:
            return dash.no_update
        if end_date is None:
            return dash.no_update
    
        end_date = min(end_date, dt.datetime.now().date())
    
        if end_date < min_end_date:
            return dash.no_update
    
        client = callback_helper.get_client()
        tickers = callback_helper.get_tickers(ticker_rows)
        if engine_id is None:
            engine_id = api.create_engine(start_date, tickers, client)
        if engine_id is None:
            return dash.no_update
    
        engine_start_date = api.get_start_date(engine_id, client)
        if engine_start_date is None:
            return dash.no_update
    
        if engine_start_date != start_date:
            engine_id = api.create_engine(start_date, tickers, client)
            if engine_id is None:
                return dash.no_update
        
        api.update_engine(engine_id, end_date, client)
        indicators = callback_helper.get_configured_indicators(indicator_rows)
        return engine_id, end_date, callback_helper.get_traces_and_layout(engine_id, indicators)