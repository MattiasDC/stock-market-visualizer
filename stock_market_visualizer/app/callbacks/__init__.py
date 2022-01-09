from .indicator_callbacks import register_indicator_callbacks
from .restoreable_state_callbacks import register_restoreable_state_callbacks
from .signal_callbacks import register_signal_callbacks

def register_callbacks(app, client_getter, redis_getter):
    register_indicator_callbacks(app, client_getter)
    register_signal_callbacks(app, client_getter)
    register_restoreable_state_callbacks(app, redis_getter)