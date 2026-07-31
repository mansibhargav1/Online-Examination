import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, exam
from app.seed import seed

app = FastAPI(
    title="Online Examination System",
    version="1.0.0",
    description="Application intake, admin-issued accounts, and a server-timed MCQ engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(exam.router)


@app.on_event("startup")
def startup() -> None:
    # Postgres may still be accepting connections late; retry briefly.
    for attempt in range(15):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError:
            print(f"[startup] database not ready, retry {attempt + 1}/15")
            time.sleep(2)
    else:
        raise RuntimeError("Could not reach the database.")

    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok"}
