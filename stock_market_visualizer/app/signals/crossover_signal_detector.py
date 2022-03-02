import json

import dash
from dash import html
from dash_extensions.enrich import Input, Output, State
from stock_market.ext.indicator import Identity
from stock_market.ext.signal import CrossoverSignalDetector
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.dropdown_button import DropdownButton
from stock_market_visualizer.app.indicator import (
    ModalIndicatorCreatorLayout,
    get_indicators_with_identity,
)
from stock_market_visualizer.app.signals.common import (
    CustomNameLayout,
    SentimentDropdownLayout,
    SignalDetectorConfigurationLayout,
    get_random_detector_id,
)
from stock_market_visualizer.app.signals.ticker_signal_detector import (
    TickerDetectorHandler,
    TickerDropdownLayout,
)

logger = get_logger(__name__)


class IndicatorGetterLayout:
    def __init__(self, name, include_identity):
        self.name = name
        self.include_identity = include_identity

        indicators = [
            i.__name__
            for i in get_indicators_with_identity()
            if include_identity or i != Identity
        ]
        self.dropdown_button = DropdownButton(
            name, f"{name} Indicator", indicators, False
        )

        self.indicator_getter_id = f"{name}-info"
        self.indicator_getter_text = html.P(
            id=self.indicator_getter_id, className="d-inline"
        )

        self.modal_layout = ModalIndicatorCreatorLayout(name)

        self.layout = [
            html.Div(
                children=[
                    self.dropdown_button.get_layout(),
                    self.indicator_getter_text,
                ],
                style={"margin-top": 5, "margin-bottom": 5},
            )
        ] + self.modal_layout.get_layout()

    def get_layout(self):
        return self.layout

    def get_info(self):
        return self.indicator_getter_id, "children"

    def get_modal_layout(self):
        return self.modal_layout

    def get_dropdown_layout(self):
        return self.dropdown_button


class CrossoverDetectorHandler(TickerDetectorHandler):
    def __init__(self, app, client, crossover_layout):
        super().__init__(
            app,
            client,
            CrossoverSignalDetector,
            crossover_layout.engine_layout,
            crossover_layout.signal_data_placeholder_layout,
            crossover_layout.ticker_dropdown,
        )
        self.crossover_layout = crossover_layout

        indicators = get_indicators_with_identity()
        for indicator in api.get_supported_indicators(client):
            if indicator["indicator_name"] not in [
                i.__name__ for i in indicators.keys()
            ]:
                logger.warning(
                    f"{indicator} is not implemented in the stock market visualizer"
                )

        for indicator in indicators.keys():
            if indicator.__name__ not in [
                i["indicator_name"] for i in api.get_supported_indicators(client)
            ]:
                logger.warning(
                    f"{indicator} is implemented in the stock market visualizer, but"
                    " not supported by the engine"
                )

        for indicator in indicators:
            self.__add_create_indicator_callbacks(
                "Responsive",
                indicator,
                indicators[indicator],
                crossover_layout.responsive_getter,
            )
            if indicator != Identity:
                self.__add_create_indicator_callbacks(
                    "Unresponsive",
                    indicator,
                    indicators[indicator],
                    crossover_layout.unresponsive_getter,
                )

        @app.callback(
            Input(*crossover_layout.custom_name_layout.get_name()),
            State(*crossover_layout.signal_data_placeholder_layout.get_data()),
            Output(*crossover_layout.signal_data_placeholder_layout.get_data()),
        )
        def update_custom_name(custom_name, data):
            data["name"] = custom_name
            return data

        @app.callback(
            Input(*crossover_layout.sentiment_dropdown_layout.get_sentiment()),
            State(*crossover_layout.signal_data_placeholder_layout.get_data()),
            Output(*crossover_layout.signal_data_placeholder_layout.get_data()),
        )
        def update_sentiment(sentiment, data):
            data["sentiment"] = sentiment
            return data

    def __add_create_indicator_callbacks(self, name, indicator, arguments, getter):
        if indicator != Identity:
            modal = getter.get_modal_layout()

            @self.app().callback(
                Input(
                    *getter.get_dropdown_layout().get_item_n_clicks(indicator.__name__)
                ),
                Output(*modal.get_is_open(indicator)),
            )
            def create_indicator_form(n_clicks):
                if n_clicks == 0 or None:
                    return False
                return True

            @self.app().callback(
                Input(*modal.get_add_n_clicks(indicator)),
                State(*self.crossover_layout.signal_data_placeholder_layout.get_data()),
                [
                    State(*modal.get_argument_value(indicator, argument))
                    for argument in arguments
                ],
                Output(*modal.get_is_open(indicator)),
                Output(
                    *self.crossover_layout.signal_data_placeholder_layout.get_data()
                ),
                Output(*getter.get_info()),
            )
            def create_indicator(n_clicks, data, arguments):
                if n_clicks == 0 or None:
                    return dash.no_update, dash.no_update, dash.no_update
                if not isinstance(arguments, list):
                    arguments = [arguments]
                created_indicator = indicator(*arguments)
                data[name] = {
                    "name": indicator.__name__,
                    "config": created_indicator.to_json(),
                }
                return False, data, str(created_indicator)

        else:

            @self.app().callback(
                Input(
                    *getter.get_dropdown_layout().get_item_n_clicks(indicator.__name__)
                ),
                State(*self.crossover_layout.signal_data_placeholder_layout.get_data()),
                Output(
                    *self.crossover_layout.signal_data_placeholder_layout.get_data()
                ),
                Output(*getter.get_info()),
            )
            def create_indicator(n_clicks, data):
                if n_clicks == 0 or None:
                    return dash.no_update, dash.no_update
                created_indicator = indicator()
                data[name] = {
                    "name": indicator.__name__,
                    "config": created_indicator.to_json(),
                }
                return data, str(created_indicator)

    def create(self, engine_id, data):
        if "name" not in data:
            return engine_id
        if "Responsive" not in data:
            return engine_id
        if "Unresponsive" not in data:
            return engine_id
        if "ticker" not in data or len(data["ticker"]) == 0:
            return engine_id
        if "sentiment" not in data:
            return engine_id
        new_engine_id = api.add_signal_detector(
            engine_id,
            {
                "static_name": self.name(),
                "config": json.dumps(
                    {
                        "id": get_random_detector_id(engine_id, self.client),
                        "name": data["name"],
                        "ticker": json.dumps(data["ticker"]),
                        "responsive_indicator_getter": data["Responsive"],
                        "unresponsive_indicator_getter": data["Unresponsive"],
                        "sentiment": json.dumps(data["sentiment"]),
                    }
                ),
            },
            self.client(),
        )
        return new_engine_id

    def get_id(self, config):
        return json.loads(config)["id"]


class CrossoverDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, engine_layout, signal_data_placeholder_layout):
        self.engine_layout = engine_layout
        self.signal_data_placeholder_layout = signal_data_placeholder_layout

        name = CrossoverSignalDetector.NAME()
        self.custom_name_layout = CustomNameLayout(name)
        self.sentiment_dropdown_layout = SentimentDropdownLayout(name)

        self.ticker_dropdown = TickerDropdownLayout(name)
        self.responsive_getter = IndicatorGetterLayout("Responsive", True)
        self.unresponsive_getter = IndicatorGetterLayout("Unresponsive", False)
        child_configs = (
            [self.custom_name_layout.get_layout(), self.ticker_dropdown.get_layout()]
            + self.responsive_getter.get_layout()
            + self.unresponsive_getter.get_layout()
            + [self.sentiment_dropdown_layout.get_layout()]
        )
        super().__init__(name, child_configs)

    def get_handler(self, app, client):
        return CrossoverDetectorHandler(app, client, self)
