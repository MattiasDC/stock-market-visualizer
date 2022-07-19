import json
from collections import OrderedDict
from functools import partial

import dash
from dash import html
from dash_extensions.enrich import Input, Output, State
from stock_market.common.factory import Factory
from stock_market.ext.signal import (
    EnterOrExit,
    GraphSignalDetector,
    GraphSignalDetectorBuilder,
    Sentiment,
    register_signal_detector_factories,
)
from utils.rnd import get_random_int_excluding

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.signals.common import (
    CustomNameLayout,
    SignalDetectorConfigurationLayout,
    get_random_detector_id,
    get_sentiment_color,
    get_signal_detector,
)
from stock_market_visualizer.app.signals.cyto_graph import CytoGraph
from stock_market_visualizer.common.button import Button
from stock_market_visualizer.common.dropdown_button import DropdownButton

GRAY_COLOR = "#999999"


def get_nodes(elements):
    return [e for e in elements if "connection" not in e["classes"]]


def get_edges(elements):
    return [e for e in elements if "connection" in e["classes"]]


def get_ids(elements):
    return [e["data"]["id"] for e in elements]


def get_elements_by_ids(ids, elements, include=True):
    if include:
        return [e for e in elements if e["data"]["id"] in ids]
    return [e for e in elements if e["data"]["id"] not in ids]


def get_element_by_id(identifier, elements):
    return get_elements_by_ids([identifier], elements)[0]


class GraphDetectorHandler:
    def __init__(self, app, engine_api, layout):
        self.__engine_api = engine_api
        self.__layout = layout

        @app.callback(
            Input(*self.__layout.add_node_button.n_clicks()),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
        )
        def add_node(n_clicks, data):
            if "graph" not in data:
                data["graph"] = []
            data["graph"].append(
                {
                    "data": {
                        "id": get_random_int_excluding(
                            get_settings().max_id_generator, get_ids(data["graph"])
                        ),
                        "label": "",
                    },
                    "classes": "transition_node",
                }
            )
            return data

        @app.callback(
            Input(*self.__layout.remove_button.n_clicks()),
            State(*self.__layout.graph.get_selected_nodes()),
            State(*self.__layout.graph.get_selected_edges()),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
        )
        def remove(n_clicks, selected_nodes, selected_edges, data):
            if selected_nodes is None:
                selected_nodes = []
            if selected_edges is None:
                selected_edges = []

            selected_elements = selected_nodes + selected_edges
            ids = [int(node["id"]) for node in selected_elements]
            data["graph"] = get_elements_by_ids(ids, data.get("graph", []), False)
            return data

        def create_detector(n_clicks, selected_detector_cell, detector_rows):
            if selected_detector_cell is None:
                return None
            if n_clicks is None or n_clicks == 0:
                return None

            detector_row = detector_rows[selected_detector_cell["row"]]
            factory = register_signal_detector_factories(Factory())
            return factory.create(detector_row["name"], detector_row["config"])

        def set_detector_on_edge(edge, detector):
            edge["data"]["detector_id"] = detector.id
            edge["data"]["detector_name"] = detector.name + "\n\n\u2800"

        @app.callback(
            Input(*self.__layout.add_edge_detector_button.n_clicks()),
            State(self.__layout.signal_table.table_id, "active_cell"),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            State(*self.__layout.graph.get_selected_nodes()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.add_edge_detector_button.n_clicks()),
        )
        def add_detector(
            n_clicks, selected_detector_cell, detector_rows, data, selected_nodes
        ):
            def add_edge(selected_nodes, detector):
                if selected_nodes is None:
                    return None

                nof_selected_nodes = len(selected_nodes)
                if (
                    selected_nodes is None
                    or nof_selected_nodes == 0
                    or nof_selected_nodes > 2
                ):
                    return None

                first_node = int(selected_nodes[0]["id"])
                second_node = first_node
                if nof_selected_nodes == 2:
                    second_node = int(selected_nodes[1]["id"])

                color = GRAY_COLOR
                for info in get_element_by_id(first_node, get_nodes(data["graph"]))[
                    "data"
                ].get("class_info", []):
                    if info["enter_or_exit"] == EnterOrExit.EXIT.value:
                        color = get_sentiment_color(Sentiment(info["node_type"]))

                edge = {
                    "data": {
                        "source": first_node,
                        "target": second_node,
                        "color": color,
                        "id": get_random_int_excluding(
                            get_settings().max_id_generator, get_ids(data["graph"])
                        ),
                    },
                    "classes": "connection",
                }
                set_detector_on_edge(edge, detector)
                return edge

            detector = create_detector(n_clicks, selected_detector_cell, detector_rows)
            if detector is None:
                return dash.no_update, 0

            edge = add_edge(selected_nodes, detector)
            if edge is None:
                return dash.no_update, 0
            data["graph"].append(edge)
            return data, 0

        @app.callback(
            Input(*self.__layout.add_edge_detector_button.n_clicks()),
            State(self.__layout.signal_table.table_id, "active_cell"),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            State(*self.__layout.graph.get_selected_edges()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.add_edge_detector_button.n_clicks()),
        )
        def change_detector(
            n_clicks, selected_detector_cell, detector_rows, data, selected_edges
        ):
            if selected_edges is None or len(selected_edges) == 0:
                return dash.no_update, 0

            detector = create_detector(n_clicks, selected_detector_cell, detector_rows)
            if detector is None:
                return dash.no_update, 0

            ids = [int(node["id"]) for node in selected_edges]
            for e in data["graph"]:
                if e["data"]["id"] in ids:
                    set_detector_on_edge(e, detector)

            return data, 0

        @app.callback(
            Input(self.__layout.signal_table.table_id, "active_cell"),
            Input(*self.__layout.graph.get_selected_nodes()),
            Input(*self.__layout.graph.get_selected_edges()),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            Output(*self.__layout.add_edge_detector_button.get_label()),
            Output(*self.__layout.add_edge_detector_button.get_disabled()),
        )
        def update_detector_label(
            selected_detector_cell, selected_nodes, selected_edges, detectors
        ):
            enabled = selected_detector_cell is not None and (
                (
                    selected_nodes is not None
                    and (len(selected_nodes) == 2 or len(selected_nodes) == 1)
                )
                or (selected_edges is not None)
            )
            selected_detector = "(selected detector)"
            if selected_detector_cell is not None:
                selected_detector = detectors[selected_detector_cell["row"]][
                    "signal-col"
                ]
            return (
                "Add " + selected_detector + " edge",
                not enabled,
            )

        @app.callback(
            Input(*self.__layout.graph.get_selected_nodes()),
            Output(*self.__layout.add_node_type_dropdown_button.get_disabled()),
        )
        def enable_add_signal(selected_nodes):
            return selected_nodes is None or len(selected_nodes) == 0

        @app.callback(
            Input(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.graph.get_elements()),
        )
        def sync_graph_data(data):
            return data.get("graph", [])

        @app.callback(
            Input(*self.__layout.custom_name_layout.get_name()),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
        )
        def update_custom_name(custom_name, data):
            data["signal_name"] = custom_name
            return data

        def add_signal_callback(node_changer, key, app):
            @app.callback(
                Input(
                    *self.__layout.add_node_type_dropdown_button.get_item_n_clicks(key)
                ),
                State(*self.__layout.graph.get_selected_nodes()),
                State(*self.__layout.signal_data_placeholder_layout.get_data()),
                Output(*self.__layout.signal_data_placeholder_layout.get_data()),
            )
            def add_signal(n_clicks, selected_nodes, data):
                if n_clicks is None or n_clicks == 0:
                    return dash.no_update
                elements = data["graph"]
                ids = [int(node["id"]) for node in selected_nodes]
                for element in get_elements_by_ids(ids, get_nodes(elements)):
                    elements = node_changer(element, elements)
                return data

        for k, node_changer in self.__layout.node_types.items():
            add_signal_callback(node_changer, k, app)

    def name(self):
        return self.__layout.name

    def id(self):
        return self.name().replace(" ", "")

    def activate(self, engine_id, data):
        data["graph"] = []
        return engine_id, data

    def create(self, engine_id, data):
        def process_node(node, builder):
            node_data = node["data"]
            identifier = str(node_data["id"])
            builder = builder.add_state(identifier)
            if "initial" in node.get("classes", []):
                builder = builder.set_initial_state(identifier)
            if "signal" in node.get("classes", []):
                for class_info in node_data["class_info"]:
                    if class_info["type"] == "signal":
                        builder = builder.add_signal_description(
                            identifier,
                            Sentiment(class_info["node_type"]),
                            EnterOrExit(class_info["enter_or_exit"]),
                        )
            return builder

        def process_edge(edge, engine_id, builder):
            detector_id = edge.get("detector_id", None)
            if detector_id is None:
                return builder

            engine = self.__engine_api.get_engine(engine_id)
            if engine is None:
                return builder

            detector = get_signal_detector(detector_id, engine)
            if detector not in builder.detectors:
                builder = builder.add_detector(detector)
            builder = builder.add_transition(
                str(edge["source"]), str(edge["target"]), detector_id
            )
            return builder

        if "graph" not in data:
            return engine_id

        engine = self.__engine_api.get_engine(engine_id)
        if engine is None:
            return engine_id

        elements = data["graph"]
        builder = GraphSignalDetectorBuilder(get_random_detector_id(engine))

        if "signal_name" not in data or data["signal_name"] is None:
            return engine_id
        builder = builder.set_name(data["signal_name"])

        # first add all states
        for n in get_nodes(elements):
            builder = process_node(n, builder)

        # then add all transitions
        for e in get_edges(elements):
            builder = process_edge(e["data"], engine_id, builder)

        if builder.initial_state is None:
            return engine_id

        detector = builder.build()
        new_engine = engine.add_signal_detector(
            {
                "static_name": self.name(),
                "config": detector.to_json(),
            },
        )
        if new_engine is None:
            return engine_id
        return new_engine.engine_id

    def get_id(self, config):
        return json.loads(config)["id"]


class GraphDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, signal_table, signal_data_placeholder_layout):
        self.signal_table = signal_table
        self.signal_data_placeholder_layout = signal_data_placeholder_layout

        name = GraphSignalDetector.NAME()
        self.custom_name_layout = CustomNameLayout(name)
        self.add_node_button = Button("add-node", "Add node")
        self.add_edge_detector_button = Button(
            "add-edge-detector", "Add (selected detector) edge", True
        )
        self.node_types = self.get_node_type_action_map()
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
                self.add_edge_detector_button.get_layout(),
                self.add_node_type_dropdown_button.get_layout(),
                self.remove_button.get_layout(),
                self.graph.get_layout(),
            ],
        )

    def get_node_type_action_map(self):
        def add_class(element, class_type):
            element["classes"] = (element["classes"] + " " + class_type).strip()
            return element

        def remove_class(element, class_type):
            element["classes"] = element["classes"].replace(class_type, "").strip()
            return element

        def add_signal(signal_type, enter_or_exit, element, elements):
            data = element["data"]
            if "class_info" not in data:
                data["class_info"] = []
            spec = {
                "type": "signal",
                "node_type": signal_type.value,
                "enter_or_exit": enter_or_exit.value,
            }
            if spec in data["class_info"]:
                return element
            for i, ci in enumerate(list(data["class_info"])):
                if (
                    spec["type"] == "signal"
                    and ci["enter_or_exit"] == enter_or_exit.value
                ):
                    del data["class_info"][i]

            data["class_info"].append(spec)

            if enter_or_exit == EnterOrExit.ENTER:
                data["color"] = get_sentiment_color(signal_type)
            else:
                if "color" not in data:
                    data["color"] = "#5DADE2"
                for e in elements:
                    if "connection" not in e["classes"]:
                        continue
                    if e["data"]["source"] == data["id"]:
                        e["data"]["color"] = get_sentiment_color(signal_type)

            if "signal" not in element["classes"]:
                element = remove_class(element, "transition_node")
                element = add_class(element, "signal")

            return elements

        def set_initial_node(element, elements):
            for e in elements:
                if "initial" in e["classes"]:
                    e = remove_class(e, "initial")
            element = add_class(element, "initial")
            return elements

        def remove_node_type(element, elements):
            data = element["data"]
            if "class_info" in data:
                del data["class_info"]
            if "color" in data:
                del data["color"]
            for e in get_edges(elements):
                edge_data = e["data"]
                if edge_data["source"] == data["id"] and "color" in edge_data:
                    edge_data["color"] = GRAY_COLOR
            element["classes"] = "transition_node"
            return elements

        node_types = OrderedDict(
            [
                (
                    s.value.lower().capitalize()
                    + " "
                    + str(enter_or_exit.value).lower().capitalize(),
                    partial(add_signal, s, enter_or_exit),
                )
                for s in Sentiment
                for enter_or_exit in EnterOrExit
                if s != Sentiment.NEUTRAL
            ]
        )
        node_types["Initial"] = set_initial_node
        node_types["None"] = remove_node_type
        return node_types

    def get_handler(self, app, engine_api):
        return GraphDetectorHandler(app, engine_api, self)
