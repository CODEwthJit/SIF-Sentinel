"""
Database Session and Engine Configuration
Phase 9.1 — SIH26165
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.core.config import settings

# Configure SQLite check_same_thread if using sqlite
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy import text


def init_db():
    """Initializes tables in database and applies lightweight SQLite migrations if needed."""
    from backend.app.db.models import User, Report, Analysis  # Ensure all models are registered

    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.begin() as conn:
            try:
                res_u = conn.execute(text("PRAGMA table_info(users)")).fetchall()
                u_cols = [r[1] for r in res_u]
                if "username" in u_cols:
                    count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                    if count == 0:
                        conn.execute(text("DROP TABLE users"))
            except Exception:
                pass

    Base.metadata.create_all(bind=engine)

    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.begin() as conn:
            try:
                res = conn.execute(text("PRAGMA table_info(reports)")).fetchall()
                col_names = [r[1] for r in res]
                if col_names and "user_id" not in col_names:
                    conn.execute(text("ALTER TABLE reports ADD COLUMN user_id INTEGER REFERENCES users(id)"))
            except Exception:
                pass

