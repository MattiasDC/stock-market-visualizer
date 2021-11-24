import datetime as dt
from dash import dcc

from stock_market_visualizer.app.config import get_settings

def get_interval_layout():
	return dcc.Interval(id='update-interval',
            			interval=dt.timedelta(seconds=get_settings().update_interval).total_seconds()*1000, # milliseconds
            			n_intervals=0)