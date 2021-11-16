import datetime as dt
import inspect

from stock_market_visualizer.common.logging import get_logger

logger = get_logger(__name__)

def from_sdate(date):
    if date is None:
        return None
    if isinstance(date, str):
        try:
            date = dt.date.fromisoformat(date)
        except ValueError as e:
            logger.warning(e)
            return None
    return date

"""
Return constructor arguments and their types as a dictionary.
self is not included.
"""
def get_constructor_arguments(class_name):
    parameters = inspect.signature(class_name.__init__).parameters
    arguments = [ p for p in parameters if p != 'self']
    return { a : parameters[a].annotation for a in arguments}