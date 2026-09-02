from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.models.models import FuelRecord, Vehicle
from backend.app.schemas.schemas import FuelCreate, FuelResponse
from backend.app.services.calculation_service import CalculationService

router = APIRouter(prefix="/fuel", tags=["fuel"])

@router.post("", response_model=FuelResponse)
def create_fuel_record(fuel_in: FuelCreate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == fuel_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    # Regra de negócio: O odômetro nunca pode diminuir sem aviso
    max_recorded = vehicle.current_odometer
    valid, warning = CalculationService.validate_odometer(max_recorded, fuel_in.odometer)
    if not valid and not fuel_in.allow_lower_odometer:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "ODOMETER_LOWER_THAN_PREVIOUS",
                "message": warning
            }
        )

    # Último abastecimento anterior para cálculo de consumo
    prev_fuel = db.query(FuelRecord)\
        .filter(FuelRecord.vehicle_id == fuel_in.vehicle_id)\
        .order_by(FuelRecord.odometer.desc())\
        .first()

    consumption = CalculationService.calculate_fuel_consumption(
        previous_fuel=prev_fuel,
        current_odometer=fuel_in.odometer,
        liters=fuel_in.liters
    )

    total_value = round(fuel_in.liters * fuel_in.price_per_liter, 2)

    record = FuelRecord(
        vehicle_id=fuel_in.vehicle_id,
        date=fuel_in.date,
        odometer=fuel_in.odometer,
        liters=fuel_in.liters,
        price_per_liter=fuel_in.price_per_liter,
        total_value=total_value,
        fuel_type=fuel_in.fuel_type,
        station=fuel_in.station,
        notes=fuel_in.notes,
        consumption_km_per_l=consumption
    )
    db.add(record)

    # Atualiza o odômetro do veículo se for maior
    if fuel_in.odometer > vehicle.current_odometer:
        vehicle.current_odometer = fuel_in.odometer

    db.commit()
    db.refresh(record)
    return record

@router.get("", response_model=List[FuelResponse])
def list_fuel_records(vehicle_id: int, db: Session = Depends(get_db)):
    return db.query(FuelRecord)\
        .filter(FuelRecord.vehicle_id == vehicle_id)\
        .order_by(FuelRecord.date.desc(), FuelRecord.id.desc())\
        .all()

@router.delete("/{record_id}")
def delete_fuel_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(FuelRecord).filter(FuelRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro de abastecimento não encontrado")
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "Abastecimento removido com sucesso"}
