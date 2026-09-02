package com.example.data.model

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(tableName = "vehicles")
data class Vehicle(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val brand: String,
    val model: String,
    val year: Int,
    val currentOdometer: Int,
    val fuelType: String, // Gasolina, Etanol, Diesel, Flex, Elétrico, Híbrido
    val licensePlate: String? = null, // Dado privado opcional
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(
    tableName = "fuel_records",
    indices = [
        Index(value = ["vehicleId"]),
        Index(value = ["date"]),
        Index(value = ["odometer"])
    ]
)
data class FuelRecord(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val vehicleId: Long,
    val date: String, // YYYY-MM-DD
    val odometer: Int,
    val liters: Double,
    val pricePerLiter: Double,
    val totalValue: Double,
    val fuelType: String,
    val station: String? = null,
    val notes: String? = null,
    val consumptionKmPerL: Double? = null, // Calculado se houver abastecimento anterior
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(
    tableName = "maintenance_records",
    indices = [
        Index(value = ["vehicleId"]),
        Index(value = ["date"]),
        Index(value = ["odometer"])
    ]
)
data class MaintenanceRecord(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val vehicleId: Long,
    val date: String, // YYYY-MM-DD
    val odometer: Int,
    val category: String, // Óleo, Filtros, Pneus, Freios, Suspensão, Motor, Elétrica, Revisão, Outro
    val description: String,
    val workshop: String? = null,
    val cost: Double,
    val nextMaintenanceKm: Int? = null,
    val nextMaintenanceDate: String? = null,
    val notes: String? = null,
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(
    tableName = "expense_records",
    indices = [
        Index(value = ["vehicleId"]),
        Index(value = ["date"])
    ]
)
data class ExpenseRecord(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val vehicleId: Long,
    val date: String, // YYYY-MM-DD
    val category: String, // combustível, manutenção, lavagem, estacionamento, pedágio, seguro, documentação, acessórios, outros
    val description: String,
    val cost: Double,
    val notes: String? = null,
    val createdAt: Long = System.currentTimeMillis()
)

data class RecentActivity(
    val id: Long,
    val type: String, // FUEL, MAINTENANCE, EXPENSE
    val title: String,
    val subtitle: String,
    val date: String,
    val value: Double,
    val category: String
)

data class DashboardSummary(
    val vehicle: Vehicle?,
    val monthExpenses: Double,
    val averageConsumption: Double?,
    val costPerKm: Double?,
    val nextMaintenanceKmRemaining: Int?,
    val nextMaintenanceTitle: String?,
    val fuelExpensePercentage: Double,
    val recentActivities: List<RecentActivity>,
    val insights: List<String>
)

data class AiParsedData(
    val type: String, // fuel, maintenance, expense
    val date: String? = null,
    val odometer: Int? = null,
    val liters: Double? = null,
    val pricePerLiter: Double? = null,
    val totalCost: Double? = null,
    val fuelType: String? = null,
    val category: String? = null,
    val description: String? = null,
    val station: String? = null,
    val workshop: String? = null
)
