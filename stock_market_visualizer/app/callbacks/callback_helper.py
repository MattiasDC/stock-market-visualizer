from stock_market_engine.core import OHLC
from stock_market_engine.core.time_series import make_relative

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.common.logging import get_logger

logger = get_logger(__name__)

class CallbackHelper:
    def __init__(self, client_getter, redis_getter):
        self.__client_getter = client_getter
        self.__redis_getter = redis_getter

    def get_client(self):
        return self.__client_getter()
        
    def get_tickers(self, rows):
        return [row['ticker-col'] for row in rows]

    def get_traces(self, engine_id):
        client = self.__client_getter()
        tickers = api.get_tickers(engine_id, client)
        if len(tickers) == 0:
            return []

        redis = self.__redis_getter()
        closes = {}
        for ticker in tickers:
            ohlc_id = api.get_ticker_ohlc(engine_id, ticker, client)
            if ohlc_id is None:
                continue
    
            ohlc_json = redis.get(ohlc_id)
            if ohlc_json is None:
                logger.warning(f"OHLC with id '{ohlc_id}' could not be found in redis database!")
                continue
            closes[ticker] = OHLC.from_json(ohlc_json).close
    
        if len(closes) > 1:
            relative_closes = zip(closes.keys(), make_relative(closes.values()))
            return [dict(type="scatter",
                         x=relative_close.dates,
                         y=relative_close.values-1,
                         name=ticker,
                         mode="lines") for ticker, relative_close in relative_closes]
    
        return [dict(type="scatter",
                     x=close.dates,
                     y=close.values,
                     name=ticker,
                     mode="lines") for ticker, close in closes.items()]
    
    def get_traces_and_layout(self, engine_id):
        traces = self.get_traces(engine_id)
        layout = {}
        if len(traces) > 1:
            layout['yaxis'] = dict(tickformat=',.1%')
        return dict(data=traces, layout=layout)