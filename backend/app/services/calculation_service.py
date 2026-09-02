import datetime
from typing import List, Optional, Tuple
from backend.app.models.models import FuelRecord, MaintenanceRecord, ExpenseRecord, Vehicle
from backend.app.schemas.schemas import (
    DashboardResponse,
    RecentActivity,
    CategoryExpenseItem,
    MonthlyExpenseItem,
    ConsumptionPoint
)

class CalculationService:

    @staticmethod
    def validate_odometer(current_max_odo: int, new_odo: int) -> Tuple[bool, Optional[str]]:
        """
        Regra 55: O odômetro nunca pode diminuir sem aviso.
        Se o usuário tentar registrar uma quilometragem menor que a anterior, alertar.
        """
        if new_odo < current_max_odo:
            return False, f"A quilometragem informada ({new_odo} km) é menor que o último registro do veículo ({current_max_odo} km). Confirme a correção se necessário."
        return True, None

    @staticmethod
    def calculate_fuel_consumption(
        previous_fuel: Optional[FuelRecord],
        current_odometer: int,
        liters: float
    ) -> Optional[float]:
        """
        Regra 16: Nunca inventar consumo.
        Só calcular com pelo menos 2 abastecimentos consecutivos válidos.
        consumo = distância / litros
        """
        if previous_fuel is None or liters <= 0:
            return None
        distance = current_odometer - previous_fuel.odometer
        if distance > 0:
            return round(distance / liters, 2)
        return None

    @staticmethod
    def calculate_dashboard(
        vehicle: Vehicle,
        fuels: List[FuelRecord],
        maintenances: List[MaintenanceRecord],
        expenses: List[ExpenseRecord]
    ) -> DashboardResponse:
        now = datetime.datetime.now(datetime.timezone.utc)
        current_year_month = now.strftime("%Y-%m")
        current_year = now.strftime("%Y")

        # 1. Gastos do mês atual
        month_fuel = sum(f.total_cost for f in fuels if f.date.startswith(current_year_month))
        month_maint = sum(m.cost for m in maintenances if m.date.startswith(current_year_month))
        month_other = sum(e.amount for e in expenses if e.date.startswith(current_year_month))
        monthly_total = round(month_fuel + month_maint + month_other, 2)

        # 2. Gastos do ano atual
        yearly_fuel = sum(f.total_cost for f in fuels if f.date.startswith(current_year))
        yearly_maint = sum(m.cost for m in maintenances if m.date.startswith(current_year))
        yearly_other = sum(e.amount for e in expenses if e.date.startswith(current_year))
        yearly_total = round(yearly_fuel + yearly_maint + yearly_other, 2)

        # Percentual de combustível no mês
        fuel_percentage = round((month_fuel / monthly_total * 100.0), 1) if monthly_total > 0 else 0.0

        # 3. Consumo médio geral baseado em abastecimentos consecutivos ordenados por odometer
        sorted_fuels = sorted(fuels, key=lambda f: f.odometer)
        consumptions = []
        consumption_points: List[ConsumptionPoint] = []

        for i in range(1, len(sorted_fuels)):
            prev = sorted_fuels[i - 1]
            curr = sorted_fuels[i]
            dist = curr.odometer - prev.odometer
            if dist > 0 and curr.liters > 0:
                km_per_l = round(dist / curr.liters, 2)
                consumptions.append(km_per_l)
                consumption_points.append(ConsumptionPoint(
                    date=curr.date,
                    odometer=curr.odometer,
                    km_per_l=km_per_l
                ))

        avg_consumption = round(sum(consumptions) / len(consumptions), 1) if len(consumptions) >= 1 else None

        # 4. Custo por km
        all_costs = sum(f.total_cost for f in fuels) + sum(m.cost for m in maintenances) + sum(e.amount for e in expenses)
        all_odos = [f.odometer for f in fuels] + [m.odometer for m in maintenances]
        min_odo = min(all_odos) if all_odos else vehicle.current_odometer
        max_odo = vehicle.current_odometer
        total_km = max_odo - min_odo

        cost_per_km = round(all_costs / total_km, 2) if (total_km >= 30 and all_costs > 0) else None

        # 5. Próxima manutenção preventiva
        upcoming = [
            m for m in maintenances 
            if m.next_due_odometer is not None and m.next_due_odometer > vehicle.current_odometer
        ]
        upcoming.sort(key=lambda m: m.next_due_odometer)

        next_km_remaining = None
        next_title = None
        if upcoming:
            closest = upcoming[0]
            next_km_remaining = closest.next_due_odometer - vehicle.current_odometer
            next_title = f"{closest.category.capitalize()}: {closest.description}"

        # 6. Texto de Resumo
        if monthly_total > 0:
            summary_text = f"Você gastou R$ {monthly_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + f" este mês. Combustível representa {int(fuel_percentage)}% das despesas."
        else:
            summary_text = "Nenhum gasto registrado neste mês ainda. Registre para acompanhar seu resumo."

        # 7. Insights Determinísticos Reais
        insights: List[str] = []
        if len(consumptions) >= 3:
            recent_3 = consumptions[-3:]
            if recent_3[-1] < recent_3[0] * 0.95:
                insights.append("Seu consumo médio caiu nos últimos abastecimentos. Vale conferir calibragem dos pneus e filtros.")
            elif recent_3[-1] > recent_3[0] * 1.05:
                insights.append("Ótimo! Sua eficiência de combustível melhorou nos abastecimentos recentes.")

        if next_km_remaining is not None:
            if next_km_remaining <= 1000:
                insights.append(f"Atenção: Sua próxima manutenção ({next_title}) está a apenas {next_km_remaining} km.")
            else:
                insights.append(f"Próxima manutenção programada em {next_km_remaining:,} km.".replace(",", "."))

        if month_maint > 0 and monthly_total > 0:
            maint_pct = int((month_maint / monthly_total) * 100)
            if maint_pct >= 30:
                insights.append(f"Manutenções representaram {maint_pct}% do total deste mês.")

        if not insights:
            insights.append("Continue registrando abastecimentos e serviços para desbloquear novos insights inteligentes.")

        # 8. Distribuição por Categoria
        categories_dict = {}
        if month_fuel > 0:
            categories_dict["Combustível"] = month_fuel
        if month_maint > 0:
            categories_dict["Manutenção"] = month_maint
        for e in expenses:
            if e.date.startswith(current_year_month):
                cat_name = e.category.capitalize()
                categories_dict[cat_name] = categories_dict.get(cat_name, 0.0) + e.amount

        category_distribution: List[CategoryExpenseItem] = []
        for cat, amt in categories_dict.items():
            pct = round((amt / monthly_total * 100.0), 1) if monthly_total > 0 else 0.0
            category_distribution.append(CategoryExpenseItem(
                category=cat,
                amount=round(amt, 2),
                percentage=pct
            ))
        category_distribution.sort(key=lambda x: x.amount, reverse=True)

        # 9. Histórico Mensal (Últimos 6 meses)
        monthly_history_dict = {}
        all_records = []
        for f in fuels:
            all_records.append((f.date[:7], f.total_cost))
        for m in maintenances:
            all_records.append((m.date[:7], m.cost))
        for e in expenses:
            all_records.append((e.date[:7], e.amount))

        for ym, val in all_records:
            monthly_history_dict[ym] = monthly_history_dict.get(ym, 0.0) + val

        monthly_history = [
            MonthlyExpenseItem(month=m, total=round(tot, 2))
            for m, tot in sorted(monthly_history_dict.items())[-6:]
        ]

        # 10. Atividades recentes unificadas
        activities: List[RecentActivity] = []
        for f in sorted(fuels, key=lambda x: x.date, reverse=True)[:6]:
            activities.append(RecentActivity(
                id=f.id,
                type="FUEL",
                title=f"Abastecimento ({f.fuel_type})",
                subtitle=f"{f.liters:.1f}L • {f.station or 'Posto'}",
                date=f.date,
                value=f.total_cost,
                odometer=f.odometer
            ))
        for m in sorted(maintenances, key=lambda x: x.date, reverse=True)[:6]:
            activities.append(RecentActivity(
                id=m.id,
                type="MAINTENANCE",
                title=f"{m.category.capitalize()} - {m.description}",
                subtitle=f"{m.workshop or 'Oficina'}",
                date=m.date,
                value=m.cost,
                odometer=m.odometer
            ))
        for e in sorted(expenses, key=lambda x: x.date, reverse=True)[:6]:
            activities.append(RecentActivity(
                id=e.id,
                type="EXPENSE",
                title=e.category.capitalize(),
                subtitle=e.description,
                date=e.date,
                value=e.amount,
                odometer=None
            ))

        activities.sort(key=lambda a: a.date, reverse=True)

        return DashboardResponse(
            monthly_total=monthly_total,
            monthly_fuel=round(month_fuel, 2),
            monthly_maintenance=round(month_maint, 2),
            monthly_other=round(month_other, 2),
            yearly_total=yearly_total,
            average_consumption=avg_consumption,
            cost_per_km=cost_per_km,
            next_maintenance_km_remaining=next_km_remaining,
            next_maintenance_title=next_title,
            fuel_expense_percentage=fuel_percentage,
            summary_text=summary_text,
            insights=insights,
            recent_activities=activities[:10],
            category_distribution=category_distribution,
            monthly_history=monthly_history,
            consumption_history=consumption_points[-10:]
        )
