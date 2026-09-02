from __future__ import annotations

import base64
import json
import os
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Optional

import bcrypt
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

st.set_page_config(page_title="Meu Carro", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

# -----------------------------------------------------------------------------
# Premium UI
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0b0d10; }
    [data-testid="stHeader"] { background: rgba(11,13,16,.88); }
    [data-testid="stSidebar"] { background: #101318; border-right: 1px solid #20242b; }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
    .block-container { max-width: 1420px; padding-top: 2.2rem; padding-bottom: 4rem; }

    .brand { display:flex; align-items:center; gap:.75rem; margin-bottom:1.8rem; }
    .brand-mark { width:42px; height:42px; border-radius:12px; display:grid; place-items:center; background:#f5c542; color:#111; font-size:22px; box-shadow:0 8px 28px rgba(245,197,66,.16); }
    .brand-title { font-size:1.15rem; font-weight:800; letter-spacing:-.03em; color:#f4f5f7; }
    .brand-sub { color:#7f8793; font-size:.72rem; margin-top:1px; }

    .hero { padding: 1.65rem 1.8rem; border:1px solid #242932; border-radius:20px; background:linear-gradient(135deg,#151920,#0f1217); margin-bottom:1.2rem; }
    .eyebrow { color:#aab1bc; font-size:.74rem; font-weight:700; text-transform:uppercase; letter-spacing:.13em; }
    .hero h1 { margin:.35rem 0 .35rem; color:#fff; font-size:2.15rem; line-height:1.1; letter-spacing:-.055em; }
    .hero p { color:#8f98a6; margin:0; font-size:.92rem; }

    .kpi { border:1px solid #242932; background:#12161c; border-radius:16px; padding:1rem 1.1rem; min-height:112px; }
    .kpi-label { color:#7f8793; font-size:.74rem; text-transform:uppercase; letter-spacing:.08em; font-weight:700; }
    .kpi-value { color:#f4f5f7; font-size:1.55rem; font-weight:800; letter-spacing:-.04em; margin-top:.35rem; }
    .kpi-note { color:#69727e; font-size:.72rem; margin-top:.3rem; }

    .section-title { color:#f1f3f5; font-size:1.05rem; font-weight:750; letter-spacing:-.025em; margin:.2rem 0 .8rem; }
    .muted { color:#7f8793; }
    .status { display:inline-flex; padding:.28rem .55rem; border-radius:999px; background:#1c222b; color:#b9c0ca; font-size:.7rem; font-weight:700; }
    .status.good { background:#15261e; color:#78d69c; }
    .status.warn { background:#292316; color:#e4bb63; }

    div[data-testid="stMetric"] { background:#12161c; border:1px solid #242932; padding:1rem; border-radius:16px; }
    div[data-testid="stMetricLabel"] { color:#7f8793; }
    div[data-testid="stMetricValue"] { color:#f4f5f7; }
    .stButton > button { border-radius:10px; font-weight:650; min-height:2.45rem; }
    .stButton > button[kind="primary"] { background:#f5c542; border-color:#f5c542; color:#111; }
    .stButton > button[kind="secondary"] { background:#171b21; border-color:#2b313a; color:#e8eaed; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div, textarea { background:#12161c !important; border-color:#2a3039 !important; border-radius:10px !important; }
    .stTabs [data-baseweb="tab-list"] { gap:.25rem; }
    .stTabs [data-baseweb="tab"] { color:#818a97; }
    .stTabs [aria-selected="true"] { color:#f5c542 !important; }
    [data-testid="stDataFrame"] { border:1px solid #242932; border-radius:14px; overflow:hidden; }
    hr { border-color:#242932; }
    </style>
    """,
    unsafe_allow_html=True,
)


def secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


DATABASE_URL = normalize_database_url(secret("DATABASE_URL", "sqlite:///meu_carro.db"))
GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", "gemini-2.5-flash")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    trial_started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default="trial", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(120))
    fuel_type: Mapped[str] = mapped_column(String(30), default="Gasolina", nullable=False)
    current_odometer: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    license_plate: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class FuelRecord(Base):
    __tablename__ = "fuel_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer: Mapped[int] = mapped_column(Integer, nullable=False)
    liters: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    price_per_liter: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    station: Mapped[Optional[str]] = mapped_column(String(120))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    workshop: Mapped[Optional[str]] = mapped_column(String(120))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    next_due_odometer: Mapped[Optional[int]] = mapped_column(Integer)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ExpenseRecord(Base):
    __tablename__ = "expense_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


try:
    Base.metadata.create_all(engine)
except SQLAlchemyError:
    st.error("Não foi possível conectar ao banco. Verifique DATABASE_URL e as credenciais.")
    st.stop()


def money(value: object) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        amount = Decimal("0")
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_km(value: int) -> str:
    return f"{int(value):,}".replace(",", ".") + " km"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def current_user() -> Optional[User]:
    user_id = st.session_state.get("user_id")
    if not isinstance(user_id, int):
        return None
    with SessionLocal() as db:
        return db.get(User, user_id)


def register_user(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1] or len(email) > 255:
        return False, "Informe um e-mail válido."
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."
    now = datetime.utcnow()
    with SessionLocal() as db:
        if db.query(User).filter(User.email == email).first():
            return False, "Este e-mail já está cadastrado."
        code = None
        for _ in range(10):
            candidate = secrets.token_hex(5).upper()
            if not db.query(User).filter(User.referral_code == candidate).first():
                code = candidate
                break
        if not code:
            return False, "Não foi possível gerar seu código de convite."
        user = User(email=email, password_hash=hash_password(password), trial_started_at=now, trial_ends_at=now + timedelta(days=30), referral_code=code)
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
        except IntegrityError:
            db.rollback()
            return False, "Não foi possível criar a conta. Tente novamente."
        st.session_state.user_id = user.id
    return True, "Conta criada. Seu período gratuito de 30 dias começou."


def login_user(email: str, password: str) -> tuple[bool, str]:
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            return False, "E-mail ou senha incorretos."
        st.session_state.user_id = user.id
    return True, "Login realizado."


def refresh_plan(user_id: int) -> User:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if user and user.plan == "trial" and datetime.utcnow() >= user.trial_ends_at:
            user.plan = "free"
            db.commit()
        return user


def vehicle_for(user_id: int) -> Optional[Vehicle]:
    with SessionLocal() as db:
        return db.query(Vehicle).filter(Vehicle.user_id == user_id).order_by(Vehicle.id).first()


def max_odometer(vehicle_id: int) -> int:
    with SessionLocal() as db:
        values = []
        for model in (FuelRecord, MaintenanceRecord):
            row = db.query(model.odometer).filter(model.vehicle_id == vehicle_id).order_by(model.odometer.desc()).first()
            if row and row[0] is not None:
                values.append(int(row[0]))
        return max(values, default=0)


def load_records(vehicle_id: int):
    with SessionLocal() as db:
        fuels = db.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle_id).order_by(FuelRecord.date, FuelRecord.id).all()
        maint = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id).order_by(MaintenanceRecord.date, MaintenanceRecord.id).all()
        expenses = db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle_id).order_by(ExpenseRecord.date, ExpenseRecord.id).all()
    return fuels, maint, expenses


def consumption_rows(fuels: list[FuelRecord]) -> list[dict]:
    rows, previous = [], None
    for fuel in fuels:
        if previous and fuel.odometer > previous.odometer and fuel.liters > 0:
            rows.append({"date": fuel.date, "consumption": round((fuel.odometer - previous.odometer) / float(fuel.liters), 2)})
        previous = fuel
    return rows


def ai_request(prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    parts = [{"text": prompt}]
    if image_bytes:
        parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}}
    try:
        response = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY}, json=payload, timeout=25)
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if not candidates:
            return None
        return candidates[0]["content"]["parts"][0]["text"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None


def parse_ai_json(text: str) -> Optional[dict]:
    try:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(cleaned.splitlines()[1:]).removesuffix("```").strip()
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except (json.JSONDecodeError, AttributeError):
        return None


def save_ai_result(vehicle: Vehicle, data: dict) -> tuple[bool, str]:
    kind = str(data.get("type", "")).lower().strip()
    try:
        record_date = date.fromisoformat(str(data.get("date"))) if data.get("date") else date.today()
        odo_raw = data.get("odometer")
        odometer = int(float(odo_raw)) if odo_raw not in (None, "") else vehicle.current_odometer
    except (ValueError, TypeError):
        return False, "A IA retornou dados inválidos. Revise a imagem e tente novamente."
    if odometer < max_odometer(vehicle.id):
        return False, "A quilometragem informada é menor que um registro existente."
    with SessionLocal() as db:
        if kind == "fuel":
            liters = Decimal(str(data.get("liters") or "0")); price = Decimal(str(data.get("price_per_liter") or "0"))
            if liters <= 0 or price <= 0: return False, "Litros e preço por litro devem ser maiores que zero."
            obj = FuelRecord(vehicle_id=vehicle.id, date=record_date, odometer=odometer, liters=liters, price_per_liter=price, total_cost=liters * price, fuel_type=str(data.get("fuel_type") or vehicle.fuel_type)[:30], station=str(data.get("station") or "")[:120] or None)
        elif kind == "maintenance":
            desc = str(data.get("description") or "").strip(); cost = Decimal(str(data.get("cost") or "0"))
            if not desc or cost <= 0: return False, "Manutenção precisa de descrição e custo válido."
            obj = MaintenanceRecord(vehicle_id=vehicle.id, date=record_date, odometer=odometer, category=str(data.get("category") or "Outros")[:50], description=desc[:255], workshop=str(data.get("workshop") or "")[:120] or None, cost=cost)
        elif kind == "expense":
            desc = str(data.get("description") or "").strip(); amount = Decimal(str(data.get("cost") or "0"))
            if not desc or amount <= 0: return False, "Despesa precisa de descrição e valor válido."
            obj = ExpenseRecord(vehicle_id=vehicle.id, date=record_date, category=str(data.get("category") or "Outros")[:50], description=desc[:255], amount=amount)
        else:
            return False, "Tipo de registro retornado pela IA é inválido."
        db.add(obj)
        current = db.get(Vehicle, vehicle.id)
        if current and odometer > current.current_odometer: current.current_odometer = odometer
        db.commit()
    return True, "Registro salvo com sucesso."


def page_header(eyebrow: str, title: str, description: str = "") -> None:
    st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>', unsafe_allow_html=True)


def kpi(label: str, value: str, note: str = "") -> None:
    st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>', unsafe_allow_html=True)


def auth_page() -> None:
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        st.markdown('<div style="margin-top:7vh">', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">GESTÃO INTELIGENTE</div><h1 style="font-size:3.3rem;letter-spacing:-.07em;margin:.3rem 0">Seu carro.<br>Sem planilhas.</h1><p class="muted" style="font-size:1rem;max-width:520px">Abastecimentos, manutenção, despesas e indicadores em um só lugar.</p>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="hero" style="margin-top:5vh">', unsafe_allow_html=True)
        st.markdown('<div class="brand"><div class="brand-mark">🚗</div><div><div class="brand-title">Meu Carro</div><div class="brand-sub">Personal vehicle intelligence</div></div></div>', unsafe_allow_html=True)
        login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])
        with login_tab:
            with st.form("login_form"):
                email = st.text_input("E-mail")
                password = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar", type="primary", use_container_width=True):
                    ok, message = login_user(email, password)
                    (st.success if ok else st.error)(message)
                    if ok: st.rerun()
        with register_tab:
            with st.form("register_form"):
                email = st.text_input("E-mail", key="register_email")
                password = st.text_input("Senha", type="password", key="register_password")
                confirm = st.text_input("Confirmar senha", type="password")
                if st.form_submit_button("Começar grátis", type="primary", use_container_width=True):
                    if password != confirm: st.error("As senhas não coincidem.")
                    else:
                        ok, message = register_user(email, password)
                        (st.success if ok else st.error)(message)
                        if ok: st.rerun()
        st.caption("30 dias grátis · Sem cartão de crédito")
        st.markdown('</div>', unsafe_allow_html=True)


def vehicle_form(user: User) -> None:
    existing = vehicle_for(user.id); fuels = ["Gasolina", "Etanol", "Diesel", "Flex", "GNV", "Elétrico"]
    with st.form("vehicle_form"):
        c1, c2 = st.columns(2); brand = c1.text_input("Marca", value=existing.brand if existing else ""); model = c2.text_input("Modelo", value=existing.model if existing else "")
        c1, c2, c3 = st.columns(3); current_year = date.today().year
        year = c1.number_input("Ano", 1950, current_year + 1, existing.year if existing else current_year, 1)
        current_fuel = existing.fuel_type if existing else "Gasolina"; fuel = c2.selectbox("Combustível", fuels, index=fuels.index(current_fuel) if current_fuel in fuels else 0)
        odo = c3.number_input("Quilometragem atual", 0, value=existing.current_odometer if existing else 0, step=1)
        version = st.text_input("Versão", value=(existing.version or "") if existing else ""); plate = st.text_input("Placa", value=(existing.license_plate or "") if existing else "")
        if st.form_submit_button("Salvar veículo", type="primary"):
            if not brand.strip() or not model.strip(): st.error("Informe marca e modelo."); return
            if existing and int(odo) < max_odometer(existing.id): st.error("A quilometragem não pode diminuir."); return
            with SessionLocal() as db:
                vehicle = db.get(Vehicle, existing.id) if existing else Vehicle(user_id=user.id)
                vehicle.brand, vehicle.model, vehicle.year, vehicle.fuel_type = brand.strip(), model.strip(), int(year), fuel
                vehicle.current_odometer, vehicle.version, vehicle.license_plate = int(odo), version.strip() or None, plate.strip().upper() or None
                db.add(vehicle); db.commit()
            st.success("Veículo salvo."); st.rerun()


def home_page(vehicle: Vehicle) -> None:
    fuels, maint, expenses = load_records(vehicle.id); today = date.today()
    month_fuel = [x for x in fuels if x.date.year == today.year and x.date.month == today.month]
    month_maint = [x for x in maint if x.date.year == today.year and x.date.month == today.month]
    month_exp = [x for x in expenses if x.date.year == today.year and x.date.month == today.month]
    fuel_total = sum((Decimal(x.total_cost) for x in month_fuel), Decimal()); maint_total = sum((Decimal(x.cost) for x in month_maint), Decimal()); exp_total = sum((Decimal(x.amount) for x in month_exp), Decimal()); total = fuel_total + maint_total + exp_total
    cons = consumption_rows(fuels); avg = sum(x["consumption"] for x in cons[-10:]) / len(cons[-10:]) if cons else None
    page_header("VISÃO GERAL", f"Olá, {vehicle.brand} {vehicle.model}", f"{vehicle.year} · {fmt_km(vehicle.current_odometer)} · {vehicle.fuel_type}")
    cols = st.columns(4)
    with cols[0]: kpi("Gasto este mês", money(total), "combustível + manutenção + despesas")
    with cols[1]: kpi("Combustível", money(fuel_total), f"{len(month_fuel)} abastecimento(s)")
    with cols[2]: kpi("Consumo médio", f"{avg:.1f} km/L" if avg else "—", "últimos abastecimentos")
    with cols[3]: kpi("Registros", str(len(fuels) + len(maint) + len(expenses)), "histórico total")
    st.write("")
    left, right = st.columns([1.6, 1], gap="large")
    with left:
        st.markdown('<div class="section-title">Evolução dos gastos</div>', unsafe_allow_html=True)
        rows = []
        for x in fuels: rows.append({"Data": x.date, "Categoria": "Combustível", "Valor": float(x.total_cost)})
        for x in maint: rows.append({"Data": x.date, "Categoria": "Manutenção", "Valor": float(x.cost)})
        for x in expenses: rows.append({"Data": x.date, "Categoria": "Despesas", "Valor": float(x.amount)})
        if rows:
            df = pd.DataFrame(rows).sort_values("Data"); chart = px.area(df, x="Data", y="Valor", color="Categoria")
            chart.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0), legend_title=None, height=320)
            st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})
        else: st.info("Comece registrando seu primeiro abastecimento.")
    with right:
        st.markdown('<div class="section-title">Resumo do veículo</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="kpi"><div class="kpi-label">Quilometragem</div><div class="kpi-value">{fmt_km(vehicle.current_odometer)}</div><div class="kpi-note">odômetro atual</div></div>', unsafe_allow_html=True)
        st.write("")
        st.markdown(f'<div class="kpi"><div class="kpi-label">Manutenção no mês</div><div class="kpi-value">{money(maint_total)}</div><div class="kpi-note">{len(month_maint)} serviço(s) registrado(s)</div></div>', unsafe_allow_html=True)
    if cons:
        st.write(""); st.markdown('<div class="section-title">Consumo</div>', unsafe_allow_html=True)
        chart = px.line(pd.DataFrame(cons), x="date", y="consumption", markers=True); chart.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0), height=270, yaxis_title="km/L", xaxis_title=None)
        st.plotly_chart(chart, use_container_width=True, config={"displayModeBar": False})


def fuel_page(vehicle: Vehicle) -> None:
    page_header("COMBUSTÍVEL", "Abastecimentos", "Registre cada parada e acompanhe o custo real do seu carro.")
    with st.expander("＋ Registrar abastecimento", expanded=True):
        with st.form("fuel_form"):
            c1,c2,c3=st.columns(3); record_date=c1.date_input("Data", value=date.today(), max_value=date.today()); odo=c2.number_input("Quilometragem",0,value=vehicle.current_odometer,step=1); liters=c3.number_input("Litros",0.001,value=1.0,step=.1)
            c1,c2,c3=st.columns(3); price=c1.number_input("Preço por litro",.001,value=1.0,step=.01); fuel_type=c2.selectbox("Combustível",["Gasolina","Etanol","Diesel","Flex","GNV"]); station=c3.text_input("Posto")
            notes=st.text_area("Observações")
            if st.form_submit_button("Registrar", type="primary"):
                if int(odo)<max_odometer(vehicle.id): st.error("A quilometragem não pode ser menor que um registro existente."); return
                total=Decimal(str(liters))*Decimal(str(price))
                with SessionLocal() as db:
                    db.add(FuelRecord(vehicle_id=vehicle.id,date=record_date,odometer=int(odo),liters=Decimal(str(liters)),price_per_liter=Decimal(str(price)),total_cost=total,fuel_type=fuel_type,station=station.strip()[:120] or None,notes=notes.strip() or None)); current=db.get(Vehicle,vehicle.id)
                    if current and int(odo)>current.current_odometer: current.current_odometer=int(odo)
                    db.commit()
                st.success(f"Abastecimento registrado · {money(total)}"); st.rerun()
    fuels,_,_=load_records(vehicle.id)
    if fuels:
        df=pd.DataFrame([{"Data":x.date.strftime("%d/%m/%Y"),"Km":x.odometer,"Litros":float(x.liters),"R$/L":money(x.price_per_liter),"Total":money(x.total_cost),"Combustível":x.fuel_type,"Posto":x.station or "—"} for x in reversed(fuels)])
        st.dataframe(df,use_container_width=True,hide_index=True)
    else: st.info("Nenhum abastecimento registrado.")


def maintenance_page(vehicle: Vehicle) -> None:
    page_header("CUIDADO", "Manutenção", "Mantenha o histórico do carro organizado e saiba quanto está investindo.")
    categories=["Óleo","Filtros","Pneus","Freios","Suspensão","Motor","Elétrica","Revisão","Inspeção","Outros"]
    with st.expander("＋ Registrar manutenção", expanded=True):
        with st.form("maintenance_form"):
            c1,c2,c3=st.columns(3); record_date=c1.date_input("Data",value=date.today(),max_value=date.today()); odo=c2.number_input("Quilometragem",0,value=vehicle.current_odometer,step=1); category=c3.selectbox("Categoria",categories)
            desc=st.text_input("Descrição"); c1,c2=st.columns(2); workshop=c1.text_input("Oficina"); cost=c2.number_input("Custo",0.0,step=10.0); next_odo=c1.number_input("Próxima revisão (km)",0, value=0, step=100)
            notes=st.text_area("Observações")
            if st.form_submit_button("Registrar",type="primary"):
                if not desc.strip() or cost<=0: st.error("Informe descrição e custo."); return
                if int(odo)<max_odometer(vehicle.id): st.error("A quilometragem não pode diminuir."); return
                with SessionLocal() as db:
                    db.add(MaintenanceRecord(vehicle_id=vehicle.id,date=record_date,odometer=int(odo),category=category,description=desc.strip()[:255],workshop=workshop.strip()[:120] or None,cost=Decimal(str(cost)),next_due_odometer=int(next_odo) if next_odo else None,notes=notes.strip() or None)); current=db.get(Vehicle,vehicle.id)
                    if current and int(odo)>current.current_odometer: current.current_odometer=int(odo)
                    db.commit()
                st.success("Manutenção registrada."); st.rerun()
    _,maint,_=load_records(vehicle.id)
    if maint: st.dataframe(pd.DataFrame([{"Data":x.date.strftime("%d/%m/%Y"),"Km":x.odometer,"Categoria":x.category,"Serviço":x.description,"Oficina":x.workshop or "—","Custo":money(x.cost),"Próxima":fmt_km(x.next_due_odometer) if x.next_due_odometer else "—"} for x in reversed(maint)]),use_container_width=True,hide_index=True)
    else: st.info("Nenhuma manutenção registrada.")


def expenses_page(vehicle: Vehicle) -> None:
    page_header("FINANCEIRO", "Despesas", "Tudo que sai do bolso para manter seu carro rodando.")
    cats=["Seguro","IPVA","Estacionamento","Pedágio","Lavagem","Multa","Documentação","Outros"]
    with st.expander("＋ Registrar despesa", expanded=True):
        with st.form("expense_form"):
            c1,c2=st.columns(2); record_date=c1.date_input("Data",value=date.today(),max_value=date.today()); category=c2.selectbox("Categoria",cats); desc=st.text_input("Descrição"); amount=st.number_input("Valor",0.0,step=10.0); notes=st.text_area("Observações")
            if st.form_submit_button("Registrar",type="primary"):
                if not desc.strip() or amount<=0: st.error("Informe descrição e valor."); return
                with SessionLocal() as db: db.add(ExpenseRecord(vehicle_id=vehicle.id,date=record_date,category=category,description=desc.strip()[:255],amount=Decimal(str(amount)),notes=notes.strip() or None)); db.commit()
                st.success("Despesa registrada."); st.rerun()
    _,_,expenses=load_records(vehicle.id)
    if expenses: st.dataframe(pd.DataFrame([{"Data":x.date.strftime("%d/%m/%Y"),"Categoria":x.category,"Descrição":x.description,"Valor":money(x.amount)} for x in reversed(expenses)]),use_container_width=True,hide_index=True)
    else: st.info("Nenhuma despesa registrada.")


def history_page(vehicle: Vehicle) -> None:
    page_header("HISTÓRICO", "Linha do tempo", "Uma visão única de tudo o que aconteceu com o veículo.")
    fuels,maint,expenses=load_records(vehicle.id); rows=[]
    for x in fuels: rows.append({"Data":x.date,"Tipo":"Abastecimento","Descrição":f"{x.liters} L · {x.fuel_type}","Valor":money(x.total_cost),"Km":x.odometer,"id":x.id,"model":"fuel"})
    for x in maint: rows.append({"Data":x.date,"Tipo":"Manutenção","Descrição":x.description,"Valor":money(x.cost),"Km":x.odometer,"id":x.id,"model":"maintenance"})
    for x in expenses: rows.append({"Data":x.date,"Tipo":"Despesa","Descrição":x.description,"Valor":money(x.amount),"Km":None,"id":x.id,"model":"expense"})
    if not rows: st.info("Seu histórico aparecerá aqui conforme você registrar eventos."); return
    df=pd.DataFrame(rows).sort_values(["Data","id"],ascending=False); st.dataframe(df[["Data","Tipo","Descrição","Valor","Km"]],use_container_width=True,hide_index=True)
    with st.expander("Excluir registro"):
        options={f"{r['Data'].strftime('%d/%m/%Y')} · {r['Tipo']} · {r['Descrição']}":r for r in rows}
        selected=st.selectbox("Selecione um registro",list(options)); r=options[selected]
        if st.button("Excluir definitivamente",type="secondary"):
            model={"fuel":FuelRecord,"maintenance":MaintenanceRecord,"expense":ExpenseRecord}[r["model"]]
            with SessionLocal() as db:
                obj=db.get(model,r["id"])
                if obj and getattr(obj,"vehicle_id",None)==vehicle.id: db.delete(obj); db.commit()
            st.success("Registro excluído."); st.rerun()


def ai_page(vehicle: Vehicle) -> None:
    page_header("ASSISTENTE", "Registrar com IA", "Envie uma foto do comprovante e deixe o Gemini estruturar os dados.")
    if not GEMINI_API_KEY:
        st.warning("A IA não está configurada. Adicione GEMINI_API_KEY aos Secrets do Streamlit.")
        return
    upload=st.file_uploader("Foto do comprovante",type=["jpg","jpeg","png","webp"],help="Use uma imagem nítida. Revise os dados antes de salvar.")
    if upload:
        st.image(upload,width=420)
        if st.button("Analisar comprovante",type="primary"):
            prompt='''Analise este comprovante automotivo. Retorne SOMENTE JSON com as chaves: type (fuel, maintenance ou expense), date (YYYY-MM-DD), odometer (number), liters (number), price_per_liter (number), fuel_type (string), station (string), category (string), description (string), cost (number). Use null quando não houver informação. Não invente valores.'''
            with st.spinner("Lendo comprovante…"):
                raw=ai_request(prompt,upload.getvalue(),upload.type or "image/jpeg")
            data=parse_ai_json(raw or "") if raw else None
            if data: st.session_state.ai_result=data
            else: st.error("Não consegui interpretar o comprovante. Tente uma foto mais nítida.")
    data=st.session_state.get("ai_result")
    if data:
        st.markdown('<div class="section-title">Revise antes de salvar</div>',unsafe_allow_html=True)
        st.json(data)
        c1,c2=st.columns(2)
        if c1.button("Salvar registro",type="primary",use_container_width=True):
            ok,msg=save_ai_result(vehicle,data); (st.success if ok else st.error)(msg)
            if ok: st.session_state.pop("ai_result",None); st.rerun()
        if c2.button("Descartar",use_container_width=True): st.session_state.pop("ai_result",None); st.rerun()


def insights_page(vehicle: Vehicle) -> None:
    fuels,maint,expenses=load_records(vehicle.id); page_header("INTELIGÊNCIA", "Insights", "Indicadores simples para você tomar decisões melhores.")
    cons=consumption_rows(fuels)
    if not fuels and not maint and not expenses: st.info("Registre alguns eventos para liberar os insights."); return
    total=sum((Decimal(x.total_cost) for x in fuels),Decimal())+sum((Decimal(x.cost) for x in maint),Decimal())+sum((Decimal(x.amount) for x in expenses),Decimal())
    avg=sum(x["consumption"] for x in cons[-10:])/len(cons[-10:]) if cons else None
    cols=st.columns(3)
    with cols[0]: kpi("Custo acumulado",money(total),"todos os registros")
    with cols[1]: kpi("Consumo",f"{avg:.1f} km/L" if avg else "—","média recente")
    with cols[2]: kpi("Manutenções",str(len(maint)),"serviços registrados")
    st.write("")
    if avg:
        st.markdown(f'<div class="kpi"><div class="kpi-label">Leitura</div><div class="kpi-value">{avg:.1f} km/L</div><div class="kpi-note">Quanto maior, menor tende a ser o gasto por quilômetro.</div></div>',unsafe_allow_html=True)
    if cons:
        chart=px.bar(pd.DataFrame(cons),x="date",y="consumption"); chart.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=300,margin=dict(l=0,r=0,t=10,b=0),yaxis_title="km/L",xaxis_title=None); st.plotly_chart(chart,use_container_width=True,config={"displayModeBar":False})


def settings_page(user: User, vehicle: Vehicle) -> None:
    page_header("CONTA", "Configurações", "Dados do veículo e preferências da sua conta.")
    tab1,tab2,tab3=st.tabs(["Veículo","Conta","Feedback"])
    with tab1: vehicle_form(user)
    with tab2:
        st.markdown(f"**E-mail**  \n{user.email}")
        st.markdown(f"**Plano**  \n{('Trial · '+str(max(0,(user.trial_ends_at.date()-date.today()).days))+' dias restantes') if user.plan=='trial' else 'Free'}")
        st.markdown(f"**Código de convite**  \n`{user.referral_code}`")
    with tab3:
        with st.form("feedback_form"):
            rating=st.slider("Como está sua experiência?",1,5,5); message=st.text_area("Comentário")
            if st.form_submit_button("Enviar feedback",type="primary"):
                with SessionLocal() as db: db.add(Feedback(user_id=user.id,rating=rating,message=message.strip())); db.commit()
                st.success("Obrigado pelo feedback.")


def main() -> None:
    user=current_user()
    if not user: auth_page(); return
    user=refresh_plan(user.id)
    if not user or not user.is_active: st.session_state.clear(); st.rerun()
    vehicle=vehicle_for(user.id)
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">🚗</div><div><div class="brand-title">Meu Carro</div><div class="brand-sub">Personal vehicle intelligence</div></div></div>',unsafe_allow_html=True)
        if vehicle: st.markdown(f'<div class="status good">● {vehicle.brand} {vehicle.model}</div><div style="height:12px"></div>',unsafe_allow_html=True)
        trial=f"{max(0,(user.trial_ends_at.date()-date.today()).days)} dias restantes" if user.plan=="trial" else "Plano Free"
        st.caption(trial)
        if vehicle:
            page=st.radio("Navegação",["Início","Abastecimentos","Manutenção","Despesas","Histórico","Registrar com IA","Insights","Configurações"],label_visibility="collapsed")
        else: page="Configurações"
        st.divider(); st.caption(user.email)
        if st.button("Sair",use_container_width=True): st.session_state.clear(); st.rerun()
    if not vehicle:
        page_header("PRIMEIRO PASSO","Cadastre seu veículo","Leva menos de um minuto e libera todo o painel.")
        vehicle_form(user); return
    routes={"Início":home_page,"Abastecimentos":fuel_page,"Manutenção":maintenance_page,"Despesas":expenses_page,"Histórico":history_page,"Registrar com IA":ai_page,"Insights":insights_page}
    if page in routes: routes[page](vehicle)
    else: settings_page(user,vehicle)


if __name__ == "__main__":
    main()
