from datetime import datetime, timedelta
from typing import Iterable
from DateTime import DateTime
import platform
import yaml

if platform.machine() == 'armv6l':
    from gsmHat import GSMHat

LEVELS = ['alert', 'warning', 'notify', 'info']

with open('alerts.yml') as file:
    yaml_alerts = yaml.load(file, Loader=yaml.FullLoader)
    minutes = int(yaml_alerts['alerts']['expiry']['minutes'])
    hours = int(yaml_alerts['alerts']['expiry']['hours'])
    EXPIRY = timedelta(minutes=minutes, hours=hours)
    ALERT_THR = int(yaml_alerts['alerts']['thresholds']['alert'])
    WARNING_THR = int(yaml_alerts['alerts']['thresholds']['warning'])
    NUMBERS = yaml_alerts['numbers']


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

    @property
    def type(self):
        return self.__class__

    @property
    def name(self):
        return 'alert'

    def __repr__(self):
        return self.__class__.__name__ + '(severity: ' + str(self.threshold.level) + ', timestamp: '\
               + str(self._timestamp) + ')'


class HumidityAlert(Alert):

    @property
    def name(self):
        return 'humidity'


class TemperatureAlert(Alert):

    @property
    def name(self):
        return 'temperature'


class Notification:
    def __init__(self):
        self._timestamp = datetime.now()

    @property
    def timestamp(self):
        return self._timestamp


class AlertState:
    from sensors import Sensor

    def __init__(self, sensor: Sensor, alerts: Iterable[Alert]):
        self._sensor = sensor
        self._expiry = EXPIRY
        self._new = []
        self._new.extend(alerts)
        self._alerts = []
        self._notified = None

    @property
    def alerts(self):
        return self._alerts + self._new

    @property
    def new(self):
        return self._new

    @property
    def type(self):
        return self.alerts[-1].type

    @property
    def name(self):
        return self.alerts[-1].name

    @property
    def severity(self):
        i = 10
        for a in self.alerts:
            v = LEVELS.index(a.threshold.level)
            i = v if v < i else i
        return LEVELS[i]

    @property
    def active(self):
        return len(self._new) > 0

    @property
    def pending(self):
        warnings = 0
        alerts = 0
        for a in self._new:
            if a.threshold.level == 'warning':
                warnings += 1
            elif a.threshold.level == 'alert':
                alerts += 1

        return (warnings >= WARNING_THR or alerts >= ALERT_THR) and self._notified is None

    @property
    def notified(self):
        return self._notified

    @notified.setter
    def notified(self, value: DateTime):
        self._notified = value

    def update(self, alerts: Iterable[Alert]):
        for a in alerts:
            if isinstance(a, self.type):
                if LEVELS.index(a.threshold.level) < LEVELS.index(self.severity):
                    self._notified = None
                self._new.append(a)
        self.prune()

    def prune(self):
        expiry = datetime.now() - self._expiry
        for a in [a for a in self._new if a.timestamp < expiry]:
            self._alerts.append(a)
            self._new.remove(a)

    def __str__(self):
        from sensors import NamedSensor
        if isinstance(self._sensor, NamedSensor):
            name = self._sensor.name
        else:
            name = self._sensor.__class__.__name__

        if self.active:
            return name.capitalize() + ': ' + self.name + ' ' + self.severity + '. Current ' + self.name + ': ' \
                + str(self.alerts[-1].value)

    def __repr__(self):
        return self.__class__.__name__ + '(type: ' + str(self.type.__name__) + ', count: '\
               + str(len(self.new)) + ')'


class AlertHandler:

    def __init__(self):
        self._alerts = {}

    def handle(self, sensor, message):

        if sensor not in self._alerts:
            self._alerts[sensor] = []

        for feature in message.keys():
            alerts = list(getattr(sensor, feature).triggers(message[feature]))
            state = None
            if alerts:
                for a in self._alerts[sensor]:
                    if a.type == alerts[0].type:
                        state = a
                if state is None:
                    state = AlertState(sensor, alerts)
                    self._alerts[sensor].append(state)
                else:
                    state.update(alerts)

        expired = []
        for a in self._alerts[sensor]:
            a.prune()
            if not a.active:
                expired.append(a)
            if a.pending:
                self.text(a)
        for a in expired:
            self._alerts[sensor].remove(a)

    @staticmethod
    def text(alert):
        if platform.machine() == 'armv6l':
            gsm = GSMHat('/dev/ttyS0', 115200)
            for number in NUMBERS:
                gsm.SMS_write(number, str(alert))
        else:
            print('SMS:', str(alert))
        alert.notified = datetime.now()

    def email(self, alert):
        pass
