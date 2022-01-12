from random import randrange

from stock_market_visualizer.app.signals.common import SignalDetectorConfigurationLayout
from stock_market_visualizer.app.config import get_settings
import stock_market_visualizer.app.sme_api_helper as api

class EmptyDetectorHandler:
    def __init__(self, client, detector_name):
        self.__client = client
        self.__detector_name = detector_name

    def name(self):
        return self.__detector_name

    def id(self):
        return self.name().replace(" ", "")

    def activate(self, engine_id):
        if engine_id is None:
            return None
        engine_id = api.add_signal_detector(engine_id,
                                            {"static_name" : self.name(),
                                             "config" : str(randrange(get_settings().max_id_generator))},
                                            self.__client)
        return engine_id

    def get_id(self, config):
        return config

class TrivialSignalDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, name):
        super().__init__(name, [])

    def get_handler(self, app, client):
        return EmptyDetectorHandler(client, self.name)
