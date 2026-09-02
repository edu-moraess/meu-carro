import math
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User, Vehicle, FuelRecord
from backend.app.schemas.schemas import (
    FuelCreate,
    FuelUpdate,
    FuelResponse,
    PaginatedFuelResponse
)
from backend.app.security.deps import get_current_user, get_user_vehicle_or_404
from backend.app.services.calculation_service import CalculationService
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Combustível"])

@router.get("/fuel", response_model=PaginatedFuelResponse)
def list_fuel_records(
    vehicle_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(vehicle_id, current_user, db)

    query = db.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle.id)
    total = query.count()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    records = query.order_by(FuelRecord.date.desc(), FuelRecord.odometer.desc())\
                   .offset((page - 1) * limit)\
                   .limit(limit)\
                   .all()

    return PaginatedFuelResponse(
        items=[FuelResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.post("/fuel", response_model=FuelResponse, status_code=status.HTTP_201_CREATED)
def create_fuel_record(
    data: FuelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(data.vehicle_id, current_user, db)

    # Validação do odômetro
    valid, warning = CalculationService.validate_odometer(vehicle.current_odometer, data.odometer)
    if not valid and not data.allow_lower_odometer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=warning
        )

    # Cálculo do custo total se não fornecido
    total_cost = data.total_cost if data.total_cost is not None else round(data.liters * data.price_per_liter, 2)

    # Busca abastecimento imediatamente anterior para cálculo de consumo
    prev_fuel = db.query(FuelRecord)\
                  .filter(FuelRecord.vehicle_id == vehicle.id, FuelRecord.odometer < data.odometer)\
                  .order_by(FuelRecord.odometer.desc())\
                  .first()

    consumption = CalculationService.calculate_fuel_consumption(
        previous_fuel=prev_fuel,
        current_odometer=data.odometer,
        liters=data.liters
    )

    record = FuelRecord(
        vehicle_id=vehicle.id,
        date=data.date,
        odometer=data.odometer,
        liters=data.liters,
        price_per_liter=data.price_per_liter,
        total_cost=total_cost,
        fuel_type=data.fuel_type.lower(),
        station=data.station.strip() if data.station else None,
        notes=data.notes.strip() if data.notes else None,
        consumption_km_per_l=consumption
    )
    db.add(record)

    # Atualiza odômetro do veículo se for maior
    if data.odometer > vehicle.current_odometer:
        vehicle.current_odometer = data.odometer

    db.commit()
    db.refresh(record)

    AnalyticsService.track_event(db, current_user.id, "fuel_created", {
        "liters": record.liters,
        "total_cost": record.total_cost
    })

    return record

@router.get("/fuel/{record_id}", response_model=FuelResponse)
def get_fuel_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(FuelRecord).join(Vehicle).filter(
        FuelRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de combustível não encontrado"
        )
    return record

@router.put("/fuel/{record_id}", response_model=FuelResponse)
def update_fuel_record(
    record_id: int,
    data: FuelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(FuelRecord).join(Vehicle).filter(
        FuelRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de combustível não encontrado"
        )

    if data.date is not None:
        record.date = data.date
    if data.odometer is not None:
        record.odometer = data.odometer
    if data.liters is not None:
        record.liters = data.liters
    if data.price_per_liter is not None:
        record.price_per_liter = data.price_per_liter
    if data.total_cost is not None:
        record.total_cost = data.total_cost
    elif data.liters is not None or data.price_per_liter is not None:
        record.total_cost = round(record.liters * record.price_per_liter, 2)
    if data.fuel_type is not None:
        record.fuel_type = data.fuel_type.lower()
    if data.station is not None:
        record.station = data.station.strip()
    if data.notes is not None:
        record.notes = data.notes.strip()

    db.commit()
    db.refresh(record)
    return record

@router.delete("/fuel/{record_id}")
def delete_fuel_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(FuelRecord).join(Vehicle).filter(
        FuelRecord.id == record_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro não encontrado"
        )

    db.delete(record)
    db.commit()
    AnalyticsService.track_event(db, current_user.id, "fuel_deleted", {"record_id": record_id})
    return {"status": "success", "message": "Registro excluído com sucesso"}
