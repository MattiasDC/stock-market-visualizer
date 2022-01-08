from utils.inspection import get_constructor_arguments

from stock_market.common.factory import Factory
from stock_market.ext.indicator import register_indicator_factories, MovingAverage, ExponentialMovingAverage, Identity

def get_indicators_with_identity():
	return { i : get_constructor_arguments(i) for i in [MovingAverage, ExponentialMovingAverage, Identity] }

def get_indicators():
	indicators = get_indicators_with_identity()
	indicators.pop(Identity)
	return indicators
	
def get_indicator_factory():
	return register_indicator_factories(Factory())