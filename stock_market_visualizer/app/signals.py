from stock_market.ext.signal import MonthlySignalDetector,\
                                    BiMonthlySignalDetector,\
                                    GoldenCrossSignalDetector,\
                                    DeathCrossSignalDetector,\
                                    CrossoverSignalDetector

import stock_market_visualizer.app.sme_api_helper as api

def get_signal_detectors(client):
	return [sd["detector_name"] for sd in api.get_supported_signal_detectors(client)]

def get_supported_trivial_config_signal_detectors():
	return [MonthlySignalDetector, BiMonthlySignalDetector]

def get_supported_ticker_based_signal_detectors():
	return [GoldenCrossSignalDetector, DeathCrossSignalDetector]

def get_supported_signal_detectors():
	return get_supported_trivial_config_signal_detectors() +\
		   get_supported_ticker_based_signal_detectors() +\
		   [CrossoverSignalDetector]