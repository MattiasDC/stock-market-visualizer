import dash
from dash_extensions.enrich import Output, Input, State

import stock_market_visualizer.app.sme_api_helper as api
from .callback_helper import CallbackHelper

def register_ticker_callbacks(app, client_getter, redis_getter):
    callback_helper = CallbackHelper(client_getter, redis_getter)

    @app.callback(
        Input('show-ticker-table', 'value'),
        Output('collapse-ticker-table', 'is_open'))
    def toggle_collapse_ticker_table(show_ticker_table):
        return 'S' in show_ticker_table

    @app.callback(
        Output('ticker-table', 'data'),
        Output('add-ticker-input', 'value'),
        Output('engine-id', 'data'),
        Output('stock-market-graph', 'figure'),
        Input('add-ticker-button', 'n_clicks'),
        Input('add-ticker-input', 'n_submit'),
        State('add-ticker-input', 'value'),
        State('engine-id', 'data'),
        State('ticker-table', 'data'),
        State('date-picker-end', 'date'),
        State('indicator-table', 'data'))
    def add_ticker(n_clicks, n_submit, ticker_symbol, engine_id, rows, end_date, indicator_rows):
        ticker_symbol = str.upper(ticker_symbol.rstrip())
        no_update = (dash.no_update, "", dash.no_update, dash.no_update) 
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

        rows = [{'ticker-col' : ticker} for ticker in api.get_tickers(engine_id, client)]
        api.update_engine(engine_id, end_date, client)
        indicators = callback_helper.get_configured_indicators(indicator_rows)
        return rows, "", engine_id, callback_helper.get_traces_and_layout(engine_id, indicators)
    
    @app.callback(
        Output('stock-market-graph', 'figure'),
        Output('engine-id', 'data'),
        Output('ticker-table', 'data'),
        Input('ticker-table', 'data_previous'),
        State('ticker-table', 'data'),
        State('engine-id', 'data'),
        State('indicator-table', 'data'))
    def remove_ticker(previous, current, engine_id, indicator_rows):
        if previous is None:
            return dash.no_update
    
        if engine_id is None:
            return dash.no_update
    
        removed_ticker_symbols = [row for row in previous if row not in current]
        assert len(removed_ticker_symbols) == 1
        ticker_symbol = next(iter(removed_ticker_symbols[0].values()))
        
        client = callback_helper.get_client()
        engine_id = api.remove_ticker(engine_id, ticker_symbol, client)
        if engine_id is None:
            return dash.no_update
    
        rows = [{'ticker-col' : ticker} for ticker in api.get_tickers(engine_id, client)]
        indicators = callback_helper.get_configured_indicators(indicator_rows)
        return callback_helper.get_traces_and_layout(engine_id, indicators), engine_id, rows