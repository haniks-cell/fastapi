from functools import wraps
import time

def complited_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        print(f"Функция '{func.__name__}' выполнилась за {execution_time:.4f} сек.")
        return result
    return wrapper


