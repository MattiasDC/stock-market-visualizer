from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import datetime as dt

earliest_start = dt.date(1990, 1, 1)

def get_start_date_layout():
	return dbc.Container(
		[
        html.P("Start"),
        dcc.DatePickerSingle(
            id='date-picker-start',
            min_date_allowed=earliest_start,
            max_date_allowed=dt.datetime.now().date() - dt.timedelta(days=1),
            placeholder='Start Date',
            display_format='D-M-Y')
        ])

def get_end_date_layout():
	return dbc.Container(
		[
        html.P("End"),
        dcc.DatePickerSingle(
            id='date-picker-end',
            min_date_allowed=earliest_start+dt.timedelta(days=1),
            placeholder='End Date',
            display_format='D-M-Y')
        ])