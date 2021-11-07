import json
from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.common.requests import concat_port

def get_create_url():
    settings = get_settings()
    return concat_port(settings.api_url, port=settings.api_port) + "/create"

def get_create_engine_json(start_date, tickers):
    return json.dumps({
        "stock_market": {
            "start_date": start_date.isoformat(),
            "tickers": [{"symbol": ticker} for ticker in tickers]
        },
        "signals": {
            "signals": [
                {
                    "name": "monthly",
                    "config": "{}"
                }
              ]
          }
      })