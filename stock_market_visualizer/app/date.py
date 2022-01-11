import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash_extensions.enrich import Output, Input, State
import datetime as dt

from utils.dateutils import from_sdate

import stock_market_visualizer.app.sme_api_helper as api

class DateLayout:
    def __init__(self, engine_layout, ticker_layout, signal_layout):
        self.engine_layout = engine_layout
        self.ticker_layout = ticker_layout
        self.signal_layout = signal_layout
        self.earliest_start = dt.date(1990, 1, 1)
        self.date_format = 'D-M-Y'
        self.start_date_picker = 'start-date-picker'
        self.end_date_picker = 'end-date-picker'

    def get_start_date(self):
        return self.start_date_picker, 'date'

    def get_end_date(self):
        return self.end_date_picker, 'date'

    def get_layout(self):
        return [self.__get_start_date_layout(), self.__get_end_date_layout()]

    def __get_start_date_layout(self):
    	return dbc.Col(dbc.Container(
    		[
            html.P("Start"),
            dcc.DatePickerSingle(
                id=self.start_date_picker,
                min_date_allowed=self.earliest_start,
                max_date_allowed=dt.datetime.now().date() - dt.timedelta(days=1),
                placeholder='Start Date',
                display_format=self.date_format)
            ]))

    def __get_end_date_layout(self):
    	return dbc.Col(dbc.Container(
    		[
            html.P("End"),
            dcc.DatePickerSingle(
                id=self.end_date_picker,
                min_date_allowed=self.earliest_start+dt.timedelta(days=1),
                placeholder='End Date',
                display_format=self.date_format)
            ]))

    def __get_signal_detectors(self, rows):
        signal_detectors = []
        for row in rows:
            sd = dict(row)
            sd.pop('signal-col')
            sd['static_name'] = sd.pop('name')
            signal_detectors.append(sd)
        return signal_detectors

    def register_callbacks(self, app, client_getter):
        client = client_getter()

        @app.callback(
            Output(self.end_date_picker, 'min_date_allowed'),
            Input(*self.get_start_date()))
        def update_min_date_allowed(start_date):
            if start_date is None:
                return dash.no_update
            return start_date

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Output(*self.get_end_date()),
            Input(*self.get_start_date()),
            Input(*self.get_end_date()),
            State(*self.ticker_layout.get_ticker_table()),
            State(*self.signal_layout.signal_detector_table.get_table()),
            State(self.end_date_picker, 'min_date_allowed'),
            State(*self.engine_layout.get_id()))
        def update_engine(start_date, end_date, ticker_rows, signal_detector_rows, min_end_date, engine_id):
            start_date = from_sdate(start_date)
            min_end_date = from_sdate(min_end_date)
            end_date = from_sdate(end_date)
        
            if start_date is None:
                return dash.no_update
            if end_date is None:
                return dash.no_update
        
            end_date = min(end_date, dt.datetime.now().date())
        
            if end_date < min_end_date:
                return dash.no_update
        
            tickers = self.ticker_layout.get_tickers(ticker_rows)
            signal_detectors = self.__get_signal_detectors(signal_detector_rows)
            if engine_id is None:
                engine_id = api.create_engine(start_date, tickers, signal_detectors, client)
            if engine_id is None:
                return dash.no_update
        
            engine_start_date = api.get_start_date(engine_id, client)
            if engine_start_date is None:
                return dash.no_update
        
            if engine_start_date != start_date:
                engine_id = api.create_engine(start_date, tickers, signal_detectors, client)
                if engine_id is None:
                    return dash.no_update
            
            api.update_engine(engine_id, end_date, client)
            return engine_id, end_date