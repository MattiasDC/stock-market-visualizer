import dash
from dash import dcc
from dash import html
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import plotly.express as px
import pandas as pd
import uvicorn as uvicorn
from stock_market_visualizer.app.config import get_settings

app = dash.Dash(__name__, requests_pathname_prefix="/dash/")
server = FastAPI()
server.mount("/dash", WSGIMiddleware(app.server))

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
df = pd.DataFrame({
    "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
    "Amount": [4, 1, 2, 2, 4, 5],
    "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
})

fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

app.layout = html.Div(children=[
    html.H1(children='Stock Market Engine'),

    html.Div(children='''
        Dash: A web application framework for your data.
    '''),

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    settings = get_settings()
    uvicorn.run("main:server",
                host=settings.host_url,
                port=settings.port,
                reload=settings.debug,
                log_level='warning',
                use_colors=True)