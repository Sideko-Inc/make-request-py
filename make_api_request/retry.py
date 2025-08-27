from typing import List, TypedDict


class RetryStrategy(TypedDict):
    """
    Configuration for retrying HTTP requests.
    """

    status_codes: List[int]
    """
    Response status codes that will trigger a retry. These must either be:
    - exact status code (100 <= code < 600), e.g. 408, or
    - unit (0 < num < 6) that represents a status code range, e.g. 5 -> 5XX
    """
    initial_delay: int
    """
    Initial wait time (milliseconds) after first request failure before a retry is sent
    """
    max_delay: int
    """
    Maximum wait time between retries
    """
    backoff_factor: float
    """
    the factor applied to the current wait time to determine the next wait time
    min(current_delay * backoff, max_delay)
    """
    max_retries: int
    """
    maximum amount of retries allowed after first request failure. if 5,
    the request could be sent a total of 6 times
    """


def should_retry(status_code: int, retry_codes: List[int]) -> bool:
    def matches_code(retry_code: int) -> bool:
        if retry_code < 6:
            # Range check (e.g., 4 means 400-499)
            return retry_code * 100 <= status_code < (retry_code + 1) * 100
        else:
            # Exact match
            return status_code == retry_code

    return any(matches_code(code) for code in retry_codes)
