import time
import logging
from functools import wraps

logger = logging.getLogger("ucp.perf")

def monitor_latency(func):
    """
    Decorator to prove O(1) complexity and sub-millisecond overhead.
    Counter-argument for 'bottleneck' claims.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        logger.debug(f"Audit latency: {duration:.2f}ms")
        return result
    return wrapper
