import dash_bootstrap_components as dbc
from dash import dash_table
from dash import dcc
from dash import html

from stock_market_visualizer.app.indicators import get_indicators
from .checkable_table_dropdown_layout import get_checkable_table_dropdown_layout

def get_create_indicator_modals_layout():
    indicators = get_indicators()
    return [
           dbc.Modal(
               [
               dbc.ModalHeader(dbc.ModalTitle(indicator.__name__)),
               dbc.ModalBody(dbc.InputGroup(children=
                   [
                   html.Div(
                        [
                        html.P(f"{argument}:"),
                        html.Div(
                            dbc.Input(id=f'{indicator.__name__}-{argument}-input',
                                      style={'margin-left': 5},
                                      type="number"),
                            className="input-group-append")
                        ],
                        className="input-group")
                   for argument in indicators[indicator]])),
               dbc.ModalFooter(dbc.Button("Add",
                                          id=f"add-{indicator.__name__}",
                                          className="ms-auto",
                                          n_clicks=0))
               ],
               id=f"modal-{indicator.__name__}",
               is_open=False)
           for indicator in indicators]

def get_indicator_table_layout():
  return get_checkable_table_dropdown_layout("indicator",
      [ i.__name__ for i in get_indicators()],
      [{'name': 'Ticker', 'id': 'ticker-col'}],
      True)