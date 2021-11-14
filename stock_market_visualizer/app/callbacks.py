import datetime as dt
from dash_extensions.enrich import Output, Input, State

from stock_market_engine.core import OHLC
from stock_market_engine.core.time_series import make_relative

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.common.logging import get_logger
from stock_market_visualizer.common.utils import from_sdate

logger = get_logger(__name__)

def register_callbacks(app, server):
    def get_traces(engine_id, client):
        tickers = api.get_tickers(engine_id, client)
        if len(tickers) == 0:
            return []
    
        closes = {}
        redis = server.state.redis
        for ticker in tickers:
            ohlc_id = api.get_ticker_ohlc(engine_id, ticker, client)
            if ohlc_id is None:
                continue
    
            ohlc_json = redis.get(ohlc_id)
            if ohlc_json is None:
                logger.warning(f"OHLC with id '{ohlc_id}' could not be found in redis database!")
                continue
            closes[ticker] = OHLC.from_json(ohlc_json).close
    
        if len(closes) > 1:
            relative_closes = zip(closes.keys(), make_relative(closes.values()))
            return [dict(type="scatter",
                         x=relative_close.dates,
                         y=relative_close.values-1,
                         name=ticker,
                         mode="lines") for ticker, relative_close in relative_closes]
    
        return [dict(type="scatter",
                     x=close.dates,
                     y=close.values,
                     name=ticker,
                     mode="lines") for ticker, close in closes.items()]
    
    def get_traces_and_layout(engine_id, client):
        traces = get_traces(engine_id, client)
        layout = {}
        if len(traces) > 1:
            layout['yaxis'] = dict(tickformat=',.1%')
        return dict(data=traces, layout=layout)
    
    def get_tickers(rows):
        return list(map(lambda row: next(iter(row.values())), rows))

    @app.callback(
        Output('engine-id', 'data'),
        Output('date-picker-end', 'date'),
        Output('stock-market-graph', 'figure'),
        Input('date-picker-start', 'date'),
        Input('date-picker-end', 'date'),
        State('date-picker-end', 'min_date_allowed'),
        State('engine-id', 'data'),
        State('ticker-table', 'data'))
    def update_engine(start_date, end_date, min_end_date, engine_id, rows):
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
    
        client = server.state.client_generator.get()
        tickers = get_tickers(rows)
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
        return engine_id, end_date, get_traces_and_layout(engine_id, client)
    
    @app.callback(
        Output('date-picker-end', 'min_date_allowed'),
        Input('date-picker-start', 'date'))
    def update_min_date_allowed(start_date):
        if start_date is None:
            return dash.no_update
        return start_date
    
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
        State('date-picker-end', 'date'))
    def add_ticker(n_clicks, n_submit, ticker_symbol, engine_id, rows, end_date):
        ticker_symbol = str.upper(ticker_symbol)
        if ticker_symbol in get_tickers(rows) or not ticker_symbol:
            return dash.no_update, "", dash.no_update, dash.no_update
    
        if n_clicks == 0 and n_submit == 0:
            return dash.no_update, "", dash.no_update, dash.no_update
        
        rows.append({'ticker-col' : ticker_symbol})
    
        if engine_id is None:
            return rows, "", dash.no_update, dash.no_update
    
        client = server.state.client_generator.get()
        engine_id = api.add_ticker(engine_id, ticker_symbol, client)
        api.update_engine(engine_id, end_date, client)
        if engine_id is None:
            return rows, "", dash.no_update, dash.no_update
    
        return rows, "", engine_id, get_traces_and_layout(engine_id, client)
    
    @app.callback(Output('stock-market-graph', 'figure'),
                  Output('engine-id', 'data'),
                  Input('ticker-table', 'data_previous'),
                  State('ticker-table', 'data'),
                  State('engine-id', 'data'))
    def remove_ticker(previous, current, engine_id):
        if previous is None:
            return dash.no_update
    
        if engine_id is None:
            return dash.no_update
    
        removed_ticker_symbols = [row for row in previous if row not in current]
        assert len(removed_ticker_symbols) == 1
        ticker_symbol = next(iter(removed_ticker_symbols[0].values()))
    
        client = server.state.client_generator.get()
        engine_id = api.remove_ticker(engine_id, ticker_symbol, client)
        if engine_id is None:
            return dash.no_update
    
        return dict(data=get_traces(engine_id, client)), engine_id