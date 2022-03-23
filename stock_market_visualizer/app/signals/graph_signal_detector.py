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

import stock_market_visualizer.app.sme_api_helper as api
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
            node_ids = get_ids(nodes)
            nodes.append(
                {
                    "data": {
                        "id": get_random_int_excluding(
                            get_settings().max_id_generator, node_ids
                        ),
                        "label": "",
                    },
                    "classes": "transition_node",
                }
            )
            return nodes

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
            return get_elements_by_ids(ids, elements, False)

        @app.callback(
            Input(*self.__layout.add_edge_detector_button.n_clicks()),
            State(self.__layout.signal_table.table_id, "active_cell"),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            State(*self.__layout.graph.get_elements()),
            State(*self.__layout.graph.get_selected_nodes()),
            Output(*self.__layout.graph.get_elements()),
        )
        def add_detector(
            n_clicks, selected_detector_cell, detector_rows, elements, selected_nodes
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

                first_node = selected_nodes[0]["id"]
                second_node = first_node
                if nof_selected_nodes == 2:
                    second_node = selected_nodes[1]["id"]

                color = "#999999"
                for info in get_element_by_id(first_node, elements)["data"].get(
                    "class_info", []
                ):
                    if info["enter_or_exit"] == EnterOrExit.EXIT.value:
                        color = get_sentiment_color(Sentiment(info["node_type"]))

                return {
                    "data": {
                        "source": first_node,
                        "target": second_node,
                        "detector_id": detector.id,
                        "detector_name": detector.name + "\n\n\u2800",
                        "color": color,
                    },
                    "classes": "connection",
                }

            if selected_detector_cell is None:
                return dash.no_update

            detector_row = detector_rows[selected_detector_cell["row"]]
            factory = register_signal_detector_factories(Factory())
            detector = factory.create(detector_row["name"], detector_row["config"])

            edge = add_edge(selected_nodes, detector)
            if edge is None:
                return dash.no_update
            elements.append(edge)
            return elements

        @app.callback(
            Input(self.__layout.signal_table.table_id, "active_cell"),
            Input(*self.__layout.graph.get_selected_nodes()),
            State(self.__layout.signal_table.table_id, "derived_virtual_data"),
            Output(*self.__layout.add_edge_detector_button.get_label()),
            Output(*self.__layout.add_edge_detector_button.get_disabled()),
        )
        def update_detector_label(selected_detector_cell, selected_nodes, detectors):
            disabled = (
                selected_detector_cell is None
                or selected_nodes is None
                or len(selected_nodes) != 2
            )
            selected_detector = "(selected detector)"
            if selected_detector_cell is not None:
                selected_detector = detectors[selected_detector_cell["row"]][
                    "signal-col"
                ]
            return (
                "Add " + selected_detector + " edge",
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

        @app.callback(
            Input(*self.__layout.custom_name_layout.get_name()),
            State(*self.__layout.signal_data_placeholder_layout.get_data()),
            Output(*self.__layout.signal_data_placeholder_layout.get_data()),
        )
        def update_custom_name(custom_name, data):
            data["name"] = custom_name
            return data

        def add_signal_callback(node_changer, key, app):
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
                for element in get_elements_by_ids(ids, get_nodes(elements)):
                    element = node_changer(element, elements)
                return elements

        for k, node_changer in self.__layout.node_types.items():
            add_signal_callback(node_changer, k, app)

    def name(self):
        return self.__layout.name

    def id(self):
        return self.name().replace(" ", "")

    def activate(self, engine_id):
        return engine_id

    def create(self, engine_id, data):
        def process_node(node, builder):
            node_data = node["data"]
            identifier = node_data["id"]
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
            detector = get_signal_detector(detector_id, engine_id, self.__client)
            if detector not in builder.detectors:
                builder = builder.add_detector(detector)
            builder = builder.add_transition(
                edge["source"], edge["target"], detector_id
            )
            return builder

        if "graph" not in data:
            return engine_id

        elements = data["graph"]
        builder = GraphSignalDetectorBuilder(
            get_random_detector_id(engine_id, self.__client)
        )

        if "name" not in data or data["name"] is None:
            return engine_id
        builder = builder.set_name(data["name"])

        # first add all states
        for n in get_nodes(elements):
            builder = process_node(n, builder)

        # then add all transitions
        for e in get_edges(elements):
            builder = process_edge(e["data"], engine_id, builder)

        if builder.initial_state is None:
            return engine_id

        detector = builder.build()
        new_engine_id = api.add_signal_detector(
            engine_id,
            {
                "static_name": self.name(),
                "config": detector.to_json(),
            },
            self.__client,
        )

        if new_engine_id is None:
            return engine_id
        return new_engine_id

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
                for e in get_edges(elements):
                    if e["data"]["source"] == data["id"]:
                        e["data"]["color"] = get_sentiment_color(signal_type)

            if "signal" not in element["classes"]:
                element = remove_class(element, "transition_node")
                element = add_class(element, "signal")

            return element

        def set_initial_node(element, elements):
            for e in elements:
                if "initial" in e["classes"]:
                    e = remove_class(e, "initial")
            element = add_class(element, "initial")
            return element

        def remove_node_type(element, elements):
            data = element["data"]
            if "class_info" in data:
                del data["class_info"]
            if "color" in data:
                del data["color"]
            for e in get_edges(elements):
                edge_data = e["data"]
                if edge_data["source"] == data["id"] and "color" in edge_data:
                    edge_data["color"] = "#999999"
            element["classes"] = "transition_node"
            return element

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

    def get_handler(self, app, client):
        return GraphDetectorHandler(app, client, self)
