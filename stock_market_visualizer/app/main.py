import uvicorn as uvicorn
from dash_extensions.enrich import DashProxy, MultiplexerTransform
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.layout import Layout
from stock_market_visualizer.app.redis_helper import init_redis_pool
from stock_market_visualizer.common.requests import ClientSessionGenerator

layout = Layout()
dash_app = DashProxy(
    __name__,
    prevent_initial_callbacks=True,
    transforms=[MultiplexerTransform()],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=layout.get_themes(),
    assets_folder="./assets",
)
dash_app.title = "Stock Market Engine"

app = FastAPI()
app.mount("/", WSGIMiddleware(dash_app.server))


@app.on_event("startup")
async def startup_event():
    app.state.client_generator = ClientSessionGenerator()
    app.state.redis = init_redis_pool()
    dash_app.layout = layout.get_layout()
    layout.register_callbacks(
        dash_app, app.state.client_generator.get, lambda: app.state.redis
    )


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
