import datetime
import json
from http import HTTPStatus

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.common.requests import concat_port

def get_create_url():
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + "/create"

def get_start_date_url(engine_id):
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + f"/getstartdate/{engine_id}"

def get_update_url(engine_id):
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + f"/update/{engine_id}"

def get_tickers_url(engine_id):
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + f"/tickers/{engine_id}"

def get_ticker_ohlc_url(engine_id, ticker):
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + f"/ticker/{engine_id}/{ticker}"

def get_add_ticker_url(engine_id, ticker):
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + f"/addticker/{engine_id}/{ticker}"    

def get_remove_ticker_url(engine_id, ticker):
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + f"/removeticker/{engine_id}/{ticker}"    

def get_create_engine_json(start_date, tickers):
    return json.dumps({
        "stock_market": {
            "start_date": start_date.isoformat(),
            "tickers": [{"symbol": ticker} for ticker in tickers]
        },
        "signal_detectors": []
      })

def create_engine(start_date, tickers, client):
    data = get_create_engine_json(start_date, tickers)
    response = client.post(url=get_create_url(), data=data)
    if response.status_code != HTTPStatus.OK:
        return None

    return response.text.strip("\"")

def get_start_date(engine_id, client):
    response = client.get(url=get_start_date_url(engine_id))
    if response.status_code != HTTPStatus.OK:
        return None
    return datetime.date.fromisoformat(response.text.strip("\""))

def update_engine(engine_id, date, client):
    return client.post(url=get_update_url(engine_id), params={'date' : str(date)})

def get_tickers(engine_id, client):
    return client.get(url=get_tickers_url(engine_id)).json()

def get_ticker_ohlc(engine_id, ticker, client):
    response = client.get(url=get_ticker_ohlc_url(engine_id, ticker))
    if response.status_code == HTTPStatus.NO_CONTENT:
        return None
    return response.json()

def add_ticker(engine_id, ticker, client):
    response = client.post(url=get_add_ticker_url(engine_id, ticker))
    if response.status_code != HTTPStatus.OK:
        return None
    return response.text.strip("\"")

def remove_ticker(engine_id, ticker, client):
    response = client.post(url=get_remove_ticker_url(engine_id, ticker))
    if response.status_code != HTTPStatus.OK:
        return None
    return response.text.strip("\"")