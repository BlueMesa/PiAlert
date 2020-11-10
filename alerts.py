from datetime import datetime


class Alert:
    def __init__(self, threshold, value: float, trigger: float):
        self._timestamp = datetime.now()
        self._threshold = threshold
        self._value = float(value)
        self._trigger = float(trigger)
        if not threshold.violated(value, trigger):
            raise ValueError

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def threshold(self):
        return self._threshold

    @property
    def trigger(self):
        return self._trigger

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return self.__class__.__name__ + '(severity: ' + str(self.threshold.level) + ', timestamp: '\
               + str(self._timestamp) + ')'


class HumidityAlert(Alert):
    pass


class TemperatureAlert(Alert):
    pass


class AlertHandler:

    def __init__(self):
        self._alerts = {}

    def handle(self, sensor, message):
        if sensor not in self._alerts:
            self._alerts[sensor] = []
        for feature in message.keys():
            self._alerts[sensor].extend(getattr(sensor, feature).triggers(message[feature]))
        print(self._alerts[sensor])

    def text(self, alert):
        pass

    def email(self, alert):
        pass
