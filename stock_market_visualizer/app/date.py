import datetime as dt

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash_extensions.enrich import Input, Output, State
from simputils.dateutils import from_sdate


class DateLayout:
    def __init__(self, engine_layout, ticker_layout, signal_layout):
        self.engine_layout = engine_layout
        self.ticker_layout = ticker_layout
        self.signal_layout = signal_layout
        self.earliest_start = dt.date(1990, 1, 1)
        self.date_format = "D-M-Y"
        self.start_date_picker = "start-date-picker"
        self.end_date_picker = "end-date-picker"

    def get_start_date(self):
        return self.start_date_picker, "date"

    def get_end_date(self):
        return self.end_date_picker, "date"

    def get_layout(self):
        return [self.__get_start_date_layout(), self.__get_end_date_layout()]

    def __get_start_date_layout(self):
        return dbc.Col(
            dbc.Container(
                [
                    html.P("Start", style={"margin-bottom": 0}),
                    dcc.DatePickerSingle(
                        id=self.start_date_picker,
                        min_date_allowed=self.earliest_start,
                        max_date_allowed=dt.datetime.now().date()
                        - dt.timedelta(days=1),
                        placeholder="Start Date",
                        display_format=self.date_format,
                    ),
                ]
            )
        )

    def __get_end_date_layout(self):
        return dbc.Col(
            dbc.Container(
                [
                    html.P("End", style={"margin-bottom": 0}),
                    dcc.DatePickerSingle(
                        id=self.end_date_picker,
                        min_date_allowed=self.earliest_start + dt.timedelta(days=1),
                        placeholder="End Date",
                        display_format=self.date_format,
                    ),
                ]
            )
        )

    def __get_signal_detectors(self, rows):
        signal_detectors = []
        for row in rows:
            sd = dict(row)
            sd.pop("signal-col")
            sd["static_name"] = sd.pop("name")
            signal_detectors.append(sd)
        return signal_detectors

    def register_callbacks(self, app, engine_api):
        @app.callback(
            Output(self.end_date_picker, "min_date_allowed"),
            Input(*self.get_start_date()),
        )
        def update_min_date_allowed(start_date):
            if start_date is None:
                return dash.no_update
            return start_date

        @app.callback(
            Output(*self.engine_layout.get_id()),
            Input(*self.get_start_date()),
            Input(*self.get_end_date()),
            State(*self.ticker_layout.get_ticker_table()),
            State(*self.signal_layout.signal_detector_table.get_table()),
            State(*self.engine_layout.get_id()),
        )
        def update_engine(
            start_date,
            end_date,
            ticker_rows,
            signal_detector_rows,
            engine_id,
        ):
            start_date = from_sdate(start_date)
            end_date = from_sdate(end_date)

            if start_date is None:
                return dash.no_update
            if end_date is None:
                return dash.no_update

            end_date = min(end_date, dt.datetime.now().date())

            tickers = self.ticker_layout.get_tickers(ticker_rows)
            signal_detectors = self.__get_signal_detectors(signal_detector_rows)
            if engine_id is None:
                engine = engine_api.create_engine(start_date, tickers, signal_detectors)
            else:
                engine = engine_api.get_engine(engine_id)

            if engine is None:
                return dash.no_update

            engine_start_date = engine.get_start_date()
            if engine_start_date is None:
                return dash.no_update

            if engine_start_date != start_date:
                engine = engine_api.create_engine(start_date, tickers, signal_detectors)
                if engine is None:
                    return dash.no_update

            new_engine = engine.update_engine(
                end_date + dt.timedelta(days=1)
            )  # Make exclusive
            return new_engine.engine_id
