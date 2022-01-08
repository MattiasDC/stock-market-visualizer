import dash_bootstrap_components as dbc

def get_layout(id, name, items, disabled):
	return dbc.DropdownMenu(
            id=f'{id}-dropdown',
            label=f"Add {name.capitalize()}",
            class_name="d-inline",
            children=[dbc.DropdownMenuItem(item,
                                           id=f'dropdown-{id}-{item.replace(" ", "")}',
                                           n_clicks=0) for item in sorted(items)],
            disabled=disabled)