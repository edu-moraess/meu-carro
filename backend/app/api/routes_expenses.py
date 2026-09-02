from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.app.core.database import get_db
from backend.app.models.models import ExpenseRecord, Vehicle
from backend.app.schemas.schemas import ExpenseCreate, ExpenseResponse

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("", response_model=ExpenseResponse)
def create_expense_record(expense_in: ExpenseCreate, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == expense_in.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Veículo não encontrado")

    record = ExpenseRecord(
        vehicle_id=expense_in.vehicle_id,
        date=expense_in.date,
        category=expense_in.category,
        description=expense_in.description,
        cost=expense_in.cost,
        notes=expense_in.notes
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("", response_model=List[ExpenseResponse])
def list_expense_records(vehicle_id: int, db: Session = Depends(get_db)):
    return db.query(ExpenseRecord)\
        .filter(ExpenseRecord.vehicle_id == vehicle_id)\
        .order_by(ExpenseRecord.date.desc(), ExpenseRecord.id.desc())\
        .all()

@router.delete("/{record_id}")
def delete_expense_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(ExpenseRecord).filter(ExpenseRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Registro de despesa não encontrado")
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "Despesa removida com sucesso"}
