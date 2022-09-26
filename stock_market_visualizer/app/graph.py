from collections import Counter, defaultdict
from itertools import groupby

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc
from dash_extensions.enrich import Input, Output
from dateutil.rrule import DAILY, FR, MO, TH, TU, WE, rrule
from simputils.algos import all_equal, max_dist_indices, split_elements
from stock_market.common.factory import Factory
from stock_market.core import OHLC, Sentiment
from stock_market.core.time_series import TimeSeries, make_relative
from stock_market.ext.indicator import register_indicator_factories

from stock_market_visualizer.app.signals.common import (
    get_sentiment_colors,
    get_sentiment_shape,
)


class SentimentColorProvider:
    def __init__(self, sentiment_counters):
        if sentiment_counters.total() == 0:
            return
        self.colors = {
            s: get_sentiment_colors(s, sentiment_counters[s]) for s in Sentiment
        }
        self.index_generators = {
            s: max_dist_indices(sentiment_counters[s]) for s in Sentiment
        }

    def get(self, sentiment):
        return self.colors[sentiment][next(self.index_generators[sentiment])]


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
            for indicator_values in [
                indicator(
                    TimeSeries(
                        ticker,
                        pd.concat(
                            [ticker_values.dates, ticker_values.values],
                            axis=1,
                        ),
                    )
                )
            ]:
                trimmed_indicator_values = indicator_values.start_at(
                    rrule(
                        DAILY,
                        dtstart=indicator_values.start,
                        byweekday=(MO, TU, WE, TH, FR),
                    )[indicator.lag_days()].date()
                )
                figure.add_trace(
                    go.Scatter(
                        x=trimmed_indicator_values.dates,
                        y=trimmed_indicator_values.values,
                        name=trimmed_indicator_values.name,
                        mode="lines",
                    )
                )

        return figure

    def __get_signal_lines(self, engine, ticker_closes, figure):
        def get_signal_name(s):
            return s.name

        def get_signal_sentiment(s):
            return s.sentiment

        def __add_signals(figure, index, signals, color_provider):
            grouped_signals = groupby(
                split_elements(signals, key=get_signal_sentiment),
                key=get_signal_sentiment,
            )
            groups = [
                list(sentiment_signals_iter)
                for _, sentiment_signals_iter in grouped_signals
            ]
            if len(groups) > 0:
                figure = figure.set_subplots(
                    rows=2, cols=1, shared_xaxes=True, row_heights=[0.9, 0.1]
                )
                figure.update_yaxes(visible=False, col=1, row=2)
            for sentiment_signals in groups:
                first = sentiment_signals[0]
                sentiment = first.sentiment
                figure.add_trace(
                    go.Scatter(
                        name=first.name
                        + ("" if len(groups) == 1 else f" ({sentiment.value})"),
                        x=[s.date for s in sentiment_signals],
                        y=[index] * len(sentiment_signals),
                        mode="markers",
                        marker_symbol=get_sentiment_shape(sentiment),
                        marker_color=color_provider.get(sentiment),
                    ),
                    col=1,
                    row=2,
                )
            return figure

        def __add_ticker_signals(figure, signals, ticker_closes, color_provider):
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
                sentiment = first.sentiment
                figure.add_trace(
                    go.Scatter(
                        name=first.name
                        + f" ({ticker_symbol})"
                        + ("" if len(groups) == 1 else f" ({sentiment.value})"),
                        x=[s.date for s in sentiment_signals],
                        y=[
                            ticker_close.time_values[
                                ticker_close.time_values.date == s.date
                            ].value.iloc[0]
                            for s in sentiment_signals
                        ],
                        mode="markers",
                        marker_symbol=get_sentiment_shape(sentiment),
                        marker_size=12,
                        marker_color=color_provider.get(sentiment),
                    )
                )
            return figure

        all_signals = sorted(engine.get_signals().signals, key=get_signal_name)
        grouped_signals = groupby(all_signals, key=get_signal_name)
        unique_name_sentiments = set((s.name, s.sentiment) for s in all_signals)
        sentiment_counters = Counter(s for (_, s) in unique_name_sentiments)
        color_provider = SentimentColorProvider(sentiment_counters)
        for i, (g, signals) in enumerate(grouped_signals):
            signals = list(signals)
            assert all_equal([s.tickers for s in signals])
            if len(signals[0].tickers) == 1:
                __add_ticker_signals(figure, signals, ticker_closes, color_provider)
            else:
                __add_signals(figure, i, signals, color_provider)

        return figure

    def __get_ticker_closes(self, engine):
        tickers = engine.get_tickers()
        closes = {}

        if len(tickers) == 0:
            return closes

        for ticker in tickers:
            ohlc_json = engine.get_ticker_ohlc(ticker)
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
            )

        for ticker, close in closes.items():
            figure = self.__create_indicator_traces(indicators, ticker, close, figure)
        return figure

    def __get_traces_and_layout(self, engine, indicators):
        figure = go.Figure()
        figure["layout"].update(margin=dict(l=0, r=0, b=0, t=0))

        ticker_closes = self.__get_ticker_closes(engine)
        nof_ticker_lines = len(ticker_closes)
        figure = self.__get_traces(ticker_closes, indicators, figure)
        if nof_ticker_lines > 1:
            figure.update_yaxes(tickformat=",.1%")
        if nof_ticker_lines > 0:
            figure = self.__get_signal_lines(engine, ticker_closes, figure)
        figure.update_layout(template="plotly_white")
        return figure

    def register_callbacks(self, app, engine_api):
        @app.callback(
            Output(*self.get_graph()),
            Input("indicator-table", "data"),
            Input(*self.engine_layout.get_id()),
        )
        def change(rows, engine_id):
            indicators = self.__get_configured_indicators(rows)
            engine = engine_api.get_engine(engine_id)
            if engine is None:
                return dash.no_update
            return self.__get_traces_and_layout(engine, indicators)
