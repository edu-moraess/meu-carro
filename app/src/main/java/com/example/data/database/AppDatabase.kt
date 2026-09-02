package com.example.data.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.example.data.dao.ExpenseDao
import com.example.data.dao.FuelDao
import com.example.data.dao.MaintenanceDao
import com.example.data.dao.VehicleDao
import com.example.data.model.ExpenseRecord
import com.example.data.model.FuelRecord
import com.example.data.model.MaintenanceRecord
import com.example.data.model.Vehicle

@Database(
    entities = [
        Vehicle::class,
        FuelRecord::class,
        MaintenanceRecord::class,
        ExpenseRecord::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun vehicleDao(): VehicleDao
    abstract fun fuelDao(): FuelDao
    abstract fun maintenanceDao(): MaintenanceDao
    abstract fun expenseDao(): ExpenseDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "meu_carro.db"
                ).fallbackToDestructiveMigration().build()
                INSTANCE = instance
                instance
            }
        }
    }
}
