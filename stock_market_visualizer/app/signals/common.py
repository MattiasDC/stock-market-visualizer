import json

from dash import dcc, html
from plotly.colors import n_colors
from simputils.rnd import get_random_int_excluding
from stock_market.common.factory import Factory
from stock_market.core import Sentiment
from stock_market.ext.signal import (
    BiMonthlySignalDetector,
    CrossoverSignalDetector,
    DeathCrossSignalDetector,
    GoldenCrossSignalDetector,
    GraphSignalDetector,
    MonthlySignalDetector,
    register_signal_detector_factories,
)

from stock_market_visualizer.app.config import get_settings


def get_sentiment_color(sentiment):
    if sentiment == Sentiment.NEUTRAL:
        return "grey"
    elif sentiment == Sentiment.BULLISH:
        return "seagreen"
    assert sentiment == Sentiment.BEARISH
    return "crimson"


def get_sentiment_colors(sentiment, n):
    if n == 0:
        return []
    if n == 1:
        return [get_sentiment_color(sentiment)]

    if sentiment == Sentiment.NEUTRAL:
        return ["grey"] * n
    elif sentiment == Sentiment.BULLISH:
        return n_colors("rgb(27,82,51)", "rgb(68,193,123)", n, colortype="rgb")
    assert sentiment == Sentiment.BEARISH
    return n_colors("rgb(150,14,41)", "rgb(239,78,110)", n, colortype="rgb")


def get_sentiment_shape(sentiment):
    if sentiment == Sentiment.NEUTRAL:
        return "circle"
    elif sentiment == Sentiment.BULLISH:
        return "triangle-up"
    assert sentiment == Sentiment.BEARISH
    return "triangle-down"


def get_signal_detectors(engine):
    factory = register_signal_detector_factories(Factory())
    return [
        factory.create(
            detector_json["static_name"], json.dumps(detector_json["config"])
        )
        for detector_json in engine.get_signal_detectors()
    ]


def get_signal_detector(detector_id, engine):
    for d in get_signal_detectors(engine):
        if d.id == detector_id:
            return d
    return None


def get_random_detector_id(engine):
    ids = [d.id for d in engine.get_signal_detectors()]
    return get_random_int_excluding(get_settings().max_id_generator, ids)


def get_api_supported_signal_detectors(engine_api):
    return [sd["detector_name"] for sd in engine_api.get_supported_signal_detectors()]


def get_supported_trivial_config_signal_detectors():
    return [MonthlySignalDetector, BiMonthlySignalDetector]


def get_supported_ticker_based_signal_detectors():
    return [GoldenCrossSignalDetector, DeathCrossSignalDetector]


def get_supported_signal_detectors():
    return (
        get_supported_trivial_config_signal_detectors()
        + get_supported_ticker_based_signal_detectors()
        + [CrossoverSignalDetector, GraphSignalDetector]
    )


class SignalDetectorConfigurationLayout:
    def __init__(self, name, children):
        self.name = name
        self.children = children
        self.config_name = f"config-{name}"
        self.layout = html.Div(id=self.config_name, children=self.children, hidden=True)

    def get_layout(self):
        return self.layout


class CustomNameLayout:
    def __init__(self, name):
        self.id = f"{name}-custom-name"
        self.layout = dcc.Input(
            id=self.id,
            debounce=True,
            placeholder="Name",
            style={"margin-top": 5, "margin-bottom": 5},
            className="d-inline",
        )

    def get_name(self):
        return self.id, "value"

    def get_layout(self):
        return self.layout


class SentimentDropdownLayout:
    def __init__(self, name):
        self.id = f"{name}-sentiment"
        sentiment_values = [
            {"value": s.value, "label": str(s.value).lower().capitalize()}
            for s in Sentiment
            if s != Sentiment.NEUTRAL
        ]
        self.layout = dcc.Dropdown(
            id=self.id, options=sentiment_values, placeholder="Sentiment"
        )

    def get_sentiment(self):
        return self.id, "value"

    def get_layout(self):
        return self.layout


class SignalDataPlaceholderLayout:
    def __init__(self):
        self.id = "signal-data-placeholder"
        self.layout = dcc.Store(id=self.id, data={})

    def get_data(self):
        return self.id, "data"

    def get_layout(self):
        return self.layout
