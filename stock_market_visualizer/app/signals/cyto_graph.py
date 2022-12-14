import dash_cytoscape as cyto


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
                    "selector": ":selected",
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
                        "content": "Initial",
                        "text-halign": "center",
                        "text-valign": "center",
                        "font-size": 10,
                    },
                },
                {
                    "selector": ".transition_node",
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
                        "line-color": "data(color)",
                        "target-arrow-color": "data(color)",
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
