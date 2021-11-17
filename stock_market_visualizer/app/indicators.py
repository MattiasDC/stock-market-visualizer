import inspect

from stock_market_engine.common.factory import Factory
from stock_market_engine.ext.indicator import MovingAverage, ExponentialMovingAverage

from stock_market_visualizer.common.utils import get_constructor_arguments

def get_indicators():
	return { i : get_constructor_arguments(i) for i in [MovingAverage, ExponentialMovingAverage] } 

def get_indicator_factory():
	factory = Factory()
	for i in get_indicators():
		factory.register(i.__name__, i.from_json)
	return factory