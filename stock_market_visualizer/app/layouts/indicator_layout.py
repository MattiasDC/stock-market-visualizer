import dash_bootstrap_components as dbc
from dash import dash_table
from dash import dcc
from dash import html

from stock_market_visualizer.app.indicators import get_indicators

def get_create_indicator_modals_layout():
    indicators = get_indicators()
    return [
           dbc.Modal(
               [
               dbc.ModalHeader(dbc.ModalTitle(indicator.__name__)),
               dbc.ModalBody(dbc.InputGroup(children=
                   [
                   html.Div(
                        [
                        html.P(f"{argument}:"),
                        html.Div(
                            dbc.Input(id=f'{indicator.__name__}-{argument}-input', style={'margin-left': 5}, type="number"),
                            className="input-group-append")
                        ],
                        className="input-group")
                   for argument in indicators[indicator]])),
               dbc.ModalFooter(dbc.Button("Close", id=f"close-{indicator.__name__}", className="ms-auto", n_clicks=0))
               ],
               id=f"modal-{indicator.__name__}",
               is_open=False)
           for indicator in indicators]

def get_indicator_table_layout():
	return dbc.Container(children=
        [
        dbc.DropdownMenu(
            id='indicator-dropdown',
            label="Add Indicator",
            children=[dbc.DropdownMenuItem(indicator.__name__,
                                           id=f"dropdown-{indicator.__name__}",
                                           n_clicks=0) for indicator in get_indicators()],
            disabled=True),
        dcc.Checklist(
            id='show-indicator-table',
            options=[{'label': ' Show Indicators', 'value': 'S'}],
            value=['S'],
            style={'margin-top': 5}),
        dbc.Collapse(
            dash_table.DataTable(
                id='indicator-table',
                columns=[{'name': 'Indicator', 'id': 'indicator-col'},
                         {'name': 'Ticker', 'id': 'ticker-col'}],
                data=[],
                row_deletable=True,
                style_table={'margin-top': 5}),
            id="collapse-indicator-table",
            is_open=True)
        ])