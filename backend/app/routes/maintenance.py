import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User, Vehicle, MaintenanceRecord
from backend.app.schemas.schemas import (
    MaintenanceCreate,
    MaintenanceUpdate,
    MaintenanceResponse,
    PaginatedMaintenanceResponse
)
from backend.app.security.deps import get_current_user, get_user_vehicle_or_404
from backend.app.services.calculation_service import CalculationService
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Manutenção"])

@router.get("/maintenance", response_model=PaginatedMaintenanceResponse)
def list_maintenance_records(
    vehicle_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(vehicle_id, current_user, db)

    query = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle.id)
    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    records = query.order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.odometer.desc())\
                   .offset((page - 1) * limit)\
                   .limit(limit)\
                   .all()

    return PaginatedMaintenanceResponse(
        items=[MaintenanceResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.post("/maintenance", response_model=MaintenanceResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_record(
    data: MaintenanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(data.vehicle_id, current_user, db)

    valid, warning = CalculationService.validate_odometer(vehicle.current_odometer, data.odometer)
    if not valid and not data.allow_lower_odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=warning
        )

    record = MaintenanceRecord(
        vehicle_id=vehicle.id,
        date=data.date,
        odometer=data.odometer,
        category=data.category.lower(),
        description=data.description.strip(),
        workshop=data.workshop.strip() if data.workshop else None,
        cost=data.cost,
        next_due_odometer=data.next_due_odometer,
        next_due_date=data.next_due_date,
        notes=data.notes.strip() if data.notes else None
    )
    db.add(record)

    if data.odometer > vehicle.current_odometer:
        vehicle.current_odometer = data.odometer

    db.commit()
    db.refresh(record)

    AnalyticsService.track_event(db, current_user.id, "maintenance_created", {
        "category": record.category,
        "cost": record.cost
    })

    return record

@router.get("/maintenance/{record_id}", response_model=MaintenanceResponse)
def get_maintenance_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MaintenanceRecord).join(Vehicle).filter(
        MaintenanceRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de manutenção não encontrado"
        )
    return record

@router.put("/maintenance/{record_id}", response_model=MaintenanceResponse)
def update_maintenance_record(
    record_id: int,
    data: MaintenanceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MaintenanceRecord).join(Vehicle).filter(
        MaintenanceRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )

    if data.date is not None:
        record.date = data.date
    if data.odometer is not None:
        record.odometer = data.odometer
    if data.category is not None:
        record.category = data.category.lower()
    if data.description is not None:
        record.description = data.description.strip()
    if data.workshop is not None:
        record.workshop = data.workshop.strip()
    if data.cost is not None:
        record.cost = data.cost
    if data.next_due_odometer is not None:
        record.next_due_odometer = data.next_due_odometer
    if data.next_due_date is not None:
        record.next_due_date = data.next_due_date
    if data.notes is not None:
        record.notes = data.notes.strip()

    db.commit()
    db.refresh(record)
    return record

@router.delete("/maintenance/{record_id}")
def delete_maintenance_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MaintenanceRecord).join(Vehicle).filter(
        MaintenanceRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )

    db.delete(record)
    db.commit()
    AnalyticsService.track_event(db, current_user.id, "maintenance_deleted", {"record_id": record_id})
    return {"status": "success", "message": "Registro de manutenção excluído com sucesso"}
