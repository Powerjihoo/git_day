import numpy as np
from functools import lru_cache, wraps
from typing import Callable


def np_cache(maxsize: int = 128) -> Callable:
    """
    Memoization decorator for functions with NumPy array arguments.

    Usage:
        @np_cache(maxsize=256)
        def my_function(array: np.ndarray) -> Any:
            # Function implementation

    Args:
        maxsize (int, optional): Maximum size of the cache. Defaults to 128.

    Returns:
        Callable: Decorated function with memoization support.
    """

    def decorator(function):
        cached_function = lru_cache(maxsize=maxsize)(function)

        @wraps(function)
        def wrapper(*args: np.ndarray):
            """
            Convert array arguments to tuples and cache the results.

            Args:
                *args (np.ndarray): Array arguments to the function.

            Returns:
                Any: Result of the function call.
            """

            tuple_args = tuple(
                tuple(arg) if arg.ndim == 1 else tuple(map(tuple, arg.tolist()))
                for arg in args
            )
            return cached_function(*tuple_args)

        # Copy lru_cache attributes over too
        wrapper.cache_info = cached_function.cache_info
        wrapper.cache_clear = cached_function.cache_clear

        return wrapper

    return decorator
