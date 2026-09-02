import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User, Vehicle, ExpenseRecord
from backend.app.schemas.schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    PaginatedExpenseResponse
)
from backend.app.security.deps import get_current_user, get_user_vehicle_or_404
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Despesas Gerais"])

@router.get("/expenses", response_model=PaginatedExpenseResponse)
def list_expense_records(
    vehicle_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(vehicle_id, current_user, db)

    query = db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle.id)
    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    records = query.order_by(ExpenseRecord.date.desc())\
                   .offset((page - 1) * limit)\
                   .limit(limit)\
                   .all()

    return PaginatedExpenseResponse(
        items=[ExpenseResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.post("/expenses", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense_record(
    data: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(data.vehicle_id, current_user, db)

    record = ExpenseRecord(
        vehicle_id=vehicle.id,
        date=data.date,
        category=data.category.lower(),
        description=data.description.strip(),
        amount=data.amount,
        notes=data.notes.strip() if data.notes else None
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    AnalyticsService.track_event(db, current_user.id, "expense_created", {
        "category": record.category,
        "amount": record.amount
    })

    return record

@router.get("/expenses/{record_id}", response_model=ExpenseResponse)
def get_expense_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(ExpenseRecord).join(Vehicle).filter(
        ExpenseRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despesa não encontrada"
        )
    return record

@router.put("/expenses/{record_id}", response_model=ExpenseResponse)
def update_expense_record(
    record_id: int,
    data: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(ExpenseRecord).join(Vehicle).filter(
        ExpenseRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despesa não encontrada"
        )

    if data.date is not None:
        record.date = data.date
    if data.category is not None:
        record.category = data.category.lower()
    if data.description is not None:
        record.description = data.description.strip()
    if data.amount is not None:
        record.amount = data.amount
    if data.notes is not None:
        record.notes = data.notes.strip()

    db.commit()
    db.refresh(record)
    return record

@router.delete("/expenses/{record_id}")
def delete_expense_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(ExpenseRecord).join(Vehicle).filter(
        ExpenseRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Despesa não encontrada"
        )

    db.delete(record)
    db.commit()
    AnalyticsService.track_event(db, current_user.id, "expense_deleted", {"record_id": record_id})
    return {"status": "success", "message": "Despesa excluída com sucesso"}
