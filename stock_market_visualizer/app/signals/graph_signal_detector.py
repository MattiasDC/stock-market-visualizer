from collections import OrderedDict

import dash
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash import html
from dash_extensions.enrich import Input, Output, State
from stock_market.common.factory import Factory
from stock_market.ext.signal import (
    GraphSignalDetector,
    Sentiment,
    register_signal_detector_factories,
)
from utils.rnd import get_random_int_excluding

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.dropdown_button import DropdownButton
from stock_market_visualizer.app.signals.common import (
    CustomNameLayout,
    SignalDetectorConfigurationLayout,
    get_sentiment_color,
)


class GraphDetectorHandler:
    def __init__(self, app, client, layout):
        self.__client = client
        self.__layout = layout

        @app.callback(
            Input(*self.__layout.add_node_button.n_clicks()),
            State(*self.__layout.graph.get_elements()),
            Output(*self.__layout.graph.get_elements()),
        )
        def add_node(n_clicks, nodes):
            if nodes is None:
                nodes = []
            node_ids = [node["data"]["id"] for node in nodes]
            nodes.append(
                {
                    "data": {
                        "id": get_random_int_excluding(
                            get_settings().max_id_generator, node_ids
                        ),
                        "label": "",
                    },
                    "classes": "transition",
                }
            )
            return nodes

        @app.callback(
            Input(*self.__layout.add_edge_button.n_clicks()),
            State(*self.__layout.graph.get_elements()),
            State(*self.__layout.graph.get_selected_nodes()),
            Output(*self.__layout.graph.get_elements()),
        )
        def add_edge(n_clicks, elements, selected_nodes):
            if selected_nodes is None or len(selected_nodes) != 2:
                return dash.no_update
            assert elements is not None

            first_node = selected_nodes[0]["id"]
            second_node = selected_nodes[1]["id"]
            edge = {"data": {"source": first_node, "target": second_node}}
            if edge not in elements:
                elements.append(edge)
            return elements

        @app.callback(
            Input(*self.__layout.remove_button.n_clicks()),
            State(*self.__layout.graph.get_selected_nodes()),
            State(*self.__layout.graph.get_selected_edges()),
            State(*self.__layout.graph.get_elements()),
            Output(*self.__layout.graph.get_elements()),
        )
        def remove(n_clicks, selected_nodes, selected_edges, elements):
            if selected_nodes is None:
                selected_nodes = []
            if selected_edges is None:
                selected_edges = []

            selected_elements = selected_nodes + selected_edges
            ids = [node["id"] for node in selected_elements]
            elements = [element for element in elements if "id" in element["data"]]
            elements = [
                element for element in elements if element["data"]["id"] not in ids
            ]

            return elements

        @app.callback(
            Input(*self.__layout.add_detector_button.n_clicks()),
            State(self.__layout.signal_table.table_id, "active_cell"),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            State(*self.__layout.graph.get_elements()),
            State(*self.__layout.graph.get_selected_edges()),
            Output(*self.__layout.graph.get_elements()),
        )
        def add_detector(
            n_clicks, selected_detector_cell, detector_rows, elements, selected_edges
        ):
            if selected_detector_cell is None:
                return dash.no_update
            detector_row = detector_rows[selected_detector_cell["row"]]
            factory = register_signal_detector_factories(Factory())
            detector = factory.create(detector_row["name"], detector_row["config"])
            selected_ids = [edge["id"] for edge in selected_edges]
            for element in elements:
                if element["data"]["id"] in selected_ids:
                    element["data"]["detector_id"] = detector.id
                    element["data"]["detector_name"] = detector.name + "\n\n\u2800"
            return elements

        @app.callback(
            Input(self.__layout.signal_table.table_id, "active_cell"),
            Input(*self.__layout.graph.get_selected_edges()),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            Output(*self.__layout.add_detector_button.get_label()),
            Output(*self.__layout.add_detector_button.get_disabled()),
        )
        def update_detector_label(selected_detector_cell, selected_edges, detectors):
            disabled = (
                selected_detector_cell is None
                or selected_edges is None
                or len(selected_edges) == 0
            )
            if disabled:
                return "Add (selected) detector", disabled
            return (
                "Add " + detectors[selected_detector_cell["row"]]["signal-col"],
                disabled,
            )

        @app.callback(
            Input(*self.__layout.graph.get_selected_nodes()),
            Output(*self.__layout.add_node_type_dropdown_button.get_disabled()),
        )
        def enable_add_signal(selected_nodes):
            return selected_nodes is None or len(selected_nodes) == 0

        @app.callback(
            Input(*self.__layout.graph.get_elements()),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
        )
        def sync_graph_data(elements, data):
            data["graph"] = elements
            return data

        def add_signal_callback(node_type, key, app):
            @app.callback(
                Input(
                    *self.__layout.add_node_type_dropdown_button.get_item_n_clicks(key)
                ),
                State(*self.__layout.graph.get_selected_nodes()),
                State(*self.__layout.graph.get_elements()),
                Output(*self.__layout.graph.get_elements()),
            )
            def add_signal(n_clicks, selected_nodes, elements):
                if n_clicks is None or n_clicks == 0:
                    return dash.no_update
                ids = [node["id"] for node in selected_nodes]
                for element in elements:
                    element_data = element["data"]
                    if element_data["id"] in ids:
                        if node_type is None:
                            del element_data["node_type"]
                            del element_data["color"]
                            element["classes"] = "transition"
                        elif node_type == Sentiment.NEUTRAL:
                            element["classes"] = "initial"
                            element_data["node_type"] = "initial"
                        else:
                            element_data["node_type"] = node_type.value
                            element_data["color"] = get_sentiment_color(node_type)
                            element["classes"] = "signal"
                return elements

        for k, t in self.__layout.node_types.items():
            add_signal_callback(t, k, app)

    def name(self):
        return self.__layout.name

    def id(self):
        return self.name().replace(" ", "")

    def activate(self, engine_id):
        return engine_id

    def create(self, engine_id, data):
        return engine_id

    def get_id(self, config):
        return config


class CytoGraph:
    def __init__(self):
        self.id = "cyto-graph"
        self.graph = cyto.Cytoscape(
            id=self.id,
            layout={"name": "cose"},
            style={
                "width": "100%",
                "height": "400px",
                "background-color": "lightgrey",
            },
            stylesheet=[
                {
                    "selector": "node:selected",
                    "style": {"overlay-opacity": 0.333, "overlay-color": "grey"},
                },
                {
                    "selector": ".signal",
                    "style": {
                        "background-color": "data(color)",
                    },
                },
                {
                    "selector": ".initial",
                    "style": {
                        "background-color": "teal",
                    },
                },
                {
                    "selector": ".transition",
                    "style": {
                        "background-color": "#5DADE2",
                    },
                },
                {
                    "selector": "edge",
                    "style": {
                        "curve-style": "bezier",
                        "target-arrow-shape": "triangle",
                        "label": "data(detector_name)",
                        "font-size": 5,
                        "text-wrap": "wrap",
                        "text-rotation": "autorotate",
                    },
                },
            ],
            elements=[],
        )

    def get_elements(self):
        return self.id, "elements"

    def get_selected_nodes(self):
        return self.id, "selectedNodeData"

    def get_selected_edges(self):
        return self.id, "selectedEdgeData"

    def get_layout(self):
        return self.graph


class Button:
    def __init__(self, identifier, name, disabled=False):
        self.id = identifier
        self.btn = dbc.Button(
            name,
            id=self.id,
            n_clicks=0,
            style={"margin-left": 5, "margin-bottom": 5},
            disabled=disabled,
        )

    def n_clicks(self):
        return self.id, "n_clicks"

    def get_label(self):
        return self.id, "children"

    def get_disabled(self):
        return self.id, "disabled"

    def get_layout(self):
        return self.btn


class GraphDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, signal_table, signal_data_placeholder_layout):
        self.signal_table = signal_table
        self.signal_data_placeholder_layout = signal_data_placeholder_layout

        name = GraphSignalDetector.NAME()
        self.custom_name_layout = CustomNameLayout(name)
        self.add_node_button = Button("add-node", "Add node")
        self.add_edge_button = Button("add-edge", "Add edge")
        self.add_detector_button = Button("add-detector", "Add detector", True)
        self.node_types = self.get_node_type_map()
        self.add_node_type_dropdown_button = DropdownButton(
            "add-node-type-dropdown-button",
            "node type",
            list(self.node_types.keys()),
            True,
            style={"margin-left": 5, "bottom": 2},
        )
        self.remove_button = Button("remove", "Remove")
        self.graph = CytoGraph()

        super().__init__(
            name,
            [
                self.custom_name_layout.get_layout(),
                html.Br(),
                self.add_node_button.get_layout(),
                self.add_edge_button.get_layout(),
                self.add_detector_button.get_layout(),
                self.add_node_type_dropdown_button.get_layout(),
                self.remove_button.get_layout(),
                self.graph.get_layout(),
            ],
        )

    def get_node_type_map(self):
        node_types = OrderedDict(
            [
                (s.value.lower().capitalize(), s)
                for s in Sentiment
                if s != Sentiment.NEUTRAL
            ]
        )
        node_types["Initial"] = Sentiment.NEUTRAL
        node_types["None"] = None
        return node_types

    def get_handler(self, app, client):
        return GraphDetectorHandler(app, client, self)
