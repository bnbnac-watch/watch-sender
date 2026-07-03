import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import db
import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    async with httpx.AsyncClient(timeout=10) as client:
        router.set_client(client)
        yield


app = FastAPI(lifespan=lifespan)


class NotifyRequest(BaseModel):
    crawler_id: int
    items: list[dict]


class BatchEntry(BaseModel):
    crawler_id: int
    items: list[dict]


class BatchNotifyRequest(BaseModel):
    entries: list[BatchEntry]


class ErrorRequest(BaseModel):
    crawler_id: int
    error: str
    fail_count: int


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/notify")
async def notify(req: NotifyRequest):
    await router.route_notify(req.crawler_id, req.items)
    return {"status": "ok"}


@app.post("/notify/batch")
async def notify_batch(req: BatchNotifyRequest):
    await router.route_notify_batch([e.model_dump() for e in req.entries])
    return {"status": "ok"}


@app.post("/error")
async def error(req: ErrorRequest):
    await router.route_error(req.crawler_id, req.error, req.fail_count)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
