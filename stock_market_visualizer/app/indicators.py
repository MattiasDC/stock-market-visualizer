from utils.inspection import get_constructor_arguments

from stock_market.common.factory import Factory
from stock_market.ext.indicator import MovingAverage, ExponentialMovingAverage

def get_indicators():
	return { i : get_constructor_arguments(i) for i in [MovingAverage, ExponentialMovingAverage] } 

def get_indicator_factory():
	factory = Factory()
	for i in get_indicators():
		factory.register(i.__name__, i.from_json)
	return factory