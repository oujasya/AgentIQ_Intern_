import logging

import httpx
import pytest

from agentiq.analysis import REFERENCE_AT
from agentiq.connector import ConnectorError, collect_pages
from agentiq.data import ingest
from agentiq.settings import Settings

URL = "https://mock.example/records"


def test_three_page_connector():
    pages = []
    def handler(request):
        page = int(request.url.params["page"])
        pages.append(page)
        return httpx.Response(200, json={"records": [{"id": str(page)}], "next_page": page + 1 if page < 3 else None})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        records = collect_pages(client, URL)
    assert pages == [1, 2, 3]
    assert [r["id"] for r in records] == ["1", "2", "3"]


@pytest.mark.parametrize("kind", ["timeout", 429, 500])
def test_transient_failure_recovers(kind):
    attempts, delays = [], []
    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            if kind == "timeout":
                raise httpx.ReadTimeout("test", request=request)
            return httpx.Response(kind, headers={"Retry-After": "2"})
        return httpx.Response(200, json={"records": [], "next_page": None})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        assert collect_pages(client, URL, sleep=delays.append) == []
    assert len(attempts) == 2
    assert delays == [1 if kind == "timeout" else 2]


@pytest.mark.parametrize("kind", ["timeout", 429, 500])
def test_retries_are_bounded(kind):
    attempts, delays = [], []
    def handler(request):
        attempts.append(request)
        if kind == "timeout":
            raise httpx.ReadTimeout("test", request=request)
        return httpx.Response(kind)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ConnectorError, match="bounded retries"):
            collect_pages(client, URL, sleep=delays.append)
    assert len(attempts) == 3
    assert delays == [1, 2]


@pytest.mark.parametrize("status", [401, 403, 404])
def test_permanent_failures_not_retried(status):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ConnectorError, match=f"Non-retryable HTTP {status}"):
            collect_pages(client, URL)
    assert len(calls) == 1


@pytest.mark.parametrize("payload", [{"records": [], "next_page": 1}, {"records": [], "next_page": "https://other.example"}, {"records": "wrong", "next_page": None}, {"records": []}])
def test_bad_pagination_rejected(payload):
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=payload))) as client:
        with pytest.raises(ConnectorError):
            collect_pages(client, URL)


def test_logs_omit_token_and_record_payload(caplog, store, valid_record):
    token = "SENTINEL_SECRET_TOKEN_123"
    title = "SENTINEL_PRIVATE_RECORD_PAYLOAD_456"
    caplog.set_level(logging.INFO, logger="agentiq")
    invalid = {**valid_record, "title": title, "owner_changes": -1}
    ingest([valid_record, invalid])
    store.upsert([valid_record])
    run = store.create_run(REFERENCE_AT, 3)
    def handler(request):
        assert request.headers["Authorization"] == f"Bearer {token}"
        return httpx.Response(401, text=title)
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ConnectorError):
            collect_pages(client, URL, token)
    assert token not in caplog.text
    assert title not in caplog.text
    assert "validation_failed" in caplog.text
    assert "ingestion" in caplog.text
    assert "connector_failure" in caplog.text
    assert run["run_id"] in caplog.text
    assert token not in repr(Settings(api_token=token))
