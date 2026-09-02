from backend.app.config import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker

    connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=settings.DEBUG and settings.ENVIRONMENT == "development"
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

except ImportError:
    # Fallback puro para ambientes de teste sem sqlalchemy instalada globalmente
    engine = None
    SessionLocal = None

    class BaseFallback:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        @classmethod
        def metadata(cls):
            pass

    Base = BaseFallback

    def get_db():
        yield None
