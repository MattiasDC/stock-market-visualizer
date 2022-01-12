import datetime
import json
from http import HTTPStatus
from functools import lru_cache

from stock_market.core import SignalSequence

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.common.requests import concat_port

MAX_CACHE_SIZE = get_settings().max_api_endpoint_cache_size


def get_create_url():
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + "/create"


def get_date_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port) + f"/getdate/{engine_id}"
    )


def get_start_date_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/getstartdate/{engine_id}"
    )


def get_update_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port) + f"/update/{engine_id}"
    )


def get_tickers_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port) + f"/tickers/{engine_id}"
    )


def get_ticker_ohlc_url(engine_id, ticker):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/ticker/{engine_id}/{ticker}"
    )


def get_add_ticker_url(engine_id, ticker):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/addticker/{engine_id}/{ticker}"
    )


def get_remove_ticker_url(engine_id, ticker):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/removeticker/{engine_id}/{ticker}"
    )


def get_supported_signal_detectors_url():
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + "/getsupportedsignaldetectors"
    )


def get_signal_detectors_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/signaldetectors/{engine_id}"
    )


def add_signal_detector_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/addsignaldetector/{engine_id}"
    )


def remove_signal_detector_url(engine_id, signal_detector_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + f"/removesignaldetector/{engine_id}/{signal_detector_id}"
    )


def get_signals_url(engine_id):
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port) + f"/signals/{engine_id}"
    )


def get_supported_indicators_url():
    settings = get_settings()
    return (
        concat_port(settings.api_url, port=settings.api_port)
        + "/getsupportedindicators"
    )


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


def create_engine(start_date, tickers, signal_detectors, client):
    data = get_create_engine_json(start_date, tickers, signal_detectors)
    response = client.post(url=get_create_url(), data=data)
    if response.status_code != HTTPStatus.OK:
        return None

    return response.text.strip('"')


@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_start_date(engine_id, client):
    if engine_id is None:
        return None

    response = client.get(url=get_start_date_url(engine_id))
    if response.status_code != HTTPStatus.OK:
        return None
    return datetime.date.fromisoformat(response.text.strip('"'))


def get_date(engine_id, client):
    if engine_id is None:
        return None

    response = client.get(url=get_date_url(engine_id))
    if response.status_code != HTTPStatus.OK:
        return None
    return datetime.date.fromisoformat(response.text.strip('"'))


def update_engine(engine_id, date, client):
    if engine_id is None:
        return None

    return client.post(url=get_update_url(engine_id), params={"date": str(date)})


@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_tickers(engine_id, client):
    if engine_id is None:
        return []

    return client.get(url=get_tickers_url(engine_id)).json()


def get_ticker_ohlc(engine_id, ticker, client):
    if engine_id is None:
        return None

    response = client.get(url=get_ticker_ohlc_url(engine_id, ticker))
    if response.status_code == HTTPStatus.NO_CONTENT:
        return None
    return response.json()


def add_ticker(engine_id, ticker, client):
    if engine_id is None:
        return None

    response = client.post(url=get_add_ticker_url(engine_id, ticker))
    if response.status_code != HTTPStatus.OK:
        return None
    return response.text.strip('"')


def remove_ticker(engine_id, ticker, client):
    if engine_id is None:
        return None

    response = client.post(url=get_remove_ticker_url(engine_id, ticker))
    if response.status_code != HTTPStatus.OK:
        return None
    return response.text.strip('"')


@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_supported_signal_detectors(client):
    response = client.get(url=get_supported_signal_detectors_url())
    if response.status_code != HTTPStatus.OK:
        return None
    return response.json()


@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_signal_detectors(engine_id, client):
    if engine_id is None:
        return []

    return client.get(url=get_signal_detectors_url(engine_id)).json()


def add_signal_detector(engine_id, signal_detector, client):
    if engine_id is None:
        return None

    response = client.post(
        url=add_signal_detector_url(engine_id), data=json.dumps(signal_detector)
    )
    if response.status_code != HTTPStatus.OK:
        return None

    return response.text.strip('"')


def remove_signal_detector(engine_id, signal_detector_id, client):
    if engine_id is None:
        return None
    response = client.post(
        url=remove_signal_detector_url(engine_id, signal_detector_id)
    )
    if response.status_code != HTTPStatus.OK:
        return None

    return response.text.strip('"')


def get_signals(engine_id, client):
    if engine_id is None:
        return SignalSequence()
    return SignalSequence.from_json(client.get(url=get_signals_url(engine_id)).json())


@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_supported_indicators(client):
    response = client.get(url=get_supported_indicators_url())
    if response.status_code != HTTPStatus.OK:
        return None
    return response.json()
