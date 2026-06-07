import pandas as pd

from decorator import timer_decorator
from validators import (
    AirQualityValidator,
    SensorMalfunctionRule,
    HealthStandardRule,
    DataGapRule,
)


df = pd.read_csv(
    "AirQualityUCI.csv",
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
