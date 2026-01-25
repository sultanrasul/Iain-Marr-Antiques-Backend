import time
from functools import wraps

def timeit(func):
    """Decorator to time a function and print how long it took."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"[TIMING] {func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper
