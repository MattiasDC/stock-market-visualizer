from collections import defaultdict
import pandas as pd

from stock_market.core import OHLC
from stock_market.core.time_series import make_relative, TimeSeries

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
            sd['name'] = sd.pop('signal-col')
            signal_detectors.append(sd)
        return signal_detectors

    def get_configured_indicators(self, rows):
        factory = get_indicator_factory()
        indicators_per_ticker = defaultdict(list)
        for row in rows:
            indicators_per_ticker[row['ticker-col']].append(factory.create(row['indicator']['name'],
                                                                           row['indicator']['config']))
        return indicators_per_ticker

    def create_indicator_traces(self, indicators_per_ticker, ticker, ticker_values):
        traces = []
        for indicator in indicators_per_ticker[ticker]:
            for indicator_values in [indicator(TimeSeries(ticker, pd.concat([ticker_values.dates,
                                                                             ticker_values.values],
                                                                             axis=1)))]:
                traces.append(dict(type="scatter",
                                   x=indicator_values.dates,
                                   y=indicator_values.values,
                                   name=indicator_values.name,
                                   mode="lines"))
                
        return traces

    def get_traces(self, engine_id, indicators):
        client = self.__client_getter()
        tickers = api.get_tickers(engine_id, client)
        if len(tickers) == 0:
            return []

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

        traces = [dict(type="scatter",
                       x=close.dates,
                       y=close.values,
                       name=ticker,
                       mode="lines") for ticker, close in closes.items()]

        indicator_traces = []
        for ticker, close in closes.items():
            indicator_traces.extend(self.create_indicator_traces(indicators,
                                                                 ticker,
                                                                 close))
        traces.extend(indicator_traces)
        return traces
    
    def get_traces_and_layout(self, engine_id, indicators):
        traces = self.get_traces(engine_id, indicators)
        layout = {}
        if len(traces) - sum(map(len, indicators.values())) > 1:
            layout['yaxis'] = dict(tickformat=',.1%')
        return dict(data=traces, layout=layout)