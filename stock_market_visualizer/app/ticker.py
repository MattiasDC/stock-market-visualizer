import dash
import dash_bootstrap_components as dbc
from dash import dash_table, dcc, html
from dash_extensions.enrich import Input, Output, State


class TickerLayout:
    def __init__(self, engine_layout):
        self.engine_layout = engine_layout
        self.add_ticker_input = "add-ticker-input"
        self.add_ticker_button = "add-ticker-button"
        self.show_ticker_table = "show-ticker-table"
        self.ticker_table_id = "ticker-table"
        self.collapse_ticker_table = "collapse-ticker-table"
        self.layout = dbc.Container(
            children=[
                html.Div(
                    [
                        dbc.Input(
                            id=self.add_ticker_input,
                            placeholder="Yahoo Ticker",
                            n_submit=0,
                        ),
                        html.Div(
                            dbc.Button(
                                "Add",
                                id=self.add_ticker_button,
                                n_clicks=0,
                                style={"margin-left": 5},
                            ),
                            className="input-group-append",
                        ),
                    ],
                    className="input-group",
                ),
                dcc.Checklist(
                    id=self.show_ticker_table,
                    options=[{"label": " Show Tickers", "value": True}],
                    value=[True],
                    style={"margin-top": 5},
                ),
                dbc.Collapse(
                    dash_table.DataTable(
                        id=self.ticker_table_id,
                        columns=[{"name": "Ticker", "id": "ticker-col"}],
                        data=[],
                        sort_action="native",
                        sort_by=[{"column_id": "ticker-col", "direction": "asc"}],
                        row_deletable=True,
                        style_table={"margin-top": 5},
                    ),
                    id=self.collapse_ticker_table,
                    is_open=True,
                ),
            ]
        )

    def get_tickers(self, rows):
        return [row["ticker-col"] for row in rows]

    def get_add_ticker_input_n_submit(self):
        return self.add_ticker_input, "n_submit"

    def get_add_ticker_input_value(self):
        return self.add_ticker_input, "value"

    def get_add_ticker_button(self):
        return self.add_ticker_button, "n_clicks"

    def get_ticker_table(self):
        return self.ticker_table_id, "data"

    def get_active_ticker(self):
        return self.ticker_table_id, "active_cell"

    def get_ticker_table_virtual(self):
        return self.ticker_table_id, "derived_virtual_data"

    def get_show_ticker_table(self):
        return self.show_ticker_table, "value"

    def get_layout(self):
        return self.layout

    def register_callbacks(self, app, engine_api):
        @app.callback(
            Input(*self.get_show_ticker_table()),
            Output(self.collapse_ticker_table, "is_open"),
        )
        def toggle_collapse_table(show_table):
            return True in show_table

        @app.callback(
            Output(*self.get_ticker_table()), Input(*self.engine_layout.get_id())
        )
        def update_ticker_table(engine_id):
            engine = engine_api.get_engine(engine_id)
            if engine is None:
                return dash.no_update

            tickers = engine.get_tickers()
            return [{"ticker-col": ticker} for ticker in tickers]

        @app.callback(
            Output(*self.get_add_ticker_input_value()),
            Output(*self.engine_layout.get_id()),
            Input(*self.get_add_ticker_button()),
            Input(*self.get_add_ticker_input_n_submit()),
            State(*self.get_add_ticker_input_value()),
            State(*self.engine_layout.get_id()),
            State(*self.get_ticker_table()),
        )
        def add_ticker(n_clicks, n_submit, ticker_symbol, engine_id, rows):
            no_update = (dash.no_update, dash.no_update)
            if ticker_symbol is None:
                return no_update

            ticker_symbol = str.upper(ticker_symbol.rstrip())
            if ticker_symbol in self.get_tickers(rows) or not ticker_symbol:
                return no_update

            if n_clicks == 0 and n_submit == 0:
                return no_update

            if engine_id is None:
                return no_update

            engine = engine_api.get_engine(engine_id)
            if engine is None:
                return no_update

            engine = engine.add_ticker(ticker_symbol)
            if engine is None:
                return no_update

            return "", engine.engine_id

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Input(self.ticker_table_id, "data_timestamp"),
            State(self.ticker_table_id, "data_previous"),
            State(*self.get_ticker_table()),
            State(*self.engine_layout.get_id()),
        )
        def remove_ticker(timestamp, previous, current, engine_id):
            if previous is None:
                return dash.no_update

            if engine_id is None:
                return dash.no_update

            removed_ticker_symbols = [row for row in previous if row not in current]
            if not removed_ticker_symbols:
                return dash.no_update

            assert len(removed_ticker_symbols) == 1
            ticker_symbol = next(iter(removed_ticker_symbols[0].values()))

            engine = engine_api.get_engine(engine_id)
            if engine is None:
                return dash.no_update

            engine = engine.remove_ticker(ticker_symbol)
            if engine is None:
                return dash.no_update

            return engine.engine_id
