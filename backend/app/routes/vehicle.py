from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.models import User, Vehicle
from backend.app.schemas.schemas import VehicleCreate, VehicleUpdate, VehicleResponse
from backend.app.security.deps import get_current_user, get_user_vehicle_or_404
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.calculation_service import CalculationService

router = APIRouter(tags=["Veículo"])

@router.get("/vehicle", response_model=Optional[VehicleResponse])
def get_primary_vehicle(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna o veículo principal do usuário autenticado."""
    vehicle = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).first()
    return vehicle

@router.get("/vehicles", response_model=List[VehicleResponse])
def list_vehicles(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Lista todos os veículos do usuário autenticado."""
    return db.query(Vehicle).filter(Vehicle.user_id == current_user.id).all()

@router.post("/vehicle", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    data: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Regra 12: No MVP limite de 1 carro por usuário no plano trial/free
    existing_count = db.query(Vehicle).filter(Vehicle.user_id == current_user.id).count()
    if existing_count >= 1 and current_user.plan != "premium":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O plano atual permite o cadastro de 1 veículo. Faça upgrade para cadastrar múltiplos carros."
        )

    vehicle = Vehicle(
        user_id=current_user.id,
        brand=data.brand.strip(),
        model=data.model.strip(),
        year=data.year,
        version=data.version.strip() if data.version else None,
        fuel_type=data.fuel_type.lower(),
        current_odometer=data.current_odometer,
        license_plate=data.license_plate.strip().upper() if data.license_plate else None
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)

    AnalyticsService.track_event(db, current_user.id, "vehicle_created", {
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year
    })

    return vehicle

@router.put("/vehicle/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    data: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(vehicle_id, current_user, db)

    if data.brand is not None:
        vehicle.brand = data.brand.strip()
    if data.model is not None:
        vehicle.model = data.model.strip()
    if data.year is not None:
        vehicle.year = data.year
    if data.version is not None:
        vehicle.version = data.version.strip()
    if data.fuel_type is not None:
        vehicle.fuel_type = data.fuel_type.lower()
    if data.license_plate is not None:
        vehicle.license_plate = data.license_plate.strip().upper()
    if data.current_odometer is not None:
        valid, _ = CalculationService.validate_odometer(vehicle.current_odometer, data.current_odometer)
        vehicle.current_odometer = data.current_odometer

    db.commit()
    db.refresh(vehicle)
    return vehicle
