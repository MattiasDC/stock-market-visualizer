import requests_cache
import uvicorn as uvicorn
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.config_store import configure_default_configs
from stock_market_visualizer.app.layout import Layout
from stock_market_visualizer.app.redis_helper import init_redis_pool
from stock_market_visualizer.app.stock_market_engine_api import StockMarketEngineApi

layout = Layout()
dash_app = DashProxy(
    __name__,
    prevent_initial_callbacks=True,
    transforms=[MultiplexerTransform()],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=layout.get_themes(),
    assets_folder="./assets",
)
dash_app.title = get_settings().title

app = FastAPI(title="Stock Market Visualizer")
app.mount("", WSGIMiddleware(dash_app.server))


@app.on_event("startup")
async def startup_event():
    settings = get_settings()

    app.state.http_client = requests_cache.CachedSession(
        cache=requests_cache.backends.SQLiteCache(),
        allowable_methods=["GET", "POST"],
        allowable_codes=[200, 203, 204, 300, 301, 308],
    )
    app.state.redis = init_redis_pool()
    configuration_task = configure_default_configs(app.state.redis, settings)
    app.state.engine_api = StockMarketEngineApi(
        settings.api_url, settings.api_port, app.state.http_client
    )
    dash_app.layout = layout.get_layout()
    layout.register_callbacks(dash_app, app.state.engine_api, app.state.redis)
    await configuration_task


@app.on_event("shutdown")
async def shutdown_event():
    app.state.http_client.close()


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
