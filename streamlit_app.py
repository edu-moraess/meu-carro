from __future__ import annotations

import base64
import io
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
from PIL import Image, ImageOps
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

st.set_page_config(page_title="MOVEXA", page_icon="assets/movexa_logo.svg", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
:root { --movexa-cyan:#16d9d2; --movexa-blue:#2496e8; --movexa-yellow:#f5c542; }
.movexa-brand{display:flex;align-items:center;gap:.85rem;margin:0 0 1.1rem}.movexa-brand img{width:54px;height:54px;object-fit:contain}.movexa-brand-name{font-size:1.55rem;font-weight:750;letter-spacing:-.035em;line-height:1}.movexa-brand-subtitle{margin-top:.28rem;opacity:.65;font-size:.82rem}
.movexa-hero{padding:.25rem 0 1.05rem}.movexa-kicker{color:var(--movexa-cyan);font-size:.76rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:.35rem}.movexa-hero h1{margin:0;font-size:clamp(2rem,4vw,3rem);letter-spacing:-.055em}.movexa-hero p{margin-top:.5rem;opacity:.7;font-size:1rem}
.movexa-vehicle{padding:1.25rem 1.4rem;border:1px solid rgba(128,128,128,.18);border-radius:18px;margin:.2rem 0 1.25rem}.movexa-vehicle-label{color:var(--movexa-cyan);font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase}.movexa-vehicle-name{font-size:1.35rem;font-weight:700;margin-top:.2rem}.movexa-vehicle-meta{opacity:.68;margin-top:.3rem;font-size:.9rem}
.movexa-section{font-size:1.05rem;font-weight:700;margin:1.15rem 0 .65rem}[data-testid="stMetric"]{border-radius:16px;padding:1rem 1.05rem;border:1px solid rgba(128,128,128,.16)}.stButton>button[kind="primary"]{border-color:var(--movexa-cyan)}
.movexa-assistant{padding:1.25rem 1.35rem;border:1px solid rgba(128,128,128,.18);border-radius:18px;margin:0 0 1rem}.movexa-assistant-title{font-size:1.25rem;font-weight:750;letter-spacing:-.02em}.movexa-assistant-sub{opacity:.68;margin:.3rem 0 1rem}
.movexa-nav{margin:.15rem 0 1.4rem}.movexa-nav-label{font-size:.72rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;opacity:.55;margin-bottom:.45rem}
</style>
""", unsafe_allow_html=True)

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
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
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
    st.error("Não foi possível conectar ao banco de dados. Verifique DATABASE_URL e as credenciais do banco.")
    st.stop()

def money(value: object) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        amount = Decimal("0")
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False

def current_user() -> Optional[User]:
    uid = st.session_state.get("user_id")
    if not isinstance(uid, int):
        return None
    with SessionLocal() as db:
        return db.get(User, uid)

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
        code = secrets.token_hex(5).upper()
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

def refresh_plan(uid: int) -> User:
    with SessionLocal() as db:
        user = db.get(User, uid)
        if user and user.plan == "trial" and datetime.utcnow() >= user.trial_ends_at:
            user.plan = "free"
            db.commit()
        return user

def vehicle_for(uid: int) -> Optional[Vehicle]:
    with SessionLocal() as db:
        return db.query(Vehicle).filter(Vehicle.user_id == uid).order_by(Vehicle.id).first()

def max_odometer(vid: int) -> int:
    with SessionLocal() as db:
        vals = []
        for model in (FuelRecord, MaintenanceRecord):
            row = db.query(model.odometer).filter(model.vehicle_id == vid).order_by(model.odometer.desc()).first()
            if row and row[0] is not None:
                vals.append(int(row[0]))
        return max(vals, default=0)

def load_records(vid: int):
    with SessionLocal() as db:
        return (
            db.query(FuelRecord).filter(FuelRecord.vehicle_id == vid).order_by(FuelRecord.date, FuelRecord.id).all(),
            db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vid).order_by(MaintenanceRecord.date, MaintenanceRecord.id).all(),
            db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vid).order_by(ExpenseRecord.date, ExpenseRecord.id).all(),
        )

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
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:])
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None

def prepare_image_for_ai(image_bytes: bytes, mime_type: str) -> tuple[bytes, str]:
    """Normalize uploaded images before sending them to Gemini.

    This prevents failures caused by very large PNGs, EXIF orientation and
    transparency while preserving the information needed for receipt OCR.
    """
    with Image.open(io.BytesIO(image_bytes)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=88, optimize=True)
    return output.getvalue(), "image/jpeg"

def ai_request(prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    parts = [{"text": prompt}]
    if image_bytes:
        try:
            normalized, normalized_mime = prepare_image_for_ai(image_bytes, mime_type)
        except (OSError, ValueError, TypeError):
            return None
        parts.append({"inline_data": {"mime_type": normalized_mime, "data": base64.b64encode(normalized).decode("ascii")}})
    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": GEMINI_API_KEY},
            json={"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"}},
            timeout=30,
        )
        response.raise_for_status()
        candidates = response.json().get("candidates", [])
        if not candidates:
            return None
        return candidates[0]["content"]["parts"][0]["text"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError):
        return None

def save_ai_result(vehicle: Vehicle, data: dict) -> tuple[bool, str]:
    kind = str(data.get("type", "")).lower().strip()
    record_date = date.today()
    try:
        if data.get("date"):
            record_date = date.fromisoformat(str(data["date"]))
    except (ValueError, TypeError):
        pass
    try:
        odometer = int(float(data.get("odometer"))) if data.get("odometer") not in (None, "") else vehicle.current_odometer
    except (ValueError, TypeError):
        return False, "A quilometragem retornada não é válida."
    if odometer < max_odometer(vehicle.id):
        return False, "A quilometragem informada é menor que um registro existente. Revise antes de salvar."
    try:
        with SessionLocal() as db:
            if kind == "fuel":
                if data.get("liters") in (None, "") or data.get("price_per_liter") in (None, ""):
                    return False, "Para abastecimento, litros e preço por litro são obrigatórios."
                liters = Decimal(str(data["liters"]))
                price = Decimal(str(data["price_per_liter"]))
                if liters <= 0 or price <= 0:
                    return False, "Litros e preço por litro devem ser maiores que zero."
                obj = FuelRecord(vehicle_id=vehicle.id, date=record_date, odometer=odometer, liters=liters, price_per_liter=price, total_cost=liters * price, fuel_type=str(data.get("fuel_type") or vehicle.fuel_type)[:30], station=str(data.get("station") or "")[:120] or None)
            elif kind == "maintenance":
                desc = str(data.get("description") or "").strip()
                cost = Decimal(str(data.get("cost") or "0"))
                if not desc or cost <= 0:
                    return False, "Manutenção precisa de descrição e custo válido."
                obj = MaintenanceRecord(vehicle_id=vehicle.id, date=record_date, odometer=odometer, category=str(data.get("category") or "Outros")[:50], description=desc[:255], workshop=str(data.get("workshop") or "")[:120] or None, cost=cost)
            elif kind == "expense":
                desc = str(data.get("description") or "").strip()
                amount = Decimal(str(data.get("cost") or "0"))
                if not desc or amount <= 0:
                    return False, "Despesa precisa de descrição e valor válido."
                obj = ExpenseRecord(vehicle_id=vehicle.id, date=record_date, odometer if False else category if False else "") if False else ExpenseRecord(vehicle_id=vehicle.id, date=record_date, category=str(data.get("category") or "Outros")[:50], description=desc[:255], amount=amount)
            else:
                return False, "Tipo de registro retornado pela IA é inválido."
            db.add(obj)
            db.commit()
            if odometer > vehicle.current_odometer:
                current = db.get(Vehicle, vehicle.id)
                if current:
                    current.current_odometer = odometer
                    db.commit()
        return True, "Registro salvo com sucesso."
    except (InvalidOperation, ValueError, TypeError, SQLAlchemyError):
        return False, "Não foi possível salvar o registro. Revise os dados e tente novamente."

def auth_page() -> None:
    st.markdown('<div class="movexa-hero"><div class="movexa-kicker">Gestão inteligente de veículos</div><h1>Bem-vindo ao MOVEXA</h1><p>Centralize combustível, manutenção e despesas em um só lugar.</p></div>', unsafe_allow_html=True)
    a, b = st.tabs(["Entrar", "Criar conta"])
    with a:
        with st.form("login_form"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                ok, msg = login_user(email, password)
                (st.success if ok else st.error)(msg)
                if ok:
                    st.rerun()
    with b:
        with st.form("register_form"):
            email = st.text_input("E-mail", key="register_email")
            password = st.text_input("Senha", type="password", key="register_password")
            confirm = st.text_input("Confirmar senha", type="password")
            if st.form_submit_button("Criar conta", type="primary"):
                if password != confirm:
                    st.error("As senhas não coincidem.")
                else:
                    ok, msg = register_user(email, password)
                    (st.success if ok else st.error)(msg)
                    if ok:
                        st.rerun()

def vehicle_form(user: User) -> None:
    existing = vehicle_for(user.id)
    fuels = ["Gasolina", "Etanol", "Diesel", "Flex", "GNV", "Elétrico"]
    with st.form("vehicle_form"):
        c1, c2 = st.columns(2)
        brand = c1.text_input("Marca", value=existing.brand if existing else "")
        model = c2.text_input("Modelo", value=existing.model if existing else "")
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("Ano", min_value=1950, max_value=date.today().year + 1, value=existing.year if existing else date.today().year)
        current_fuel = existing.fuel_type if existing else "Gasolina"
        fuel = c2.selectbox("Combustível", fuels, index=fuels.index(current_fuel) if current_fuel in fuels else 0)
        odo = c3.number_input("Quilometragem atual", min_value=0, value=existing.current_odometer if existing else 0)
        version = st.text_input("Versão (opcional)", value=(existing.version or "") if existing else "")
        plate = st.text_input("Placa (opcional)", value=(existing.license_plate or "") if existing else "")
        if st.form_submit_button("Salvar veículo", type="primary"):
            if not brand.strip() or not model.strip():
                st.error("Informe marca e modelo.")
                return
            if existing and int(odo) < max_odometer(existing.id):
                st.error("A quilometragem não pode ser menor que um registro existente.")
                return
            with SessionLocal() as db:
                v = db.get(Vehicle, existing.id) if existing else Vehicle(user_id=user.id)
                v.brand, v.model, v.year, v.fuel_type = brand.strip(), model.strip(), int(year), fuel
                v.current_odometer = int(odo)
                v.version = version.strip() or None
                v.license_plate = plate.strip().upper() or None
                db.add(v)
                db.commit()
            st.success("Veículo salvo.")
            st.rerun()

def ai_capture_page(vehicle: Vehicle) -> None:
    st.markdown('<div class="movexa-hero"><div class="movexa-kicker">MOVEXA Assistente</div><h1>Conte o que aconteceu.</h1><p>Você fala. O MOVEXA organiza.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="movexa-assistant"><div class="movexa-assistant-title">O que aconteceu com seu veículo?</div><div class="movexa-assistant-sub">Digite de forma natural ou envie uma foto. Você revisa tudo antes de salvar.</div></div>', unsafe_allow_html=True)
    text = st.text_area("Descrição", value=st.session_state.get("capture_text", ""), placeholder="Ex.: Abasteci R$ 200 de gasolina, 32 litros, com 82.430 km.", height=110, label_visibility="collapsed")
    image = st.file_uploader("Enviar comprovante ou nota fiscal (opcional)", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=False)
    if image:
        if image.size > 12 * 1024 * 1024:
            st.error("A imagem é muito grande. Envie um arquivo de até 12 MB.")
            image = None
        else:
            try:
                with Image.open(image) as preview:
                    st.caption(f"Imagem pronta para análise · {preview.width}×{preview.height}px")
            except (OSError, ValueError):
                st.error("Não foi possível abrir essa imagem. Tente JPG ou PNG.")
                image = None
    if st.button("Analisar com MOVEXA", type="primary", use_container_width=True):
        if not text.strip() and not image:
            st.warning("Descreva o que aconteceu ou envie uma imagem.")
            return
        prompt = f'''Você é o assistente de registro do MOVEXA. Extraia APENAS informações presentes no texto/imagem. Nunca invente valores. Campos ausentes devem ser null. Data atual: {date.today().isoformat()}. Veículo: {vehicle.brand} {vehicle.model}; combustível padrão: {vehicle.fuel_type}. Texto: {text.strip()}
Retorne SOMENTE JSON com type (fuel, maintenance ou expense), date (YYYY-MM-DD), odometer (number|null), liters (number|null), price_per_liter (number|null), fuel_type (string|null), station (string|null), category (string|null), description (string|null), workshop (string|null), cost (number|null).'''
        with st.spinner("Analisando comprovante..." if image else "Analisando..."):
            raw = ai_request(prompt, image.getvalue() if image else None, image.type if image else "image/jpeg")
        data = parse_ai_json(raw) if raw else None
        if not data:
            st.error("Não foi possível interpretar essa informação. Confira se a foto está nítida, inteira e bem iluminada e tente novamente.")
            return
        st.session_state.ai_capture = data
    data = st.session_state.get("ai_capture")
    if isinstance(data, dict):
        st.markdown('<div class="movexa-section">Confira antes de salvar</div>', unsafe_allow_html=True)
        st.json(data)
        c1, c2 = st.columns(2)
        if c1.button("Confirmar e salvar", type="primary", use_container_width=True):
            ok, msg = save_ai_result(vehicle, data)
            if ok:
                st.session_state.pop("ai_capture", None)
                st.session_state.pop("capture_text", None)
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)
        if c2.button("Descartar", use_container_width=True):
            st.session_state.pop("ai_capture", None)
            st.session_state.pop("capture_text", None)
            st.rerun()

def home_page(vehicle: Vehicle) -> None:
    st.markdown('<div class="movexa-hero"><div class="movexa-kicker">Visão geral</div><h1>Seu veículo, sob controle.</h1><p>Conte ao MOVEXA o que aconteceu e deixe a organização por nossa conta.</p></div>', unsafe_allow_html=True)
    meta = f"{vehicle.year} · {vehicle.current_odometer:,} km · {vehicle.fuel_type}".replace(",", ".")
    st.markdown(f'<div class="movexa-vehicle"><div class="movexa-vehicle-label">Veículo ativo</div><div class="movexa-vehicle-name">{vehicle.brand} {vehicle.model}</div><div class="movexa-vehicle-meta">{meta}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="movexa-assistant"><div class="movexa-assistant-title">O que aconteceu com seu veículo?</div><div class="movexa-assistant-sub">Abasteceu, fez manutenção ou teve uma despesa? Conte em uma frase.</div></div>', unsafe_allow_html=True)
    quick = st.text_input("Entrada rápida", placeholder="Ex.: Troquei o óleo por R$ 280 aos 83.000 km.", label_visibility="collapsed")
    if st.button("Processar com MOVEXA", type="primary", use_container_width=True):
        if quick.strip():
            st.session_state.capture_text = quick
            st.session_state.page = "Assistente"
            st.rerun()
        else:
            st.warning("Conte ao MOVEXA o que aconteceu.")
    fuels, maint, expenses = load_records(vehicle.id)
    today = date.today()
    mf = [x for x in fuels if x.date.year == today.year and x.date.month == today.month]
    mm = [x for x in maint if x.date.year == today.year and x.date.month == today.month]
    me = [x for x in expenses if x.date.year == today.year and x.date.month == today.month]
    total = sum((Decimal(x.total_cost) for x in mf), Decimal()) + sum((Decimal(x.cost) for x in mm), Decimal()) + sum((Decimal(x.amount) for x in me), Decimal())
    cons = consumption_rows(fuels)
    avg = sum(x["consumption"] for x in cons[-10:]) / len(cons[-10:]) if cons else None
    c = st.columns(4)
    c[0].metric("Gasto total", money(total))
    c[1].metric("Combustível", money(sum((Decimal(x.total_cost) for x in mf), Decimal())))
    c[2].metric("Consumo médio", f"{avg:.2f} km/L" if avg else "—")
    c[3].metric("Movimentações", len(mf) + len(mm) + len(me))
    st.markdown('<div class="movexa-section">Atividade recente</div>', unsafe_allow_html=True)
    items = [(x.date, "Abastecimento", f"{x.liters} L · {money(x.total_cost)}") for x in fuels] + [(x.date, "Manutenção", f"{x.description} · {money(x.cost)}") for x in maint] + [(x.date, "Despesa", f"{x.description} · {money(x.amount)}") for x in expenses]
    if items:
        st.dataframe(pd.DataFrame([{"Data": d.strftime("%d/%m/%Y"), "Tipo": t, "Detalhe": v} for d, t, v in sorted(items, key=lambda x: x[0], reverse=True)[:5]]), use_container_width=True, hide_index=True)
    else:
        st.info("Sua atividade aparecerá aqui depois do primeiro registro.")

def manual_page(vehicle: Vehicle, page: str) -> None:
    if page == "Abastecimentos":
        st.title("Abastecimentos")
        with st.form("fuel_form"):
            c1, c2, c3 = st.columns(3)
            d = c1.date_input("Data", value=date.today(), max_value=date.today())
            o = c2.number_input("Quilometragem", min_value=0, value=vehicle.current_odometer)
            l = c3.number_input("Litros", min_value=.001, value=1.0, step=.1)
            c1, c2, c3 = st.columns(3)
            p = c1.number_input("Preço por litro", min_value=.001, value=1.0, step=.01)
            ft = c2.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel", "Flex", "GNV"])
            s = c3.text_input("Posto (opcional)")
            if st.form_submit_button("Salvar abastecimento", type="primary"):
                if int(o) < max_odometer(vehicle.id):
                    st.error("A quilometragem não pode ser menor que um registro existente.")
                else:
                    with SessionLocal() as db:
                        db.add(FuelRecord(vehicle_id=vehicle.id, date=d, odometer=int(o), liters=Decimal(str(l)), price_per_liter=Decimal(str(p)), total_cost=Decimal(str(l)) * Decimal(str(p)), fuel_type=ft, station=s.strip() or None))
                        db.commit()
                    st.success("Abastecimento salvo.")
                    st.rerun()
    elif page == "Manutenção":
        st.title("Manutenção")
        with st.form("maintenance_form"):
            d = st.date_input("Data", value=date.today(), max_value=date.today())
            o = st.number_input("Quilometragem", min_value=0, value=vehicle.current_odometer)
            cat = st.selectbox("Categoria", ["Óleo", "Pneus", "Freios", "Revisão", "Elétrica", "Outros"])
            desc = st.text_input("Descrição")
            work = st.text_input("Oficina (opcional)")
            cost = st.number_input("Custo", min_value=.01, value=1.0, step=10.)
            if st.form_submit_button("Salvar manutenção", type="primary"):
                if not desc.strip():
                    st.error("Informe a descrição.")
                elif int(o) < max_odometer(vehicle.id):
                    st.error("A quilometragem não pode ser menor que um registro existente.")
                else:
                    with SessionLocal() as db:
                        db.add(MaintenanceRecord(vehicle_id=vehicle.id, date=d, odometer=int(o), category=cat, description=desc.strip(), workshop=work.strip() or None, cost=Decimal(str(cost))))
                        db.commit()
                    st.success("Manutenção salva.")
                    st.rerun()
    elif page == "Despesas":
        st.title("Despesas")
        with st.form("expense_form"):
            d = st.date_input("Data", value=date.today(), max_value=date.today())
            cat = st.selectbox("Categoria", ["Seguro", "Imposto", "Estacionamento", "Pedágio", "Lavagem", "Outros"])
            desc = st.text_input("Descrição")
            amount = st.number_input("Valor", min_value=.01, value=1.0, step=10.)
            if st.form_submit_button("Salvar despesa", type="primary"):
                if not desc.strip():
                    st.error("Informe a descrição.")
                else:
                    with SessionLocal() as db:
                        db.add(ExpenseRecord(vehicle_id=vehicle.id, date=d, category=cat, description=desc.strip(), amount=Decimal(str(amount))))
                        db.commit()
                    st.success("Despesa salva.")
                    st.rerun()
    else:
        fuels, maint, expenses = load_records(vehicle.id)
        if page == "Histórico":
            items = [(x.date, "Abastecimento", f"{x.liters} L · {money(x.total_cost)}") for x in fuels] + [(x.date, "Manutenção", f"{x.description} · {money(x.cost)}") for x in maint] + [(x.date, "Despesa", f"{x.description} · {money(x.amount)}") for x in expenses]
            st.title("Histórico")
            if items:
                st.dataframe(pd.DataFrame([{"Data": d.strftime("%d/%m/%Y"), "Tipo": t, "Detalhe": v} for d, t, v in sorted(items, key=lambda x: x[0], reverse=True)]), use_container_width=True, hide_index=True)
            else:
                st.info("Ainda não há movimentações.")
        elif page == "Insights":
            st.title("Insights")
            total = sum((Decimal(x.total_cost) for x in fuels), Decimal()) + sum((Decimal(x.cost) for x in maint), Decimal()) + sum((Decimal(x.amount) for x in expenses), Decimal())
            st.metric("Gasto total", money(total))
            cons = consumption_rows(fuels)
            if cons:
                st.line_chart(pd.DataFrame(cons).set_index("date"))
        elif page == "Configurações":
            st.title("Configurações")
            user = current_user()
            if user:
                st.caption(user.email)
                vehicle_form(user)

def main() -> None:
    user = current_user()
    if not user:
        auth_page()
        return
    user = refresh_plan(user.id)
    if not user or not user.is_active:
        st.session_state.clear()
        st.error("Sua sessão não está mais ativa.")
        st.rerun()
    vehicle = vehicle_for(user.id)
    if not vehicle:
        st.markdown('<div class="movexa-hero"><div class="movexa-kicker">Primeiro passo</div><h1>Vamos começar.</h1><p>Cadastre seu veículo para usar o MOVEXA.</p></div>', unsafe_allow_html=True)
        vehicle_form(user)
        return
    with st.sidebar:
        st.markdown("### MOVEXA")
        st.caption(user.email)
        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    pages = ["Início", "Assistente", "Abastecimentos", "Manutenção", "Despesas", "Histórico", "Insights", "Configurações"]
    if "page" not in st.session_state or st.session_state.page not in pages:
        st.session_state.page = "Início"
    st.markdown('<div class="movexa-nav"><div class="movexa-nav-label">Navegação</div></div>', unsafe_allow_html=True)
    try:
        page = st.segmented_control("Navegação", pages, default=st.session_state.page, label_visibility="collapsed")
    except AttributeError:
        page = st.radio("Navegação", pages, index=pages.index(st.session_state.page), horizontal=True, label_visibility="collapsed")
    if page:
        st.session_state.page = page
    page = st.session_state.page
    if page == "Início":
        home_page(vehicle)
    elif page == "Assistente":
        ai_capture_page(vehicle)
    else:
        manual_page(vehicle, page)

if __name__ == "__main__":
    main()
