"""Tenacity retry demo: exponential backoff over a flaky claim lookup."""

import logging
import time

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reliability_demo")

_call_count = 0
_permanent_call_count = 0


def flaky_lookup(claim_id: str) -> dict:
    """Times out on the first three calls, then succeeds."""
    global _call_count
    _call_count += 1
    logger.info("flaky_lookup(%r) -> attempt #%d", claim_id, _call_count)
    if _call_count <= 3:
        raise TimeoutError(f"lookup service timed out (attempt {_call_count})")
    return {"claim_id": claim_id, "status": "approved"}


def permanent_not_found(claim_id: str) -> dict:
    """Always fails -- simulates a claim ID that genuinely does not exist."""
    global _permanent_call_count
    _permanent_call_count += 1
    logger.info("permanent_not_found(%r) -> attempt #%d", claim_id, _permanent_call_count)
    raise ValueError("claim not found")


def is_transient_error(exc: BaseException) -> bool:
    """Fault classification: only retry errors that might clear up on their own.

    TimeoutError means the service was reachable but slow, so trying again is
    reasonable. ValueError here means the claim genuinely doesn't exist --
    retrying can't fix that, so it must not be retried at all.
    """
    return isinstance(exc, TimeoutError)


_retry_config = dict(
    retry=retry_if_exception(is_transient_error),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


@retry(**_retry_config)
def lookup_claim(claim_id: str) -> dict:
    return flaky_lookup(claim_id)


@retry(**_retry_config)
def lookup_claim_strict(claim_id: str) -> dict:
    return permanent_not_found(claim_id)


if __name__ == "__main__":
    start = time.monotonic()
    result = lookup_claim("CLM-1042")
    elapsed = time.monotonic() - start
    logger.info("Succeeded after %.2fs total: %s", elapsed, result)

    start = time.monotonic()
    try:
        lookup_claim_strict("CLM-9999")
    except ValueError as exc:
        elapsed = time.monotonic() - start
        logger.info(
            "Failed fast after %.2fs, %d attempt(s): %s",
            elapsed,
            _permanent_call_count,
            exc,
        )
