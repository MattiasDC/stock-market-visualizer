from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Output, Input

from stock_market_visualizer.app.dropdown_button import DropdownButton

class CheckableTableLayout:
    def __init__(self, name, items, extra_columns, disabled):
        self.name = name
        self.extra_columns = extra_columns

        self.show_table = f'show-{self.name}-table'
        self.table_id = f'{name}-table'
        self.collapse_table_id = f'collapse-{name}-table'
        self.main_column = f'{name}-col'

        self.dropdown_button = DropdownButton(name, name, items, disabled)

    def get_table(self):
        return self.table_id, 'data'

    def get_table_selected(self):
        return self.table_id, 'selected_rows'
        
    def get_show_table(self):
        return self.show_table, 'value'

    def get_dropdown(self):
        return self.dropdown_button

    def get_layout(self):
    	return dbc.Container(children=
            [
            self.dropdown_button.get_layout(),
            dcc.Checklist(
                id=self.show_table,
                options=[{'label': f'Show {self.name.capitalize()}s', 'value': 'S'}],
                value=['S'],
                style={'margin-top': 5}),
            dbc.Collapse(
                dash_table.DataTable(
                    id=self.table_id,
                    columns=[{'name': f'{self.name.capitalize()}', 'id': self.main_column}] + self.extra_columns,
                    data=[],
                    sort_action='native',
                    sort_by=[{'column_id' : self.main_column, 'direction' : 'asc'}],
                    row_deletable=True,
                    row_selectable="multi",
                    selected_rows=[],
                    style_table={'margin-top': 5}),
                id=self.collapse_table_id,
                is_open=True)
            ])

    def register_callbacks(self, app):
        @app.callback(
            Input(*self.get_show_table()),
            Output(self.collapse_table_id, 'is_open'))
        def toggle_collapse_table(show_table):
            return 'S' in show_table