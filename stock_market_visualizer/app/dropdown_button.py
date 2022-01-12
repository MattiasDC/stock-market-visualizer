import dash_bootstrap_components as dbc


class DropdownButton:
    def __init__(self, identifier, name, items, disabled):
        self.identifier = identifier
        self.name = name
        self.items = items
        self.disabled = disabled
        self.dropdown_id = f"{identifier}-dropdown"
        self.layout = dbc.DropdownMenu(
            id=self.dropdown_id,
            label=f"Add {self.name.capitalize()}",
            class_name="d-inline",
            children=[
                dbc.DropdownMenuItem(item, id=self.get_item(item), n_clicks=0)
                for item in sorted(self.items)
            ],
            disabled=self.disabled,
        )

    def get_label(self):
        return self.dropdown_id, "label"

    def get_disabled(self):
        return self.dropdown_id, "disabled"

    def get_item(self, item):
        return f'dropdown-{self.identifier}-{item.replace(" ", "")}'

    def get_item_n_clicks(self, item):
        return self.get_item(item), "n_clicks"

    def get_layout(self):
        return self.layout
