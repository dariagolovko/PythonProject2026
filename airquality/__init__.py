# airquality/__init__.py
"""Air Quality Data Processing Package"""

# Экспортируем основные классы для удобного импорта
from .strategy import (
    FillGapStrategy,
    FillMedianStrategy,
    FillMeanStrategy,
    FillPreviousStrategy,
    DropRowStrategy,
)
from .validators import (
    AirQualityValidator,
    SensorMalfunctionRule,
    HealthStandardRule,
    DataGapRule,
)
from .exceptions import (
    SensorMalfunctionError,
    HealthStandardExceededError,
    DataGapError,
)
from .decorators import timer_decorator

__all__ = [
    'FillGapStrategy',
    'FillMedianStrategy',
    'FillMeanStrategy',
    'FillPreviousStrategy',
    'DropRowStrategy',
    'AirQualityValidator',
    'SensorMalfunctionRule',
    'HealthStandardRule',
    'DataGapRule',
    'SensorMalfunctionError',
    'HealthStandardExceededError',
    'DataGapError',
    'timer_decorator',
]
