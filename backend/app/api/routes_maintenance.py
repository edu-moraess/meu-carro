from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.models.models import MaintenanceRecord, Vehicle
from backend.app.schemas.schemas import MaintenanceCreate, MaintenanceResponse
from backend.app.services.calculation_service import CalculationService

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

@router.post("", response_model=MaintenanceResponse)
def create_maintenance_record(maint_in: MaintenanceCreate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == maint_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    max_recorded = vehicle.current_odometer
    valid, warning = CalculationService.validate_odometer(max_recorded, maint_in.odometer)
    if not valid and not maint_in.allow_lower_odometer:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ODOMETER_LOWER_THAN_PREVIOUS",
                "message": warning
            }
        )

    record = MaintenanceRecord(
        vehicle_id=maint_in.vehicle_id,
        date=maint_in.date,
        odometer=maint_in.odometer,
        category=maint_in.category,
        description=maint_in.description,
        workshop=maint_in.workshop,
        cost=maint_in.cost,
        next_maintenance_km=maint_in.next_maintenance_km,
        next_maintenance_date=maint_in.next_maintenance_date,
        notes=maint_in.notes
    )
    db.add(record)

    if maint_in.odometer > vehicle.current_odometer:
        vehicle.current_odometer = maint_in.odometer

    db.commit()
    db.refresh(record)
    return record

@router.get("", response_model=List[MaintenanceResponse])
def list_maintenance_records(vehicle_id: int, db: Session = Depends(get_db)):
    return db.query(MaintenanceRecord)\
        .filter(MaintenanceRecord.vehicle_id == vehicle_id)\
        .order_by(MaintenanceRecord.date.desc(), MaintenanceRecord.id.desc())\
        .all()

@router.delete("/{record_id}")
def delete_maintenance_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(MaintenanceRecord).filter(MaintenanceRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro de manutenção não encontrado")
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "Manutenção removida com sucesso"}
