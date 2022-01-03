from dash_extensions.enrich import Output, Input, State

def register_header_callbacks(app):

    @app.callback(
        Output('header-title', 'size'),
        Input('header-title', 'value'))
    def update_header_size(header_title):
        return len(header_title)
