from collections import defaultdict
import datetime as dt
import json
import pandas as pd
import plotly.graph_objects as go

from stock_market.core import OHLC, Signal, Sentiment
from stock_market.core.time_series import make_relative, TimeSeries
from stock_market.ext.signal import register_signal_detector_factories
from stock_market.common.factory import Factory

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.indicators import get_indicator_factory
from utils.logging import get_logger

logger = get_logger(__name__)

class CallbackHelper:
    def __init__(self, client_getter):
        self.__client_getter = client_getter

    def get_client(self):
        return self.__client_getter()
        
    def get_tickers(self, rows):
        return [row['ticker-col'] for row in rows]

    def get_signal_detectors(self, rows):
        signal_detectors = []
        for row in rows:
            sd = dict(row)
            sd.pop('signal-col')
            sd['static_name'] = sd.pop('name')
            signal_detectors.append(sd)
        return signal_detectors

    def get_configured_indicators(self, rows):
        factory = get_indicator_factory()
        indicators_per_ticker = defaultdict(list)
        for row in rows:
            indicators_per_ticker[row['ticker-col']].append(factory.create(row['indicator']['name'],
                                                                           row['indicator']['config']))
        return indicators_per_ticker

    def create_indicator_traces(self, indicators_per_ticker, ticker, ticker_values, figure):
        for indicator in indicators_per_ticker[ticker]:
            for indicator_values in [indicator(TimeSeries(ticker, pd.concat([ticker_values.dates,
                                                                             ticker_values.values],
                                                                             axis=1)))]:
                figure.add_trace(go.Scatter(x=indicator_values.dates,
                                            y=indicator_values.values,
                                            name=indicator_values.name,
                                            mode="lines"))
                
        return figure

    def __get_color(self, sentiment):
      if sentiment == Sentiment.NEUTRAL:
        return 'grey'
      elif sentiment == Sentiment.BULLISH:
        return 'green'
      assert sentiment == Sentiment.BEARISH
      return 'red'

    def __get_enabled_signal_detectors(self, engine_id, client, enabled_signal_detectors):
      signal_detector_factory = register_signal_detector_factories(Factory())      
      enabled_signal_detector_ids = []
      for i, sd in enumerate(api.get_signal_detectors(engine_id, client)):
        config = sd['config']
        if type(config) is not str:
          config = json.dumps(config)
        signal_detector = signal_detector_factory.create(sd['static_name'], config)
        if i in enabled_signal_detectors:
          enabled_signal_detector_ids.append(signal_detector.id)
      return enabled_signal_detector_ids

    def get_signal_lines(self, engine_id, client, figure, enabled_signal_detectors):
      enabled_signal_detector_ids = self.__get_enabled_signal_detectors(engine_id, client, enabled_signal_detectors)
      signal_sequence = api.get_signals(engine_id, client)
      date_dict = defaultdict(list)
      for s in signal_sequence.signals:
        if s.id in enabled_signal_detector_ids:
          date_dict[s.date].append(s)

      for date, signals in date_dict.items():
        for s in signals[:-1]:
          figure.add_vrect(x0=date,
                           x1=date,
                           line_color=self.__get_color(s.sentiment))

        figure.add_vrect(x0=date,
                         x1=date,
                         line_color=self.__get_color(signals[-1].sentiment),
                         annotation_text=", ".join([s.name for s in signals]),
                         annotation_position="top left",
                         annotation_textangle=90)
      return figure

    def get_traces(self, engine_id, indicators, figure):
        client = self.__client_getter()
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
            closes = {ticker : TimeSeries(ticker, pd.concat([relative_close.dates, relative_close.values-1], axis=1))
                      for ticker, relative_close in closes}

        for ticker, close in closes.items():
          figure.add_trace(go.Scatter(x=close.dates, y=close.values, name=ticker, mode="lines"))

        for ticker, close in closes.items():
            figure = self.create_indicator_traces(indicators,
                                                  ticker,
                                                  close,
                                                  figure)
        return figure, len(closes)
    
    def get_traces_and_layout(self, engine_id, indicators, selected_signal_indices):
        figure = go.Figure()
        figure, nof_ticker_lines = self.get_traces(engine_id, indicators, figure)
        layout = {}
        if nof_ticker_lines - sum(map(len, indicators.values())) > 1:
            figure.update_yaxes(tickformat=',.1%')
        if nof_ticker_lines > 0:
            figure = self.get_signal_lines(engine_id, self.__client_getter(), figure, selected_signal_indices)
        figure.update_layout(template='plotly_white')
        return figure