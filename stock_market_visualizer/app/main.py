from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
import uvicorn as uvicorn
from dash_extensions.enrich import DashProxy, MultiplexerTransform

from stock_market_visualizer.app.config import get_settings
import stock_market_visualizer.app.layouts as layout
from stock_market_visualizer.app.callbacks import register_callbacks
from stock_market_visualizer.common.requests import ClientSessionGenerator


app = DashProxy(__name__,
                requests_pathname_prefix="/sme/",
                prevent_initial_callbacks=True,
                transforms=[MultiplexerTransform()],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
                external_stylesheets=layout.get_themes())
app.title = "Stock Market Engine"

server = FastAPI()
server.mount("/sme", WSGIMiddleware(app.server))

def get_client_generator():
    return server.state.client_generator.get()

@server.on_event("startup")
async def startup_event():
    server.state.client_generator = ClientSessionGenerator()
    register_callbacks(app, get_client_generator)
    app.layout = layout.get_layout(server.state.client_generator.get())

if __name__ == '__main__':
    settings = get_settings()
    uvicorn.run("main:server",
                host=settings.host_url,
                port=settings.port,
                reload=settings.debug,
                log_level='warning',
                use_colors=True)