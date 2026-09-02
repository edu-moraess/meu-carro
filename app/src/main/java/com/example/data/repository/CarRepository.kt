package com.example.data.repository

import com.example.data.dao.ExpenseDao
import com.example.data.dao.FuelDao
import com.example.data.dao.MaintenanceDao
import com.example.data.dao.VehicleDao
import com.example.data.model.DashboardSummary
import com.example.data.model.ExpenseRecord
import com.example.data.model.FuelRecord
import com.example.data.model.MaintenanceRecord
import com.example.data.model.RecentActivity
import com.example.data.model.Vehicle
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.combine
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

class CarRepository(
    private val vehicleDao: VehicleDao,
    private val fuelDao: FuelDao,
    private val maintenanceDao: MaintenanceDao,
    private val expenseDao: ExpenseDao
) {
    val vehicleFlow: Flow<Vehicle?> = vehicleDao.getPrimaryVehicle()

    suspend fun getPrimaryVehicleOnce(): Vehicle? = vehicleDao.getPrimaryVehicleOnce()

    suspend fun registerVehicle(
        brand: String,
        model: String,
        year: Int,
        odometer: Int,
        fuelType: String,
        licensePlate: String?
    ): Long {
        val vehicle = Vehicle(
            brand = brand.trim(),
            model = model.trim(),
            year = year,
            currentOdometer = odometer,
            fuelType = fuelType,
            licensePlate = licensePlate?.trim()?.ifBlank { null }
        )
        return vehicleDao.insertVehicle(vehicle)
    }

    suspend fun updateVehicle(vehicle: Vehicle) {
        vehicleDao.updateVehicle(vehicle)
    }

    suspend fun getMaxRecordedOdometer(vehicleId: Long): Int {
        val vehicle = vehicleDao.getPrimaryVehicleOnce() ?: return 0
        val maxFuelOdo = fuelDao.getMaxOdometer(vehicleId) ?: 0
        val maxMaintOdo = maintenanceDao.getMaxOdometer(vehicleId) ?: 0
        return maxOf(vehicle.currentOdometer, maxFuelOdo, maxMaintOdo)
    }

    fun getFuelRecords(vehicleId: Long): Flow<List<FuelRecord>> =
        fuelDao.getFuelRecords(vehicleId)

    fun getMaintenanceRecords(vehicleId: Long): Flow<List<MaintenanceRecord>> =
        maintenanceDao.getMaintenanceRecords(vehicleId)

    fun getExpenseRecords(vehicleId: Long): Flow<List<ExpenseRecord>> =
        expenseDao.getExpenseRecords(vehicleId)

    suspend fun addFuelRecord(
        vehicleId: Long,
        date: String,
        odometer: Int,
        liters: Double,
        pricePerLiter: Double,
        fuelType: String,
        station: String?,
        notes: String?
    ): FuelRecord {
        val totalValue = liters * pricePerLiter

        // Determinar consumo com base no abastecimento imediatamente anterior com menor km
        val previousRecord = fuelDao.getPreviousFuelRecord(vehicleId, odometer)
        val consumption = if (previousRecord != null && odometer > previousRecord.odometer && liters > 0) {
            val distance = (odometer - previousRecord.odometer).toDouble()
            (distance / liters * 100.0).roundToInt() / 100.0
        } else {
            null
        }

        val record = FuelRecord(
            vehicleId = vehicleId,
            date = date,
            odometer = odometer,
            liters = liters,
            pricePerLiter = pricePerLiter,
            totalValue = totalValue,
            fuelType = fuelType,
            station = station?.trim()?.ifBlank { null },
            notes = notes?.trim()?.ifBlank { null },
            consumptionKmPerL = consumption
        )
        val id = fuelDao.insertFuelRecord(record)

        // Atualizar km atual do veículo se for maior
        val vehicle = vehicleDao.getPrimaryVehicleOnce()
        if (vehicle != null && odometer > vehicle.currentOdometer) {
            vehicleDao.updateOdometer(vehicleId, odometer)
        }

        return record.copy(id = id)
    }

    suspend fun deleteFuelRecord(id: Long) {
        fuelDao.deleteFuelRecord(id)
    }

    suspend fun addMaintenanceRecord(
        vehicleId: Long,
        date: String,
        odometer: Int,
        category: String,
        description: String,
        workshop: String?,
        cost: Double,
        nextMaintenanceKm: Int?,
        nextMaintenanceDate: String?,
        notes: String?
    ): MaintenanceRecord {
        val record = MaintenanceRecord(
            vehicleId = vehicleId,
            date = date,
            odometer = odometer,
            category = category,
            description = description.trim(),
            workshop = workshop?.trim()?.ifBlank { null },
            cost = cost,
            nextMaintenanceKm = nextMaintenanceKm,
            nextMaintenanceDate = nextMaintenanceDate?.trim()?.ifBlank { null },
            notes = notes?.trim()?.ifBlank { null }
        )
        val id = maintenanceDao.insertMaintenance(record)

        val vehicle = vehicleDao.getPrimaryVehicleOnce()
        if (vehicle != null && odometer > vehicle.currentOdometer) {
            vehicleDao.updateOdometer(vehicleId, odometer)
        }

        return record.copy(id = id)
    }

    suspend fun deleteMaintenance(id: Long) {
        maintenanceDao.deleteMaintenance(id)
    }

    suspend fun addExpenseRecord(
        vehicleId: Long,
        date: String,
        category: String,
        description: String,
        cost: Double,
        notes: String?
    ): ExpenseRecord {
        val record = ExpenseRecord(
            vehicleId = vehicleId,
            date = date,
            category = category,
            description = description.trim(),
            cost = cost,
            notes = notes?.trim()?.ifBlank { null }
        )
        val id = expenseDao.insertExpense(record)
        return record.copy(id = id)
    }

    suspend fun deleteExpense(id: Long) {
        expenseDao.deleteExpense(id)
    }

    fun getDashboardStream(vehicleId: Long): Flow<DashboardSummary> {
        val currentYearMonth = SimpleDateFormat("yyyy-MM", Locale.getDefault()).format(Date())

        return combine(
            vehicleFlow,
            fuelDao.getFuelRecords(vehicleId),
            maintenanceDao.getMaintenanceRecords(vehicleId),
            expenseDao.getExpenseRecords(vehicleId)
        ) { vehicle, fuels, maintenances, expenses ->
            var monthFuel = 0.0
            var monthMaint = 0.0
            var monthOther = 0.0

            fuels.filter { it.date.startsWith(currentYearMonth) }.forEach { monthFuel += it.totalValue }
            maintenances.filter { it.date.startsWith(currentYearMonth) }.forEach { monthMaint += it.cost }
            expenses.filter { it.date.startsWith(currentYearMonth) }.forEach { monthOther += it.cost }

            val totalMonth = monthFuel + monthMaint + monthOther
            val fuelPercent = if (totalMonth > 0) (monthFuel / totalMonth) * 100.0 else 0.0

            // Consumo médio
            val validConsumptions = fuels.mapNotNull { it.consumptionKmPerL }
            val avgConsumption = if (validConsumptions.isNotEmpty()) {
                (validConsumptions.average() * 10.0).roundToInt() / 10.0
            } else null

            // Custo por km: total gasto / km rodado
            val currentOdo = vehicle?.currentOdometer ?: 0
            val minOdo = fuels.minOfOrNull { it.odometer } ?: currentOdo
            val totalDistance = maxOf(0, currentOdo - minOdo)
            val allExpensesTotal = fuels.sumOf { it.totalValue } + maintenances.sumOf { it.cost } + expenses.sumOf { it.cost }
            val costPerKm = if (totalDistance > 0 && allExpensesTotal > 0) {
                (allExpensesTotal / totalDistance * 100.0).roundToInt() / 100.0
            } else null

            // Próxima manutenção
            val upcoming = maintenances
                .filter { (it.nextMaintenanceKm ?: 0) > currentOdo }
                .minByOrNull { it.nextMaintenanceKm ?: Int.MAX_VALUE }

            val nextMaintKmRemaining = upcoming?.nextMaintenanceKm?.let { it - currentOdo }
            val nextMaintTitle = upcoming?.let { "${it.category} (${it.description})" }

            // Atividades recentes combinadas
            val activities = mutableListOf<RecentActivity>()
            fuels.take(5).forEach {
                activities.add(
                    RecentActivity(
                        id = it.id,
                        type = "FUEL",
                        title = "Abastecimento - ${it.fuelType}",
                        subtitle = "${String.format(Locale.getDefault(), "%.1f", it.liters)}L • ${it.station ?: "Posto"}",
                        date = it.date,
                        value = it.totalValue,
                        category = "combustível"
                    )
                )
            }
            maintenances.take(5).forEach {
                activities.add(
                    RecentActivity(
                        id = it.id,
                        type = "MAINTENANCE",
                        title = "Manutenção - ${it.category}",
                        subtitle = it.description,
                        date = it.date,
                        value = it.cost,
                        category = "manutenção"
                    )
                )
            }
            expenses.take(5).forEach {
                activities.add(
                    RecentActivity(
                        id = it.id,
                        type = "EXPENSE",
                        title = it.category.replaceFirstChar { c -> c.uppercase() },
                        subtitle = it.description,
                        date = it.date,
                        value = it.cost,
                        category = it.category
                    )
                )
            }
            activities.sortByDescending { it.date }

            // Insights determinísticos
            val insights = mutableListOf<String>()
            if (fuels.size >= 3) {
                val last3 = fuels.take(3).mapNotNull { it.consumptionKmPerL }
                if (last3.size >= 2) {
                    val recent = last3[0]
                    val prev = last3[1]
                    if (recent > prev) {
                        insights.add("Seu consumo melhorou no último abastecimento: ${String.format(Locale.getDefault(), "%.1f", recent)} km/L.")
                    } else if (recent < prev) {
                        insights.add("Seu consumo médio aumentou nos últimos abastecimentos.")
                    }
                }
            }
            if (fuelPercent > 50 && totalMonth > 0) {
                insights.add("Combustível representa ${fuelPercent.roundToInt()}% dos seus gastos este mês.")
            }
            if (nextMaintKmRemaining != null) {
                if (nextMaintKmRemaining <= 1500) {
                    insights.add("Atenção: Seu próximo serviço está muito próximo (${nextMaintKmRemaining} km).")
                } else {
                    insights.add("Próxima manutenção prevista em ${nextMaintKmRemaining} km.")
                }
            }
            if (insights.isEmpty()) {
                insights.add("Cadastre seus abastecimentos e manutenções para liberar insights automáticos.")
            }

            DashboardSummary(
                vehicle = vehicle,
                monthExpenses = totalMonth,
                averageConsumption = avgConsumption,
                costPerKm = costPerKm,
                nextMaintenanceKmRemaining = nextMaintKmRemaining,
                nextMaintenanceTitle = nextMaintTitle,
                fuelExpensePercentage = fuelPercent,
                recentActivities = activities.take(8),
                insights = insights
            )
        }
    }
}
