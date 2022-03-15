import dash_bootstrap_components as dbc


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
