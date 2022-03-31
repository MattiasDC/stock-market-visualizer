import stock_market_visualizer.app.sme_api_helper as api
from stock_market_visualizer.app.signals.common import (
    SignalDetectorConfigurationLayout,
    get_random_detector_id,
)


class EmptyDetectorHandler:
    def __init__(self, client, detector_name):
        self.__client = client
        self.__detector_name = detector_name

    def name(self):
        return self.__detector_name

    def id(self):
        return self.name().replace(" ", "")

    def activate(self, engine_id, data):
        if engine_id is None:
            return None, data
        new_engine_id = api.add_signal_detector(
            engine_id,
            {
                "static_name": self.name(),
                "config": str(get_random_detector_id(engine_id, self.__client)),
            },
            self.__client,
        )
        if new_engine_id is None:
            return engine_id, data
        return new_engine_id, data

    def get_id(self, config):
        return config


class TrivialSignalDetectorConfigurationLayout(SignalDetectorConfigurationLayout):
    def __init__(self, name):
        super().__init__(name, [])

    def get_handler(self, app, client):
        return EmptyDetectorHandler(client, self.name)
