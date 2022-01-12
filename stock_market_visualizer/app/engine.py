from dash import dcc


class EngineLayout:
    def __init__(self):
        self.engine_id = "engine-id"
        self.layout = dcc.Store(id=self.engine_id)

    def get_layout(self):
        return self.layout

    def get_id(self):
        return self.engine_id, "data"
