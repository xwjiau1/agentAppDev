import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .models import EncodeRequest, Encoder, Reranker, RerankRequest, VectorInputError


logger = logging.getLogger("uvicorn.error")


class InferenceSlot:
    def __init__(self, wait_seconds: float):
        self.lock = asyncio.Lock()
        self.wait_seconds = wait_seconds
        self.waiting = 0
        self.workers: set[asyncio.Task] = set()

    async def run(self, operation):
        if self.waiting >= 2:
            raise HTTPException(503, "Inference queue is full")
        self.waiting += 1
        try:
            async with asyncio.timeout(self.wait_seconds):
                await self.lock.acquire()
        except TimeoutError as exc:
            raise HTTPException(503, "Inference service is busy") from exc
        finally:
            self.waiting -= 1

        # The background task owns the slot even if the caller stops waiting.
        async def compute():
            try:
                return await asyncio.to_thread(operation)
            finally:
                self.lock.release()

        worker = asyncio.create_task(compute())
        self.workers.add(worker)
        worker.add_done_callback(self.finished)
        return await asyncio.shield(worker)

    def finished(self, task: asyncio.Task):
        self.workers.discard(task)
        if not task.cancelled():
            task.exception()

    async def drain(self):
        await asyncio.gather(*self.workers, return_exceptions=True)


def create_app(role: str, factory=None, *, wait_seconds: float = 1.0) -> FastAPI:
    if role not in {"encoder", "reranker"}:
        raise ValueError(f"Unknown model role: {role}")
    if factory is None:
        factory = Encoder if role == "encoder" else Reranker

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.model = await asyncio.to_thread(factory)
        app.state.slot = InferenceSlot(wait_seconds)
        try:
            yield
        finally:
            await app.state.slot.drain()

    app = FastAPI(lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, _error: RequestValidationError):
        return JSONResponse({"detail": "Invalid inference request"}, status_code=422)

    @app.get("/health/live")
    async def live():
        return {"status": "live"}

    @app.get("/health/ready")
    async def ready():
        return {"status": "ready", "modelSignature": app.state.model.signature}

    async def infer(request: Request, operation, batch_size: int):
        started = time.monotonic()
        try:
            return await app.state.slot.run(operation)
        except VectorInputError as exc:
            raise HTTPException(422, str(exc)) from exc
        finally:
            request_id = request.headers.get("X-Request-ID", "-")[:64]
            logger.info("role=%s requestId=%s batch=%d elapsedMs=%.0f", role,
                        request_id if request_id.isprintable() else "-", batch_size,
                        (time.monotonic() - started) * 1000)

    def encode_route(dense: bool, sparse: bool):
        async def encode(body: EncodeRequest, request: Request):
            model = app.state.model
            operation = partial(model.encode, body.texts, dense=dense, sparse=sparse)
            return {"modelSignature": model.signature, "items": await infer(request, operation, len(body.texts))}

        return encode

    if role == "encoder":
        app.post("/encode", operation_id="encode")(encode_route(True, True))
        app.post("/dense", operation_id="dense")(encode_route(True, False))
        app.post("/sparse", operation_id="sparse")(encode_route(False, True))
    else:
        @app.post("/rerank")
        async def rerank(body: RerankRequest, request: Request):
            if len({item.chunkId for item in body.candidates}) != len(body.candidates):
                raise HTTPException(422, "Candidate IDs must be unique")
            model = app.state.model
            operation = partial(model.score, body.query, body.candidates)
            return {"modelSignature": model.signature, "items": await infer(request, operation, len(body.candidates))}

    return app


def from_environment() -> FastAPI:
    return create_app(os.environ["MODEL_ROLE"], wait_seconds=float(os.getenv("MODEL_QUEUE_SECONDS", "1")))
