from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import logging
from threading import BoundedSemaphore

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.agent import Agent
from app.api.routes import router
from app.config import Settings
from app.services.database import Store

logger = logging.getLogger("review-agent")


def create_app(settings=None, agent_factory=Agent):
    settings = settings or Settings()
    store = Store(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        store.initialize()
        app.state.executor = ThreadPoolExecutor(max_workers=settings.max_workers)
        yield
        app.state.executor.shutdown(wait=True)
        store.engine.dispose()

    app = FastAPI(title="Autonomous GitHub Code Review Agent", version="1.0.0", lifespan=lifespan)
    app.state.settings, app.state.store = settings, store
    app.state.capacity = BoundedSemaphore(settings.max_workers + settings.max_queued)

    def run_review(identifier, goal):
        try:
            report = agent_factory(settings).run(goal, lambda kind, data: store.emit(identifier, kind, data))
            store.finish(identifier, report)
        except Exception:
            logger.error("review_failed", extra={"review_id": identifier})
            store.emit(identifier, "review_failed", {"error": "Internal error; start a new review"})
            store.finish(identifier, {"review": {"status": "failed"}, "issues": [],
                                      "limitations": ["Internal error; start a new review"]})
        finally:
            app.state.capacity.release()

    app.state.run_review = run_review
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if "*" in origins:
        raise ValueError("Configure explicit CORS origins")
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                       allow_headers=["Content-Type", "Authorization"], allow_credentials=False)
    app.include_router(router)

    @app.get("/api/health")
    def health():
        from sqlalchemy import text
        with store.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy"}

    return app


app = create_app()
