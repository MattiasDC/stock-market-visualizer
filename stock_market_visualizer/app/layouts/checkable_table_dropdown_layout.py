import dash_bootstrap_components as dbc
from dash import dash_table
from dash import dcc
from dash import html

def get_checkable_table_dropdown_layout(name, items, extra_columns, disabled):
	return dbc.Container(children=
        [
        dbc.DropdownMenu(
            id=f'{name}-dropdown',
            label=f"Add {name.capitalize()}",
            children=[dbc.DropdownMenuItem(item,
                                           id=f"dropdown-{item}",
                                           n_clicks=0) for item in sorted(items)],
            disabled=disabled),
        dcc.Checklist(
            id=f'show-{name}-table',
            options=[{'label': f'Show {name.capitalize()}s', 'value': 'S'}],
            value=['S'],
            style={'margin-top': 5}),
        dbc.Collapse(
            dash_table.DataTable(
                id=f'{name}-table',
                columns=[{'name': f'{name.capitalize()}', 'id': f'{name}-col'}] + extra_columns,
                data=[],
                row_deletable=True,
                style_table={'margin-top': 5}),
            id=f"collapse-{name}-table",
            is_open=True)
        ])