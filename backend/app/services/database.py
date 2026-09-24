from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from app.security.redaction import redact


def now():
    return datetime.now(timezone.utc).isoformat()


class Base(DeclarativeBase):
    pass


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    repository_url: Mapped[str] = mapped_column(String(300))
    objective: Mapped[str] = mapped_column(String(1500))
    status: Mapped[str] = mapped_column(String(30), default="queued")
    created_at: Mapped[str] = mapped_column(String(40), default=now)
    completed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    report: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Event(Base):
    __tablename__ = "events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    type: Mapped[str] = mapped_column(String(50))
    data: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[str] = mapped_column(String(40), default=now)


class ReviewStep(Base):
    __tablename__ = "review_steps"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    step_number: Mapped[int] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)


class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    tool_name: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    input_summary: Mapped[str] = mapped_column(String(500), default="")
    output_summary: Mapped[str] = mapped_column(String(1000), default="")
    error: Mapped[str] = mapped_column(String(1000), default="")
    retry_count: Mapped[int] = mapped_column(Integer)


class Finding(Base):
    __tablename__ = "issues"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    review_id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), index=True)
    data: Mapped[dict] = mapped_column(JSON)


class Repository(Base):
    __tablename__ = "repositories"
    id: Mapped[str] = mapped_column(ForeignKey("reviews.id"), primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


class Store:
    def __init__(self, url):
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine = create_engine(url, pool_pre_ping=True,
                                   connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {})
        self.session = sessionmaker(self.engine, expire_on_commit=False)

    def initialize(self):
        Base.metadata.create_all(self.engine)
        with self.session.begin() as session:
            for review in session.scalars(select(Review).where(Review.status.in_(["queued", "running"]))):
                review.status = "failed"
                review.completed_at = now()
                review.report = {"review": {"status": "failed"}, "issues": [],
                                 "limitations": ["Server restarted during execution; start a new review."]}
                session.add(Event(review_id=review.id, type="review_failed", data={"error": "Server restarted"}))

    def create(self, goal):
        identifier = str(uuid4())
        with self.session.begin() as session:
            session.add(Review(id=identifier, **redact(goal.model_dump())))
        return identifier

    def get(self, identifier):
        with self.session() as session:
            review = session.get(Review, identifier)
            if review is None:
                return None
            return {key: getattr(review, key) for key in ("id", "repository_url", "objective", "status",
                                                        "created_at", "completed_at", "report")}

    def list(self, limit=50, offset=0):
        with self.session() as session:
            rows = session.scalars(select(Review).order_by(Review.created_at.desc()).offset(offset).limit(limit))
            return [{key: getattr(r, key) for key in ("id", "repository_url", "objective", "status", "created_at")}
                    for r in rows]

    def events(self, identifier, after=0):
        with self.session() as session:
            rows = session.scalars(select(Event).where(Event.review_id == identifier, Event.id > after)
                                   .order_by(Event.id).limit(500))
            return [{"id": e.id, "type": e.type, "data": e.data, "created_at": e.created_at} for e in rows]

    def emit(self, identifier, kind, data):
        data = redact(data)
        with self.session.begin() as session:
            session.add(Event(review_id=identifier, type=kind, data=data))
            review = session.get(Review, identifier)
            if kind == "plan_created":
                review.status = "running"
            if kind in {"step_started", "step_completed"}:
                key = f"{identifier}:{data['id']}"
                step = session.get(ReviewStep, key)
                if step is None:
                    step = ReviewStep(id=key, review_id=identifier, step_number=data["id"],
                                      action=data["action"], status=data["status"])
                    session.add(step)
                step.status = data["status"]
                if kind == "step_started":
                    step.started_at = now()
                else:
                    step.completed_at = now()
            if kind in {"tool_started", "tool_completed", "tool_failed"}:
                key = f"{identifier}:{data['tool']}:{data['attempt']}"
                call = session.get(ToolCall, key)
                if call is None:
                    call = ToolCall(id=key, review_id=identifier, tool_name=data["tool"],
                                    status="running", retry_count=data["attempt"], input_summary=data.get("action", ""))
                    session.add(call)
                call.status = {"tool_started": "running", "tool_completed": data.get("status", "ok"),
                               "tool_failed": "failed"}[kind]
                call.output_summary = data.get("observation", "")
                call.error = data.get("error", "")

    def finish(self, identifier, report):
        report = redact(report)
        with self.session.begin() as session:
            review = session.get(Review, identifier)
            review.status = report["review"]["status"]
            review.completed_at = now()
            review.report = report
            session.add(Repository(id=identifier, data=report.get("repository", {})))
            for i, issue in enumerate(report.get("issues", [])):
                session.add(Finding(id=f"{identifier}:{i}", review_id=identifier, data=issue))
