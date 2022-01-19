import dash_bootstrap_components as dbc
from dash import html
from dash_extensions.enrich import Input, Output, State
from stock_market.ext.indicator import ExponentialMovingAverage, Identity, MovingAverage
from utils.inspection import get_constructor_arguments

from stock_market_visualizer.app.checkable_table import CheckableTableLayout


def get_indicators_with_identity():
    return {
        i: get_constructor_arguments(i)
        for i in [MovingAverage, ExponentialMovingAverage, Identity]
    }


def get_indicators():
    indicators = get_indicators_with_identity()
    indicators.pop(Identity)
    return indicators


class ModalIndicatorCreatorLayout:
    def __init__(self, name):
        self.name = name
        self.indicators = get_indicators()
        self.layout = [
            dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(indicator.__name__)),
                    dbc.ModalBody(
                        dbc.InputGroup(
                            children=[
                                html.Div(
                                    [
                                        html.P(f"{argument}:"),
                                        html.Div(
                                            dbc.Input(
                                                id=self.get_argument(
                                                    indicator, argument
                                                ),
                                                style={"margin-left": 5},
                                                type="number",
                                            ),
                                            className="input-group-append",
                                        ),
                                    ],
                                    className="input-group",
                                )
                                for argument in self.indicators[indicator]
                            ]
                        )
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Add",
                            id=self.get_add(indicator),
                            className="ms-auto",
                            n_clicks=0,
                        )
                    ),
                ],
                id=self.get_modal(indicator),
                is_open=False,
            )
            for indicator in self.indicators
        ]

    def get_argument(self, indicator, argument):
        return f"{self.name}-{indicator.__name__}-{argument}-input"

    def get_argument_value(self, indicator, argument):
        return self.get_argument(indicator, argument), "value"

    def get_modal(self, indicator):
        return f"modal-{self.name}-{indicator.__name__}"

    def get_is_open(self, indicator):
        return self.get_modal(indicator), "is_open"

    def get_add(self, indicator):
        return f"add-{self.name}-{indicator.__name__}"

    def get_add_n_clicks(self, indicator):
        return self.get_add(indicator), "n_clicks"

    def get_layout(self):
        return self.layout


class IndicatorLayout:
    def __init__(self, engine_layout, ticker_layout):
        self.engine_layout = engine_layout
        self.ticker_layout = ticker_layout
        self.checkable_table = CheckableTableLayout(
            "indicator",
            [i.__name__ for i in get_indicators()],
            [{"name": "Ticker", "id": "ticker-col"}],
            True,
        )
        self.modal_creator = ModalIndicatorCreatorLayout("indicator")

    def get_layout(self):
        return [self.checkable_table.get_layout()] + self.modal_creator.get_layout()

    def register_callbacks(self, app, client_getter):
        self.checkable_table.register_callbacks(app)

        def get_active_ticker(cell, rows):
            return rows[cell["row"]][cell["column_id"]]

        @app.callback(
            Input(*self.ticker_layout.get_show_ticker_table()),
            Input(*self.ticker_layout.get_active_ticker()),
            Output(*self.checkable_table.dropdown_button.get_disabled()),
        )
        def deactivate_indicator_dropdown(show_tickers, ticker_cell):
            return not show_tickers or ticker_cell is None

        @app.callback(
            Input(*self.checkable_table.dropdown_button.get_disabled()),
            Input(*self.ticker_layout.get_active_ticker()),
            Input(*self.ticker_layout.get_ticker_table_virtual()),
            Output(*self.checkable_table.dropdown_button.get_label()),
        )
        def update_indicator_dropdown_label(disabled, ticker_cell, rows):
            if disabled:
                return "Add Indicator"
            ticker = get_active_ticker(ticker_cell, rows)
            return f"Add {ticker} Indicator"

        @app.callback(
            Input(*self.ticker_layout.get_ticker_table()),
            State(*self.checkable_table.get_table()),
            State(*self.engine_layout.get_id()),
            Output(*self.checkable_table.get_table()),
        )
        def remove_indicator_on_ticker_removal(ticker_rows, indicator_rows, engine_id):
            return [
                ir
                for ir in indicator_rows
                if {"ticker-col": ir["ticker-col"]} in ticker_rows
            ]

        def add_create_indicator_callbacks(indicator, arguments):
            @app.callback(
                Input(
                    *self.checkable_table.dropdown_button.get_item_n_clicks(
                        indicator.__name__
                    )
                ),
                Output(*self.modal_creator.get_is_open(indicator)),
            )
            def create_indicator_form(n_clicks):
                if n_clicks == 0 or None:
                    return False
                return True

            @app.callback(
                Input(*self.modal_creator.get_add_n_clicks(indicator)),
                State(*self.checkable_table.get_table()),
                State(*self.ticker_layout.get_active_ticker()),
                State(*self.ticker_layout.get_ticker_table_virtual()),
                [
                    State(*self.modal_creator.get_argument_value(indicator, argument))
                    for argument in arguments
                ],
                Output(*self.modal_creator.get_is_open(indicator)),
                Output(*self.checkable_table.get_table()),
            )
            def create_indicator(
                n_clicks,
                indicator_rows,
                ticker_cell,
                ticker_rows,
                arguments,
            ):
                if not isinstance(arguments, list):
                    arguments = [arguments]

                created_indicator = indicator(*arguments)
                new_entry = {
                    "indicator-col": str(created_indicator),
                    "ticker-col": get_active_ticker(ticker_cell, ticker_rows),
                    "indicator": {
                        "name": indicator.__name__,
                        "config": created_indicator.to_json(),
                    },
                }

                if new_entry not in indicator_rows:
                    indicator_rows.append(new_entry)
                return False, indicator_rows

        indicators = get_indicators()
        for indicator in indicators:
            add_create_indicator_callbacks(indicator, indicators[indicator])
