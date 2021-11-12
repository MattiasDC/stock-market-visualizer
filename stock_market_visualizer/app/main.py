import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import datetime as dt
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import plotly.graph_objects as go
import pandas as pd
import uvicorn as uvicorn
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform

from stock_market_engine.core.ohlc import OHLC

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.redis_helper import init_redis_pool
import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.common.logging import get_logger
from stock_market_visualizer.common.requests import ClientSessionGenerator

logger = get_logger(__name__)

app = DashProxy(__name__,
                requests_pathname_prefix="/sme/",
                prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Stock Market Engine"

server = FastAPI()
server.mount("/sme", WSGIMiddleware(app.server))

earliest_start = dt.date(1990, 1, 1)

app.layout = dbc.Container(children=[
    html.H1(children='Stock Market Engine'),
    dbc.Container(
        [
             dbc.Row(
                [
                    dbc.Col(
                        [
                            html.P("Start"),
                            dcc.DatePickerSingle(
                                id='date-picker-start',
                                min_date_allowed=earliest_start,
                                max_date_allowed=dt.datetime.now().date() - dt.timedelta(days=1),
                                placeholder='Start Date',
                                display_format='D-M-Y')
                        ]),
                    dbc.Col(
                        [
                            html.P("End"),
                            dcc.DatePickerSingle(
                                id='date-picker-end',
                                min_date_allowed=earliest_start+dt.timedelta(days=1),
                                placeholder='End Date',
                                display_format='D-M-Y')
                        ])
                ])
        ]),
    dcc.Graph(id='stock-market-graph'),
    dcc.Store(id='engine-id')
])

@server.on_event("startup")
async def startup_event():
    server.state.client_generator = ClientSessionGenerator()
    server.state.redis = init_redis_pool()

def from_sdate(date):
    if date is None:
        return None
    if isinstance(date, str):
        try:
            date = dt.date.fromisoformat(date)
        except ValueError as e:
            logger.warning(e)
            return None
    return date

def get_traces(engine_id, client):
    tickers = api.get_tickers(engine_id, client)
    if len(tickers) == 0:
        logger.warning(f"No tickers could be found for engine with id '{engine_id}'")
        return

    traces = []
    redis = server.state.redis
    for ticker in tickers:
        ohlc_id = api.get_ticker_ohlc(engine_id, ticker, client)
        if ohlc_id is None:
            continue

        ohlc_json = redis.get(ohlc_id)
        if ohlc_json is None:
            logger.warning(f"OHLC with id '{ohlc_id}' could not be found in redis database!")
            continue
        ohlc = OHLC.from_json(ohlc_json)
        traces.append(dict(
            type="scatter",
            x=ohlc.close.dates,
            y=ohlc.close.values,
            name=ticker,
            mode="lines"))
    return traces

@app.callback(
    Output('engine-id', 'data'),
    Output('date-picker-end', 'date'),
    Output('stock-market-graph', 'figure'),
    Input('date-picker-start', 'date'),
    Input('date-picker-end', 'min_date_allowed'),
    Input('date-picker-end', 'date'),
    Input('engine-id', 'data'))
def update_engine(start_date, min_end_date, end_date, engine_id):
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
    tickers = ["QQQ", "SPY"]
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
    traces = get_traces(engine_id, client)
    return engine_id, end_date, dict(data=traces)

@app.callback(
    Output('date-picker-end', 'min_date_allowed'),
    Input('date-picker-start', 'date'))
def update_min_date_allowed(start_date):
    if start_date is None:
        return dash.no_update
    return start_date

if __name__ == '__main__':
    settings = get_settings()
    uvicorn.run("main:server",
                host=settings.host_url,
                port=settings.port,
                reload=settings.debug,
                log_level='warning',
                use_colors=True)