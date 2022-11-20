import datetime
import json
from http import HTTPStatus

import backoff
import httpx
from lru import LRU
from simputils.logging import get_logger
from stock_market.core import SignalSequence

from stock_market_visualizer.app.config import get_settings

MAX_CACHE_SIZE = get_settings().max_api_endpoint_cache_size
logger = get_logger(__name__)


def get_create_engine_json(start_date, tickers, signal_detectors):
    return json.dumps(
        {
            "stock_market": {
                "start_date": start_date.isoformat(),
                "tickers": [{"symbol": ticker} for ticker in tickers],
            },
            "signal_detectors": signal_detectors,
        }
    )


class HttpRequester:
    def __init__(self, base_url, http_client):
        self.base_url = base_url
        self.http_client = http_client

    @backoff.on_exception(backoff.expo, (httpx.ConnectError))
    def request_json(self, **kwargs):
        kwargs_dict = dict(kwargs)
        kwargs_dict["url"] = self.base_url + kwargs_dict.pop("url")

        response = self.http_client.request(**kwargs_dict)
        code = response.status_code
        if code != HTTPStatus.OK:
            if code >= 400:
                logger.warning(
                    f"Encountered error code '{code}' for request '{kwargs_dict}'."
                    f" Response: {response.text[:500]}"
                )
            return None

        response = response.json()
        return response


class StockEngineProxy:
    def __init__(self, engine_id, engine_api):
        assert engine_id is not None
        self.engine_id = engine_id
        self.engine_api = engine_api
        self.engine_api._store_engine(self)

    def get_date_path(self):
        return f"/getdate/{self.engine_id}"

    def get_start_date_path(self):
        return f"/getstartdate/{self.engine_id}"

    def get_update_path(self):
        return f"/update/{self.engine_id}"

    def get_tickers_path(self):
        return f"/tickers/{self.engine_id}"

    def get_ticker_ohlc_path(self, ticker):
        return f"/ticker/{self.engine_id}/{ticker}"

    def get_add_ticker_path(self, ticker):
        return f"/addticker/{self.engine_id}/{ticker}"

    def get_remove_ticker_path(self, ticker):
        return f"/removeticker/{self.engine_id}/{ticker}"

    def get_signal_detectors_path(self):
        return f"/signaldetectors/{self.engine_id}"

    def add_signal_detector_path(self):
        return f"/addsignaldetector/{self.engine_id}"

    def remove_signal_detector_path(self, signal_detector_id):
        return f"/removesignaldetector/{self.engine_id}/{signal_detector_id}"

    def get_signals_path(self):
        return f"/signals/{self.engine_id}"

    def create_engine_proxy(self, engine_id):
        return StockEngineProxy(engine_id, self.engine_api)

    def perform_engine_operation(self, **kwargs):
        engine_id = self.engine_api.http_requester.request_json(method="POST", **kwargs)
        if engine_id is None:
            return self
        return self.create_engine_proxy(engine_id)

    def get_start_date(self):
        result = self.engine_api.http_requester.request_json(
            method="GET", url=self.get_start_date_path()
        )
        if result is None:
            return None
        return datetime.date.fromisoformat(result)

    def get_date(self):
        result = self.engine_api.http_requester.request_json(
            method="GET", url=self.get_date_path()
        )
        if result is None:
            return None
        return datetime.date.fromisoformat(result)

    def update_engine(self, date):
        engine_id = self.engine_api.http_requester.request_json(
            method="POST",
            url=self.get_update_path(),
            params={"date": str(date)},
        )
        if engine_id is None:
            return self
        return self.create_engine_proxy(engine_id)

    def get_tickers(self):
        result = self.engine_api.http_requester.request_json(
            method="GET", url=self.get_tickers_path()
        )
        if result is None:
            return []
        return result

    def get_ticker_ohlc(self, ticker):
        result = self.engine_api.http_requester.request_json(
            method="GET", url=self.get_ticker_ohlc_path(ticker)
        )
        return result

    def add_ticker(self, ticker):
        engine_proxy = self.perform_engine_operation(
            url=self.get_add_ticker_path(ticker)
        )
        return engine_proxy

    def remove_ticker(self, ticker):
        engine_proxy = self.perform_engine_operation(
            url=self.get_remove_ticker_path(ticker)
        )
        return engine_proxy

    def get_signal_detectors(self):
        result = self.engine_api.http_requester.request_json(
            method="GET", url=self.get_signal_detectors_path()
        )
        if result is None:
            return []
        return result

    def add_signal_detector(self, signal_detector):
        engine_proxy = self.perform_engine_operation(
            url=self.add_signal_detector_path(),
            data=json.dumps(signal_detector),
        )
        return engine_proxy

    def remove_signal_detector(self, signal_detector_id):
        engine_proxy = self.perform_engine_operation(
            url=self.remove_signal_detector_path(signal_detector_id),
        )
        return engine_proxy

    def get_signals(self):
        result = self.engine_api.http_requester.request_json(
            method="GET",
            url=self.get_signals_path(),
        )
        if result is None:
            return SignalSequence()
        return SignalSequence.from_json(result)


def concat_port(url, port):
    return url + ":" + str(port)


class StockMarketEngineApi:
    def __init__(self, api_url, api_port, http_client):
        self.http_requester = HttpRequester(
            concat_port(api_url, port=api_port), http_client
        )
        self.cache = LRU(MAX_CACHE_SIZE)

    def get_create_path(self):
        return "/create"

    def get_supported_signal_detectors_path(self):
        return "/getsupportedsignaldetectors"

    def get_supported_indicators_path(self):
        return "/getsupportedindicators"

    def _store_engine(self, engine_proxy):
        self.cache[engine_proxy.engine_id] = engine_proxy

    def get_engine(self, engine_id):
        if engine_id in self.cache:
            return self.cache[engine_id]
        return StockEngineProxy(engine_id, self)

    def create_engine(self, start_date, tickers, signal_detectors):
        data = get_create_engine_json(start_date, tickers, signal_detectors)
        return self.create_engine_from_json(data)

    def create_engine_from_json(self, json_config):
        result = self.http_requester.request_json(
            method="POST", url=self.get_create_path(), data=json_config
        )
        return StockEngineProxy(result, self)

    def get_supported_indicators(self):
        result = self.http_requester.request_json(
            method="GET", url=self.get_supported_indicators_path()
        )
        return result

    def get_supported_signal_detectors(self):
        result = self.http_requester.request_json(
            method="GET", url=self.get_supported_signal_detectors_path()
        )
        return result
