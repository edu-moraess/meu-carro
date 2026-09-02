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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

st.set_page_config(page_title="Meu Carro", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

def secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


DATABASE_URL = secret("DATABASE_URL", "sqlite:///meu_carro.db")
GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", "gemini-2.5-flash")

# SQLite needs check_same_thread=False for Streamlit's rerun/session model.
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
    version: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    fuel_type: Mapped[str] = mapped_column(String(30), default="Gasolina", nullable=False)
    current_odometer: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    license_plate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
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
    station: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    workshop: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    next_due_odometer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


Base.metadata.create_all(engine)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,.15); }
    .small-muted { color: #777; font-size: .9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def money(value: object) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        amount = Decimal("0")
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
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
    if "@" not in email or len(email) > 255:
        return False, "Informe um e-mail válido."
    if len(password) < 8:
        return False, "A senha deve ter pelo menos 8 caracteres."

    with SessionLocal() as db:
        if db.query(User).filter(User.email == email).first():
            return False, "Este e-mail já está cadastrado."
        now = datetime.utcnow()
        user = User(
            email=email,
            password_hash=hash_password(password),
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=30),
            plan="trial",
            referral_code=secrets.token_hex(5).upper(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
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


def vehicle_odometer_is_valid(vehicle_id: int, odometer: int) -> bool:
    with SessionLocal() as db:
        fuel_max = db.query(FuelRecord.odometer).filter(FuelRecord.vehicle_id == vehicle_id).order_by(FuelRecord.odometer.desc()).first()
        maint_max = db.query(MaintenanceRecord.odometer).filter(MaintenanceRecord.vehicle_id == vehicle_id).order_by(MaintenanceRecord.odometer.desc()).first()
    maximums = [row[0] for row in (fuel_max, maint_max) if row]
    return not maximums or odometer >= max(maximums)


def load_records(vehicle_id: int):
    with SessionLocal() as db:
        fuels = db.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle_id).order_by(FuelRecord.date, FuelRecord.id).all()
        maint = db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle_id).order_by(MaintenanceRecord.date, MaintenanceRecord.id).all()
        expenses = db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle_id).order_by(ExpenseRecord.date, ExpenseRecord.id).all()
    return fuels, maint, expenses


def consumption_rows(fuels: list[FuelRecord]) -> list[dict]:
    rows = []
    previous = None
    for fuel in fuels:
        if previous and fuel.odometer > previous.odometer and fuel.liters > 0:
            rows.append({"date": fuel.date, "consumption": round((fuel.odometer - previous.odometer) / float(fuel.liters), 2)})
        previous = fuel
    return rows


def parse_ai_json(text: str) -> Optional[dict]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0].strip()
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def ai_request(prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    parts = [{"text": prompt}]
    if image_bytes:
        parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }
    try:
        response = requests.post(url, json=payload, timeout=25)
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if not candidates:
            return None
        return candidates[0]["content"]["parts"][0]["text"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None


# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------


def auth_page() -> None:
    st.markdown("# 🚗 Meu Carro")
    st.caption("Controle combustível, manutenção e despesas do seu veículo.")
    login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])

    with login_tab:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                ok, message = login_user(email, password)
                (st.success if ok else st.error)(message)
                if ok:
                    st.rerun()

    with register_tab:
        with st.form("register_form"):
            email = st.text_input("E-mail", key="register_email")
            password = st.text_input("Senha", type="password", key="register_password")
            confirm = st.text_input("Confirmar senha", type="password")
            if st.form_submit_button("Criar conta", type="primary"):
                if password != confirm:
                    st.error("As senhas não coincidem.")
                else:
                    ok, message = register_user(email, password)
                    (st.success if ok else st.error)(message)
                    if ok:
                        st.rerun()


def vehicle_form(user: User) -> None:
    existing = vehicle_for(user.id)
    with st.form("vehicle_form"):
        c1, c2 = st.columns(2)
        brand = c1.text_input("Marca", value=existing.brand if existing else "")
        model = c2.text_input("Modelo", value=existing.model if existing else "")
        c1, c2, c3 = st.columns(3)
        current_year = date.today().year
        year = c1.number_input("Ano", min_value=1950, max_value=current_year + 1, value=existing.year if existing else current_year, step=1)
        fuels = ["Gasolina", "Etanol", "Diesel", "Flex", "GNV", "Elétrico"]
        current_fuel = existing.fuel_type if existing else "Gasolina"
        fuel = c2.selectbox("Combustível", fuels, index=fuels.index(current_fuel) if current_fuel in fuels else 0)
        odo = c3.number_input("Quilometragem atual", min_value=0, value=existing.current_odometer if existing else 0, step=1)
        version = st.text_input("Versão (opcional)", value=(existing.version or "") if existing else "")
        plate = st.text_input("Placa (opcional)", value=(existing.license_plate or "") if existing else "")
        if st.form_submit_button("Salvar veículo", type="primary"):
            if not brand.strip() or not model.strip():
                st.error("Informe marca e modelo.")
            else:
                with SessionLocal() as db:
                    vehicle = db.get(Vehicle, existing.id) if existing else Vehicle(user_id=user.id)
                    if vehicle is None:
                        st.error("Veículo não encontrado.")
                        return
                    vehicle.brand = brand.strip()
                    vehicle.model = model.strip()
                    vehicle.year = int(year)
                    vehicle.fuel_type = fuel
                    vehicle.current_odometer = max(vehicle.current_odometer, int(odo))
                    vehicle.version = version.strip() or None
                    vehicle.license_plate = plate.strip().upper() or None
                    db.add(vehicle)
                    db.commit()
                st.success("Veículo salvo.")
                st.rerun()


def home_page(vehicle: Vehicle) -> None:
    st.title("Início")
    st.caption(f"{vehicle.brand} {vehicle.model} · {vehicle.year} · {vehicle.current_odometer:,} km".replace(",", "."))
    fuels, maint, expenses = load_records(vehicle.id)
    today = date.today()
    month_fuel = [x for x in fuels if x.date.year == today.year and x.date.month == today.month]
    month_maint = [x for x in maint if x.date.year == today.year and x.date.month == today.month]
    month_exp = [x for x in expenses if x.date.year == today.year and x.date.month == today.month]
    total = sum((Decimal(x.total_cost) for x in month_fuel), Decimal(0)) + sum((Decimal(x.cost) for x in month_maint), Decimal(0)) + sum((Decimal(x.amount) for x in month_exp), Decimal(0))
    consumptions = consumption_rows(fuels)
    avg = sum(x["consumption"] for x in consumptions[-10:]) / len(consumptions[-10:]) if consumptions else None
    distance = fuels[-1].odometer - fuels[0].odometer if len(fuels) >= 2 else 0
    cost_km = float(total) / distance if distance > 0 else None

    cols = st.columns(4)
    cols[0].metric("Gasto no mês", money(total))
    cols[1].metric("Combustível", money(sum((Decimal(x.total_cost) for x in month_fuel), Decimal(0))))
    cols[2].metric("Consumo médio", f"{avg:.2f} km/L" if avg else "—")
    cols[3].metric("Custo/km", money(cost_km) if cost_km is not None else "—")

    st.divider()
    if fuels:
        df = pd.DataFrame([{"Data": x.date, "Valor": float(x.total_cost)} for x in fuels])
        st.plotly_chart(px.line(df, x="Data", y="Valor", markers=True, title="Gastos com combustível"), use_container_width=True)
    else:
        st.info("Ainda não há abastecimentos. Registre o primeiro para começar a acompanhar seu consumo.")
    if consumptions:
        df = pd.DataFrame(consumptions)
        st.plotly_chart(px.line(df, x="date", y="consumption", markers=True, title="Consumo ao longo do tempo"), use_container_width=True)


def fuel_page(vehicle: Vehicle) -> None:
    st.title("⛽ Abastecimentos")
    with st.form("fuel_form"):
        c1, c2, c3 = st.columns(3)
        record_date = c1.date_input("Data", value=date.today())
        odometer = c2.number_input("Quilometragem", min_value=0, value=vehicle.current_odometer, step=1)
        liters = c3.number_input("Litros", min_value=0.001, value=1.0, step=0.1)
        c1, c2, c3 = st.columns(3)
        price = c1.number_input("Preço por litro", min_value=0.001, value=1.0, step=0.01)
        fuel_type = c2.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel", "Flex", "GNV"])
        station = c3.text_input("Posto (opcional)")
        notes = st.text_area("Observações")
        if st.form_submit_button("Registrar abastecimento", type="primary"):
            if not vehicle_odometer_is_valid(vehicle.id, int(odometer)):
                st.error("A quilometragem não pode ser menor que um registro existente.")
            else:
                total = Decimal(str(liters)) * Decimal(str(price))
                with SessionLocal() as db:
                    db.add(FuelRecord(vehicle_id=vehicle.id, date=record_date, odometer=int(odometer), liters=Decimal(str(liters)), price_per_liter=Decimal(str(price)), total_cost=total, fuel_type=fuel_type, station=station.strip() or None, notes=notes.strip() or None))
                    db.commit()
                with SessionLocal() as db:
                    current = db.get(Vehicle, vehicle.id)
                    if current and int(odometer) > current.current_odometer:
                        current.current_odometer = int(odometer)
                        db.commit()
                st.success(f"Abastecimento registrado: {money(total)}")
                st.rerun()

    fuels, _, _ = load_records(vehicle.id)
    if not fuels:
        st.info("Nenhum abastecimento registrado ainda.")
        return
    st.subheader("Histórico")
    st.dataframe(pd.DataFrame([{"Data": x.date.strftime("%d/%m/%Y"), "Km": x.odometer, "Litros": float(x.liters), "R$/L": money(x.price_per_liter), "Total": money(x.total_cost), "Combustível": x.fuel_type, "Posto": x.station or "—"} for x in reversed(fuels)]), use_container_width=True, hide_index=True)


def maintenance_page(vehicle: Vehicle) -> None:
    st.title("🔧 Manutenção")
    categories = ["Óleo", "Filtros", "Pneus", "Freios", "Suspensão", "Motor", "Elétrica", "Revisão", "Inspeção", "Outros"]
    with st.form("maintenance_form"):
        c1, c2, c3 = st.columns(3)
        record_date = c1.date_input("Data", value=date.today())
        odometer = c2.number_input("Quilometragem", min_value=0, value=vehicle.current_odometer, step=1)
        category = c3.selectbox("Categoria", categories)
        description = st.text_input("Descrição")
        c1, c2 = st.columns(2)
        workshop = c1.text_input("Oficina (opcional)")
        cost = c2.number_input("Custo", min_value=0.01, value=1.0, step=10.0)
        c1, c2 = st.columns(2)
        next_odo = c1.number_input("Próxima revisão em km (opcional)", min_value=0, value=0, step=1)
        next_date = c2.date_input("Próxima data (opcional)", value=None)
        notes = st.text_area("Observações")
        if st.form_submit_button("Registrar manutenção", type="primary"):
            if not description.strip():
                st.error("Informe a descrição.")
            elif not vehicle_odometer_is_valid(vehicle.id, int(odometer)):
                st.error("A quilometragem não pode regredir.")
            else:
                with SessionLocal() as db:
                    db.add(MaintenanceRecord(vehicle_id=vehicle.id, date=record_date, odometer=int(odometer), category=category, description=description.strip(), workshop=workshop.strip() or None, cost=Decimal(str(cost)), next_due_odometer=int(next_odo) if next_odo else None, next_due_date=next_date, notes=notes.strip() or None))
                    db.commit()
                with SessionLocal() as db:
                    current = db.get(Vehicle, vehicle.id)
                    if current and int(odometer) > current.current_odometer:
                        current.current_odometer = int(odometer)
                        db.commit()
                st.success("Manutenção registrada.")
                st.rerun()

    _, records, _ = load_records(vehicle.id)
    if not records:
        st.info("Nenhuma manutenção registrada ainda.")
        return
    st.dataframe(pd.DataFrame([{"Data": x.date.strftime("%d/%m/%Y"), "Km": x.odometer, "Categoria": x.category, "Descrição": x.description, "Custo": money(x.cost), "Próxima": f"{x.next_due_odometer:,} km" if x.next_due_odometer else (x.next_due_date.strftime("%d/%m/%Y") if x.next_due_date else "—")} for x in reversed(records)]), use_container_width=True, hide_index=True)


def expenses_page(vehicle: Vehicle) -> None:
    st.title("💰 Despesas")
    categories = ["Lavagem", "Estacionamento", "Pedágio", "Seguro", "Documentação", "Acessórios", "Multa", "Outros"]
    with st.form("expense_form"):
        c1, c2, c3 = st.columns(3)
        record_date = c1.date_input("Data", value=date.today())
        category = c2.selectbox("Categoria", categories)
        amount = c3.number_input("Valor", min_value=0.01, value=1.0, step=5.0)
        description = st.text_input("Descrição")
        notes = st.text_area("Observações")
        if st.form_submit_button("Registrar despesa", type="primary"):
            if not description.strip():
                st.error("Informe a descrição.")
            else:
                with SessionLocal() as db:
                    db.add(ExpenseRecord(vehicle_id=vehicle.id, date=record_date, category=category, description=description.strip(), amount=Decimal(str(amount)), notes=notes.strip() or None))
                    db.commit()
                st.success("Despesa registrada.")
                st.rerun()

    _, _, records = load_records(vehicle.id)
    if not records:
        st.info("Nenhuma despesa registrada ainda.")
        return
    st.dataframe(pd.DataFrame([{"Data": x.date.strftime("%d/%m/%Y"), "Categoria": x.category, "Descrição": x.description, "Valor": money(x.amount)} for x in reversed(records)]), use_container_width=True, hide_index=True)


def history_page(vehicle: Vehicle) -> None:
    st.title("📋 Histórico")
    fuels, maint, expenses = load_records(vehicle.id)
    items = [(x.date, "⛽ Abastecimento", f"{x.liters} L · {money(x.total_cost)}", x.id, "fuel") for x in fuels]
    items += [(x.date, "🔧 Manutenção", f"{x.description} · {money(x.cost)}", x.id, "maintenance") for x in maint]
    items += [(x.date, "💰 Despesa", f"{x.description} · {money(x.amount)}", x.id, "expense") for x in expenses]
    if not items:
        st.info("Seu histórico aparecerá aqui conforme você registrar atividades.")
        return

    for record_date, title, detail, record_id, kind in sorted(items, key=lambda item: (item[0], item[3]), reverse=True):
        left, right = st.columns([5, 1])
        left.markdown(f"**{record_date.strftime('%d/%m/%Y')} — {title}**\n\n{detail}")
        if right.button("Excluir", key=f"delete-{kind}-{record_id}"):
            confirmation_key = (kind, record_id)
            if st.session_state.get("confirm_delete") == confirmation_key:
                model = {"fuel": FuelRecord, "maintenance": MaintenanceRecord, "expense": ExpenseRecord}[kind]
                with SessionLocal() as db:
                    obj = db.get(model, record_id)
                    if obj and obj.vehicle_id == vehicle.id:
                        db.delete(obj)
                        db.commit()
                st.session_state.pop("confirm_delete", None)
                st.rerun()
            else:
                st.session_state.confirm_delete = confirmation_key
                st.warning("Clique novamente para confirmar.")
        st.divider()


def ai_page(vehicle: Vehicle) -> None:
    st.title("🤖 Registrar com IA")
    st.caption("A IA interpreta o texto ou recibo. Nada é salvo sem sua confirmação.")
    text = st.text_area("Descreva o que aconteceu", placeholder="Abasteci hoje com 42 litros de gasolina a 6,19 e o carro estava com 72.430 km.")
    upload = st.file_uploader("Ou envie uma foto de recibo", type=["jpg", "jpeg", "png", "webp"], max_upload_size=10)

    if st.button("Analisar", type="primary"):
        if not GEMINI_API_KEY:
            st.error("GEMINI_API_KEY não configurada.")
        elif not text.strip() and not upload:
            st.warning("Informe um texto ou envie um recibo.")
        else:
            prompt = (
                "Você é um extrator de registros automotivos. Retorne SOMENTE JSON válido. "
                "Nunca invente dados; use null quando desconhecido. Tipos permitidos: fuel, maintenance, expense. "
                "Campos possíveis: type, date, odometer, liters, price_per_liter, fuel_type, category, description, "
                "cost, station, workshop, confidence. Preserve exatamente os números fornecidos. "
                "Não inclua placa, e-mail ou outros dados pessoais."
            )
            if text.strip():
                prompt += "\nTexto do usuário:\n" + text.strip()
            if upload:
                prompt += "\nAnalise somente os dados visíveis no recibo."
            result = ai_request(prompt, upload.getvalue() if upload else None, upload.type if upload else "image/jpeg")
            parsed = parse_ai_json(result) if result else None
            if parsed:
                st.session_state.ai_result = parsed
                st.success("Análise concluída. Revise antes de salvar.")
            else:
                st.error("A IA não retornou um JSON válido. Tente novamente.")

    if st.session_state.get("ai_result"):
        st.subheader("Resultado para revisão")
        st.json(st.session_state.ai_result)
        st.info("O resultado acima é apenas uma sugestão. Nesta versão, ele não é gravado automaticamente no banco.")
        if st.button("Descartar resultado"):
            st.session_state.pop("ai_result", None)
            st.rerun()


def insights_page(vehicle: Vehicle) -> None:
    st.title("💡 Insights")
    fuels, maint, expenses = load_records(vehicle.id)
    if not fuels and not maint and not expenses:
        st.info("Registre alguns dados para receber insights reais.")
        return
    total_fuel = sum((Decimal(x.total_cost) for x in fuels), Decimal(0))
    total_maint = sum((Decimal(x.cost) for x in maint), Decimal(0))
    total_exp = sum((Decimal(x.amount) for x in expenses), Decimal(0))
    st.write(f"**Combustível:** {money(total_fuel)} · **Manutenção:** {money(total_maint)} · **Outras despesas:** {money(total_exp)}")
    consumptions = consumption_rows(fuels)
    if consumptions:
        avg = sum(x["consumption"] for x in consumptions) / len(consumptions)
        st.success(f"Seu consumo médio calculável está em **{avg:.2f} km/L**.")
    if len(fuels) >= 2:
        distance = fuels[-1].odometer - fuels[0].odometer
        if distance > 0:
            st.success(f"Há {distance:,} km de histórico entre os abastecimentos calculáveis.".replace(",", "."))

    if GEMINI_API_KEY and st.button("Gerar explicação com Gemini"):
        summary = f"combustível={float(total_fuel):.2f}; manutenção={float(total_maint):.2f}; outras={float(total_exp):.2f}; abastecimentos={len(fuels)}; manutenções={len(maint)}; despesas={len(expenses)}"
        explanation = ai_request("Explique de forma curta e útil estes indicadores. Não crie números novos: " + summary)
        if explanation:
            st.write(explanation)
        else:
            st.error("Não foi possível gerar a explicação agora.")


def settings_page(user: User) -> None:
    st.title("⚙️ Configurações")
    st.write(f"**Conta:** {user.email}")
    if user.plan == "trial":
        days = max(0, (user.trial_ends_at.date() - date.today()).days)
        st.info(f"Período gratuito: **{days} dias restantes**.")
    else:
        st.info("Plano atual: **Free**.")

    st.divider()
    st.subheader("Veículo")
    vehicle_form(user)

    st.divider()
    st.subheader("Feedback")
    with st.form("feedback_form"):
        rating = st.slider("Como está sua experiência?", 1, 5, 5)
        message = st.text_area("Comentários")
        if st.form_submit_button("Enviar feedback"):
            with SessionLocal() as db:
                db.add(Feedback(user_id=user.id, rating=rating, message=message.strip()))
                db.commit()
            st.success("Obrigado pelo feedback!")


def main() -> None:
    user = current_user()
    if not user:
        auth_page()
        return

    user = refresh_plan(user.id)
    with st.sidebar:
        st.markdown("# 🚗 Meu Carro")
        st.caption(user.email)
        if user.plan == "trial":
            days = max(0, (user.trial_ends_at.date() - date.today()).days)
            st.caption(f"Trial: {days} dias restantes")
        else:
            st.caption("Plano: Free")
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

    vehicle = vehicle_for(user.id)
    if not vehicle:
        st.title("Vamos começar")
        st.write("Cadastre seu veículo para usar o Meu Carro.")
        vehicle_form(user)
        return

    with st.sidebar:
        page = st.radio("Menu", ["🏠 Início", "⛽ Abastecimentos", "🔧 Manutenção", "💰 Despesas", "📋 Histórico", "🤖 Registrar com IA", "💡 Insights", "⚙️ Configurações"])

    if page == "🏠 Início":
        home_page(vehicle)
    elif page == "⛽ Abastecimentos":
        fuel_page(vehicle)
    elif page == "🔧 Manutenção":
        maintenance_page(vehicle)
    elif page == "💰 Despesas":
        expenses_page(vehicle)
    elif page == "📋 Histórico":
        history_page(vehicle)
    elif page == "🤖 Registrar com IA":
        ai_page(vehicle)
    elif page == "💡 Insights":
        insights_page(vehicle)
    else:
        settings_page(user)


if __name__ == "__main__":
    main()
