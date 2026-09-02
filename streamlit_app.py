from __future__ import annotations

import base64
import hashlib
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
from PIL import Image
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

st.set_page_config(page_title="Meu Carro", page_icon="🚗", layout="wide", initial_sidebar_state="expanded")

DATABASE_URL = os.getenv("DATABASE_URL") or st.secrets.get("DATABASE_URL", "sqlite:///meu_carro.db")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or st.secrets.get("GEMINI_MODEL", "gemini-2.5-flash")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trial_started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    trial_ends_at: Mapped[datetime] = mapped_column(DateTime)
    plan: Mapped[str] = mapped_column(String(20), default="trial")
    is_active: Mapped[bool] = mapped_column(default=True)
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    vehicles: Mapped[list["Vehicle"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    brand: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(80))
    year: Mapped[int] = mapped_column(Integer)
    version: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    fuel_type: Mapped[str] = mapped_column(String(30), default="Gasolina")
    current_odometer: Mapped[int] = mapped_column(Integer, default=0)
    license_plate: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="vehicles")

class FuelRecord(Base):
    __tablename__ = "fuel_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    odometer: Mapped[int] = mapped_column(Integer)
    liters: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    price_per_liter: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    total_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fuel_type: Mapped[str] = mapped_column(String(30))
    station: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    odometer: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(255))
    workshop: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    next_due_odometer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    next_due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ExpenseRecord(Base):
    __tablename__ = "expense_records"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date)
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

st.markdown("""
<style>
[data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,.15); }
.metric-card { padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.18); border-radius: 14px; background: rgba(128,128,128,.05); }
.small-muted { color: #777; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)


def money(v) -> str:
    try:
        return f"R$ {Decimal(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def current_user() -> Optional[User]:
    uid = st.session_state.get("user_id")
    if not uid:
        return None
    with SessionLocal() as db:
        return db.get(User, uid)


def register(email: str, password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    if "@" not in email or len(password) < 8:
        return False, "Use um e-mail válido e uma senha com pelo menos 8 caracteres."
    with SessionLocal() as db:
        if db.query(User).filter_by(email=email).first():
            return False, "Este e-mail já está cadastrado."
        now = datetime.utcnow()
        user = User(email=email, password_hash=hash_password(password), trial_started_at=now,
                    trial_ends_at=now + timedelta(days=30), plan="trial",
                    referral_code=secrets.token_urlsafe(6).replace("-", "").replace("_", "").upper())
        db.add(user); db.commit(); db.refresh(user)
        st.session_state.user_id = user.id
    return True, "Conta criada. Seu período gratuito de 30 dias começou."


def login(email: str, password: str) -> tuple[bool, str]:
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=email.strip().lower()).first()
        if not user or not user.is_active or not verify_password(password, user.password_hash):
            return False, "E-mail ou senha incorretos."
        st.session_state.user_id = user.id
    return True, "Login realizado."


def ensure_plan(user: User) -> None:
    if user.plan == "trial" and datetime.utcnow() >= user.trial_ends_at:
        with SessionLocal() as db:
            u = db.get(User, user.id)
            if u:
                u.plan = "free"; db.commit()


def vehicle_for(user_id: int) -> Optional[Vehicle]:
    with SessionLocal() as db:
        return db.query(Vehicle).filter_by(user_id=user_id).order_by(Vehicle.id).first()


def parse_decimal(s: str) -> Optional[Decimal]:
    try:
        return Decimal(str(s).replace(".", "").replace(",", ".")) if "," in str(s) else Decimal(str(s))
    except (InvalidOperation, ValueError):
        return None


def valid_odometer(vehicle_id: int, odo: int, ignore_id: Optional[int] = None) -> bool:
    with SessionLocal() as db:
        q = db.query(FuelRecord.odometer).filter(FuelRecord.vehicle_id == vehicle_id)
        if ignore_id: q = q.filter(FuelRecord.id != ignore_id)
        vals = [r[0] for r in q.all()]
        q2 = db.query(MaintenanceRecord.odometer).filter(MaintenanceRecord.vehicle_id == vehicle_id)
        if ignore_id: q2 = q2.filter(MaintenanceRecord.id != ignore_id)
        vals += [r[0] for r in q2.all()]
    return not vals or odo >= max(vals)


def dashboard_data(vehicle_id: int):
    with SessionLocal() as db:
        fuels = db.query(FuelRecord).filter_by(vehicle_id=vehicle_id).order_by(FuelRecord.date, FuelRecord.id).all()
        maint = db.query(MaintenanceRecord).filter_by(vehicle_id=vehicle_id).all()
        exp = db.query(ExpenseRecord).filter_by(vehicle_id=vehicle_id).all()
    return fuels, maint, exp


def consumption_rows(fuels):
    rows = []
    prev = None
    for f in fuels:
        if prev and f.odometer > prev.odometer and f.liters > 0:
            rows.append({"date": f.date, "consumption": round((f.odometer - prev.odometer) / float(f.liters), 2)})
        prev = f
    return rows


def ai_request(prompt: str, image_bytes: Optional[bytes] = None) -> Optional[str]:
    if not GEMINI_API_KEY:
        return None
    parts = [{"text": prompt}]
    if image_bytes:
        mime = "image/jpeg"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(image_bytes).decode()}})
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1}}
    try:
        r = requests.post(url, json=payload, timeout=25)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def login_page():
    st.markdown("# 🚗 Meu Carro")
    st.caption("Controle combustível, manutenção e despesas do seu veículo.")
    tab1, tab2 = st.tabs(["Entrar", "Criar conta"])
    with tab1:
        with st.form("login"):
            email = st.text_input("E-mail")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                ok, msg = login(email, password)
                (st.success if ok else st.error)(msg)
                if ok: st.rerun()
    with tab2:
        with st.form("register"):
            email = st.text_input("E-mail", key="reg_email")
            password = st.text_input("Senha", type="password", key="reg_pass")
            confirm = st.text_input("Confirmar senha", type="password")
            if st.form_submit_button("Criar conta", type="primary"):
                if password != confirm: st.error("As senhas não coincidem.")
                else:
                    ok, msg = register(email, password)
                    (st.success if ok else st.error)(msg)
                    if ok: st.rerun()


def vehicle_form(user: User):
    st.subheader("Seu veículo")
    existing = vehicle_for(user.id)
    with st.form("vehicle"):
        c1, c2 = st.columns(2)
        brand = c1.text_input("Marca", value=existing.brand if existing else "")
        model = c2.text_input("Modelo", value=existing.model if existing else "")
        c1, c2, c3 = st.columns(3)
        year = c1.number_input("Ano", 1950, 2100, existing.year if existing else date.today().year)
        fuel = c2.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel", "Flex", "GNV", "Elétrico"], index=["Gasolina","Etanol","Diesel","Flex","GNV","Elétrico"].index(existing.fuel_type) if existing and existing.fuel_type in ["Gasolina","Etanol","Diesel","Flex","GNV","Elétrico"] else 0)
        odo = c3.number_input("Quilometragem atual", min_value=0, value=existing.current_odometer if existing else 0, step=1)
        version = st.text_input("Versão (opcional)", value=existing.version or "" if existing else "")
        plate = st.text_input("Placa (opcional)", value=existing.license_plate or "" if existing else "")
        if st.form_submit_button("Salvar veículo", type="primary"):
            if not brand.strip() or not model.strip(): st.error("Informe marca e modelo.")
            else:
                with SessionLocal() as db:
                    v = db.get(Vehicle, existing.id) if existing else Vehicle(user_id=user.id)
                    v.brand, v.model, v.year, v.fuel_type, v.current_odometer = brand.strip(), model.strip(), int(year), fuel, int(odo)
                    v.version, v.license_plate = version.strip() or None, plate.strip().upper() or None
                    db.add(v); db.commit()
                st.success("Veículo salvo."); st.rerun()


def home(user: User, vehicle: Vehicle):
    st.title("Olá 👋")
    st.caption(f"{vehicle.brand} {vehicle.model} · {vehicle.year} · {vehicle.current_odometer:,} km".replace(",", "."))
    fuels, maint, expenses = dashboard_data(vehicle.id)
    now = date.today(); month = [x for x in fuels if x.date.year == now.year and x.date.month == now.month]
    mnt = [x for x in maint if x.date.year == now.year and x.date.month == now.month]
    ex = [x for x in expenses if x.date.year == now.year and x.date.month == now.month]
    total = sum((Decimal(x.total_cost) for x in month), Decimal(0)) + sum((Decimal(x.cost) for x in mnt), Decimal(0)) + sum((Decimal(x.amount) for x in ex), Decimal(0))
    valid_cons = consumption_rows(fuels)
    avg = sum(x["consumption"] for x in valid_cons[-10:]) / len(valid_cons[-10:]) if valid_cons else None
    distance = (fuels[-1].odometer - fuels[0].odometer) if len(fuels) > 1 else 0
    cost_km = (float(total) / distance) if distance > 0 else None
    cols = st.columns(4)
    cols[0].metric("Gasto no mês", money(total)); cols[1].metric("Combustível", money(sum((Decimal(x.total_cost) for x in month), Decimal(0))))
    cols[2].metric("Consumo médio", f"{avg:.2f} km/L" if avg else "—"); cols[3].metric("Custo/km", money(cost_km) if cost_km else "—")
    st.divider()
    if fuels:
        df = pd.DataFrame([{"Data": f.date, "Valor": float(f.total_cost), "Categoria": "Combustível"} for f in fuels])
        st.plotly_chart(px.line(df, x="Data", y="Valor", markers=True, title="Gastos com combustível"), use_container_width=True)
    else:
        st.info("Ainda não há abastecimentos. Registre o primeiro para começar a acompanhar seu consumo.")
    if valid_cons:
        cdf = pd.DataFrame(valid_cons)
        st.plotly_chart(px.line(cdf, x="date", y="consumption", markers=True, title="Consumo ao longo do tempo"), use_container_width=True)


def fuel_page(user, vehicle):
    st.title("⛽ Abastecimentos")
    with st.form("fuel_add"):
        c1, c2, c3 = st.columns(3); d = c1.date_input("Data", value=date.today()); odo = c2.number_input("Quilometragem", 0, value=vehicle.current_odometer); liters = c3.number_input("Litros", 0.001, step=0.1)
        c1, c2, c3 = st.columns(3); price = c1.number_input("Preço por litro", 0.001, step=0.01); ftype = c2.selectbox("Combustível", ["Gasolina", "Etanol", "Diesel", "Flex", "GNV"]); station = c3.text_input("Posto (opcional)")
        notes = st.text_area("Observações")
        if st.form_submit_button("Registrar abastecimento", type="primary"):
            if not valid_odometer(vehicle.id, int(odo)): st.error("A quilometragem não pode ser menor que um registro existente.")
            else:
                total = Decimal(str(liters)) * Decimal(str(price))
                with SessionLocal() as db:
                    db.add(FuelRecord(vehicle_id=vehicle.id, date=d, odometer=int(odo), liters=Decimal(str(liters)), price_per_liter=Decimal(str(price)), total_cost=total, fuel_type=ftype, station=station.strip() or None, notes=notes.strip() or None))
                    v = db.get(Vehicle, vehicle.id); v.current_odometer = max(v.current_odometer, int(odo)); db.commit()
                st.success(f"Abastecimento registrado: {money(total)}"); st.rerun()
    fuels, _, _ = dashboard_data(vehicle.id)
    if fuels:
        st.subheader("Histórico")
        st.dataframe(pd.DataFrame([{"Data": f.date.strftime("%d/%m/%Y"), "Km": f.odometer, "Litros": float(f.liters), "R$/L": money(f.price_per_liter), "Total": money(f.total_cost), "Combustível": f.fuel_type, "Posto": f.station or "—"} for f in reversed(fuels)]), use_container_width=True, hide_index=True)
    else: st.info("Nenhum abastecimento registrado ainda.")


def maintenance_page(user, vehicle):
    st.title("🔧 Manutenção")
    cats = ["Óleo", "Filtros", "Pneus", "Freios", "Suspensão", "Motor", "Elétrica", "Revisão", "Inspeção", "Outros"]
    with st.form("maint_add"):
        c1, c2, c3 = st.columns(3); d = c1.date_input("Data", date.today()); odo = c2.number_input("Quilometragem", 0, value=vehicle.current_odometer); cat = c3.selectbox("Categoria", cats)
        desc = st.text_input("Descrição"); c1, c2 = st.columns(2); workshop = c1.text_input("Oficina (opcional)"); cost = c2.number_input("Custo", 0.01, step=10.0)
        c1, c2 = st.columns(2); next_odo = c1.number_input("Próxima revisão em km (opcional)", 0, value=0); next_date = c2.date_input("Próxima data", value=None)
        notes = st.text_area("Observações")
        if st.form_submit_button("Registrar manutenção", type="primary"):
            if not desc.strip(): st.error("Informe a descrição.")
            elif not valid_odometer(vehicle.id, int(odo)): st.error("A quilometragem não pode regredir.")
            else:
                with SessionLocal() as db:
                    db.add(MaintenanceRecord(vehicle_id=vehicle.id, date=d, odometer=int(odo), category=cat, description=desc.strip(), workshop=workshop.strip() or None, cost=Decimal(str(cost)), next_due_odometer=int(next_odo) if next_odo else None, next_due_date=next_date, notes=notes.strip() or None)); db.commit()
                st.success("Manutenção registrada."); st.rerun()
    _, records, _ = dashboard_data(vehicle.id)
    if records: st.dataframe(pd.DataFrame([{"Data": r.date.strftime("%d/%m/%Y"), "Km": r.odometer, "Categoria": r.category, "Descrição": r.description, "Custo": money(r.cost), "Próxima": f"{r.next_due_odometer:,} km" if r.next_due_odometer else (r.next_due_date.strftime("%d/%m/%Y") if r.next_due_date else "—")} for r in sorted(records, key=lambda x:x.date, reverse=True)]), use_container_width=True, hide_index=True)
    else: st.info("Nenhuma manutenção registrada ainda.")


def expenses_page(user, vehicle):
    st.title("💰 Despesas")
    cats = ["Lavagem", "Estacionamento", "Pedágio", "Seguro", "Documentação", "Acessórios", "Multa", "Outros"]
    with st.form("expense_add"):
        c1, c2, c3 = st.columns(3); d = c1.date_input("Data", date.today()); cat = c2.selectbox("Categoria", cats); amount = c3.number_input("Valor", 0.01, step=5.0)
        desc = st.text_input("Descrição"); notes = st.text_area("Observações")
        if st.form_submit_button("Registrar despesa", type="primary"):
            if not desc.strip(): st.error("Informe a descrição.")
            else:
                with SessionLocal() as db: db.add(ExpenseRecord(vehicle_id=vehicle.id, date=d, category=cat, description=desc.strip(), amount=Decimal(str(amount)), notes=notes.strip() or None)); db.commit()
                st.success("Despesa registrada."); st.rerun()
    _, _, records = dashboard_data(vehicle.id)
    if records: st.dataframe(pd.DataFrame([{"Data": r.date.strftime("%d/%m/%Y"), "Categoria": r.category, "Descrição": r.description, "Valor": money(r.amount)} for r in sorted(records, key=lambda x:x.date, reverse=True)]), use_container_width=True, hide_index=True)
    else: st.info("Nenhuma despesa registrada ainda.")


def history_page(vehicle):
    st.title("📋 Histórico")
    fuels, maint, exp = dashboard_data(vehicle.id); items = []
    items += [(f.date, "⛽ Abastecimento", f"{f.liters} L · {money(f.total_cost)}", f.id, "fuel") for f in fuels]
    items += [(m.date, "🔧 Manutenção", f"{m.description} · {money(m.cost)}", m.id, "maintenance") for m in maint]
    items += [(e.date, "💰 Despesa", f"{e.description} · {money(e.amount)}", e.id, "expense") for e in exp]
    if not items: st.info("Seu histórico aparecerá aqui conforme você registrar atividades."); return
    for d, title, detail, rid, kind in sorted(items, reverse=True):
        c1, c2 = st.columns([5,1]); c1.markdown(f"**{d.strftime('%d/%m/%Y')} — {title}**  \n{detail}")
        if c2.button("Excluir", key=f"del-{kind}-{rid}"):
            if st.session_state.get("confirm_delete") == (kind, rid):
                cls = {"fuel": FuelRecord, "maintenance": MaintenanceRecord, "expense": ExpenseRecord}[kind]
                with SessionLocal() as db: obj = db.get(cls, rid); db.delete(obj); db.commit()
                st.session_state.pop("confirm_delete", None); st.rerun()
            else: st.session_state.confirm_delete = (kind, rid); st.warning("Clique novamente para confirmar.")
        st.divider()


def ai_page(vehicle):
    st.title("🤖 Registrar com IA")
    st.caption("A IA interpreta seu texto e você confirma antes de qualquer gravação.")
    text = st.text_area("Descreva o que aconteceu", placeholder="Abasteci hoje com 42 litros de gasolina a 6,19 e o carro estava com 72.430 km.")
    image = st.file_uploader("Ou envie uma foto de recibo", type=["jpg", "jpeg", "png", "webp"])
    if st.button("Analisar", type="primary"):
        if not GEMINI_API_KEY: st.error("GEMINI_API_KEY não configurada. A funcionalidade manual continua disponível."); return
        prompt = "Você é um extrator de registros automotivos. Retorne SOMENTE JSON válido. Nunca invente valores; use null quando desconhecido. Tipos permitidos: fuel, maintenance, expense. Preserve números fornecidos. Para texto, extraia data, odometer, liters, price_per_liter, fuel_type, category, description, cost, station, workshop, confidence."
        if text.strip(): prompt += "\nTexto do usuário:\n" + text.strip()
        if image: prompt += "\nAnalise o recibo e extraia somente dados visíveis."
        result = ai_request(prompt, image.getvalue() if image else None)
        if result: st.session_state.ai_result = result; st.success("Análise concluída. Revise antes de salvar.")
        else: st.error("Não foi possível consultar a IA agora.")
    if st.session_state.get("ai_result"):
        st.subheader("Resultado para revisão")
        st.code(st.session_state.ai_result, language="json")
        st.info("Nesta versão, o resultado da IA é apenas uma sugestão. O salvamento automático não é permitido.")


def insights_page(vehicle):
    st.title("💡 Insights")
    fuels, maint, exp = dashboard_data(vehicle.id)
    if not fuels and not maint and not exp: st.info("Registre alguns dados para receber insights reais."); return
    total_fuel = sum((Decimal(f.total_cost) for f in fuels), Decimal(0)); total_maint = sum((Decimal(m.cost) for m in maint), Decimal(0)); total_exp = sum((Decimal(e.amount) for e in exp), Decimal(0))
    st.write(f"**Combustível:** {money(total_fuel)} · **Manutenção:** {money(total_maint)} · **Outras despesas:** {money(total_exp)}")
    cons = consumption_rows(fuels)
    if cons:
        avg = sum(x["consumption"] for x in cons) / len(cons); st.success(f"Seu consumo médio calculável está em **{avg:.2f} km/L**.")
    if len(fuels) >= 2:
        km = fuels[-1].odometer - fuels[0].odometer
        if km > 0: st.success(f"Há {km:,} km de histórico entre os abastecimentos mais antigo e mais recente.".replace(",", "."))
    if GEMINI_API_KEY and st.button("Gerar explicação com Gemini"):
        summary = f"Combustível={float(total_fuel):.2f}; manutenção={float(total_maint):.2f}; outras={float(total_exp):.2f}; abastecimentos={len(fuels)}; manutenções={len(maint)}; despesas={len(exp)}"
        result = ai_request("Explique de forma curta e útil estes indicadores de um veículo, sem criar números novos: " + summary)
        if result: st.write(result)


def settings_page(user, vehicle):
    st.title("⚙️ Configurações")
    st.write(f"**Conta:** {user.email}")
    if user.plan == "trial":
        days = max(0, (user.trial_ends_at.date() - date.today()).days); st.info(f"Período gratuito: **{days} dias restantes**.")
    else: st.info("Plano atual: **Free**.")
    st.divider(); vehicle_form(user)
    st.divider(); st.subheader("Feedback")
    with st.form("feedback"):
        rating = st.slider("Como está sua experiência?", 1, 5, 5); msg = st.text_area("Comentários")
        if st.form_submit_button("Enviar feedback"):
            with SessionLocal() as db: db.add(Feedback(user_id=user.id, rating=rating, message=msg.strip())); db.commit()
            st.success("Obrigado pelo feedback!")


def main():
    user = current_user()
    if not user:
        login_page(); return
    ensure_plan(user); user = current_user()
    with st.sidebar:
        st.markdown("# 🚗 Meu Carro")
        st.caption(user.email)
        if st.button("Sair"): st.session_state.clear(); st.rerun()
    vehicle = vehicle_for(user.id)
    if not vehicle:
        st.title("Vamos começar")
        st.write("Cadastre seu veículo para usar o Meu Carro.")
        vehicle_form(user); return
    with st.sidebar:
        page = st.radio("Menu", ["🏠 Início", "⛽ Abastecimentos", "🔧 Manutenção", "💰 Despesas", "📋 Histórico", "🤖 Registrar com IA", "💡 Insights", "⚙️ Configurações"])
    if page == "🏠 Início": home(user, vehicle)
    elif page == "⛽ Abastecimentos": fuel_page(user, vehicle)
    elif page == "🔧 Manutenção": maintenance_page(user, vehicle)
    elif page == "💰 Despesas": expenses_page(user, vehicle)
    elif page == "📋 Histórico": history_page(vehicle)
    elif page == "🤖 Registrar com IA": ai_page(vehicle)
    elif page == "💡 Insights": insights_page(vehicle)
    else: settings_page(user, vehicle)

if __name__ == "__main__":
    main()
