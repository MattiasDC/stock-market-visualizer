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
from stock_market_visualizer.common.requests import ClientSessionGenerator, concat_port
from stock_market_visualizer.common.sync_wrapper import sync_wrapper

app = dash.Dash(__name__, requests_pathname_prefix="/sme/")
server = FastAPI()
server.mount("/sme", WSGIMiddleware(app.server))

app.layout = html.Div(children=[
    html.H1(children='Stock Market Engine'),
     dcc.DatePickerRange(
        id='start-date',
        min_date_allowed=dt.date(1990, 1, 1),
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
@sync_wrapper
async def update_start_date(date_value):
    settings = get_settings()
    client = await server.state.client_generator.get()
    url = concat_port(settings.api_url, port=settings.api_port) + "/create"
    print(url)
    response = await client.post(url)
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