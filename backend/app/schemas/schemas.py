import datetime
from typing import Optional, List, Any

try:
    from pydantic import BaseModel, EmailStr, Field
except ImportError:
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        @classmethod
        def model_validate(cls, obj):
            if isinstance(obj, dict):
                return cls(**obj)
            d = {}
            for k in dir(obj):
                if not k.startswith("_"):
                    val = getattr(obj, k)
                    if not callable(val):
                        d[k] = val
            return cls(**d)
    
    EmailStr = str
    def Field(*args, **kwargs):
        return None

# --- Auth & User ---
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Senha mínima de 6 caracteres")
    referral_code: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    plan: str
    trial_started_at: datetime.datetime
    trial_ends_at: datetime.datetime
    referral_code: str
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Subscription ---
class SubscriptionResponse(BaseModel):
    plan: str
    trial_active: bool
    trial_days_remaining: int
    trial_ends_at: datetime.datetime
    warning_message: Optional[str] = None


# --- Vehicle ---
class VehicleCreate(BaseModel):
    brand: str = Field(min_length=1)
    model: str = Field(min_length=1)
    year: int = Field(ge=1900, le=2050)
    version: Optional[str] = None
    fuel_type: str = "flex"
    current_odometer: int = Field(ge=0)
    license_plate: Optional[str] = None

class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    version: Optional[str] = None
    fuel_type: Optional[str] = None
    current_odometer: Optional[int] = Field(None, ge=0)
    license_plate: Optional[str] = None

class VehicleResponse(BaseModel):
    id: int
    user_id: int
    brand: str
    model: str
    year: int
    version: Optional[str] = None
    fuel_type: str
    current_odometer: int
    license_plate: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# --- Fuel ---
class FuelCreate(BaseModel):
    vehicle_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="Formato YYYY-MM-DD")
    odometer: int = Field(ge=0)
    liters: float = Field(gt=0)
    price_per_liter: float = Field(gt=0)
    total_cost: Optional[float] = Field(None, gt=0)
    fuel_type: str = "gasoline"
    station: Optional[str] = None
    notes: Optional[str] = None
    allow_lower_odometer: bool = False

class FuelUpdate(BaseModel):
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    odometer: Optional[int] = Field(None, ge=0)
    liters: Optional[float] = Field(None, gt=0)
    price_per_liter: Optional[float] = Field(None, gt=0)
    total_cost: Optional[float] = Field(None, gt=0)
    fuel_type: Optional[str] = None
    station: Optional[str] = None
    notes: Optional[str] = None

class FuelResponse(BaseModel):
    id: int
    vehicle_id: int
    date: str
    odometer: int
    liters: float
    price_per_liter: float
    total_cost: float
    fuel_type: str
    station: Optional[str] = None
    notes: Optional[str] = None
    consumption_km_per_l: Optional[float] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PaginatedFuelResponse(BaseModel):
    items: List[FuelResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# --- Maintenance ---
class MaintenanceCreate(BaseModel):
    vehicle_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    odometer: int = Field(ge=0)
    category: str
    description: str = Field(min_length=1)
    workshop: Optional[str] = None
    cost: float = Field(ge=0)
    next_due_odometer: Optional[int] = None
    next_due_date: Optional[str] = None
    notes: Optional[str] = None
    allow_lower_odometer: bool = False

class MaintenanceUpdate(BaseModel):
    date: Optional[str] = None
    odometer: Optional[int] = None
    category: Optional[str] = None
    description: Optional[str] = None
    workshop: Optional[str] = None
    cost: Optional[float] = None
    next_due_odometer: Optional[int] = None
    next_due_date: Optional[str] = None
    notes: Optional[str] = None

class MaintenanceResponse(BaseModel):
    id: int
    vehicle_id: int
    date: str
    odometer: int
    category: str
    description: str
    workshop: Optional[str] = None
    cost: float
    next_due_odometer: Optional[int] = None
    next_due_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PaginatedMaintenanceResponse(BaseModel):
    items: List[MaintenanceResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# --- Expense ---
class ExpenseCreate(BaseModel):
    vehicle_id: int
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    category: str
    description: str = Field(min_length=1)
    amount: float = Field(gt=0)
    notes: Optional[str] = None

class ExpenseUpdate(BaseModel):
    date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: int
    vehicle_id: int
    date: str
    category: str
    description: str
    amount: float
    notes: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PaginatedExpenseResponse(BaseModel):
    items: List[ExpenseResponse]
    total: int
    page: int
    limit: int
    total_pages: int


# --- Dashboard & Charts ---
class RecentActivity(BaseModel):
    id: int
    type: str
    title: str
    subtitle: str
    date: str
    value: float
    odometer: Optional[int] = None

class CategoryExpenseItem(BaseModel):
    category: str
    amount: float
    percentage: float

class MonthlyExpenseItem(BaseModel):
    month: str
    total: float

class ConsumptionPoint(BaseModel):
    date: str
    odometer: int
    km_per_l: float

class DashboardResponse(BaseModel):
    monthly_total: float
    monthly_fuel: float
    monthly_maintenance: float
    monthly_other: float
    yearly_total: float
    average_consumption: Optional[float] = None
    cost_per_km: Optional[float] = None
    next_maintenance_km_remaining: Optional[int] = None
    next_maintenance_title: Optional[str] = None
    fuel_expense_percentage: float
    summary_text: str
    insights: List[str]
    recent_activities: List[RecentActivity]
    category_distribution: List[CategoryExpenseItem]
    monthly_history: List[MonthlyExpenseItem]
    consumption_history: List[ConsumptionPoint]

class InsightsResponse(BaseModel):
    insights: List[str]


# --- AI ---
class AiParseTextRequest(BaseModel):
    text: str = Field(min_length=3)

class AiAnalyzeReceiptRequest(BaseModel):
    receipt_text: Optional[str] = None
    image_base64: Optional[str] = None

class AiParsedData(BaseModel):
    type: str = "fuel"
    date: Optional[str] = None
    odometer: Optional[int] = None
    liters: Optional[float] = None
    price_per_liter: Optional[float] = None
    total_cost: Optional[float] = None
    fuel_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    station: Optional[str] = None
    workshop: Optional[str] = None
    confidence: float = 0.95


# --- Referral & Feedback ---
class ReferralResponse(BaseModel):
    referral_code: str
    referred_users: int
    share_text: str

class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    message: str = Field(min_length=2)

class FeedbackResponse(BaseModel):
    id: int
    status: str = "success"
    message: str = "Obrigado por ajudar a melhorar o Meu Carro!"
