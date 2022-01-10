from .restoreable_state_callbacks import register_restoreable_state_callbacks

def register_callbacks(app, client_getter, redis_getter):
    register_restoreable_state_callbacks(app, redis_getter)