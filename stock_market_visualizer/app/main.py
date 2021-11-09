import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import datetime as dt
from fastapi import FastAPI
from http import HTTPStatus
from starlette.middleware.wsgi import WSGIMiddleware
import plotly.graph_objects as go
import pandas as pd
import uvicorn as uvicorn
from dash_extensions.enrich import Output, DashProxy, Input, MultiplexerTransform

from stock_market_engine.core import Engine
from stock_market_engine.common.factory import Factory
from stock_market_engine.ext.signal import register_signal_detector_factories 
from stock_market_engine.ext.updater import register_stock_updater_factories 

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.redis_helper import init_redis_pool
from stock_market_visualizer.app.sme_api_helper import get_create_url, get_create_engine_json
from stock_market_visualizer.common.requests import ClientSessionGenerator

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


def get_signal_detector_factory():
    return register_signal_detector_factories(Factory())

def get_stock_updater_factory():
    return register_stock_updater_factories(Factory())

def get_engine(engine_id, redis):
    if engine_id is None:
        return None
    engine_json = redis.get(engine_id)
    if engine_json is None:
        return None
    return Engine.from_json(engine_json, get_stock_updater_factory(), get_signal_detector_factory())

def from_sdate(date):
    if isinstance(date, str):
        date = dt.date.fromisoformat(date)
    return date

def get_traces(engine):
    traces = []
    for ticker in engine.stock_market.tickers:
        ohlc = engine.stock_market.ohlc(ticker)
        if ohlc is not None:
            traces.append(dict(
                type="scatter",
                x=ohlc.close.dates,
                y=ohlc.close.values,
                name=ticker.symbol,
                mode="lines"))
    return traces

def create_engine(start_date, tickers):
    client = server.state.client_generator.get()
        
    data = get_create_engine_json(start_date, tickers)
    response = client.post(url=get_create_url(), data=data)
    if response.status_code != HTTPStatus.OK:
        return None

    return response.text.strip("\"")

@app.callback(
    Output('engine-id', 'data'),
    Output('date-picker-end', 'date'),
    Output('stock-market-graph', 'figure'),
    Input('date-picker-start', 'date'),
    Input('date-picker-end', 'min_date_allowed'),
    Input('date-picker-end', 'date'),
    Input('engine-id', 'data'))
def update_engine(start_date, min_end_date, end_date, engine_id):
    if start_date is None:
        return dash.no_update
    if end_date is None:
        return dash.no_update

    start_date = from_sdate(start_date)
    min_end_date = from_sdate(min_end_date)
    end_date = from_sdate(end_date)
    end_date = min(end_date, dt.datetime.now().date())

    if end_date < min_end_date:
        return dash.no_update

    tickers = ["QQQ", "SPY"]
    if engine_id is None:
        engine_id = create_engine(start_date, tickers)
    if engine_id is None:
        return dash.no_update

    redis = server.state.redis
    engine = get_engine(engine_id, redis)
    if engine is None:
        return dash.no_update
    if engine.stock_market.start_date != start_date:
        engine_id = create_engine(start_date, tickers)
        if engine_id is None:
            return dash.no_update
        engine = get_engine(engine_id, redis)
    
    engine.update(end_date)
    return engine_id, end_date, dict(data=get_traces(engine))

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