from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from streamlit_app import (
    ExpenseRecord,
    FuelRecord,
    MaintenanceRecord,
    SessionLocal,
    current_user,
    money,
    vehicle_for,
)

st.set_page_config(page_title="MOVEXA · Gráficos", page_icon="📊", layout="wide")

user = current_user()
if user is None:
    st.warning("Faça login para acessar as análises.")
    st.stop()

session = SessionLocal()
try:
    vehicle = vehicle_for(user.id)
    if vehicle is None:
        st.info("Cadastre um veículo para visualizar os gráficos.")
        st.stop()
    fuel_rows = session.query(FuelRecord).filter(FuelRecord.vehicle_id == vehicle.id).order_by(FuelRecord.date.asc()).all()
    maintenance_rows = session.query(MaintenanceRecord).filter(MaintenanceRecord.vehicle_id == vehicle.id).order_by(MaintenanceRecord.date.asc()).all()
    expense_rows = session.query(ExpenseRecord).filter(ExpenseRecord.vehicle_id == vehicle.id).order_by(ExpenseRecord.date.asc()).all()
finally:
    session.close()


def frame(rows, fields: list[str]) -> pd.DataFrame:
    return pd.DataFrame([{field: getattr(row, field, None) for field in fields} for row in rows])


fuel = frame(fuel_rows, ["date", "liters", "total_cost", "odometer", "price_per_liter"])
maintenance = frame(maintenance_rows, ["date", "cost", "category", "odometer"])
expenses = frame(expense_rows, ["date", "amount", "category"])

for df in (fuel, maintenance, expenses):
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
if not fuel.empty:
    fuel["total_cost"] = pd.to_numeric(fuel["total_cost"], errors="coerce").fillna(0)
    fuel["liters"] = pd.to_numeric(fuel["liters"], errors="coerce")
    fuel["odometer"] = pd.to_numeric(fuel["odometer"], errors="coerce")
if not maintenance.empty:
    maintenance["cost"] = pd.to_numeric(maintenance["cost"], errors="coerce").fillna(0)
    maintenance["odometer"] = pd.to_numeric(maintenance["odometer"], errors="coerce")
if not expenses.empty:
    expenses["amount"] = pd.to_numeric(expenses["amount"], errors="coerce").fillna(0)

fuel_total = float(fuel["total_cost"].sum()) if not fuel.empty else 0.0
maintenance_total = float(maintenance["cost"].sum()) if not maintenance.empty else 0.0
expenses_total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
grand_total = fuel_total + maintenance_total + expenses_total

st.title("📊 Gráficos")
st.caption(f"Análises de {getattr(vehicle, 'brand', '')} {getattr(vehicle, 'model', 'veículo')} — sem dados simulados.")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total registrado", money(grand_total))
k2.metric("Combustível / energia", money(fuel_total))
k3.metric("Manutenção", money(maintenance_total))
k4.metric("Outras despesas", money(expenses_total))


def monthly_costs() -> pd.DataFrame:
    parts = []
    if not fuel.empty:
        parts.append(fuel[["date", "total_cost"]].rename(columns={"total_cost": "value"}))
    if not maintenance.empty:
        parts.append(maintenance[["date", "cost"]].rename(columns={"cost": "value"}))
    if not expenses.empty:
        parts.append(expenses[["date", "amount"]].rename(columns={"amount": "value"}))
    if not parts:
        return pd.DataFrame(columns=["month", "value"])
    result = pd.concat(parts, ignore_index=True).dropna(subset=["date"])
    result["month"] = result["date"].dt.to_period("M").astype(str)
    return result.groupby("month", as_index=False)["value"].sum().sort_values("month")


monthly = monthly_costs()
tab_overview, tab_fuel, tab_maintenance, tab_expenses, tab_odometer = st.tabs(
    ["Visão geral", "Combustível / Energia", "Manutenção", "Despesas", "Quilometragem"]
)

with tab_overview:
    if monthly.empty:
        st.info("Ainda não há lançamentos suficientes para gerar gráficos.")
    else:
        fig = px.bar(monthly, x="month", y="value", title="Gastos por mês")
        fig.update_layout(xaxis_title="Mês", yaxis_title="Valor")
        st.plotly_chart(fig, use_container_width=True)
        cumulative = monthly.copy()
        cumulative["cumulative"] = cumulative["value"].cumsum()
        fig2 = px.line(cumulative, x="month", y="cumulative", markers=True, title="Gasto acumulado")
        fig2.update_layout(xaxis_title="Mês", yaxis_title="Valor acumulado")
        st.plotly_chart(fig2, use_container_width=True)

with tab_fuel:
    if fuel.empty:
        st.info("Nenhum abastecimento/recarga registrado.")
    else:
        valid_dates = fuel.dropna(subset=["date"]).copy()
        if valid_dates.empty:
            st.info("Não há datas válidas nos registros de abastecimento.")
        else:
            valid_dates["month"] = valid_dates["date"].dt.to_period("M").astype(str)
            monthly_fuel = valid_dates.groupby("month", as_index=False).agg(gasto=("total_cost", "sum"), quantidade=("liters", "sum"))
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.bar(monthly_fuel, x="month", y="gasto", title="Gasto mensal"), use_container_width=True)
            with c2:
                st.plotly_chart(px.bar(monthly_fuel, x="month", y="quantidade", title="Quantidade mensal"), use_container_width=True)
            valid = valid_dates.dropna(subset=["odometer", "liters"]).sort_values(["odometer", "date"]).copy()
            valid = valid[valid["liters"] > 0]
            valid["distance"] = valid["odometer"].diff()
            valid["consumption"] = valid["distance"] / valid["liters"]
            valid = valid[(valid["distance"] > 0) & (valid["consumption"] > 0)]
            if valid.empty:
                st.info("Registre abastecimentos com quilometragem crescente para calcular consumo.")
            else:
                fig = px.line(valid, x="date", y="consumption", markers=True, title="Consumo estimado")
                fig.update_layout(xaxis_title="Data", yaxis_title="km/L")
                st.plotly_chart(fig, use_container_width=True)

with tab_maintenance:
    if maintenance.empty:
        st.info("Nenhuma manutenção registrada.")
    else:
        by_category = maintenance.groupby("category", dropna=False, as_index=False)["cost"].sum()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(by_category, names="category", values="cost", title="Manutenção por categoria"), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(maintenance.dropna(subset=["date"]), x="date", y="cost", title="Gasto com manutenção"), use_container_width=True)

with tab_expenses:
    if expenses.empty:
        st.info("Nenhuma outra despesa registrada.")
    else:
        by_category = expenses.groupby("category", dropna=False, as_index=False)["amount"].sum()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(by_category, names="category", values="amount", title="Despesas por categoria"), use_container_width=True)
        with c2:
            st.plotly_chart(px.bar(expenses.dropna(subset=["date"]), x="date", y="amount", title="Evolução das despesas"), use_container_width=True)

with tab_odometer:
    odo_parts = []
    if not fuel.empty:
        odo_parts.append(fuel[["date", "odometer"]].assign(origem="Combustível"))
    if not maintenance.empty:
        odo_parts.append(maintenance[["date", "odometer"]].assign(origem="Manutenção"))
    if not odo_parts:
        st.info("Ainda não há histórico de quilometragem suficiente.")
    else:
        odo = pd.concat(odo_parts, ignore_index=True).dropna(subset=["date", "odometer"])
        odo["odometer"] = pd.to_numeric(odo["odometer"], errors="coerce")
        odo = odo.dropna(subset=["odometer"]).sort_values("date")
        if odo.empty:
            st.info("Ainda não há leituras de quilometragem válidas.")
        else:
            fig = px.line(odo, x="date", y="odometer", color="origem", markers=True, title="Evolução da quilometragem")
            fig.update_layout(xaxis_title="Data", yaxis_title="Quilometragem")
            st.plotly_chart(fig, use_container_width=True)
