from .date_callbacks import register_date_callbacks
from .indicator_callbacks import register_indicator_callbacks
from .graph_callbacks import register_graph_callbacks
from .restoreable_state_callbacks import register_restoreable_state_callbacks
from .signal_callbacks import register_signal_callbacks
from .ticker_callbacks import register_ticker_callbacks

def register_callbacks(app, client_getter, redis_getter):
    register_date_callbacks(app, client_getter)
    register_ticker_callbacks(app, client_getter)
    register_indicator_callbacks(app, client_getter)
    register_graph_callbacks(app, client_getter)
    register_signal_callbacks(app, client_getter)
    register_restoreable_state_callbacks(app, redis_getter)