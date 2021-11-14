import datetime as dt

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