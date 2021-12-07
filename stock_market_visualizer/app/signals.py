from stock_market_visualizer.app.sme_api_helper import get_supported_signal_detectors

def get_signal_detectors(client):
	return [sd["detector_name"] for sd in get_supported_signal_detectors(client)]