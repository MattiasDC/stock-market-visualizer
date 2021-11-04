import asyncio
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import datetime as dt
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import plotly.graph_objects as go
import pandas as pd
import uvicorn as uvicorn
from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.sme_api import get_create_url, get_create_engine_json
from stock_market_visualizer.common.requests import ClientSessionGenerator

app = dash.Dash(__name__, requests_pathname_prefix="/sme/")
server = FastAPI()
server.mount("/sme", WSGIMiddleware(app.server))

earliest_start = dt.date(1990, 1, 1)

app.layout = html.Div(children=[
    html.H1(children='Stock Market Engine'),
     dcc.DatePickerRange(
        id='start-date',
        min_date_allowed=earliest_start,
        max_date_allowed=dt.datetime.now().date()
    ),
    dcc.Graph(id='stock-market-graph')
])

@server.on_event("startup")
async def startup_event():
    server.state.client_generator = ClientSessionGenerator()

@app.callback(
    Output('stock-market-graph', 'figure'),
    Input('start-date', 'start_date'))
def update_start_date(start_date):
    if start_date is None:
        start_date = earliest_start
    settings = get_settings()
    client = server.state.client_generator.get()
    data = get_create_engine_json(dt.date.fromisoformat(start_date), ["SPY"])
    response = client.post(url=get_create_url(), data=data)
    fig = go.Scatter()
    return fig

if __name__ == '__main__':
    settings = get_settings()
    uvicorn.run("main:server",
                host=settings.host_url,
                port=settings.port,
                reload=settings.debug,
                log_level='warning',
                use_colors=True)