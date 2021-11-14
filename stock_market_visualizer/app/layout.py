from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

def get_themes():
    return [dbc.themes.BOOTSTRAP]
    
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
                        dbc.Col(
                            [
                                dbc.Row(
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
                                        className="input-group")),
                                dbc.Row(
                                    [
                                        dcc.Checklist(
                                            id='show-ticker-table',
                                            options=[{'label': ' Show Tickers', 'value': 'S'}],
                                            value=['S']),
                                        dbc.Collapse(
                                            dash_table.DataTable(
                                                id='ticker-table',
                                                columns=[{
                                                    'name': 'Ticker',
                                                    'id': 'ticker-col'}],
                                                data=[],
                                                row_deletable=True,
                                                style_table={'margin-top': 10}),
                                            id="collapse-ticker-table",
                                            is_open=True)
                                    ])
                            ])
                    ])
            ]),
        dcc.Graph(id='stock-market-graph'),
        dcc.Store(id='engine-id')
    ])