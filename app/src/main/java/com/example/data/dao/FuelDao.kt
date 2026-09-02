package com.example.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.data.model.FuelRecord
import kotlinx.coroutines.flow.Flow

@Dao
interface FuelDao {
    @Query("SELECT * FROM fuel_records WHERE vehicleId = :vehicleId ORDER BY date DESC, odometer DESC")
    fun getFuelRecords(vehicleId: Long): Flow<List<FuelRecord>>

    @Query("SELECT * FROM fuel_records WHERE vehicleId = :vehicleId ORDER BY odometer DESC")
    suspend fun getFuelRecordsSortedByOdometer(vehicleId: Long): List<FuelRecord>

    @Query("SELECT * FROM fuel_records WHERE vehicleId = :vehicleId AND odometer < :odometer ORDER BY odometer DESC LIMIT 1")
    suspend fun getPreviousFuelRecord(vehicleId: Long, odometer: Int): FuelRecord?

    @Query("SELECT MAX(odometer) FROM fuel_records WHERE vehicleId = :vehicleId")
    suspend fun getMaxOdometer(vehicleId: Long): Int?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertFuelRecord(record: FuelRecord): Long

    @Update
    suspend fun updateFuelRecord(record: FuelRecord)

    @Query("DELETE FROM fuel_records WHERE id = :id")
    suspend fun deleteFuelRecord(id: Long)

    @Query("SELECT SUM(totalValue) FROM fuel_records WHERE vehicleId = :vehicleId AND date LIKE :yearMonth || '%'")
    suspend fun getMonthlyFuelTotal(vehicleId: Long, yearMonth: String): Double?
}
