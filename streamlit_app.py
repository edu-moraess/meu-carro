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
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, create_engine, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

APP_NAME = "MOVEXA"
VEHICLE_TYPES = ["Carro", "Moto", "Caminhão", "Ônibus", "Van", "Utilitário", "Máquina", "Outro"]
FUEL_TYPES = ["Gasolina", "Etanol", "Diesel", "Flex", "GNV", "Elétrico", "Híbrido", "Outro"]

st.set_page_config(page_title=APP_NAME, page_icon="🚘", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:Inter,sans-serif}.stApp{background:#0b0d10}
[data-testid="stHeader"]{background:rgba(11,13,16,.9)}[data-testid="stSidebar"]{background:#101318;border-right:1px solid #20242b}
.block-container{max-width:1420px;padding-top:2.1rem;padding-bottom:4rem}.brand{display:flex;align-items:center;gap:.75rem;margin-bottom:1.5rem}
.brand-mark{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;background:#f5c542;color:#111;font-size:21px;box-shadow:0 8px 28px rgba(245,197,66,.14)}
.brand-title{font-size:1.12rem;font-weight:800;letter-spacing:-.03em;color:#f4f5f7}.brand-sub{color:#7f8793;font-size:.7rem}
.hero{padding:1.6rem 1.8rem;border:1px solid #242932;border-radius:20px;background:linear-gradient(135deg,#151920,#0f1217);margin-bottom:1.2rem}
.eyebrow{color:#aab1bc;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.13em}.hero h1{margin:.35rem 0;color:#fff;font-size:2.15rem;line-height:1.1;letter-spacing:-.055em}.hero p{color:#8f98a6;margin:0;font-size:.92rem}
.kpi{border:1px solid #242932;background:#12161c;border-radius:16px;padding:1rem 1.1rem;min-height:108px}.kpi-label{color:#7f8793;font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700}.kpi-value{color:#f4f5f7;font-size:1.5rem;font-weight:800;letter-spacing:-.04em;margin-top:.35rem}.kpi-note{color:#69727e;font-size:.72rem;margin-top:.3rem}
.section-title{color:#f1f3f5;font-size:1.05rem;font-weight:750;letter-spacing:-.025em;margin:.2rem 0 .8rem}.muted{color:#7f8793}.status{display:inline-flex;padding:.28rem .55rem;border-radius:999px;background:#1c222b;color:#b9c0ca;font-size:.7rem;font-weight:700}.status.good{background:#15261e;color:#78d69c}
div[data-testid="stMetric"]{background:#12161c;border:1px solid #242932;padding:1rem;border-radius:16px}.stButton>button{border-radius:10px;font-weight:650;min-height:2.45rem}.stButton>button[kind="primary"]{background:#f5c542;border-color:#f5c542;color:#111}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,textarea{background:#12161c!important;border-color:#2a3039!important;border-radius:10px!important}.stTabs [aria-selected="true"]{color:#f5c542!important}[data-testid="stDataFrame"]{border:1px solid #242932;border-radius:14px;overflow:hidden}hr{border-color:#242932}
</style>""", unsafe_allow_html=True)


def secret(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value: return value
    try: return st.secrets.get(name, default)
    except Exception: return default


def db_url(url: str) -> str:
    if url.startswith("postgres://"): return "postgresql+psycopg://" + url[11:]
    if url.startswith("postgresql://"): return "postgresql+psycopg://" + url[13:]
    return url

DATABASE_URL = db_url(secret("DATABASE_URL", "sqlite:///meu_carro.db"))
GEMINI_API_KEY = secret("GEMINI_API_KEY")
GEMINI_MODEL = secret("GEMINI_MODEL", "gemini-2.5-flash")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
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
    vehicle_type: Mapped[str] = mapped_column(String(40), default="Carro", nullable=False)
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
    with engine.begin() as conn:
        cols=[r[1] for r in conn.execute(text("PRAGMA table_info(vehicles)"))] if DATABASE_URL.startswith("sqlite") else [r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='vehicles'"))]
        if "vehicle_type" not in cols:
            conn.execute(text("ALTER TABLE vehicles ADD COLUMN vehicle_type VARCHAR(40) NOT NULL DEFAULT 'Carro'"))
except SQLAlchemyError:
    st.error("Não foi possível conectar ao banco. Verifique DATABASE_URL e as credenciais."); st.stop()


def money(v:object)->str:
    try: a=Decimal(str(v))
    except (InvalidOperation,ValueError,TypeError): a=Decimal("0")
    return f"R$ {a:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def km(v:int)->str: return f"{int(v):,}".replace(",",".")+" km"
def hash_password(p:str)->str: return bcrypt.hashpw(p.encode(),bcrypt.gensalt()).decode()
def verify_password(p:str,h:str)->bool:
    try:return bcrypt.checkpw(p.encode(),h.encode())
    except (ValueError,TypeError):return False

def current_user()->Optional[User]:
    uid=st.session_state.get("user_id")
    if not isinstance(uid,int):return None
    with SessionLocal() as db:return db.get(User,uid)

def register_user(email:str,password:str)->tuple[bool,str]:
    email=email.strip().lower()
    if "@" not in email or "." not in email.rsplit("@",1)[-1]:return False,"Informe um e-mail válido."
    if len(password)<8:return False,"A senha deve ter pelo menos 8 caracteres."
    with SessionLocal() as db:
        if db.query(User).filter(User.email==email).first():return False,"Este e-mail já está cadastrado."
        code=secrets.token_hex(5).upper(); now=datetime.utcnow(); user=User(email=email,password_hash=hash_password(password),trial_started_at=now,trial_ends_at=now+timedelta(days=30),referral_code=code); db.add(user)
        try:db.commit();db.refresh(user)
        except IntegrityError:db.rollback();return False,"Não foi possível criar a conta."
        st.session_state.user_id=user.id
    return True,"Conta criada. Seu período gratuito começou."

def login_user(email:str,password:str)->tuple[bool,str]:
    with SessionLocal() as db:
        u=db.query(User).filter(User.email==email.strip().lower()).first()
        if not u or not u.is_active or not verify_password(password,u.password_hash):return False,"E-mail ou senha incorretos."
        st.session_state.user_id=u.id
    return True,"Login realizado."

def refresh_plan(uid:int)->User:
    with SessionLocal() as db:
        u=db.get(User,uid)
        if u and u.plan=="trial" and datetime.utcnow()>=u.trial_ends_at:u.plan="free";db.commit()
        return u

def vehicle_for(uid:int)->Optional[Vehicle]:
    with SessionLocal() as db:return db.query(Vehicle).filter(Vehicle.user_id==uid).order_by(Vehicle.id).first()

def max_odo(vid:int)->int:
    with SessionLocal() as db:
        vals=[]
        for m in (FuelRecord,MaintenanceRecord):
            r=db.query(m.odometer).filter(m.vehicle_id==vid).order_by(m.odometer.desc()).first()
            if r and r[0] is not None:vals.append(int(r[0]))
        return max(vals,default=0)

def records(vid:int):
    with SessionLocal() as db:
        return (db.query(FuelRecord).filter(FuelRecord.vehicle_id==vid).order_by(FuelRecord.date, FuelRecord.id).all(),db.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id==vid).order_by(MaintenanceRecord.date,MaintenanceRecord.id).all(),db.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id==vid).order_by(ExpenseRecord.date,ExpenseRecord.id).all())

def header(eyebrow,title,description=""):st.markdown(f'<div class="hero"><div class="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>',unsafe_allow_html=True)
def card(label,value,note=""):st.markdown(f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>',unsafe_allow_html=True)

def auth_page():
    a,b=st.columns([1.15,.85],gap="large")
    with a:
        st.markdown('<div style="margin-top:8vh"><div class="eyebrow">GESTÃO DE VEÍCULOS</div><h1 style="font-size:3.2rem;letter-spacing:-.07em;margin:.3rem 0">Sua frota.<br>Sem planilhas.</h1><p class="muted" style="font-size:1rem;max-width:520px">Controle abastecimentos, manutenção, despesas e indicadores de qualquer veículo em um só lugar.</p></div>',unsafe_allow_html=True)
    with b:
        st.markdown('<div class="hero" style="margin-top:5vh">',unsafe_allow_html=True);st.markdown(f'<div class="brand"><div class="brand-mark">🚘</div><div><div class="brand-title">{APP_NAME}</div><div class="brand-sub">Gestão inteligente de veículos</div></div></div>',unsafe_allow_html=True)
        t1,t2=st.tabs(["Entrar","Criar conta"])
        with t1:
            with st.form("login"):
                e=st.text_input("E-mail");p=st.text_input("Senha",type="password")
                if st.form_submit_button("Entrar",type="primary",use_container_width=True):
                    ok,msg=login_user(e,p);(st.success if ok else st.error)(msg)
                    if ok:st.rerun()
        with t2:
            with st.form("register"):
                e=st.text_input("E-mail",key="reg_e");p=st.text_input("Senha",type="password",key="reg_p");c=st.text_input("Confirmar senha",type="password")
                if st.form_submit_button("Começar grátis",type="primary",use_container_width=True):
                    if p!=c:st.error("As senhas não coincidem.")
                    else:
                        ok,msg=register_user(e,p);(st.success if ok else st.error)(msg)
                        if ok:st.rerun()
        st.caption("30 dias grátis · Sem cartão de crédito");st.markdown('</div>',unsafe_allow_html=True)

def vehicle_form(user:User):
    v=vehicle_for(user.id); current=getattr(v,"vehicle_type","Carro") if v else "Carro"
    with st.form("vehicle_form"):
        c1,c2,c3=st.columns(3);typ=c1.selectbox("Tipo de veículo",VEHICLE_TYPES,index=VEHICLE_TYPES.index(current) if current in VEHICLE_TYPES else 0);brand=c2.text_input("Marca",value=v.brand if v else "");model=c3.text_input("Modelo",value=v.model if v else "")
        c1,c2,c3=st.columns(3);year=c1.number_input("Ano",1950,date.today().year+1,v.year if v else date.today().year);fuel=c2.selectbox("Combustível / energia",FUEL_TYPES,index=FUEL_TYPES.index(v.fuel_type) if v and v.fuel_type in FUEL_TYPES else 0);odo=c3.number_input("Quilometragem atual",0,value=v.current_odometer if v else 0,step=1)
        c1,c2=st.columns(2);version=c1.text_input("Versão",value=(v.version or "") if v else "");plate=c2.text_input("Placa / identificação",value=(v.license_plate or "") if v else "")
        if st.form_submit_button("Salvar veículo",type="primary"):
            if not brand.strip() or not model.strip():st.error("Informe marca e modelo.");return
            if v and int(odo)<max_odo(v.id):st.error("A quilometragem não pode diminuir.");return
            with SessionLocal() as db:
                obj=db.get(Vehicle,v.id) if v else Vehicle(user_id=user.id);obj.brand=brand.strip();obj.model=model.strip();obj.year=int(year);obj.fuel_type=fuel;obj.current_odometer=int(odo);obj.version=version.strip() or None;obj.license_plate=plate.strip().upper() or None;db.add(obj);db.flush()
                db.execute(text("UPDATE vehicles SET vehicle_type=:t WHERE id=:id"),{"t":typ,"id":obj.id});db.commit()
            st.success("Veículo salvo.");st.rerun()

def home(v:Vehicle):
    fuels,maint,exp=records(v.id);today=date.today();mf=[x for x in fuels if x.date.year==today.year and x.date.month==today.month];mm=[x for x in maint if x.date.year==today.year and x.date.month==today.month];me=[x for x in exp if x.date.year==today.year and x.date.month==today.month];total=sum((Decimal(x.total_cost) for x in mf),Decimal())+sum((Decimal(x.cost) for x in mm),Decimal())+sum((Decimal(x.amount) for x in me),Decimal());typ=getattr(v,"vehicle_type","Carro")
    header("VISÃO GERAL",f"{v.brand} {v.model}",f"{typ} · {v.year} · {km(v.current_odometer)} · {v.fuel_type}");cs=st.columns(4)
    for col,(lab,val,note) in zip(cs,[("Gasto este mês",money(total),"todos os custos"),("Combustível",money(sum((Decimal(x.total_cost) for x in mf),Decimal())),f"{len(mf)} abastecimento(s)"),("Manutenções",money(sum((Decimal(x.cost) for x in mm),Decimal())),f"{len(mm)} serviço(s)"),("Registros",str(len(fuels)+len(maint)+len(exp)),"histórico total")]):
        with col:card(lab,val,note)
    st.write("");left,right=st.columns([1.6,1],gap="large")
    with left:
        st.markdown('<div class="section-title">Evolução dos gastos</div>',unsafe_allow_html=True);rows=[{"Data":x.date,"Categoria":"Combustível","Valor":float(x.total_cost)} for x in fuels]+[{"Data":x.date,"Categoria":"Manutenção","Valor":float(x.cost)} for x in maint]+[{"Data":x.date,"Categoria":"Despesas","Valor":float(x.amount)} for x in exp]
        if rows:
            ch=px.area(pd.DataFrame(rows).sort_values("Data"),x="Data",y="Valor",color="Categoria");ch.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=320,margin=dict(l=0,r=0,t=10,b=0),legend_title=None);st.plotly_chart(ch,use_container_width=True,config={"displayModeBar":False})
        else:st.info("Comece registrando um abastecimento, serviço ou despesa.")
    with right:
        card("Tipo de veículo",typ,"categoria atual");st.write("");card("Quilometragem",km(v.current_odometer),"odômetro atual")

def fuel_page(v:Vehicle):
    header("ENERGIA","Abastecimentos","Registre combustível ou energia e acompanhe o custo operacional.")
    with st.expander("＋ Registrar abastecimento",expanded=True):
        with st.form("fuel"):
            c1,c2,c3=st.columns(3);d=c1.date_input("Data",date.today(),max_value=date.today());o=c2.number_input("Quilometragem",0,value=v.current_odometer);lit=c3.number_input("Quantidade",.001,value=1.0,step=.1);c1,c2,c3=st.columns(3);price=c1.number_input("Preço por unidade",.001,value=1.0,step=.01);ft=c2.selectbox("Combustível / energia",FUEL_TYPES);station=c3.text_input("Posto / carregador");notes=st.text_area("Observações")
            if st.form_submit_button("Registrar",type="primary"):
                if int(o)<max_odo(v.id):st.error("A quilometragem não pode ser menor que um registro existente.");return
                with SessionLocal() as db:db.add(FuelRecord(vehicle_id=v.id,date=d,odometer=int(o),liters=Decimal(str(lit)),price_per_liter=Decimal(str(price)),total_cost=Decimal(str(lit))*Decimal(str(price)),fuel_type=ft,station=station.strip()[:120] or None,notes=notes.strip() or None));cur=db.get(Vehicle,v.id);cur.current_odometer=max(cur.current_odometer,int(o));db.commit()
                st.success("Abastecimento registrado.");st.rerun()
    fuels,_,_=records(v.id);st.dataframe(pd.DataFrame([{"Data":x.date.strftime('%d/%m/%Y'),"Km":x.odometer,"Quantidade":float(x.liters),"Preço":money(x.price_per_liter),"Total":money(x.total_cost),"Energia":x.fuel_type,"Local":x.station or "—"} for x in reversed(fuels)]),use_container_width=True,hide_index=True) if fuels else st.info("Nenhum abastecimento registrado.")

def maintenance_page(v:Vehicle):
    header("CUIDADO","Manutenção","Histórico técnico e próximos serviços do veículo.");cats=["Revisão","Óleo","Filtros","Pneus","Freios","Suspensão","Motor","Elétrica","Inspeção","Outros"]
    with st.expander("＋ Registrar manutenção",expanded=True):
        with st.form("maint"):
            c1,c2,c3=st.columns(3);d=c1.date_input("Data",date.today(),max_value=date.today());o=c2.number_input("Quilometragem",0,value=v.current_odometer);cat=c3.selectbox("Categoria",cats);desc=st.text_input("Serviço realizado");c1,c2=st.columns(2);work=c1.text_input("Oficina / prestador");cost=c2.number_input("Custo",0.0,step=10.0);nexto=c1.number_input("Próxima revisão (km)",0,value=0,step=100);notes=st.text_area("Observações")
            if st.form_submit_button("Registrar",type="primary"):
                if not desc.strip() or cost<=0:st.error("Informe serviço e custo.");return
                if int(o)<max_odo(v.id):st.error("A quilometragem não pode diminuir.");return
                with SessionLocal() as db:db.add(MaintenanceRecord(vehicle_id=v.id,date=d,odometer=int(o),category=cat,description=desc.strip()[:255],workshop=work.strip()[:120] or None,cost=Decimal(str(cost)),next_due_odometer=int(nexto) if nexto else None,notes=notes.strip() or None));cur=db.get(Vehicle,v.id);cur.current_odometer=max(cur.current_odometer,int(o));db.commit()
                st.success("Manutenção registrada.");st.rerun()
    _,m,_=records(v.id);st.dataframe(pd.DataFrame([{"Data":x.date.strftime('%d/%m/%Y'),"Km":x.odometer,"Categoria":x.category,"Serviço":x.description,"Prestador":x.workshop or "—","Custo":money(x.cost),"Próxima":km(x.next_due_odometer) if x.next_due_odometer else "—"} for x in reversed(m)]),use_container_width=True,hide_index=True) if m else st.info("Nenhuma manutenção registrada.")

def expenses_page(v:Vehicle):
    header("FINANCEIRO","Despesas","Custos administrativos e operacionais associados ao veículo.");cats=["Seguro","Impostos","Documentação","Estacionamento","Pedágio","Lavagem","Multa","Outros"]
    with st.expander("＋ Registrar despesa",expanded=True):
        with st.form("expense"):
            c1,c2=st.columns(2);d=c1.date_input("Data",date.today(),max_value=date.today());cat=c2.selectbox("Categoria",cats);desc=st.text_input("Descrição");amount=st.number_input("Valor",0.0,step=10.0);notes=st.text_area("Observações")
            if st.form_submit_button("Registrar",type="primary"):
                if not desc.strip() or amount<=0:st.error("Informe descrição e valor.");return
                with SessionLocal() as db:db.add(ExpenseRecord(vehicle_id=v.id,date=d,category=cat,description=desc.strip()[:255],amount=Decimal(str(amount)),notes=notes.strip() or None));db.commit()
                st.success("Despesa registrada.");st.rerun()
    _,_,e=records(v.id);st.dataframe(pd.DataFrame([{"Data":x.date.strftime('%d/%m/%Y'),"Categoria":x.category,"Descrição":x.description,"Valor":money(x.amount)} for x in reversed(e)]),use_container_width=True,hide_index=True) if e else st.info("Nenhuma despesa registrada.")

def history_page(v:Vehicle):
    header("HISTÓRICO","Linha do tempo","Tudo o que foi registrado para este veículo.");f,m,e=records(v.id);rows=[{"Data":x.date,"Tipo":"Abastecimento","Descrição":f"{x.liters} · {x.fuel_type}","Valor":money(x.total_cost),"Km":x.odometer,"id":x.id,"model":"fuel"} for x in f]+[{"Data":x.date,"Tipo":"Manutenção","Descrição":x.description,"Valor":money(x.cost),"Km":x.odometer,"id":x.id,"model":"maintenance"} for x in m]+[{"Data":x.date,"Tipo":"Despesa","Descrição":x.description,"Valor":money(x.amount),"Km":None,"id":x.id,"model":"expense"} for x in e]
    if not rows:st.info("Seu histórico aparecerá aqui.");return
    st.dataframe(pd.DataFrame(rows).sort_values(["Data","id"],ascending=False)[["Data","Tipo","Descrição","Valor","Km"]],use_container_width=True,hide_index=True)
    with st.expander("Excluir registro"):
        opts={f"{r['Data'].strftime('%d/%m/%Y')} · {r['Tipo']} · {r['Descrição']}":r for r in rows};sel=st.selectbox("Registro",list(opts));r=opts[sel]
        if st.button("Excluir definitivamente"):
            model={"fuel":FuelRecord,"maintenance":MaintenanceRecord,"expense":ExpenseRecord}[r["model"]]
            with SessionLocal() as db:o=db.get(model,r["id"]);db.delete(o) if o and o.vehicle_id==v.id else None;db.commit()
            st.success("Registro excluído.");st.rerun()

def ai_page(v:Vehicle):
    header("ASSISTENTE","Registrar com IA","Use uma foto de comprovante para estruturar o lançamento. Revise antes de salvar.")
    if not GEMINI_API_KEY:st.warning("Configure GEMINI_API_KEY nos Secrets do Streamlit.");return
    up=st.file_uploader("Imagem do comprovante",type=["jpg","jpeg","png","webp"])
    if up:
        if len(up.getvalue())>10*1024*1024:st.error("A imagem deve ter no máximo 10 MB.");return
        st.image(up,width=420)
        if st.button("Analisar comprovante",type="primary"):
            prompt='Analise este comprovante de veículo. Retorne somente JSON com type (fuel, maintenance ou expense), date (YYYY-MM-DD), odometer, liters, price_per_liter, fuel_type, station, category, description e cost. Use null quando ausente. Não invente valores.';parts=[{"text":prompt},{"inline_data":{"mime_type":up.type or "image/jpeg","data":base64.b64encode(up.getvalue()).decode()}}]
            try:
                r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",headers={"x-goog-api-key":GEMINI_API_KEY},json={"contents":[{"parts":parts}],"generationConfig":{"temperature":.1,"responseMimeType":"application/json"}},timeout=25);r.raise_for_status();raw=r.json()["candidates"][0]["content"]["parts"][0]["text"];st.session_state.ai_result=json.loads(raw.strip().strip("`"))
            except (requests.RequestException,KeyError,IndexError,TypeError,ValueError,json.JSONDecodeError):st.error("Não consegui interpretar o comprovante.")
    data=st.session_state.get("ai_result")
    if data:
        st.markdown('<div class="section-title">Revise antes de salvar</div>',unsafe_allow_html=True);st.json(data);a,b=st.columns(2)
        if a.button("Salvar registro",type="primary",use_container_width=True):
            typ=str(data.get("type","")).lower();d=date.fromisoformat(str(data.get("date"))) if data.get("date") else date.today();o=int(float(data.get("odometer") or v.current_odometer));
            if o<max_odo(v.id):st.error("A quilometragem retornada é menor que um registro existente.")
            else:
                with SessionLocal() as db:
                    if typ=="fuel":db.add(FuelRecord(vehicle_id=v.id,date=d,odometer=o,liters=Decimal(str(data.get("liters") or 0)),price_per_liter=Decimal(str(data.get("price_per_liter") or 0)),total_cost=Decimal(str(data.get("liters") or 0))*Decimal(str(data.get("price_per_liter") or 0)),fuel_type=str(data.get("fuel_type") or v.fuel_type)[:30],station=str(data.get("station") or "")[:120] or None))
                    elif typ=="maintenance":db.add(MaintenanceRecord(vehicle_id=v.id,date=d,odometer=o,category=str(data.get("category") or "Outros")[:50],description=str(data.get("description") or "Registro IA")[:255],cost=Decimal(str(data.get("cost") or 0))))
                    elif typ=="expense":db.add(ExpenseRecord(vehicle_id=v.id,date=d,category=str(data.get("category") or "Outros")[:50],description=str(data.get("description") or "Registro IA")[:255],amount=Decimal(str(data.get("cost") or 0))))
                    else:st.error("Tipo retornado pela IA inválido.");return
                    cur=db.get(Vehicle,v.id);cur.current_odometer=max(cur.current_odometer,o);db.commit()
                st.session_state.pop("ai_result",None);st.success("Registro salvo.");st.rerun()
        if b.button("Descartar",use_container_width=True):st.session_state.pop("ai_result",None);st.rerun()

def insights_page(v:Vehicle):
    f,m,e=records(v.id);header("INTELIGÊNCIA","Insights","Indicadores para entender o custo e o uso do seu veículo.");total=sum((Decimal(x.total_cost) for x in f),Decimal())+sum((Decimal(x.cost) for x in m),Decimal())+sum((Decimal(x.amount) for x in e),Decimal());c=st.columns(3)
    with c[0]:card("Custo acumulado",money(total),"todos os registros")
    with c[1]:card("Manutenções",str(len(m)),"serviços")
    with c[2]:card("Abastecimentos",str(len(f)),"lançamentos")
    if f:
        rows=[];prev=None
        for x in f:
            if prev and x.odometer>prev.odometer and x.liters>0:rows.append({"Data":x.date,"Consumo":round((x.odometer-prev.odometer)/float(x.liters),2)})
            prev=x
        if rows:
            st.write("");ch=px.line(pd.DataFrame(rows),x="Data",y="Consumo",markers=True);ch.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=300,yaxis_title="km/L",xaxis_title=None);st.plotly_chart(ch,use_container_width=True,config={"displayModeBar":False})

def settings_page(user:User,v:Vehicle):
    header("CONFIGURAÇÕES","Veículo e conta","Atualize os dados do veículo e suas preferências.");a,b,c=st.tabs(["Veículo","Conta","Feedback"])
    with a:vehicle_form(user)
    with b:st.markdown(f"**E-mail**\n\n{user.email}\n\n**Plano**\n\n{('Trial · '+str(max(0,(user.trial_ends_at.date()-date.today()).days))+' dias restantes') if user.plan=='trial' else 'Free'}\n\n**Código de convite**\n\n`{user.referral_code}`")
    with c:
        with st.form("feedback"):
            r=st.slider("Experiência",1,5,5);msg=st.text_area("Comentário")
            if st.form_submit_button("Enviar feedback",type="primary"):
                with SessionLocal() as db:db.add(Feedback(user_id=user.id,rating=r,message=msg.strip()));db.commit()
                st.success("Obrigado pelo feedback.")

def main():
    user=current_user()
    if not user:auth_page();return
    user=refresh_plan(user.id);v=vehicle_for(user.id)
    with st.sidebar:
        st.markdown(f'<div class="brand"><div class="brand-mark">🚘</div><div><div class="brand-title">{APP_NAME}</div><div class="brand-sub">Gestão inteligente de veículos</div></div></div>',unsafe_allow_html=True)
        if v:st.markdown(f'<div class="status good">● {getattr(v,"vehicle_type","Carro")} · {v.brand} {v.model}</div>',unsafe_allow_html=True)
        st.caption(f"{max(0,(user.trial_ends_at.date()-date.today()).days)} dias restantes" if user.plan=="trial" else "Plano Free")
        page=st.radio("Navegação",["Início","Abastecimentos","Manutenção","Despesas","Histórico","Registrar com IA","Insights","Configurações"],label_visibility="collapsed") if v else "Configurações"
        st.divider();st.caption(user.email)
        if st.button("Sair",use_container_width=True):st.session_state.clear();st.rerun()
    if not v:header("PRIMEIRO PASSO","Cadastre seu veículo","Carro, moto, caminhão, ônibus, van, utilitário, máquina ou outro.");vehicle_form(user);return
    routes={"Início":home,"Abastecimentos":fuel_page,"Manutenção":maintenance_page,"Despesas":expenses_page,"Histórico":history_page,"Registrar com IA":ai_page,"Insights":insights_page};routes.get(page,lambda x:settings_page(user,x))(v)

if __name__=="__main__":main()
