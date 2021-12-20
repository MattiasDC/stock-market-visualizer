from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

def get_ticker_table_layout():
	return dbc.Container(children=
        [
        html.Div(
            [
            dbc.Input(
                id='add-ticker-input',
                placeholder='Ticker',
                n_submit=0),
            html.Div(dbc.Button('Add',
                id='add-ticker-button',
                n_clicks=0,
                style={'margin-left': 5}),
                className="input-group-append")
            ],
            className="input-group"),
        dcc.Checklist(
            id='show-ticker-table',
            options=[{'label': ' Show Tickers', 'value': 'S'}],
            value=['S'],
            style={'margin-top': 5}),
        dbc.Collapse(
            dash_table.DataTable(
                id='ticker-table',
                columns=[{'name': 'Ticker', 'id': 'ticker-col'}],
                data=[],
                sort_action='native',
                sort_by=[{'column_id' : 'ticker-col', 'direction' : 'asc'}],
                row_deletable=True,
                style_table={'margin-top': 5}),
            id="collapse-ticker-table",
            is_open=True)
        ])