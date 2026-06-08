from abc import ABC, abstractmethod
import pandas as pd

class MissingValueStrategy(ABC):
     @abstractmethod
     def handle(self, value, series, idx, df):
         pass

class DropRowStrategy(MissingValueStrategy):
    """Удаляет строки с долей пропусков выше порога"""
    def __init__(self, threshold=0.5):
        self.threshold = threshold
    def handle(self, value, series, idx, df):
        return df.dropna(thresh=int(len(df.columns)*(1 - self.threshold)))

class FillMedianStrategy(MissingValueStrategy):
    """Заполняет пропуск медианным значением колонки"""
    def handle(self, value, series, idx, df):
        if pd.isna(value):
            return series.median()
        else:
            return value

class FillMeanStrategy(MissingValueStrategy):
    """Заполняет пропуск средним арифметическим колонки"""
    def handle(self, value, series, idx, df):
        if pd.isna(value):
            return series.mean()
        else:
            return value

class FillPreviousStrategy(MissingValueStrategy):
    """Заполняет пропуск предыдущим значением в колонке"""
    def handle(self, value, series, idx, df):
        mask = [x for x in series[:idx] if not pd.isna(x)]
        if (pd.isna(value) and idx != 0 and mask):
            return mask[-1]
        return value

class FillGapStrategy:
    """Контекст для работы со стратегиями заполнения пропусков"""
    def __init__(self, strategy):
        self.strategy = strategy
    def set_strategy(self, strategy):
        """Позволяет менять стратегию во время выполнения"""
        self.strategy = strategy
    def apply_to_column(self, series, df):
        """Применяет текущую стратегию ко всей колонке"""
        if not self.strategy:
            raise ValueError("Стратегия не установлена")
        result = series.copy()
        for idx, value in enumerate(series):
            result.iloc[idx] = self.strategy.handle(value, series, idx, df)
        return result
    def apply_to_selected_columns(self, df, columns):
        """Применяет текущую стратегию к выбранным колонкам"""
        if not self.strategy:
            raise ValueError("Стратегия не установлена")
        result = df.copy()
        for column in columns:
            self.apply_to_column(result[column], result)
        return result




