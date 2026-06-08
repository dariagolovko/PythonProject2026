import pandas as pd

from decorator import timer_decorator

from validators import (
    AirQualityValidator,
    SensorMalfunctionRule,
    HealthStandardRule,
    DataGapRule,
)
from strategy import(
    FillGapStrategy,
    FillMedianStrategy,
    FillMeanStrategy,
    FillPreviousStrategy,
    DropRowStrategy
)

df = pd.read_csv(
    "data/AirQualityUCI.csv",
    sep=";",
    decimal=",",
    na_values=-200,
)

df = df.dropna(how="all", axis=1).dropna(how="all")

numeric_cols = df.select_dtypes(include="number").columns


@timer_decorator
def run_validation(df, numeric_cols):
    validator = AirQualityValidator(
        rules=[
            SensorMalfunctionRule(),
            HealthStandardRule(),
            DataGapRule(max_gap_hours=10),
        ]
    )

    errors = validator.validate(df, numeric_cols)

    print(f"Найдено ошибок: {len(errors)}\n")

    return errors


errors = run_validation(df, numeric_cols)

print(f"Пропусков до обработки: {df[numeric_cols].isnull().sum().sum()}")

#Заполняем загрязнители медианой (устойчива к выбросам)
filler = FillGapStrategy(FillMedianStrategy())
pollutants = ['CO(GT)', 'C6H6(GT)', 'NOx(GT)', 'NO2(GT)', 'NMHC(GT)']
existing_pollutants = [col for col in pollutants if col in df.columns]
if existing_pollutants:
    df = filler.apply_to_selected_columns(df, existing_pollutants)
    print(f"  Заполнены медианой: {existing_pollutants}")

#Заполняем метеоданные средним (более стабильны)
filler.set_strategy(FillMeanStrategy())
weather = ['T', 'RH', 'AH']
existing_weather = [col for col in weather if col in df.columns]
if existing_weather:
    df = filler.apply_to_selected_columns(df, existing_weather)
    print(f"  Заполнены средним: {existing_weather}")

#Заполняем сенсоры предыдущим значением (для временных рядов)
filler.set_strategy(FillPreviousStrategy())
sensors = ['PT08.S1(CO)', 'PT08.S2(NMHC)', 'PT08.S3(NOx)', 'PT08.S4(NO2)', 'PT08.S5(O3)']
existing_sensors = [col for col in sensors if col in df.columns]
if existing_sensors:
    df = filler.apply_to_selected_columns(df, existing_sensors)
    print(f"  Заполнены предыдущим: {existing_sensors}")


#Удаляем строки, где осталось много пропусков
dropper = DropRowStrategy(threshold=0.3)
df = dropper.handle(None, None, None, df)
print(f"Пропусков после обработки: {df[numeric_cols].isnull().sum().sum()}")

# Обновляем numeric_cols (на случай изменений)
numeric_cols = df.select_dtypes(include="number").columns

# Повторная валидация после очистки
print("\n--- Повторная валидация после очистки ---")
errors_after = run_validation(df, numeric_cols)

# Сохраняем результат
df.to_csv("AirQuality_cleaned.csv", index=False)
print("Очищенные данные сохранены в 'data/AirQuality_cleaned.csv'")
