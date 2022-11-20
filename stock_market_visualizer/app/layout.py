import dash_bootstrap_components as dbc

from stock_market_visualizer.app.date import DateLayout
from stock_market_visualizer.app.disclaimer import DisclaimerLayout
from stock_market_visualizer.app.engine import EngineLayout
from stock_market_visualizer.app.graph import GraphLayout
from stock_market_visualizer.app.header import HeaderLayout
from stock_market_visualizer.app.indicator import IndicatorLayout
from stock_market_visualizer.app.restoreable_state import RestoreableStateLayout
from stock_market_visualizer.app.signals import SignalDetectorLayout
from stock_market_visualizer.app.ticker import TickerLayout


class Layout:
    def __init__(self):
        self.engine_layout = EngineLayout()
        self.header_layout = HeaderLayout()
        self.ticker_layout = TickerLayout(self.engine_layout)
        self.indicator_layout = IndicatorLayout(self.engine_layout, self.ticker_layout)
        self.signal_detector_layout = SignalDetectorLayout(self.engine_layout)
        self.date_layout = DateLayout(
            self.engine_layout, self.ticker_layout, self.signal_detector_layout
        )
        self.graph_layout = GraphLayout(self.engine_layout)
        self.disclaimer_layout = DisclaimerLayout()
        self.restoreable_state_layout = RestoreableStateLayout()

        self.layout = dbc.Container(
            children=self.restoreable_state_layout.get_layout()
            + [
                self.header_layout.get_layout(),
                dbc.Container(
                    [
                        dbc.Row(
                            self.date_layout.get_layout()
                            + [
                                dbc.Col(self.ticker_layout.get_layout()),
                                dbc.Col(self.indicator_layout.get_layout()),
                            ]
                        ),
                        dbc.Row(
                            self.graph_layout.get_layout(),
                            style={"margin-bottom": "10px"},
                        ),
                        dbc.Row(children=self.signal_detector_layout.get_layout()),
                    ]
                ),
                self.engine_layout.get_layout(),
                self.disclaimer_layout.get_layout(),
            ]
        )

    def get_themes(self):
        return [dbc.themes.BOOTSTRAP]

    def get_layout(self):
        return self.layout

    def register_callbacks(self, app, engine_api, redis):
        self.disclaimer_layout.register_callbacks(app)
        self.header_layout.register_callbacks(app)
        self.date_layout.register_callbacks(app, engine_api)
        self.graph_layout.register_callbacks(app, engine_api)
        self.ticker_layout.register_callbacks(app, engine_api)
        self.indicator_layout.register_callbacks(app)
        self.signal_detector_layout.register_callbacks(app, engine_api)
        self.restoreable_state_layout.register_callbacks(app, engine_api, redis)
