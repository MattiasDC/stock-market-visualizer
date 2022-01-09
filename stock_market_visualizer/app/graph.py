import dash
from dash import dcc
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Output, Input, State
import datetime as dt

from utils.dateutils import from_sdate
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.callbacks.callback_helper import CallbackHelper
from stock_market_visualizer.app.interval import IntervalLayout

logger = get_logger(__name__)

class GraphLayout:
    def __init__(self, engine_layout, date_layout):
        self.engine_layout = engine_layout
        self.date_layout = date_layout
        self.interval_layout = IntervalLayout()
        self.stock_market_graph = 'stock-market-graph'

    def get_layout(self):
        return dbc.Col(dbc.Container([dcc.Graph(id=self.stock_market_graph), self.interval_layout.get_layout()]))

    def get_graph(self):
        return self.stock_market_graph, 'figure'

    def register_callbacks(self, app, client_getter):
        helper = CallbackHelper(client_getter)

        @app.callback(
            Output(*self.get_graph()),
            Input('indicator-table', 'data'),
            Input(*self.engine_layout.get_id()),
            Input('ticker-table', 'selected_rows'),
            Input('indicator-table', 'selected_rows'),
            Input('signal-table', 'selected_rows'))
        def change(rows,
                   engine_id,
                   selected_ticker_rows,
                   selected_indicator_rows,
                   selected_signal_rows):
            indicators = helper.get_configured_indicators(rows, selected_indicator_rows)
            return helper.get_traces_and_layout(engine_id,
                                                indicators,
                                                selected_ticker_rows,
                                                selected_signal_rows)

        @app.callback(
            Output(*self.get_graph()),
            Input(*self.interval_layout.get_interval()),
            State(*self.date_layout.get_end_date()),
            State(*self.engine_layout.get_id()),
            State('indicator-table', 'data'),
            State('ticker-table', 'selected_rows'),
            State('indicator-table', 'selected_rows'),
            State('signal-table', 'selected_rows'))
        def update_on_interval(n_intervals,
                               end_date,
                               engine_id,
                               indicator_rows,
                               selected_ticker_rows,
                               selected_indicator_rows,
                               selected_signal_rows):
            end_date = from_sdate(end_date) 
            now = dt.datetime.now()
            # We still want to update on interval if we just crossed a day
            if end_date is None or\
              now - dt.datetime.combine(end_date, dt.time()) > dt.timedelta(days=1,
                                                                            minutes=1,
                                                                            seconds=get_settings().update_interval):
                return dash.no_update
            
            logger.info("Interval callback triggered: updating engine")
            client = helper.get_client()
            api.update_engine(engine_id, end_date, client)
            indicators = helper.get_configured_indicators(indicator_rows, selected_indicator_rows)
            return helper.get_traces_and_layout(engine_id,
                                                indicators,
                                                selected_ticker_rows,
                                                selected_signal_rows)