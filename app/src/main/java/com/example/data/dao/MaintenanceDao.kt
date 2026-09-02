package com.example.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.data.model.MaintenanceRecord
import kotlinx.coroutines.flow.Flow

@Dao
interface MaintenanceDao {
    @Query("SELECT * FROM maintenance_records WHERE vehicleId = :vehicleId ORDER BY date DESC, odometer DESC")
    fun getMaintenanceRecords(vehicleId: Long): Flow<List<MaintenanceRecord>>

    @Query("SELECT * FROM maintenance_records WHERE vehicleId = :vehicleId AND nextMaintenanceKm IS NOT NULL AND nextMaintenanceKm > :currentOdometer ORDER BY nextMaintenanceKm ASC LIMIT 1")
    suspend fun getNextUpcomingMaintenance(vehicleId: Long, currentOdometer: Int): MaintenanceRecord?

    @Query("SELECT MAX(odometer) FROM maintenance_records WHERE vehicleId = :vehicleId")
    suspend fun getMaxOdometer(vehicleId: Long): Int?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMaintenance(record: MaintenanceRecord): Long

    @Update
    suspend fun updateMaintenance(record: MaintenanceRecord)

    @Query("DELETE FROM maintenance_records WHERE id = :id")
    suspend fun deleteMaintenance(id: Long)

    @Query("SELECT SUM(cost) FROM maintenance_records WHERE vehicleId = :vehicleId AND date LIKE :yearMonth || '%'")
    suspend fun getMonthlyMaintenanceTotal(vehicleId: Long, yearMonth: String): Double?
}
