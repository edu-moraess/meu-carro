import datetime

try:
    from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Numeric
    from sqlalchemy.orm import relationship
    from backend.app.database import Base
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False
    from backend.app.database import Base
    def Column(*args, **kwargs): return None
    def Integer(*args, **kwargs): return None
    def String(*args, **kwargs): return None
    def Float(*args, **kwargs): return None
    def DateTime(*args, **kwargs): return None
    def ForeignKey(*args, **kwargs): return None
    def Text(*args, **kwargs): return None
    def Boolean(*args, **kwargs): return None
    def Numeric(*args, **kwargs): return None
    def relationship(*args, **kwargs): return None

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)

class ModelBase(Base):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class User(ModelBase):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    
    trial_started_at = Column(DateTime(timezone=True), default=utcnow)
    trial_ends_at = Column(DateTime(timezone=True), nullable=False)
    plan = Column(String(20), default="trial", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    referral_code = Column(String(20), unique=True, index=True, nullable=False)
    referred_by = Column(String(20), nullable=True)

    vehicles = relationship("Vehicle", back_populates="user", cascade="all, delete-orphan")
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    events = relationship("AnalyticsEvent", back_populates="user", cascade="all, delete-orphan")


class Vehicle(ModelBase):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    brand = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    version = Column(String(50), nullable=True)
    fuel_type = Column(String(30), nullable=False, default="flex")
    current_odometer = Column(Integer, nullable=False, default=0)
    license_plate = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="vehicles")
    fuel_records = relationship("FuelRecord", back_populates="vehicle", cascade="all, delete-orphan")
    maintenance_records = relationship("MaintenanceRecord", back_populates="vehicle", cascade="all, delete-orphan")
    expense_records = relationship("ExpenseRecord", back_populates="vehicle", cascade="all, delete-orphan")


class FuelRecord(ModelBase):
    __tablename__ = "fuel_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    odometer = Column(Integer, nullable=False)
    liters = Column(Float, nullable=False)
    price_per_liter = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    fuel_type = Column(String(30), nullable=False, default="gasoline")
    station = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    consumption_km_per_l = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    vehicle = relationship("Vehicle", back_populates="fuel_records")


class MaintenanceRecord(ModelBase):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    odometer = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    workshop = Column(String(100), nullable=True)
    cost = Column(Float, nullable=False)
    next_due_odometer = Column(Integer, nullable=True)
    next_due_date = Column(String(10), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    vehicle = relationship("Vehicle", back_populates="maintenance_records")


class ExpenseRecord(ModelBase):
    __tablename__ = "expense_records"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String(10), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    vehicle = relationship("Vehicle", back_populates="expense_records")


class Feedback(ModelBase):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="feedbacks")


class AnalyticsEvent(ModelBase):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_name = Column(String(100), nullable=False, index=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="events")
