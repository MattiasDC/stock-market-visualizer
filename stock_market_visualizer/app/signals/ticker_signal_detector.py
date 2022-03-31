import json

from dash import dcc
from dash_extensions.enrich import Input, Output, State

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.signals.common import (
    SignalDetectorConfigurationLayout,
    get_random_detector_id,
)


class TickerDropdownLayout:
    def __init__(self, name):
        self.dropdown_name = f"config-dropdown-ticker-{name}"
        self.layout = dcc.Dropdown(
            id=self.dropdown_name, options=[], placeholder="Ticker"
        )

    def get_options(self):
        return self.dropdown_name, "options"

    def get_value(self):
        return self.dropdown_name, "value"

    def get_layout(self):
        return self.layout


class TickerDetectorHandler:
    def __init__(
        self,
        app,
        client,
        detector_cls,
        engine_layout,
        signal_data_placeholder_layout,
        dropdown_layout,
    ):
        self.__app = app
        self.__client = client
        self.__detector_cls = detector_cls

        @self.__app.callback(
            Output(*dropdown_layout.get_options()),
            Output(*dropdown_layout.get_value()),
            Input(*engine_layout.get_id()),
            State(*dropdown_layout.get_value()),
        )
        def update_dropdown_list(engine_id, value):
            options = self.__get_options(engine_id)
            if len(options) == 1:
                value = options[0]["value"]
            return options, value

        @self.__app.callback(
            Input(*dropdown_layout.get_value()),
            State(*signal_data_placeholder_layout.get_data()),
            Output(*signal_data_placeholder_layout.get_data()),
        )
        def update_active_ticker(ticker_value, data):
            data["ticker"] = ticker_value
            return data

    def name(self):
        return self.__detector_cls.NAME()

    def id(self):
        return self.name().replace(" ", "")

    def app(self):
        return self.__app

    def client(self):
        return self.__client

    def __get_options(self, engine_id):
        tickers = api.get_tickers(engine_id, self.__client)
        return [{"label": t, "value": t} for t in tickers]

    def activate(self, engine_id, data):
        return engine_id, data

    def create(self, engine_id, data):
        new_engine_id = api.add_signal_detector(
            engine_id,
            {
                "static_name": self.name(),
                "config": json.dumps(
                    {
                        "id": get_random_detector_id(engine_id, self.__client),
                        "ticker": json.dumps(data["ticker"]),
                    }
                ),
            },
            self.__client,
        )
        return new_engine_id

    def get_id(self, config):
        return json.loads(config)["id"]


class TickerDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, detector_cls, engine_layout, signal_data_placeholder_layout):
        self.detector_cls = detector_cls
        self.ticker_dropdown = TickerDropdownLayout(self.get_id())
        self.engine_layout = engine_layout
        self.signal_data_placeholder_layout = signal_data_placeholder_layout

        super().__init__(self.get_id(), self.ticker_dropdown.get_layout())

    def get_id(self):
        return self.detector_cls.NAME().replace(" ", "")

    def get_handler(self, app, client):
        return TickerDetectorHandler(
            app,
            client,
            self.detector_cls,
            self.engine_layout,
            self.signal_data_placeholder_layout,
            self.ticker_dropdown,
        )
