import time
def timer_decorator(func):
    """Декоратор для измерения времени выполнения функции."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[ТАЙМИНГ] Функция '{func.__name__}' выполнилась за {end - start:.4f} секунд\n")
        return result
    return wrapper
