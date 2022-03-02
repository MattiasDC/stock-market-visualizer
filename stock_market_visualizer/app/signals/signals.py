import json

import dash
import dash_bootstrap_components as dbc
from dash import html
from dash_extensions.enrich import Input, Output, State
from utils.logging import get_logger

import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.checkable_table import CheckableTableLayout
from stock_market_visualizer.app.signals.common import (
    SignalDataPlaceholderLayout,
    get_api_supported_signal_detectors,
    get_supported_signal_detectors,
    get_supported_ticker_based_signal_detectors,
    get_supported_trivial_config_signal_detectors,
)
from stock_market_visualizer.app.signals.crossover_signal_detector import (
    CrossoverDetectorConfigurationLayout,
)
from stock_market_visualizer.app.signals.graph_signal_detector import (
    GraphDetectorConfigurationLayout,
)
from stock_market_visualizer.app.signals.ticker_signal_detector import (
    TickerDetectorConfigurationLayout,
)
from stock_market_visualizer.app.signals.trivial_signal_detector import (
    TrivialSignalDetectorConfigurationLayout,
)

logger = get_logger(__name__)


class SignalDetectorLayout:
    def __init__(self, engine_layout):
        self.engine_layout = engine_layout
        self.signal_detector_table = CheckableTableLayout(
            "signal", [sd.NAME() for sd in get_supported_signal_detectors()], [], False
        )
        self.legend_id = "signal-edit-legend"
        self.legend = html.Legend(id=self.legend_id, children="", className="w-auto")
        self.signal_detector_data_layout = SignalDataPlaceholderLayout()

        self.trivial_config_layouts = [
            TrivialSignalDetectorConfigurationLayout(sd.NAME().replace(" ", ""))
            for sd in get_supported_trivial_config_signal_detectors()
        ]
        self.ticker_based_config_layouts = [
            TickerDetectorConfigurationLayout(
                sd, engine_layout, self.signal_detector_data_layout
            )
            for sd in get_supported_ticker_based_signal_detectors()
        ]
        self.crossover_config_layout = CrossoverDetectorConfigurationLayout(
            engine_layout, self.signal_detector_data_layout
        )
        self.graph_config_layout = GraphDetectorConfigurationLayout(
            self.signal_detector_table, self.signal_detector_data_layout
        )

        self.signal_edit_placeholder_id = "signal-edit-placeholder"
        self.add_button_id = "signal-add"
        self.signal_edit_fieldset_id = "signal-edit-fieldset"

    def get_config_layouts(self):
        layouts = list(self.trivial_config_layouts)
        layouts.extend(self.ticker_based_config_layouts)
        layouts.append(self.crossover_config_layout)
        layouts.append(self.graph_config_layout)
        return layouts

    def get_layout(self):
        config_layouts = [self.legend, html.Br()] + [
            cl.get_layout() for cl in self.get_config_layouts()
        ]
        return [
            dbc.Col(width=3, children=self.signal_detector_table.get_layout()),
            dbc.Col(
                html.Div(
                    id=self.signal_edit_placeholder_id,
                    hidden=True,
                    children=[
                        html.Fieldset(
                            id=self.signal_edit_fieldset_id,
                            className="border p-2",
                            children=config_layouts
                            + [self.signal_detector_data_layout.get_layout()],
                        ),
                        dbc.Button(
                            "Add",
                            id=self.add_button_id,
                            n_clicks=0,
                            style={"margin-top": 5},
                        ),
                    ],
                )
            ),
        ]

    def register_callbacks(self, app, client_getter):
        self.signal_detector_table.register_callbacks(app)

        client = client_getter()
        detector_handlers = {
            dh.name(): dh
            for dh in [cl.get_handler(app, client) for cl in self.get_config_layouts()]
        }

        @app.callback(
            Output(self.signal_edit_placeholder_id, "hidden"),
            Input(self.signal_detector_table.collapse_table_id, "is_open"),
            State(self.legend_id, "children"),
        )
        def hide_edit_fieldset(is_open, name):
            return (
                not is_open
                or name in [h.name for h in self.trivial_config_layouts]
                or len(name) == 0
            )

        @app.callback(
            Output(*self.signal_detector_table.get_table()),
            Input(*self.engine_layout.get_id()),
        )
        def update_signal_table(engine_id):
            return [
                {
                    "signal-col": signal_detector["name"],
                    "name": signal_detector["static_name"],
                    "config": json.dumps(signal_detector["config"]),
                }
                for signal_detector in api.get_signal_detectors(engine_id, client)
            ]

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Output(self.signal_edit_placeholder_id, "hidden"),
            Input(self.add_button_id, "n_clicks"),
            State(*self.engine_layout.get_id()),
            State(self.legend_id, "children"),
            State(*self.signal_detector_data_layout.get_data()),
        )
        def add_signal_detector(n_clicks, engine_id, handler_name, data):
            if n_clicks == 0:
                return dash.no_update, dash.no_update, dash.no_update
            handler = detector_handlers[handler_name]
            new_engine_id = handler.create(engine_id, data)

            return new_engine_id, new_engine_id != engine_id

        def register_dropdown_callback(handler):
            @app.callback(
                Output(*self.engine_layout.get_id()),
                Output(self.signal_edit_fieldset_id, "children"),
                Output(self.signal_edit_placeholder_id, "hidden"),
                Input(
                    *self.signal_detector_table.get_dropdown().get_item_n_clicks(
                        handler.id()
                    )
                ),
                State(self.signal_edit_fieldset_id, "children"),
                State(*self.engine_layout.get_id()),
            )
            def add_signal_detector(clicks, fieldset_children, engine_id):
                if clicks == 0:
                    return (dash.no_update, dash.no_update, dash.no_update)
                engine_id = handler.activate(engine_id)

                hide_fieldset = False
                for child in fieldset_children:
                    child_props = child["props"]
                    if "id" not in child_props:
                        continue
                    name = child_props["id"]
                    if "signal-edit-legend" == name:
                        child_props["children"] = handler.name()
                    if "config-" in name:
                        child_props["hidden"] = True
                    if handler.id() in name.replace("config-", ""):
                        if len(child_props["children"]) != 0:
                            child_props["hidden"] = False
                        else:
                            hide_fieldset = True

                return (engine_id, fieldset_children, hide_fieldset)

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Input(self.signal_detector_table.table_id, "data_timestamp"),
            State(self.signal_detector_table.table_id, "data_previous"),
            State(*self.signal_detector_table.get_table()),
            State(*self.engine_layout.get_id()),
        )
        def remove_signal_detector(timestamp, previous, current, engine_id):
            if engine_id is None:
                return dash.no_update

            removed_signal_detectors = [row for row in previous if row not in current]
            if not removed_signal_detectors:
                return dash.no_update

            assert len(removed_signal_detectors) == 1
            removed_sd = removed_signal_detectors[0]
            signal_detector_id = detector_handlers[removed_sd["name"]].get_id(
                removed_sd["config"]
            )
            new_engine_id = api.remove_signal_detector(
                engine_id, signal_detector_id, client
            )

            if new_engine_id is None:
                return dash.no_update
            return new_engine_id

        for sd in get_api_supported_signal_detectors(client):
            if sd not in detector_handlers.keys():
                logger.warning(
                    f"{sd} signal detector is not implemented in the stock market"
                    " visualizer"
                )

        for sd in detector_handlers.keys():
            if sd not in get_api_supported_signal_detectors(client):
                logger.warning(
                    f"{sd} signal detector is implemented in the stock market"
                    " visualizer, but not supported by the engine"
                )

        for _, l in detector_handlers.items():
            register_dropdown_callback(l)
