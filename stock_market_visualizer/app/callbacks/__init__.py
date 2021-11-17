from .date_callbacks import register_date_callbacks
from .indicator_callbacks import register_indicator_callbacks
from .ticker_callbacks import register_ticker_callbacks

def register_callbacks(app, client_getter, redis_getter):
    register_date_callbacks(app, client_getter, redis_getter)
    register_ticker_callbacks(app, client_getter, redis_getter)
    register_indicator_callbacks(app, client_getter, redis_getter)