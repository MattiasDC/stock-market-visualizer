import dash_bootstrap_components as dbc
from dash import dash_table
from dash import dcc
from dash import html

import stock_market_visualizer.app.layouts.dropdown_button_layout as dropdown_button_layout

def get_layout(name, items, extra_columns, disabled):
	return dbc.Container(children=
        [
        dropdown_button_layout.get_layout(name, name, items, disabled),
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
                sort_action='native',
                sort_by=[{'column_id' : f'{name}-col', 'direction' : 'asc'}],
                row_deletable=True,
                row_selectable="multi",
                selected_rows=[],
                style_table={'margin-top': 5}),
            id=f"collapse-{name}-table",
            is_open=True)
        ])