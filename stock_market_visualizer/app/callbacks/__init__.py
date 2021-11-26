from .date_callbacks import register_date_callbacks
from .indicator_callbacks import register_indicator_callbacks
from .interval_callbacks import register_interval_callbacks
from .ticker_callbacks import register_ticker_callbacks

def register_callbacks(app, client_getter):
    register_date_callbacks(app, client_getter)
    register_ticker_callbacks(app, client_getter)
    register_indicator_callbacks(app, client_getter)
    register_interval_callbacks(app, client_getter)