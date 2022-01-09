from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import uvicorn as uvicorn
from dash_extensions.enrich import DashProxy, MultiplexerTransform

from stock_market_visualizer.app.config import get_settings
from stock_market_visualizer.app.layout import Layout
from stock_market_visualizer.app.callbacks import register_callbacks
from stock_market_visualizer.app.redis_helper import init_redis_pool
from stock_market_visualizer.common.requests import ClientSessionGenerator

layout = Layout()

app = DashProxy(__name__,
                requests_pathname_prefix="/sme/",
                prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                external_stylesheets=layout.get_themes(),
                assets_folder='./assets')
app.title = "Stock Market Engine"

server = FastAPI()
server.mount("/sme", WSGIMiddleware(app.server))

def get_client_generator():
    return server.state.client_generator.get()

def get_redis():
    return server.state.redis

@server.on_event("startup")
async def startup_event():
    server.state.client_generator = ClientSessionGenerator()
    server.state.redis = init_redis_pool()
    app.layout = layout.get_layout()
    layout.register_callbacks(app, get_client_generator, get_redis)

if __name__ == '__main__':
    settings = get_settings()
    app.enable_dev_tools(debug=True, dev_tools_hot_reload=True)
    uvicorn.run("main:server",
                host=settings.host_url,
                port=settings.port,
                ssl_keyfile=settings.ssl_keyfile,
                ssl_certfile=settings.ssl_certfile,
                reload=settings.debug,
                log_level='warning',
                use_colors=True)