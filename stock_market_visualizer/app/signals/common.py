from dash import dcc
from dash import html

from stock_market.core import Sentiment
from stock_market.ext.signal import (
    MonthlySignalDetector,
    BiMonthlySignalDetector,
    GoldenCrossSignalDetector,
    DeathCrossSignalDetector,
    CrossoverSignalDetector,
)

import stock_market_visualizer.app.sme_api_helper as api


def get_api_supported_signal_detectors(client):
    return [sd["detector_name"] for sd in api.get_supported_signal_detectors(client)]


def get_supported_trivial_config_signal_detectors():
    return [MonthlySignalDetector, BiMonthlySignalDetector]


def get_supported_ticker_based_signal_detectors():
    return [GoldenCrossSignalDetector, DeathCrossSignalDetector]


def get_supported_signal_detectors():
    return (
        get_supported_trivial_config_signal_detectors()
        + get_supported_ticker_based_signal_detectors()
        + [CrossoverSignalDetector]
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
