from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

from stock_market_visualizer.app.indicators import get_indicators

def get_themes():
    return [dbc.themes.BOOTSTRAP]
   
def get_indicator_modals():
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

def get_layout():
    earliest_start = dt.date(1990, 1, 1)

    return dbc.Container(children=[
        html.H1(children='Stock Market Engine'),
        dbc.Container(
            [
             dbc.Row(
                [
                dbc.Col(
                    [
                    html.P("Start"),
                    dcc.DatePickerSingle(
                        id='date-picker-start',
                        min_date_allowed=earliest_start,
                        max_date_allowed=dt.datetime.now().date() - dt.timedelta(days=1),
                        placeholder='Start Date',
                        display_format='D-M-Y')
                    ]),
                dbc.Col(
                    [
                    html.P("End"),
                    dcc.DatePickerSingle(
                        id='date-picker-end',
                        min_date_allowed=earliest_start+dt.timedelta(days=1),
                        placeholder='End Date',
                        display_format='D-M-Y')
                    ]),
                dbc.Col(children=
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
                            row_deletable=True,
                            style_table={'margin-top': 5}),
                        id="collapse-ticker-table",
                        is_open=True)
                    ]),
                dbc.Col(children=
                    [
                    dbc.DropdownMenu(
                        id='indicator-dropdown',
                        label="Add Indicator",
                        children=[dbc.DropdownMenuItem(indicator.__name__,
                                                       id=f"dropdown-{indicator.__name__}",
                                                       n_clicks=0) for indicator in get_indicators().keys()],
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
                ])
        ]),
        dcc.Graph(id='stock-market-graph'),
        dcc.Store(id='engine-id')
    ] + get_indicator_modals())