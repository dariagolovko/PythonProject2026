import csv
import os
from typing import Generator, Dict, Any, Iterable

# =====================================================================
# ТРЕБОВАНИЕ 1: Итерируемый объект для чтения данных (DataSource)
# =====================================================================
class AirQualityDataSource:
    """
    Компонент загрузчика данных (Пункт 4).
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
        2. Преобразует числовые маркеры пропусков (-200) в "None".
        3. Фильтрует поток: оставляет только вечерние замеры (с 18:00 до 23:00).
        """
        for row in self.data_stream:
            # --- Шаг 1: Очистка "на лету" ---
            # Убираем лишние пробелы в дате и времени
            time_str = row.get('Time', '').strip()
            
            # Извлекаем час для последующей фильтрации (формат времени в датасете: HH.MM.SS)
            try:
                hour = int(time_str.split('.')[0])
            except (ValueError, IndexError):
                continue  # Пропускаем строку, если время повреждено

            # --- Шаг 2: Нормализация аномалий ---
            # Если значение концентрации CO(GT) равно -200 (маркер пропуска UCI), меняем его на None
            co_value = row.get('CO(GT)', '').replace(',', '.') # Заменяем запятую на точку для чисел
            try:
                co_float = float(co_value)
                if co_float == -200.0:
                    row['CO(GT)'] = None
                else:
                    row['CO(GT)'] = co_float
            except ValueError:
                row['CO(GT)'] = None

            # --- Шаг 3: Ленивая фильтрация ---
            # Отбираем только замеры в часы вечернего пика (например, с 18 до 23 часов)
            if 18 <= hour <= 23:
                yield {
                    'Date': row.get('Date', '').strip(),
                    'Time': time_str,
                    'Hour': hour,
                    'CO(GT)_Cleaned': row['CO(GT)'],
                    'NO2(GT)': row.get('NO2(GT)', '').strip()
                }


# =====================================================================
# Компонент экспорта результатов (Пункт 4)
# =====================================================================
class StreamExporter:
    """Отвечает за сохранение ленивого потока данных в файл."""
    @staticmethod
    def save_stream_to_csv(stream: Iterable[Dict[str, Any]], output_path: str):
        """Построчно записывает проходящий ленивый поток в итоговый CSV."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        writer = None
        with open(output_path, mode='w', encoding='utf-8', newline='') as file:
            for row in stream:
                # Инициализируем заголовки по первому пришедшему элементу
                if writer is None:
                    writer = csv.DictWriter(file, fieldnames=row.keys(), delimiter=';')
                    writer.writeheader()
                writer.writerow(row)


# Блок для локальной проверки работы файла напрямую
if __name__ == "__main__":
    # Предполагаем, что файл AirQualityUCI.csv лежит в корне проекта
    input_csv = "data/AirQualityUCI.csv"
    output_csv = "data/stream_output_cleaned.csv"
    
    print("--- Запуск потоковой обработки (Пункт 3) ---")
    
    # 1. Создаем ленивый источник данных (Итерируемый объект)
    source = AirQualityDataSource(file_path=input_csv, delimiter=';')
    
    # 2. Оборачиваем его в итератор-фильтр
    transformer = AirQualityFilterTransformer(data_stream=source)
    
    # 3. Получаем ленивый пайплайн (генератор)
    clean_stream = transformer.lazy_filter_and_clean()
    
    # 4. Передаем поток в экспортер, который запишет данные, тратя минимум памяти
    print("Обработка пошла... Данные читаются и пишутся построчно.")
    StreamExporter.save_stream_to_csv(clean_stream, output_csv)
    
    print(f"Потоковая обработка успешно завершена! Результат сохранен в: {output_csv}")
