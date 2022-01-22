import datetime as dt
import json
from collections import defaultdict

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from dash_extensions.enrich import Input, Output, State
from stock_market.common.factory import Factory
from stock_market.core import OHLC, Sentiment
from stock_market.core.time_series import TimeSeries, make_relative
from stock_market.ext.indicator import register_indicator_factories
from stock_market.ext.signal import register_signal_detector_factories
from utils.dateutils import from_sdate
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.interval import IntervalLayout

logger = get_logger(__name__)


class GraphLayout:
    def __init__(self, engine_layout, date_layout):
        self.engine_layout = engine_layout
        self.date_layout = date_layout
        self.interval_layout = IntervalLayout()
        self.stock_market_graph = "stock-market-graph"
        self.layout = dbc.Col(
            dbc.Container(
                [
                    dcc.Graph(id=self.stock_market_graph),
                    self.interval_layout.get_layout(),
                ]
            )
        )

    def get_layout(self):
        return self.layout

    def get_graph(self):
        return self.stock_market_graph, "figure"

    def __get_configured_indicators(self, rows):
        factory = register_indicator_factories(Factory())
        indicators_per_ticker = defaultdict(list)
        for i, row in enumerate(rows):
            indicators_per_ticker[row["ticker-col"]].append(
                factory.create(row["indicator"]["name"], row["indicator"]["config"])
            )
        return indicators_per_ticker

    def __create_indicator_traces(
        self, indicators_per_ticker, ticker, ticker_values, figure
    ):
        for indicator in indicators_per_ticker[ticker]:
            for indicator_values in [
                indicator(
                    TimeSeries(
                        ticker,
                        pd.concat([ticker_values.dates, ticker_values.values], axis=1),
                    )
                )
            ]:
                figure.add_trace(
                    go.Scatter(
                        x=indicator_values.dates,
                        y=indicator_values.values,
                        name=indicator_values.name,
                        mode="lines",
                    )
                )

        return figure

    def __get_color(self, sentiment):
        if sentiment == Sentiment.NEUTRAL:
            return "grey"
        elif sentiment == Sentiment.BULLISH:
            return "green"
        assert sentiment == Sentiment.BEARISH
        return "red"

    def __get_signal_detectors(self, engine_id, client):
        signal_detector_factory = register_signal_detector_factories(Factory())
        signal_detector_ids = []
        for i, sd in enumerate(api.get_signal_detectors(engine_id, client)):
            config = sd["config"]
            if type(config) is not str:
                config = json.dumps(config)
            signal_detector = signal_detector_factory.create(sd["static_name"], config)
            signal_detector_ids.append(signal_detector.id)
        return signal_detector_ids

    def __get_signal_lines(self, engine_id, client, figure):
        signal_detector_ids = self.__get_signal_detectors(engine_id, client)
        signal_sequence = api.get_signals(engine_id, client)
        date_dict = defaultdict(list)
        for s in signal_sequence.signals:
            if s.id in signal_detector_ids:
                date_dict[s.date].append(s)

        for date, signals in date_dict.items():
            for s in signals[:-1]:
                figure.add_vline(
                    x=date,
                    line_color=self.__get_color(s.sentiment),
                )
            figure.add_vline(
                # https://github.com/plotly/plotly.py/issues/3065
                x=dt.datetime.combine(date, dt.time()).timestamp() * 1000,
                line_color=self.__get_color(signals[-1].sentiment),
                annotation_text=", ".join([s.name for s in signals]),
                annotation_position="top left",
                annotation_textangle=90,
            )
        return figure

    def __get_traces(self, client, engine_id, indicators, figure):
        tickers = api.get_tickers(engine_id, client)
        if len(tickers) == 0:
            return figure, 0

        closes = {}
        for ticker in tickers:
            ohlc_json = api.get_ticker_ohlc(engine_id, ticker, client)
            if ohlc_json is None:
                continue
            closes[ticker] = OHLC.from_json(ohlc_json).close

        if len(closes) > 1:
            closes = zip(closes.keys(), make_relative(closes.values()))
            closes = {
                ticker: TimeSeries(
                    ticker,
                    pd.concat(
                        [relative_close.dates, relative_close.values - 1], axis=1
                    ),
                )
                for ticker, relative_close in closes
            }

        for ticker, close in closes.items():
            figure.add_trace(
                go.Scatter(x=close.dates, y=close.values, name=ticker, mode="lines")
            )

        for ticker, close in closes.items():
            figure = self.__create_indicator_traces(indicators, ticker, close, figure)
        return figure, len(closes)

    def __get_traces_and_layout(self, client, engine_id, indicators):
        figure = go.Figure()
        figure, nof_ticker_lines = self.__get_traces(
            client, engine_id, indicators, figure
        )
        if nof_ticker_lines - sum(map(len, indicators.values())) > 1:
            figure.update_yaxes(tickformat=",.1%")
        if nof_ticker_lines > 0:
            figure = self.__get_signal_lines(engine_id, client, figure)
        figure.update_layout(template="plotly_white")
        return figure

    def register_callbacks(self, app, client_getter):
        client = client_getter()

        @app.callback(
            Output(*self.get_graph()),
            Input("indicator-table", "data"),
            Input(*self.engine_layout.get_id()),
        )
        def change(rows, engine_id):
            indicators = self.__get_configured_indicators(rows)
            return self.__get_traces_and_layout(client, engine_id, indicators)

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Output(*self.get_graph()),
            Input(*self.interval_layout.get_interval()),
            State(*self.date_layout.get_end_date()),
            State(*self.engine_layout.get_id()),
            State("indicator-table", "data"),
        )
        def update_on_interval(n_intervals, end_date, engine_id, indicator_rows):
            end_date = from_sdate(end_date)
            now = dt.datetime.now()
            # We still want to update on interval if we just crossed a day
            if end_date is None or now - dt.datetime.combine(
                end_date, dt.time()
            ) > dt.timedelta(days=1, minutes=1, seconds=get_settings().update_interval):
                return dash.no_update

            logger.info("Interval callback triggered: updating engine")
            client = client_getter()
            new_engine_id = api.update_engine(engine_id, end_date, client)
            indicators = self.__get_configured_indicators(indicator_rows)
            return new_engine_id, self.__get_traces_and_layout(
                new_engine_id, indicators
            )