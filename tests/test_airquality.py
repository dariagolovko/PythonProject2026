import pytest
from pytest import approx
import pandas as pd
import numpy as np
from pandas.testing import assert_frame_equal
from airquality.exceptions import SensorMalfunctionError, HealthStandardExceededError, DataGapError
from airquality.validators import SensorMalfunctionRule, HealthStandardRule, DataGapRule
from airquality.strategy import FillMedianStrategy, FillMeanStrategy, FillPreviousStrategy, DropRowStrategy
from airquality.exceptions_thrower import check_sensor_value, check_health_standard, check_data_gap


@pytest.mark.parametrize("value, col, date, time, should_raise", [
        (pd.NA, 'CO(GT)', '01/01/2024', '12:00', True),
        (None, 'NO2(GT)', '01/01/2024', '13:00', True),
        (2.5, 'CO(GT)', '01/01/2024', '14:00', False),
        (0.0, 'O3(GT)', '01/01/2024', '15:00', False),
])

@pytest.mark.validation
def test_sensor_malfunction_raises(value, col, date, time, should_raise):
    if should_raise:
        with pytest.raises(SensorMalfunctionError):
            check_sensor_value(value, col, date, time)
    else:
        check_sensor_value(value, col, date, time)


@pytest.mark.validation
def test_health_standard_rule():
    rule = HealthStandardRule()
    df = pd.DataFrame({
        'Date': [
            '01/01/2024',
            '02/01/2024',
            '03/01/2024',
            '04/01/2024',
            '05/01/2024',
        ],
        'Time': [
            '12:00',
            '13:00',
            '14:00',
            '15:00',
            '16:00',
        ],
        'C6H6(GT)': [
            2.0,
            10.0,
            3.0,
            8.0,
            1.0,
        ]}
    )
    errors = rule.validate(df, ['C6H6(GT)'])
    assert len(errors) == 2


@pytest.mark.validation
def test_data_gap_rule_multiple_columns():
    """Несколько колонок с разрывами"""
    rule = DataGapRule(max_gap_hours=10)

    df = pd.DataFrame({
        'Date': ['01/01/2024'] * 20,
        'Time': [f'{i}.00.00' for i in range(20)],
        'CO(GT)': [1.0] * 5 + [np.nan] * 15,  # разрыв 15 часов
        'NO2(GT)': [np.nan] * 15 + [1.0] * 5,  # разрыв 15 часов
        'C6H6(GT)': [1.0] * 20  # без разрывов
    })

    errors = rule.validate(df, ['CO(GT)', 'NO2(GT)', 'C6H6(GT)'])

    # Должны быть ошибки для CO(GT) и NO2(GT), но не для C6H6(GT)
    assert len(errors) == 2
    for error in errors:
        assert isinstance(error, DataGapError)
        assert error.gap_hours == 15

@pytest.fixture()
def sample_series():
    return pd.Series([1.0, np.nan, 3.0, 4.0, np.nan])

@pytest.mark.parametrize("Strategy, expected", [
    (FillMedianStrategy, 3.0),
    (FillMeanStrategy, 2.67),
])

@pytest.mark.strategy
def test_fill_strategies(sample_series, Strategy, expected):
    handler = Strategy()
    result = handler.handle(np.nan, sample_series, 1, None)
    assert result == approx(expected, abs=0.01)

@pytest.mark.strategy
def test_fill_previous_strategy():
    series = pd.Series([1.0, np.nan, np.nan, 4.0])
    handler = FillPreviousStrategy()
    for idx in range(1, len(series)-1):
        result = handler.handle(np.nan, series, idx, None)
        assert result == 1.0
    assert handler.handle(4.0, series, 3, None) == 4.0

@pytest.mark.strategy
def test_fill_previous_first_element_nan():
    """Краевой случай: первый элемент NaN"""
    series = pd.Series([np.nan, 2.0, 3.0])
    handler = FillPreviousStrategy()
    assert pd.isna(handler.handle(np.nan, series, 0, None))

@pytest.mark.strategy
def test_drop_row_strategy():
    df = pd.DataFrame({
        'A': [1.0, np.nan, np.nan, 4.0],
        'B': [np.nan, np.nan, np.nan, 5.0],
        'C': [1.0, 2.0, 3.0, 4.0]
    })
    dropper = DropRowStrategy(threshold=0.5)
    expected = pd.DataFrame({
        'A': [1.0, 4.0],
        'B': [np.nan, 5.0],
        'C': [1.0, 4.0]})
    result = dropper.handle(None, None, None, df).reset_index(drop=True)
    assert_frame_equal(result, expected)
