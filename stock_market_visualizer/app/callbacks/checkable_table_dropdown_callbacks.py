from dash_extensions.enrich import Output, Input

def register_callbacks(app, name):
    @app.callback(
        Input(f'show-{name}-table', 'value'),
        Output(f'collapse-{name}-table', 'is_open'))
    def toggle_collapse_table(show_table):
        return 'S' in show_table