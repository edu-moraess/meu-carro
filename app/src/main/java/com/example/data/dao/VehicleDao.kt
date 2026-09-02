package com.example.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.data.model.Vehicle
import kotlinx.coroutines.flow.Flow

@Dao
interface VehicleDao {
    @Query("SELECT * FROM vehicles LIMIT 1")
    fun getPrimaryVehicle(): Flow<Vehicle?>

    @Query("SELECT * FROM vehicles LIMIT 1")
    suspend fun getPrimaryVehicleOnce(): Vehicle?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertVehicle(vehicle: Vehicle): Long

    @Update
    suspend fun updateVehicle(vehicle: Vehicle)

    @Query("UPDATE vehicles SET currentOdometer = :odometer WHERE id = :vehicleId")
    suspend fun updateOdometer(vehicleId: Long, odometer: Int)
}
