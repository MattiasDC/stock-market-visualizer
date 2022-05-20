import datetime as dt
import uuid

import uvicorn as uvicorn
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.layout import Layout
from stock_market_visualizer.app.redis_helper import init_redis_pool
from stock_market_visualizer.app.restoreable_state import store_state
from stock_market_visualizer.common.requests import ClientSessionGenerator

layout = Layout()
dash_app = DashProxy(
    __name__,
    requests_pathname_prefix="/sme/",
    prevent_initial_callbacks=True,
    transforms=[MultiplexerTransform()],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=layout.get_themes(),
    assets_folder="./assets",
)
dash_app.title = "Stock Market Engine"

app = FastAPI(title="Stock Market Visualizer")
app.mount("/sme", WSGIMiddleware(dash_app.server))


@app.on_event("startup")
async def startup_event():
    app.state.client_generator = ClientSessionGenerator()
    app.state.redis = init_redis_pool()
    dash_app.layout = layout.get_layout()
    layout.register_callbacks(
        dash_app, app.state.client_generator.get, lambda: app.state.redis
    )


@app.post("/store_external_configuration")
async def store_external_configuration(
    header_title: str,
    engine_id: uuid.UUID,
    start_date: dt.date,
    end_date: dt.date,
    show_ticker_table: bool,
    show_indicator_table: bool,
    show_signal_table: bool,
):
    def bool_to_list(value):
        return [True] if value else []

    state_id = store_state(
        app.state.redis,
        header_title,
        str(engine_id),
        start_date.isoformat(),
        end_date.isoformat(),
        [],
        bool_to_list(show_ticker_table),
        bool_to_list(show_indicator_table),
        bool_to_list(show_signal_table),
    )
    return state_id


if __name__ == "__main__":
    settings = get_settings()
    if settings.debug:
        dash_app.enable_dev_tools(debug=True, dev_tools_hot_reload=True)
    uvicorn.run(
        "main:app",
        host=settings.host_url,
        port=settings.port,
        ssl_keyfile=settings.ssl_keyfile,
        ssl_certfile=settings.ssl_certfile,
        reload=settings.debug,
        log_level="warning",
        use_colors=True,
    )
