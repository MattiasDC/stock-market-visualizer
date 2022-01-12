from dash import dcc
from dash import html
from dash_extensions.enrich import Output, Input, State


class HeaderLayout:
    def __init__(self):
        self.title = "header-title"
        self.url_copy = "url-copy"
        self.layout = html.Div(
            children=[
                html.H1(
                    className="d-inline",
                    children=[
                        dcc.Clipboard(
                            id=self.url_copy,
                            title="save url",
                            n_clicks=0,
                            className="d-inline",
                            style={"margin-right": 5, "fontSize": 30},
                        ),
                        dcc.Input(
                            id=self.title,
                            type="text",
                            value="Stock Market Engine",
                            className="d-inline",
                            style={"border-style": "none"},
                        ),
                    ],
                )
            ]
        )

    def get_title(self):
        return self.title, "value"

    def get_url_copy_content(self):
        return self.url_copy, "content"

    def get_url_copy_clicks(self):
        return self.url_copy, "n_clicks"

    def get_layout(self):
        return self.layout

    def register_callbacks(self, app):
        @app.callback(Output(self.title, "size"), Input(*self.get_title()))
        def update_header_size(title):
            return len(title)
