"""Q11-13, 19-20: FastAPI endpoints sharing the CLI ingestion functions."""

import logging
from typing import Annotated, Any, Literal

from fastapi import Body, FastAPI, HTTPException, Query

from agentiq.data import ingest
from agentiq.settings import Settings
from agentiq.storage import Store


def create_app(settings=None):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.CRITICAL)
    logging.getLogger("httpcore").setLevel(logging.CRITICAL)
    settings = settings or Settings.from_env()
    store = Store(settings.database_path)
    app = FastAPI(title="AgentIQ Assessment", version="1.0.0")
    app.state.store = store

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/records")
    def post_records(records: Annotated[list[Any], Body()]):
        result = ingest(records)
        store.upsert(result["records"])
        # The response includes rejection evidence; logging never includes it.
        return {key: value for key, value in result.items() if key != "records"}

    @app.get("/records")
    def get_records(
        source: Literal["Salesforce", "ServiceNow", "Jira"] | None = None,
        status: Literal["open", "resolved"] | None = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        return store.list_records(source, status, limit, offset)

    @app.post("/runs", status_code=201)
    def create_run():
        return store.create_run(settings.reference_at, settings.handoff_threshold)

    @app.get("/runs/{run_id}/findings")
    def get_findings(run_id: str):
        result = store.get_findings(run_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Analysis run not found")
        return result

    return app
