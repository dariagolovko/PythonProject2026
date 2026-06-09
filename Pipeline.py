import csv
import os
from typing import Generator, Dict, Any, Iterable

# =====================================================================
# ТРЕБОВАНИЕ 1: Итерируемый объект для чтения данных (DataSource)
# =====================================================================
class AirQualityDataSource:
    """
    Компонент загрузчика данных
    Реализует ленивое чтение CSV-файла по одной строке за раз.
    """
    def __init__(self, file_path: str, delimiter: str = ';'):
        self.file_path = file_path
        self.delimiter = delimiter

    # ТРЕБОВАНИЕ 2: Кастомный генератор с yield
    def __iter__(self) -> Generator[Dict[str, Any], None, None]:
        """Лениво читает файл построчно и возвращает каждую строку в виде словаря."""
        if not os.path.exists(self.file_path):
            print(f"Ошибка: Файл {self.file_path} не найден.")
            return

        with open(self.file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=self.delimiter)
            for row in reader:
                # Отсекаем пустые строки, которые часто генерируются в конце AirQualityUCI.csv
                if row.get('Date') is not None and row.get('Date').strip() != '':
                    yield row


# =====================================================================
# ТРЕБОВАНИЕ 3: Итератор-фильтр/преобразователь (Ленивая обертка)
# =====================================================================
class AirQualityFilterTransformer:
    """
    Компонент-пайплайн обработки (Пункт 4).
    Оборачивает входной итератор и лениво трансформирует/фильтрует поток.
    """
    def __init__(self, data_stream: Iterable[Dict[str, Any]]):
        self.data_stream = data_stream

    def lazy_filter_and_clean(self) -> Generator[Dict[str, Any], None, None]:
        """
        Ленивый генератор, который:
        1. Очищает текстовые поля (удаляет пробелы).
        2. Преобразует числовые маркеры пропусков (-200) в None ВО ВСЕХ столбцах.
        3. Фильтрует поток: оставляет только вечерние замеры (с 18:00 до 23:00).
        """
        for row in self.data_stream:
            # --- Шаг 1: Очистка временных полей ---
            time_str = row.get('Time', '').strip()
            date_str = row.get('Date', '').strip()
            
            # Извлекаем час для фильтрации (формат времени в датасете: HH.MM.SS)
            try:
                hour = int(time_str.split('.')[0])
            except (ValueError, IndexError):
                continue  # Пропускаем строку, если время повреждено

            # --- Шаг 2: Ленивая фильтрация по времени ---
            # Фильтруем сразу, чтобы не тратить ресурсы на нормализацию ненужных строк
            if not (18 <= hour <= 23):
                continue

            # --- Шаг 3: Динамическая нормализация аномалий по ВСЕМ столбцам ---
            cleaned_row = {
                'Date': date_str,
                'Time': time_str,
                'Hour': hour
            }

            for key, val in row.items():
                # Пропускаем уже обработанные поля даты и времени
                if key in ('Date', 'Time'):
                    continue
                
                if val is None:
                    cleaned_row[key] = None
                    continue

                # Очищаем строку от пробелов и приводим европейский формат дробей (суффикс ,) к стандартному
                cleaned_val = str(val).strip().replace(',', '.')
                
                try:
                    # Пробуем перевести в число
                    num_val = float(cleaned_val)
                    # Если это маркер пропуска UCI (-200), то сбрасываем в None
                    if num_val == -200.0:
                        cleaned_row[key] = None
                    else:
                        # Если это целое число (например, 150.0), сохраняем как int для красоты, иначе float
                        cleaned_row[key] = int(num_val) if num_val.is_integer() else num_val
                except ValueError:
                    # Если значение не числовое и не -200, оставляем как очищенную строку или None, если она пустая
                    cleaned_row[key] = cleaned_val if cleaned_val != '' else None

            yield cleaned_row