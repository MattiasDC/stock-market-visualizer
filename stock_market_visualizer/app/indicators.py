from utils.inspection import get_constructor_arguments

from stock_market.common.factory import Factory
from stock_market.ext.indicator import register_indicator_factories, MovingAverage, ExponentialMovingAverage

def get_indicators():
	return { i : get_constructor_arguments(i) for i in [MovingAverage, ExponentialMovingAverage] } 

def get_indicator_factory():
	return register_indicator_factories(Factory())