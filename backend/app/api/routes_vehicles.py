from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.core.database import get_db
from backend.app.models.models import Vehicle
from backend.app.schemas.schemas import VehicleCreate, VehicleResponse, VehicleUpdate

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

@router.post("", response_model=VehicleResponse)
def create_vehicle(vehicle_in: VehicleCreate, db: Session = Depends(get_db)):
    vehicle = Vehicle(
        brand=vehicle_in.brand,
        model=vehicle_in.model,
        year=vehicle_in.year,
        current_odometer=vehicle_in.current_odometer,
        fuel_type=vehicle_in.fuel_type,
        license_plate=vehicle_in.license_plate
    )
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@router.get("", response_model=List[VehicleResponse])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).all()

@router.get("/current", response_model=Optional[VehicleResponse])
def get_current_vehicle(db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).order_by(Vehicle.id.desc()).first()
    return vehicle

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(vehicle_id: int, vehicle_in: VehicleUpdate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")
    
    update_data = vehicle_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(vehicle, field, val)
        
    db.commit()
    db.refresh(vehicle)
    return vehicle
