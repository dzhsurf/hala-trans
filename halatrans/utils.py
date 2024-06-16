import logging
import time
from typing import Any, Callable


def performance_check(fn: Callable[[Any], Any], *args):
    t1 = time.time()
    if fn:
        fn(*args)
    t2 = time.time()
    logging.info(f"Time Cost: {t2-t1}")
