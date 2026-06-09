import pandas as pd
from airquality.exceptions import SensorMalfunctionError, HealthStandardExceededError, DataGapError

def check_sensor_value(value, col, date, time):
    """Выбрасывает исключение, если значение NaN"""
    if pd.isna(value):
        raise SensorMalfunctionError(
            sensor_column=col,
            date=date,
            time=time
        )

def check_health_standard(value, col, standard, date, time):
    """Выбрасывает исключение, если значение превышает норму"""
    if value > standard:
        raise HealthStandardExceededError(
            pollutant=col,
            value=value,
            standard=standard,
            date=date,
            time=time
        )

def check_data_gap(column, gap_hours, from_datetime, to_datetime):
    if gap_hours > 10:
        raise DataGapError(
            column=column,
            gap_hours=gap_hours,
            from_datetime=from_datetime,
            to_datetime=to_datetime
        )
