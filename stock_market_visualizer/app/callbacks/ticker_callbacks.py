import dash
from dash_extensions.enrich import Output, Input, State

import stock_market_visualizer.app.callbacks.checkable_table_dropdown_callbacks as checkable_table
import stock_market_visualizer.app.sme_api_helper as api
from .callback_helper import CallbackHelper

def register_ticker_callbacks(app, client_getter):
    callback_helper = CallbackHelper(client_getter)

    checkable_table.register_callbacks(app, 'ticker')

    @app.callback(
        Output('ticker-table', 'data'),
        Input('engine-id', 'data'))
    def update_ticker_table(engine_id):
        client = callback_helper.get_client()
        return [{'ticker-col' : ticker} for ticker in api.get_tickers(engine_id, client)]

    @app.callback(
        Output('add-ticker-input', 'value'),
        Output('engine-id', 'data'),
        Input('add-ticker-button', 'n_clicks'),
        Input('add-ticker-input', 'n_submit'),
        State('add-ticker-input', 'value'),
        State('engine-id', 'data'),
        State('ticker-table', 'data'),
        State('date-picker-end', 'date'))
    def add_ticker(n_clicks, n_submit, ticker_symbol, engine_id, rows, end_date):
        ticker_symbol = str.upper(ticker_symbol.rstrip())
        no_update = (dash.no_update, dash.no_update) 
        if ticker_symbol in callback_helper.get_tickers(rows) or not ticker_symbol:
            return no_update
    
        if n_clicks == 0 and n_submit == 0:
            return no_update
        
        if engine_id is None:
            return no_update

        client = callback_helper.get_client()
        engine_id = api.add_ticker(engine_id, ticker_symbol, client)
        if engine_id is None:
            return no_update

        api.update_engine(engine_id, end_date, client)
        return "", engine_id
    
    @app.callback(
        Output('engine-id', 'data'),
        Input('ticker-table', 'data_timestamp'),
        State('ticker-table', 'data_previous'),
        State('ticker-table', 'data'),
        State('engine-id', 'data'))
    def remove_ticker(timestamp, previous, current, engine_id):
        if previous is None:
            return dash.no_update
    
        if engine_id is None:
            return dash.no_update
    
        removed_ticker_symbols = [row for row in previous if row not in current]
        if not removed_ticker_symbols:
            return dash.no_update
        
        assert len(removed_ticker_symbols) == 1
        ticker_symbol = next(iter(removed_ticker_symbols[0].values()))
        
        client = callback_helper.get_client()
        engine_id = api.remove_ticker(engine_id, ticker_symbol, client)
        if engine_id is None:
            return dash.no_update
    
        return engine_id