from dash import dcc
from dash import html

def get_header_layout():
	return html.Div(children=[html.H1(className="d-inline",
                                   children=[dcc.Input(id="header-title",
                                                       type="text",
                                                       value="Stock Market Engine",
                                                       className='d-inline',
                                                       style={'border-style' : 'none'})]),
                              dcc.Clipboard(id="url-copy",
                                            title='copy url',
                                            n_clicks=0,
                                            className="d-inline",
                                            style={"margin-left" : 5, "fontSize": 30})])