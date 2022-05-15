import datetime as dt
from collections import defaultdict
from itertools import groupby

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from dash_extensions.enrich import Input, Output
from plotly.subplots import make_subplots
from stock_market.common.factory import Factory
from stock_market.core import OHLC
from stock_market.core.time_series import TimeSeries, make_relative
from stock_market.ext.indicator import register_indicator_factories
from utils.algos import all_equal, split_elements

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.signals.common import get_sentiment_shape


class GraphLayout:
    def __init__(self, engine_layout):
        self.engine_layout = engine_layout
        self.stock_market_graph = "stock-market-graph"
        self.layout = dbc.Col(
            dbc.Container(
                dcc.Graph(id=self.stock_market_graph, style={"height": "60vh"})
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
            trimmed_ticker_values = ticker_values.start_at(
                ticker_values.start + dt.timedelta(days=indicator.lag_days())
            )
            for indicator_values in [
                indicator(
                    TimeSeries(
                        ticker,
                        pd.concat(
                            [trimmed_ticker_values.dates, trimmed_ticker_values.values],
                            axis=1,
                        ),
                    )
                )
            ]:
                figure.add_trace(
                    go.Scatter(
                        x=indicator_values.dates,
                        y=indicator_values.values,
                        name=indicator_values.name,
                        mode="lines",
                    ),
                    row=1,
                    col=1,
                )

        return figure

    def __get_signal_lines(self, engine_id, client, ticker_closes, figure):
        def get_signal_name(s):
            return s.name

        def get_signal_sentiment(s):
            return s.sentiment

        def __add_signals(figure, index, signals):
            grouped_signals = groupby(
                split_elements(signals, key=get_signal_sentiment),
                key=get_signal_sentiment,
            )
            groups = [
                list(sentiment_signals_iter)
                for _, sentiment_signals_iter in grouped_signals
            ]
            for sentiment_signals in groups:
                first = sentiment_signals[0]
                figure.add_trace(
                    go.Scatter(
                        name=first.name
                        + ("" if len(groups) == 1 else f" ({first.sentiment.value})"),
                        x=[s.date for s in sentiment_signals],
                        y=[index] * len(sentiment_signals),
                        mode="markers",
                        marker_symbol=get_sentiment_shape(first.sentiment),
                    ),
                    col=1,
                    row=2,
                )
            return figure

        def __add_ticker_signals(figure, signals, ticker_closes):
            ticker_symbol = signals[0].tickers[0].symbol
            ticker_close = ticker_closes[ticker_symbol]
            grouped_signals = groupby(
                split_elements(signals, key=get_signal_sentiment),
                key=get_signal_sentiment,
            )
            groups = [
                list(sentiment_signals_iter)
                for _, sentiment_signals_iter in grouped_signals
            ]
            for sentiment_signals in groups:
                first = sentiment_signals[0]
                figure.add_trace(
                    go.Scatter(
                        name=first.name
                        + f" ({ticker_symbol})"
                        + ("" if len(groups) == 1 else f" ({first.sentiment.value})"),
                        x=[s.date for s in sentiment_signals],
                        y=[
                            ticker_close.time_values[
                                ticker_close.time_values.date == s.date
                            ].value.iloc[0]
                            for s in sentiment_signals
                        ],
                        mode="markers",
                        marker_symbol=get_sentiment_shape(first.sentiment),
                        marker_size=12,
                    ),
                    col=1,
                    row=1,
                )
            return figure

        all_signals = sorted(
            api.get_signals(engine_id, client).signals, key=get_signal_name
        )
        grouped_signals = groupby(all_signals, key=get_signal_name)
        for i, (g, signals) in enumerate(grouped_signals):
            signals = list(signals)
            assert all_equal([s.tickers for s in signals])
            if len(signals[0].tickers) == 1:
                __add_ticker_signals(figure, signals, ticker_closes)
            else:
                __add_signals(figure, i, signals)

        figure.update_yaxes(visible=False, col=1, row=2)
        return figure

    def __get_ticker_closes(self, client, engine_id):
        tickers = api.get_tickers(engine_id, client)
        closes = {}

        if len(tickers) == 0:
            return closes

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
        return closes

    def __get_traces(self, closes, indicators, figure):
        for ticker, close in closes.items():
            figure.add_trace(
                go.Scatter(x=close.dates, y=close.values, name=ticker, mode="lines"),
                row=1,
                col=1,
            )

        for ticker, close in closes.items():
            figure = self.__create_indicator_traces(indicators, ticker, close, figure)
        return figure, len(closes)

    def __get_traces_and_layout(self, client, engine_id, indicators):
        share_x_axes = len(api.get_signals(engine_id, client).signals) > 0
        figure = make_subplots(
            rows=2, cols=1, shared_xaxes=share_x_axes, row_heights=[0.9, 0.1]
        )
        figure["layout"].update(margin=dict(l=0, r=0, b=0, t=0))

        ticker_closes = self.__get_ticker_closes(client, engine_id)
        figure, nof_ticker_lines = self.__get_traces(ticker_closes, indicators, figure)
        if nof_ticker_lines - sum(map(len, indicators.values())) > 1:
            figure.update_yaxes(tickformat=",.1%", row=1, col=1)
        if nof_ticker_lines > 0:
            figure = self.__get_signal_lines(engine_id, client, ticker_closes, figure)
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
