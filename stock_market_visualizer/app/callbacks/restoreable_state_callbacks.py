import dash
from dash_extensions.enrich import Output, Input, State

def register_restoreable_state_callbacks(app, redis_getter):
    @app.callback(
      Output('restoreable-state', 'data'),
      Input('url', 'pathname'))
    def update_state_from_url(pathname):
      state_id = pathname.replace("/sme/", "")
      if len(state_id) == 0:
        return dash.no_update
      return state_id

    @app.callback(
      Output('engine-id', 'data'),
      Input('restoreable-state', 'data'))
    def update_from_state(state_id):
      return state_id