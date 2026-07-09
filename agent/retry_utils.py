import asyncio
import logging
import random
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    pass


def with_groq_retry(max_retries: int = 4, base_delay: float = 10.0):
    """
    Decorator that handles Groq 429 rate limit errors with
    exponential backoff and jitter.
    """
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                        if attempt == max_retries - 1:
                            raise
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 5)
                        logger.warning(
                            f"Groq rate limit hit (attempt {attempt + 1}/{max_retries}). "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        last_error = e
                    else:
                        raise
            raise last_error
        return wrapper
    return decorator