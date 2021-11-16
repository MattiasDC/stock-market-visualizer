from dash_extensions.enrich import Output, Input, State

from stock_market_visualizer.app.indicators import get_indicators

def get_active_ticker(cell, rows):
        return rows[cell['row']][cell['column_id']]

def register_indicator_callbacks(app):
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

    def add_create_indicator_callbacks(indicator, arguments):
        @app.callback(Input(f'dropdown-{indicator.__name__}', 'n_clicks'),
                      State('indicator-table', 'data'),
                      Output(f'modal-{indicator.__name__}', 'is_open'))
        def create_indicator_form(n_clicks, rows):
            return True

        @app.callback(Input(f'close-{indicator.__name__}', 'n_clicks'),
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
                                   'ticker-col': get_active_ticker(ticker_cell, ticker_rows)})
            return False, indicator_rows

    indicators = get_indicators()
    for indicator in indicators:
        add_create_indicator_callbacks(indicator, indicators[indicator])