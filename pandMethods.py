import os
import pandas as pd
import numpy as np

class PandasAirQualityEngine:
    """
    Класс для полноценного анализа и предобработки данных качества воздуха 
    с помощью библиотеки Pandas.
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path

    def run_analytics(self, output_report_path: str):
        print("Запуск аналитики в Pandas...")
        
        # --- Шаг 1: Чтение данных с учетом особенностей датасета ---
        # В AirQualityUCI разделителем является ';', а также в конце строк часто идут пустые колонки
        df = pd.read_csv(self.file_path, sep=';', decimal=',')
        # Удаляем полностью пустые строки и столбцы, которые часто возникают при чтении этого CSV
        df = df.dropna(how='all').dropna(how='all', axis=1)
        # --- Шаг 2: Очистка аномалий и пропусков (Очистка/нормализация) ---
        # В этом датасете значение -200 означает пропущенное значение (NaN по стандарту UCI)
        # Заменяем все -200 на честные NaN для корректного расчета статистик
        target_columns = [col for col in df.columns if col not in ['Date', 'Time']]
        for col in target_columns:
            df[col] = df[col].replace(-200, np.nan)
        # Заполняем пропуски в ключевых столбцах средним значением (импутация)
        # чтобы данные не терялись при фильтрации
        if 'CO(GT)' in df.columns:
            df['CO(GT)'] = df['CO(GT)'].fillna(df['CO(GT)'].mean())
        if 'NO2(GT)' in df.columns:
            df['NO2(GT)'] = df['NO2(GT)'].fillna(df['NO2(GT)'].mean())
        # --- Шаг 3: Нормализация дат и времени (Работа со временем) ---
        # Объединяем колонки Date и Time в один полноценный datetime объект
        # В датасете даты могут быть в формате DD/MM/YYYY, а время с точками (HH.MM.SS)
        df['Time'] = df['Time'].str.replace('.', ':', regex=False)
        df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], format='%d/%m/%Y %H:%M:%S', errors='coerce')
        
        # Удаляем строки, где дата не смогла распарситься
        df = df.dropna(subset=['datetime'])
        
        # --- Шаг 4: Фильтрация и создание новых колонок ---
        # Создаем новые признаки на основе даты
        df['Hour'] = df['datetime'].dt.hour
        df['Month'] = df['datetime'].dt.month
        
        # Фильтрация: отбираем только дневные часы активного трафика (с 8:00 до 20:00),
        # так как именно в это время выбросы наиболее критичны
        df_traffic_hours = df[(df['Hour'] >= 8) & (df['Hour'] <= 20)].copy()
        
        # Создаем кастомный индекс качества воздуха (условный коэффициент загрязнения CO/NO2)
        # Избегаем деления на ноль с помощью небольшой дельты
        df_traffic_hours['Pollution_Ratio'] = df_traffic_hours['CO(GT)'] / (df_traffic_hours['NO2(GT)'] + 0.1)

        # --- Шаг 5: Агрегация, группировка и формирование отчета ---
        # Сгруппируем данные по месяцам, чтобы увидеть динамику загрязнения в дневные часы
        report = df_traffic_hours.groupby('Month').agg(
            avg_CO=('CO(GT)', 'mean'),
            max_CO=('CO(GT)', 'max'),
            avg_NO2=('NO2(GT)', 'mean'),
            avg_pollution_ratio=('Pollution_Ratio', 'mean'),
            total_valid_records=('datetime', 'count')
        ).reset_index()
        
        # Округляем значения для красивого вывода в отчете
        report = report.round(3)

        # --- Сохранение результата ---
        # Создаем директорию для вывода, если её нет
        os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
        report.to_csv(output_report_path, index=False, sep=';')
        
        print(f"Аналитический отчет успешно сохранен в: {output_report_path}")
        return report

# Пример изолированного запуска для проверки:
if __name__ == "__main__":
    # Укажите правильный путь к вашему файлу AirQualityUCI.csv
    input_file = "data/AirQualityUCI.csv" 
    output_file = "data/air_quality_monthly_report.csv"
    
    if os.path.exists(input_file):
        engine = PandasAirQualityEngine(input_file)
        report_df = engine.run_analytics(output_file)
        print("\nПервые строки созданного отчета:")
        print(report_df.head())
    else:
        print(f"Файл {input_file} не найден. Поместите его в корень проекта.")
