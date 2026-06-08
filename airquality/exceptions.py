class AirQualityError(Exception):
    """Базовое исключение для всех ошибок анализа воздуха."""
    pass

class SensorMalfunctionError(AirQualityError):
    """Датчик показал невалидное значение -200."""
    def __init__(self, sensor_column, date, time):
        self.sensor_column = sensor_column
        self.date = date
        self.time = time
        super().__init__(
            f"Датчик '{sensor_column}' неисправен в {date} {time}"
        )

class HealthStandardExceededError(AirQualityError):
    """Превышение нормы."""
    def __init__(self, pollutant, value, standard, date, time):
        self.pollutant = pollutant
        self.value = value
        self.standard = standard
        self.date = date
        self.time = time
        super().__init__(
            f"ПРЕВЫШЕНИЕ! {pollutant} = {value} (норма: {standard}) в {date} {time}"
        )

class DataGapError(AirQualityError):
    """Слишком большой разрыв между измерениями"""
    def __init__(self, column, gap_hours, from_datetime, to_datetime):
        self.column = column
        self.gap_hours = gap_hours
        self.from_datetime = from_datetime
        self.to_datetime = to_datetime
        super().__init__(
            f"Разрыв {gap_hours:.1f} часов в колонке '{column}' "
            f"(с {from_datetime} по {to_datetime})"
        )
