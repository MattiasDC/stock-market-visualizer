from dash_extensions.enrich import Output, Input, State

import stock_market_visualizer.app.callbacks.checkable_table_dropdown_callbacks as checkable_table
from stock_market_visualizer.app.callbacks.callback_helper import CallbackHelper

def register_signal_callbacks(app, client_getter):
    callback_helper = CallbackHelper(client_getter)

    checkable_table.register_callbacks(app, 'signal')