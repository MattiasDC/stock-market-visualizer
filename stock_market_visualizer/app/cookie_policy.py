import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash_extensions.enrich import Input, Output, State


class CookiePolicyLayout:
    def __init__(self):
        self.cookie_policy_store_id = "cookie_policy"
        self.cookie_policy_store = dcc.Store(
            id=self.cookie_policy_store_id, storage_type="local"
        )
        self.button_id = "accept_cookie_policy"
        self.accept_button = dbc.Button(
            id=self.button_id,
            className="btn btn-dark mt-3 px-4",
            children="Okay",
            n_clicks=0,
        )
        self.modal_id = "modal_cookie_policy"
        self.layout = dbc.Modal(
            id=self.modal_id,
            children=html.Div(
                children=[
                    html.Div(
                        children=[
                            html.Img(src="https://i.imgur.com/Tl8ZBUe.png", width=50),
                            html.Span(
                                className="mt-2",
                                children=(
                                    "We use third party cookies to personalize content,"
                                    " ads and analyze site traffic."
                                ),
                            ),
                            html.A(
                                className="d-flex align-items-center",
                                href=(
                                    "https://www.cookiepolicygenerator.com/live.php?"
                                    "token=jGOdYvv1mykMNzyg7sa9tuJvtqpSxfy4"
                                ),
                                children=[
                                    "Learn more",
                                    html.I(className="fa fa-angle-right ml-2"),
                                ],
                            ),
                            self.accept_button,
                        ],
                        className=(
                            "d-flex align-items-center align-self-center card p-3"
                            " text-center cookies"
                        ),
                    )
                ],
                className="d-flex justify-content-center mt-5 h-100",
            ),
            is_open=False,
            keyboard=False,
            backdrop="static",
        )

    def get_stored_cookie_policy(self):
        return self.cookie_policy_store_id, "data"

    def get_layout(self):
        return html.Div(children=[self.layout, self.cookie_policy_store])

    def is_open(self):
        return self.modal_id, "is_open"

    def n_clicks(self):
        return self.button_id, "n_clicks"

    def register_callbacks(self, app):
        @app.callback(Output(*self.is_open()), Input(*self.get_stored_cookie_policy()))
        def show_cookie_policy(store):
            return store is None or "accepted" not in store

        @app.callback(
            Output(*self.get_stored_cookie_policy()),
            Input(*self.n_clicks()),
            State(*self.get_stored_cookie_policy()),
        )
        def accept_cookie_policy(n_clicks, store):
            if n_clicks is None or n_clicks == 0:
                return dash.no_update
            return {"accepted": True}
