from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

from stock_market_visualizer.app.layouts.indicator_layout import get_indicator_table_layout
from stock_market_visualizer.app.layouts.signal_layout import get_signal_layout
from stock_market_visualizer.app.date import DateLayout
from stock_market_visualizer.app.engine import EngineLayout
from stock_market_visualizer.app.graph import GraphLayout
from stock_market_visualizer.app.header import HeaderLayout
from stock_market_visualizer.app.ticker import TickerLayout
from stock_market_visualizer.app.callbacks import register_callbacks as rc

class Layout:
    def __init__(self):
        self.engine_layout = EngineLayout()
        self.header_layout = HeaderLayout()
        self.ticker_layout = TickerLayout(self.engine_layout)
        self.date_layout = DateLayout(self.engine_layout, self.ticker_layout)
        self.graph_layout = GraphLayout(self.engine_layout, self.date_layout)

    def get_themes(self):
        return [dbc.themes.BOOTSTRAP]

    def get_layout(self):
        return dbc.Container(children=
            [
            dcc.Location(id='url', refresh=False),
            dcc.Store(id='restoreable-state'),
            self.header_layout.get_layout(),
            dbc.Container(
                [
                 dbc.Row(
                    self.date_layout.get_layout() +
                    [
                    dbc.Col(self.ticker_layout.get_layout()),
                    dbc.Col(get_indicator_table_layout())
                    ]),
                 dbc.Row(self.graph_layout.get_layout()),
                 dbc.Row(children=get_signal_layout())
            ]),
            self.engine_layout.get_layout()
            ])

    def register_callbacks(self, app, client_getter, redis_getter):
        rc(app, client_getter, redis_getter)
        self.header_layout.register_callbacks(app)
        self.date_layout.register_callbacks(app, client_getter)
        self.graph_layout.register_callbacks(app, client_getter)
        self.ticker_layout.register_callbacks(app, client_getter)