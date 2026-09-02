from __future__ import annotations

import base64
import json
import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

import requests
import streamlit as st
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

st.set_page_config(page_title="MOVEXA · Assistente", page_icon="assets/movexa_logo.svg", layout="wide")


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
    email: Mapped[str] = mapped_column(String(255), nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    model: Mapped[str] = mapped_column(String(80), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    current_odometer: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class FuelRecord(Base):
    __tablename__ = "fuel_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer: Mapped[int] = mapped_column(Integer, nullable=False)
    liters: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    price_per_liter: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    fuel_type: Mapped[str] = mapped_column(String(30), nullable=False)
    station: Mapped[Optional[str]] = mapped_column(String(120))


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    odometer: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    workshop: Mapped[Optional[str]] = mapped_column(String(120))
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    next_due_odometer: Mapped[Optional[int]] = mapped_column(Integer)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)


class ExpenseRecord(Base):
    __tablename__ = "expense_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)



def money(value: object) -> str:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        amount = Decimal("0")
    return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ai_request(prompt: str, image_bytes: Optional[bytes] = None, mime_type: str = "image/jpeg") -> Optional[dict]:
    if not GEMINI_API_KEY:
        return None
    parts = [{"text": prompt}]
    if image_bytes:
        parts.append({"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    try:
        response = requests.post(url, headers={"x-goog-api-key": GEMINI_API_KEY}, json=payload, timeout=25)
        response.raise_for_status()
        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
        return None


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


def save_record(vehicle: Vehicle, data: dict) -> tuple[bool, str]:
    kind = str(data.get("type", "")).strip().lower()
    try:
        record_date = date.fromisoformat(str(data.get("date"))) if data.get("date") else date.today()
        odometer = int(float(data.get("odometer", vehicle.current_odometer)))
    except (ValueError, TypeError):
        return False, "Data ou quilometragem inválida."
    if odometer < max_odometer(vehicle.id):
        return False, "A quilometragem é menor que um registro existente. Revise antes de salvar."

    with SessionLocal() as db:
        if kind == "fuel":
            try:
                liters = Decimal(str(data["liters"]))
                price = Decimal(str(data["price_per_liter"]))
            except (KeyError, InvalidOperation, ValueError):
                return False, "Para abastecimento, informe litros e preço por litro."
            if liters <= 0 or price <= 0:
                return False, "Litros e preço por litro devem ser maiores que zero."
            obj = FuelRecord(
                vehicle_id=vehicle.id,
                date=record_date,
                odometer=odometer,
                liters=liters,
                price_per_liter=price,
                total_cost=liters * price,
                fuel_type=str(data.get("fuel_type") or vehicle.fuel_type)[:30],
                station=str(data.get("station") or "")[:120] or None,
            )
        elif kind == "maintenance":
            description = str(data.get("description") or "").strip()
            try:
                cost = Decimal(str(data.get("cost")))
            except (InvalidOperation, ValueError, TypeError):
                cost = Decimal("0")
            if not description or cost <= 0:
                return False, "Manutenção precisa de descrição e custo válido."
            obj = MaintenanceRecord(
                vehicle_id=vehicle.id, date=record_date, odometer=odometer,
                category=str(data.get("category") or "Outros")[:50],
                description=description[:255], workshop=str(data.get("workshop") or "")[:120] or None,
                cost=cost,
            )
        elif kind == "expense":
            description = str(data.get("description") or "").strip()
            try:
                amount = Decimal(str(data.get("cost")))
            except (InvalidOperation, ValueError, TypeError):
                amount = Decimal("0")
            if not description or amount <= 0:
                return False, "Despesa precisa de descrição e valor válido."
            obj = ExpenseRecord(
                vehicle_id=vehicle.id, date=record_date, category=str(data.get("category") or "Outros")[:50],
                description=description[:255], amount=amount,
            )
        else:
            return False, "O MOVEXA não conseguiu identificar o tipo de evento."

        db.add(obj)
        db.commit()
        if odometer > vehicle.current_odometer:
            current = db.get(Vehicle, vehicle.id)
            if current:
                current.current_odometer = odometer
                db.commit()
    return True, "Registro salvo no histórico do veículo."


user_id = st.session_state.get("user_id")
if not isinstance(user_id, int):
    st.warning("Entre na sua conta pelo MOVEXA para usar o assistente.")
    st.stop()

vehicle = vehicle_for(user_id)
if vehicle is None:
    st.info("Cadastre seu veículo primeiro para começar.")
    st.stop()

st.markdown("## MOVEXA Assistente")
st.caption(f"{vehicle.brand} {vehicle.model} · {vehicle.year} · {vehicle.current_odometer:,} km".replace(",", "."))
st.markdown("### O que aconteceu com seu veículo?")
st.caption("Conte em linguagem natural. Você não precisa preencher um formulário.")

prompt = st.text_area(
    "Descrição do evento",
    placeholder="Ex.: Abasteci R$ 200 de gasolina, 32 litros, hoje, com 82.430 km.",
    height=120,
    label_visibility="collapsed",
)
upload = st.file_uploader("Ou envie uma nota, recibo ou comprovante", type=["jpg", "jpeg", "png", "webp", "pdf"])

if st.button("Interpretar com IA", type="primary", use_container_width=True):
    if not prompt.strip() and upload is None:
        st.warning("Descreva o que aconteceu ou envie um arquivo.")
    else:
        system_prompt = f"""
Você é o assistente de registros do MOVEXA. Analise exclusivamente os dados fornecidos pelo usuário.
Não invente valores ausentes. Se algo não estiver presente, use null.
Data de hoje: {date.today().isoformat()}.
Veículo: {vehicle.brand} {vehicle.model}, combustível padrão {vehicle.fuel_type}.
Retorne SOMENTE JSON com estas chaves:
type (fuel|maintenance|expense|null), date (YYYY-MM-DD|null), odometer (integer|null),
liters (number|null), price_per_liter (number|null), fuel_type (string|null), station (string|null),
category (string|null), description (string|null), workshop (string|null), cost (number|null).
Para fuel, se total e litros forem informados mas preço/litro não, calcule price_per_liter.
Para maintenance e expense, cost é o valor total.
"""
        image_bytes = upload.getvalue() if upload and upload.type.startswith("image/") else None
        if upload and upload.type == "application/pdf":
            st.error("Nesta primeira versão, envie imagens de notas/recibos. PDF será adicionado depois.")
        else:
            result = ai_request(system_prompt + "\nEntrada do usuário:\n" + prompt, image_bytes, upload.type if upload else "image/jpeg")
            if result is None:
                st.error("Não foi possível interpretar a entrada. Verifique a chave GEMINI_API_KEY e tente novamente.")
            else:
                st.session_state["movexa_ai_result"] = result

result = st.session_state.get("movexa_ai_result")
if isinstance(result, dict):
    st.markdown("### Confira antes de salvar")
    st.json(result)
    confirm = st.checkbox("Confirmo que os dados acima estão corretos.")
    c1, c2 = st.columns(2)
    if c1.button("Salvar no histórico", type="primary", disabled=not confirm, use_container_width=True):
        ok, message = save_record(vehicle, result)
        (st.success if ok else st.error)(message)
        if ok:
            st.session_state.pop("movexa_ai_result", None)
            st.rerun()
    if c2.button("Descartar", use_container_width=True):
        st.session_state.pop("movexa_ai_result", None)
        st.rerun()
