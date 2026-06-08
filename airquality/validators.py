import pandas as pd

from exceptions import (
    SensorMalfunctionError,
    HealthStandardExceededError,
    DataGapError,
)


class ValidationRule:
    def validate(self, df, numeric_cols):
        raise NotImplementedError(
            "Метод validate() должен быть реализован в дочернем классе"
        )


class SensorMalfunctionRule(ValidationRule):
    def validate(self, df, numeric_cols):
        errors = []

        for _, row in df.iterrows():
            for col in numeric_cols:
                value = row[col]

                try:
                    if pd.isna(value):
                        raise SensorMalfunctionError(
                            sensor_column=col,
                            date=row["Date"],
                            time=row["Time"],
                        )

                except SensorMalfunctionError as error:
                    errors.append(error)

        return errors


class HealthStandardRule(ValidationRule):
    def __init__(self):
        self.standards = {
            "CO(GT)": 30.0,
            "NO2(GT)": 200.0,
            "C6H6(GT)": 5.0,
            "NOx(GT)": 200.0,
        }

    def validate(self, df, numeric_cols):
        errors = []

        for _, row in df.iterrows():
            for col in numeric_cols:
                value = row[col]

                try:
                    if col in self.standards:
                        standard = self.standards[col]

                        if not pd.isna(value) and value > standard:
                            raise HealthStandardExceededError(
                                pollutant=col,
                                value=value,
                                standard=standard,
                                date=row["Date"],
                                time=row["Time"],
                            )

                except HealthStandardExceededError as error:
                    errors.append(error)

        return errors

class DataGapRule(ValidationRule):
    def __init__(self, max_gap_hours=10):
        self.max_gap_hours = max_gap_hours

    def validate(self, df, numeric_cols):
        errors = []

        data = df.copy()
        data["datetime"] = pd.to_datetime(
            data["Date"] + " " + data["Time"],
            format="%d/%m/%Y %H.%M.%S"
        )

        for col in numeric_cols:
            gap_count = 0
            gap_start = None
            gap_end = None

            for _, row in data.iterrows():
                if pd.isna(row[col]):
                    if gap_count == 0:
                        gap_start = row["datetime"]

                    gap_count += 1
                    gap_end = row["datetime"]

                else:
                    if gap_count > self.max_gap_hours:
                        try:
                            raise DataGapError(
                                column=col,
                                gap_hours=gap_count,
                                from_datetime=gap_start,
                                to_datetime=gap_end,
                            )

                        except DataGapError as error:
                            errors.append(error)

                    gap_count = 0
                    gap_start = None
                    gap_end = None

            if gap_count > self.max_gap_hours:
                try:
                    raise DataGapError(
                        column=col,
                        gap_hours=gap_count,
                        from_datetime=gap_start,
                        to_datetime=gap_end,
                    )

                except DataGapError as error:
                    errors.append(error)

        return errors

class AirQualityValidator:
    def __init__(self, rules):
        self.rules = rules

    def validate(self, df, numeric_cols):
        all_errors = []

        for rule in self.rules:
            errors = rule.validate(df, numeric_cols)
            all_errors.extend(errors)

        return all_errors
    
