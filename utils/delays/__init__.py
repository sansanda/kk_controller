# utils/delays/__init__.py

from .delays import DelayFactory, DelayType
from .delays import TimeDelay, StatisticsDelay

# Registro de clases por defecto
DelayFactory.register_delay(DelayType.TIME.value, TimeDelay)
DelayFactory.register_delay(DelayType.STATISTICS.value, StatisticsDelay)

__all__ = ["DelayFactory", "DelayType", "TimeDelay", "StatisticsDelay"]