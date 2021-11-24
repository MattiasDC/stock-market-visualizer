from dash_extensions.enrich import Output, Input, State

from stock_market_visualizer.app.indicators import get_indicators, get_indicator_factory
from .callback_helper import CallbackHelper

def get_active_ticker(cell, rows):
        return rows[cell['row']][cell['column_id']]

def register_indicator_callbacks(app, client_getter, redis_getter):
    callback_helper = CallbackHelper(client_getter, redis_getter)

    @app.callback(
        Input('show-indicator-table', 'value'),
        Output('collapse-indicator-table', 'is_open'))
    def toggle_collapse_indicator_table(show_indicator_table):
        return 'S' in show_indicator_table

    @app.callback(
        Input('show-ticker-table', 'value'),
        Input('ticker-table', 'active_cell'),
        Output('indicator-dropdown', 'disabled'))
    def deactivate_indicator_dropdown(show_tickers, ticker_cell):
        return not show_tickers or ticker_cell is None

    @app.callback(
        Input('indicator-dropdown', 'disabled'),
        Input('ticker-table', 'active_cell'),
        State('ticker-table', 'data'),
        Output('indicator-dropdown', 'label'))
    def update_indicator_dropdown_label(disabled, ticker_cell, rows):
        if disabled:
            return "Add Indicator"
        ticker = get_active_ticker(ticker_cell, rows)
        return f"Add {ticker} Indicator"

    @app.callback(
        Input('ticker-table', 'data'),
        State('indicator-table', 'data'),
        State('engine-id', 'data'),
        Output('indicator-table', 'data'))
    def remove_indicator_on_ticker_removal(ticker_rows, indicator_rows, engine_id):
        return [ ir for ir in indicator_rows if {'ticker-col' : ir['ticker-col']} in ticker_rows ]

    @app.callback(
        Input('indicator-table', 'data'),
        State('engine-id', 'data'),
        Output('stock-market-graph', 'figure'))
    def indicators_change(rows, engine_id):
        indicators = callback_helper.get_configured_indicators(rows)
        return callback_helper.get_traces_and_layout(engine_id, indicators)

    def add_create_indicator_callbacks(indicator, arguments):
        @app.callback(Input(f'dropdown-{indicator.__name__}', 'n_clicks'),
                      State('indicator-table', 'data'),
                      Output(f'modal-{indicator.__name__}', 'is_open'))
        def create_indicator_form(n_clicks, rows):
            return True

        @app.callback(Input(f'add-{indicator.__name__}', 'n_clicks'),
                      State('indicator-table', 'data'),
                      State('ticker-table', 'active_cell'),
                      State('ticker-table', 'data'),
                      [State(f'{indicator.__name__}-{argument}-input', 'value') for argument in arguments],
                      Output(f'modal-{indicator.__name__}', 'is_open'),
                      Output('indicator-table', 'data'))
        def create_indicator(n_clicks, indicator_rows, ticker_cell, ticker_rows, arguments):
            if not isinstance(arguments, list):
                arguments = [arguments]

            created_indicator = indicator(*arguments)
            indicator_rows.append({'indicator-col':str(created_indicator),
                                   'ticker-col': get_active_ticker(ticker_cell, ticker_rows),
                                   'indicator' : { 'name' : indicator.__name__, "config" : created_indicator.to_json()}})
            
            return False, indicator_rows

    indicators = get_indicators()
    for indicator in indicators:
        add_create_indicator_callbacks(indicator, indicators[indicator])