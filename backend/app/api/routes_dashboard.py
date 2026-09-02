from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.models import Vehicle, FuelRecord, MaintenanceRecord, ExpenseRecord
from backend.app.schemas.schemas import DashboardResponse
from backend.app.services.calculation_service import CalculationService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("", response_model=DashboardResponse)
def get_dashboard_summary(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    fuels = db.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle_id).all()
    maintenances = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id).all()
    expenses = db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle_id).all()

    return CalculationService.calculate_dashboard(
        vehicle=vehicle,
        fuels=fuels,
        maintenances=maintenances,
        expenses=expenses
    )
