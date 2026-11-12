"""Q14-15: bounded pagination and retries, independent of analysis."""

import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

logger = logging.getLogger("agentiq")
RETRYABLE = {429, 500, 502, 503, 504}


class ConnectorError(RuntimeError):
    """A sanitized integration failure; never include credentials or bodies."""


def retry_delay(response, attempt):
    """Honor Retry-After (seconds or HTTP date), capped at 30 seconds."""
    fallback = min(2 ** attempt, 30)
    if response is None:
        return fallback
    header = response.headers.get("Retry-After")
    if header is None:
        return fallback
    try:
        seconds = float(header)
    except ValueError:
        try:
            date = parsedate_to_datetime(header)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            seconds = (date - datetime.now(timezone.utc)).total_seconds()
        except (ValueError, TypeError, OverflowError):
            return fallback
    return min(max(seconds, 0), 30)


def collect_pages(client, url, token="", *, max_attempts=3, max_pages=100, sleep=time.sleep):
    """Contract: GET ?page=N -> {records: [...], next_page: N+1 or null}.

    Only numeric cursors are followed; credentials always go to the original URL.
    max_attempts includes the first request, and applies separately to each page.
    """
    if max_attempts < 1 or max_pages < 1:
        raise ValueError("Retry and page bounds must be positive")
    records, visited, page = [], set(), 1
    while page is not None:
        if page in visited or len(visited) >= max_pages:
            raise ConnectorError("Pagination cycle or page limit reached")
        visited.add(page)
        for attempt in range(max_attempts):
            response = None
            try:
                response = client.get(
                    url, params={"page": page},
                    headers={"Authorization": f"Bearer {token}"} if token else {},
                    timeout=10, follow_redirects=False,
                )
            except httpx.TransportError:
                logger.warning("connector_failure page=%d attempt=%d kind=transport", page, attempt + 1)
                if attempt + 1 == max_attempts:
                    raise ConnectorError("Transport failure after bounded retries") from None
            else:
                if response.status_code == 200:
                    break
                logger.warning("connector_failure page=%d attempt=%d status=%d", page, attempt + 1, response.status_code)
                if response.status_code not in RETRYABLE:
                    raise ConnectorError(f"Non-retryable HTTP {response.status_code}")
                if attempt + 1 == max_attempts:
                    raise ConnectorError(f"HTTP {response.status_code} after bounded retries")
            sleep(retry_delay(response, attempt))
        try:
            payload = response.json()
        except ValueError:
            raise ConnectorError("External API returned invalid JSON") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list) or "next_page" not in payload:
            raise ConnectorError("External API returned an invalid page schema")
        next_page = payload["next_page"]
        if next_page is not None and (type(next_page) is not int or next_page <= 0):
            raise ConnectorError("External API returned an invalid page cursor")
        records.extend(payload["records"])
        page = next_page
    logger.info("connector_completed pages=%d records=%d", len(visited), len(records))
    return records
