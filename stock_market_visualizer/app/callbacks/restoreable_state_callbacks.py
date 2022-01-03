import dash
from dash_extensions.enrich import Output, Input, State
import json
import uuid

from stock_market_visualizer.app.config import get_settings

FIXED_PATH = "/sme/"

def register_restoreable_state_callbacks(app, redis_getter):
    @app.callback(
      Output('restoreable-state', 'data'),
      Input('url', 'href'))
    def update_state_from_url(url):
      url_splitted = url.split(FIXED_PATH, 1)
      state_id = url_splitted[1]
      if len(state_id) == 0:
        return dash.no_update
      return state_id

    @app.callback(
      Output('engine-id', 'data'),
      Output('date-picker-start', 'date'),
      Output('date-picker-end', 'date'),
      Output('ticker-table', 'selected_rows'),
      Output('indicator-table', 'selected_rows'),
      Output('signal-table', 'selected_rows'),
      Output('indicator-table', 'data'),
      Output('show-ticker-table', 'value'),
      Output('show-indicator-table', 'value'),
      Output('show-signal-table', 'value'),
      Input('restoreable-state', 'data'))
    def update_from_state(state_id):
      redis = redis_getter()
      state = json.loads(redis.get(state_id))
      keys = ['engine-id',
              'start-date',
              'end-date',
              'selected-tickers',
              'selected-indicators',
              'selected-signals',
              'indicators',
              'show-ticker-table',
              'show-indicator-table',
              'show-signal-table']    
      return [state.get(key) if state.get(key) is not None else dash.no_update for key in keys]

    @app.callback(
      Output('url-copy', 'content'),
      Input('url-copy', 'n_clicks'),
      State('url', 'href'),
      State('engine-id', 'data'),
      State('date-picker-start', 'date'),
      State('date-picker-end','date'),
      State('ticker-table', 'selected_rows'),
      State('indicator-table', 'selected_rows'),
      State('signal-table', 'selected_rows'),
      State('indicator-table', 'data'),
      State('show-ticker-table', 'value'),
      State('show-indicator-table', 'value'),
      State('show-signal-table', 'value'))
    def create_url(n_clicks,
                   url,
                   engine_id,
                   start_date,
                   end_date,
                   selected_tickers,
                   selected_indicators,
                   selected_signals,
                   indicators,
                   show_ticker_table,
                   show_indicator_table,
                   show_signal_table):
      if n_clicks == 0:
        return dash.no_update
      url = url.split(FIXED_PATH, 1)[0]
      state = {}
      state['engine-id'] =  engine_id
      state['start-date'] = start_date
      state['end-date'] = end_date
      state['selected-tickers'] = selected_tickers
      state['selected-indicators'] = selected_indicators
      state['selected-signals'] = selected_signals
      state['indicators'] = indicators
      state['show-ticker-table'] = show_ticker_table
      state['show-indicator-table'] = show_indicator_table
      state['show-signal-table'] = show_signal_table

      redis = redis_getter()
      state_id = str(uuid.uuid4())
      redis.set(state_id, json.dumps(state), get_settings().redis_restoreable_state_expiration_time)

      return url + FIXED_PATH + state_id