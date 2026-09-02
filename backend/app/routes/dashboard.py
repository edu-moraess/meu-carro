from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User, Vehicle, FuelRecord, MaintenanceRecord, ExpenseRecord
from backend.app.schemas.schemas import DashboardResponse, InsightsResponse
from backend.app.security.deps import get_current_user, get_user_vehicle_or_404
from backend.app.services.calculation_service import CalculationService

router = APIRouter(tags=["Painel & Insights"])

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(vehicle_id, current_user, db)

    fuels = db.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle.id).all()
    maints = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle.id).all()
    expenses = db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle.id).all()

    return CalculationService.calculate_dashboard(
        vehicle=vehicle,
        fuels=fuels,
        maintenances=maints,
        expenses=expenses
    )

@router.get("/insights", response_model=InsightsResponse)
def get_insights(
    vehicle_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    vehicle = get_user_vehicle_or_404(vehicle_id, current_user, db)

    fuels = db.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle.id).all()
    maints = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle.id).all()
    expenses = db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle.id).all()

    dash = CalculationService.calculate_dashboard(
        vehicle=vehicle,
        fuels=fuels,
        maintenances=maints,
        expenses=expenses
    )
    return InsightsResponse(insights=dash.insights)
