"""SQLAlchemy database connection management and County model for AgriRisk Kenya."""

from typing import Generator, Optional
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from agririsk.core.config import settings
from agririsk.core.constants import KENYA_COUNTIES

Base = declarative_base()


class County(Base):
    """SQLAlchemy model representing an official county in Kenya.

    Attributes:
        code: Official 3-digit county identifier (e.g. '001' to '047').
        name: Official administrative name of the county.
        asal_category: Arid and Semi-Arid Land category ('Arid', 'Semi-Arid', 'Non-ASAL').
        centroid_lat: Centroid latitude coordinate in WGS84 (EPSG:4326).
        centroid_lon: Centroid longitude coordinate in WGS84 (EPSG:4326).
    """

    __tablename__ = "counties"

    code = Column(String(10), primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    asal_category = Column(String(20), nullable=False)  # 'Arid', 'Semi-Arid', 'Non-ASAL'
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<County(code='{self.code}', name='{self.name}', asal='{self.asal_category}')>"


def get_engine(database_url: Optional[str] = None) -> Engine:
    """Create and return an SQLAlchemy engine.

    Args:
        database_url: Database connection URI. Defaults to settings.database.url.

    Returns:
        SQLAlchemy Engine instance.
    """
    url = database_url or settings.database.url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    return create_engine(url, connect_args=connect_args, echo=settings.database.echo_sql)


# Global engine and session factory
engine: Engine = get_engine()
SessionLocal: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db(target_engine: Optional[Engine] = None) -> None:
    """Initialize database tables for all registered models.

    Args:
        target_engine: Optional engine instance. Defaults to global engine.
    """
    eng = target_engine or engine
    Base.metadata.create_all(bind=eng)


def seed_counties(session: Session) -> int:
    """Seed the 47 official Kenyan counties if they do not exist.

    Args:
        session: Active SQLAlchemy database session.

    Returns:
        Number of new county records inserted.
    """
    count = 0
    for county_data in KENYA_COUNTIES:
        existing = session.query(County).filter_by(code=county_data["code"]).first()
        if not existing:
            county = County(
                code=county_data["code"],
                name=county_data["name"],
                asal_category=county_data["asal_category"],
                centroid_lat=county_data["lat"],
                centroid_lon=county_data["lon"],
            )
            session.add(county)
            count += 1
    if count > 0:
        session.commit()
    return count


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency generator yielding an active database session.

    Yields:
        Active SQLAlchemy Session instance, automatically closed on completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
