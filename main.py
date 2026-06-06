import pandas as pd
from exceptions import (
    AirQualityError,
    SensorMalfunctionError,
    HealthStandardExceededError,
    DataGapError
)
from decorator import timer_decorator

def check_sensor_malfunction(value, column, row):
    """Проверка на пропущенные данные."""
    if pd.isna(value):
        raise SensorMalfunctionError(sensor_column=column, date=row['Date'], time=row['Time'])

def check_health_standard(value, column, row):
    """Проверка превышения норм для конкретного вещества."""
    standards = {
        'CO(GT)': 30.0,  # мг/м³ (среднечасовая норма)
        'NO2(GT)': 200.0,  # мкг/м³ (среднечасовая норма)
        'C6H6(GT)': 5.0,  # мкг/м³ (бензол, примерная норма)
        'NOx(GT)': 200.0,  # мкг/м³ (оксиды азота)
    }
    if column in standards:
        if not pd.isna(value) and value > standards[column]:
            raise HealthStandardExceededError(
                pollutant=column,
                value=value,
                standard=standards[column],
                date=row['Date'],
                time=row['Time'],
            )

def check_data_gap(df, column, max_gap_hours):
    df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H.%M.%S')
    count = 0
    mx = 0
    current_start = df['datetime'].iloc[0]
    current_end = current_start
    start = current_start
    end = current_end
    for idx, row in df.iterrows():
        if pd.isna(row[column]):
            if count == 0:
                current_start = row['datetime']
                current_end = current_start
            count += 1
            if count > mx:
               start = current_start
               end = current_end
               mx = count
            else:
               current_end = row['datetime']
        else:
            count = 0
    if mx > max_gap_hours:
        raise DataGapError(column, mx, start, end)

df = pd.read_csv('AirQualityUCI.csv', sep=';', decimal=',', na_values=-200)
df = df.dropna(how='all', axis=1).dropna(how='all')

numeric_cols = df.select_dtypes(include='number').columns

@timer_decorator
def checker(df, numeric_cols):
    errors = []
    for idx, row in df.iterrows():
        for col in numeric_cols:
            value = row[col]
            try:
                check_sensor_malfunction(value, col, row)
                check_health_standard(value, col, row)
            except (SensorMalfunctionError, HealthStandardExceededError) as e:
                errors.append(e)
    print(f"Найдено ошибок: {len(errors)}\n")
    return errors

@timer_decorator
def search_gaps(df, numeric_cols):
    big_gaps = []
    for col in numeric_cols:
        try:
            check_data_gap(df, col, 10)
        except DataGapError as e:
            big_gaps.append(e)
    print(f"Найдено больших пропусков: {len(big_gaps)}\n")
    return big_gaps

errors = checker(df, numeric_cols)
big_gaps = search_gaps(df, numeric_cols)
