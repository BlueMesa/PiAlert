from typing import Union, Tuple
from urllib.parse import urlparse

ThresholdValue = Union[float, str, Tuple[float, float], Tuple[str, str]]
SensorValue = Union['MonitoredValue', float, None]


class Threshold:

    def __init__(self, lower: Union[float, Tuple[float, float]], upper: float = None, level: str = 'warning'):
        if isinstance(lower, tuple) and len(lower) == 2 and upper is None:
            lower, upper = lower
        if upper is None:
            upper = lower
        self._lower = None
        self._upper = None
        self._level = None
        self.lower = lower
        self.upper = upper
        self.level = level

    @property
    def lower(self) -> float:
        return self._lower

    @lower.setter
    def lower(self, value: float):
        self._upper = value

    @property
    def upper(self) -> float:
        return self._upper

    @upper.setter
    def upper(self, value: float):
        self._upper = value

    @property
    def level(self) -> str:
        return self._level

    @level.setter
    def level(self, value: str):
        if value in ['alert', 'warning', 'notify', 'info']:
            self._level = value
        else:
            raise ValueError

    def violates(self, value: float, setting: float = 0):
        return (value > (setting + self.upper)) or (value < (setting - self.lower))

    def __iter__(self):
        for v in [self._lower, self._upper]:
            yield v


class FractionThreshold(Threshold):

    def __init__(self, lower: Union[float, str, Tuple[float, float], Tuple[str, str]],
                 upper: Union[float, str] = None, level: str = 'warning'):
        if isinstance(lower, tuple) and len(lower) == 2 and upper is None:
            lower, upper = lower
        lower = self.__percent_to_float(lower)
        upper = self.__percent_to_float(upper)
        super().__init__(lower, upper, level)

    def violated(self, value: float, setting: float = 0):
        return (value > (setting + setting * self.upper)) or (value < (setting - setting * self.lower))

    @staticmethod
    def __percent_to_float(value):
        if isinstance(value, str) and value.endswith('%'):
            return float(value.strip(' %')) / 100
        elif isinstance(value, float):
            return value
        else:
            raise ValueError


class MonitoredValue:

    def __init__(self, v_set: float, warn: ThresholdValue = None, alert: ThresholdValue = None):
        self._set = v_set
        self._alerts = [self.__threshold_factory(*x) for x in [(warn, '10%', 'warning'), (alert, '20%', 'alert')]]

    @property
    def value(self):
        return self._set

    @value.setter
    def value(self, value: SensorValue):
        if isinstance(value, MonitoredValue):
            value = value.value
        self._set = value

    @property
    def warning(self):
        for a in self._alerts:
            if a.level == 'warning':
                yield a

    @property
    def alert(self):
        for a in self._alerts:
            if a.level == 'alert':
                yield a

    @property
    def alerts(self):
        return self._alerts

    def triggers(self, value: float):
        for a in self._alerts:
            if a.violated(value, self.value):
                yield a

    @staticmethod
    def __threshold_factory(value: ThresholdValue, default: ThresholdValue, level: str):
        if value is None:
            value = default
        if isinstance(value, str) and value.endswith('%'):
            return FractionThreshold(value, level=level)
        else:
            return Threshold(value, level=level)

    def __float__(self):
        return self._set

    def __int__(self):
        return int(self._set)

    def __str__(self):
        return str(self._set)

    def __repr__(self):
        return str(self._set)


class Sensor:
    @staticmethod
    def _default_value(v: SensorValue, default: float, warn: float, alert: float):
        if v is None:
            v = MonitoredValue(default, warn=warn, alert=alert)
        if isinstance(v, float):
            v = MonitoredValue(v, warn=warn, alert=alert)
        return v


class TemperatureSensor(Sensor):

    def __init__(self, temperature: SensorValue = None):
        self.temperature = temperature

    @property
    def temperature(self):
        return self._temperature

    @temperature.setter
    def temperature(self, value: SensorValue):
        if not isinstance(value, MonitoredValue):
            value = self._default_value(value, 25, 3, 5)
        self._temperature = value


class HumiditySensor(Sensor):

    def __init__(self, humidity: SensorValue = None):
        self.humidity = humidity

    @property
    def humidity(self):
        return self._humidity

    @humidity.setter
    def humidity(self, value: SensorValue):
        if not isinstance(value, MonitoredValue):
            value = self._default_value(value, 50, 10, 20)
        self._humidity = value


class WebSensor(Sensor):

    def __init__(self, url: str = None):
        self._url = None
        self.url = url

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value: str):
        parsed = urlparse(value)
        if parsed.scheme and parsed.netloc:
            self._url = value
        else:
            raise ValueError


class IncubatorSensor(TemperatureSensor, HumiditySensor, WebSensor):

    def __init__(self, temperature: SensorValue = 25, humidity: SensorValue = 50, url: str = None):
        TemperatureSensor.__init__(self, temperature)
        HumiditySensor.__init__(self, humidity)
        WebSensor.__init__(self, url)
