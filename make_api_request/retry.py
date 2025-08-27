from typing import List, Optional

from typing_extensions import NotRequired, TypedDict


class RetryStrategy(TypedDict):
    """
    Configuration for retrying HTTP requests.
    """

    max_retries: NotRequired[int]
    """
    maximum amount of retries allowed after first request failure. if 5,
    the request could be sent a total of 6 times
    """
    status_codes: NotRequired[List[int]]
    """
    Response status codes that will trigger a retry. These must either be:
    - exact status code (100 <= code < 600), e.g. 408, or
    - unit (0 < num < 6) that represents a status code range, e.g. 5 -> 5XX
    """
    initial_delay: NotRequired[int]
    """
    Initial wait time (milliseconds) after first request failure before a retry is sent
    """
    max_delay: NotRequired[int]
    """
    Maximum wait time between retries
    """
    backoff_factor: NotRequired[float]
    """
    the factor applied to the current wait time to determine the next wait time
    min(current_delay * backoff, max_delay)
    """


class RetryConfig:
    max_retries: int
    status_codes: List[int]
    initial_delay: int
    max_delay: int
    backoff_factor: float

    def __init__(
        self,
        *,
        base: Optional[RetryStrategy] = None,
        override: Optional[RetryStrategy] = None
    ):
        _base: RetryStrategy = base or {}
        _override: RetryStrategy = override or {}

        self.max_retries = _override.get("max_retries", _base.get("max_retries", 5))
        self.status_codes = _override.get(
            "status_codes",
            _base.get(
                "status_codes",
                [
                    5,  # 5XX
                    408,  # Timeout
                    409,  # Conflict
                    429,  # Too Many Requests
                ],
            ),
        )
        self.initial_delay = _override.get(
            "initial_delay", _base.get("initial_delay", 500)
        )
        self.max_delay = _override.get("max_delay", _base.get("max_delay", 10000))
        self.backoff_factor = _override.get(
            "backoff_factor", _base.get("backoff_factor", 2.0)
        )

    def _matches_code(self, status_code: int, retry_code: int) -> bool:
        """
        Custom status_code comparison to support exact match and
        range matches
        """
        if retry_code < 6:
            # Range check (e.g., 4 means 400-499)
            return retry_code * 100 <= status_code < (retry_code + 1) * 100
        else:
            # Exact match
            return status_code == retry_code

    def should_retry(self, *, attempt: int, status_code: int) -> bool:
        """
        Checks if a retry is allowed according to the config
        """
        return attempt <= self.max_retries and any(
            self._matches_code(status_code, c) for c in self.status_codes
        )

    def calc_next_delay(self, *, curr_delay: float) -> float:
        """
        Calculates the time (ms) the retrier should wait before the
        next attempt according to the config
        """
        return min(float(self.max_delay), curr_delay * self.backoff_factor)
