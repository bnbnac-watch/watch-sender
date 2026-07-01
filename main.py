from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
import db
import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init()
    yield


app = FastAPI(lifespan=lifespan)


class NotifyRequest(BaseModel):
    crawler_id: str
    items: list[dict]


class ErrorRequest(BaseModel):
    crawler_id: str
    error: str
    fail_count: int


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/notify")
async def notify(req: NotifyRequest):
    await router.route_notify(req.crawler_id, req.items)
    return {"status": "ok"}


@app.post("/error")
async def error(req: ErrorRequest):
    await router.route_error(req.crawler_id, req.error, req.fail_count)
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
