"""Counties catalog endpoint for AgriRisk Kenya API."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from agririsk.core.database import County, get_db
from agririsk.validation.schemas import CountyRead

router = APIRouter(prefix="/counties", tags=["Counties"])


@router.get("", response_model=List[CountyRead], summary="List all counties")
def list_counties(
    asal_category: Optional[str] = Query(
        default=None,
        description="Filter by ASAL category ('Arid', 'Semi-Arid', 'Non-ASAL')"
    ),
    db: Session = Depends(get_db),
) -> List[CountyRead]:
    """Retrieve all 47 counties of Kenya, with optional filtering by ASAL category.

    Args:
        asal_category: Optional ecological classification filter.
        db: Active database session.

    Returns:
        List of CountyRead objects.
    """
    query = db.query(County)
    if asal_category:
        query = query.filter(County.asal_category == asal_category)
    return query.order_by(County.code).all()


@router.get("/{county_code}", response_model=CountyRead, summary="Get county by code")
def get_county(
    county_code: str,
    db: Session = Depends(get_db)
) -> CountyRead:
    """Retrieve a single county by its 3-digit code.

    Args:
        county_code: County code (e.g. '001' to '047').
        db: Active database session.

    Returns:
        CountyRead object.

    Raises:
        HTTPException: If county with given code is not found.
    """
    normalized_code = county_code.zfill(3)
    county = db.query(County).filter(County.code == normalized_code).first()
    if not county:
        raise HTTPException(
            status_code=404,
            detail=f"County with code '{county_code}' not found."
        )
    return county
