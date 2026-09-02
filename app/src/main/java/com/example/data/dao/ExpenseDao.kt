package com.example.data.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.data.model.ExpenseRecord
import kotlinx.coroutines.flow.Flow

@Dao
interface ExpenseDao {
    @Query("SELECT * FROM expense_records WHERE vehicleId = :vehicleId ORDER BY date DESC, id DESC")
    fun getExpenseRecords(vehicleId: Long): Flow<List<ExpenseRecord>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertExpense(record: ExpenseRecord): Long

    @Update
    suspend fun updateExpense(record: ExpenseRecord)

    @Query("DELETE FROM expense_records WHERE id = :id")
    suspend fun deleteExpense(id: Long)

    @Query("SELECT SUM(cost) FROM expense_records WHERE vehicleId = :vehicleId AND date LIKE :yearMonth || '%'")
    suspend fun getMonthlyExpenseTotal(vehicleId: Long, yearMonth: String): Double?

    @Query("SELECT SUM(cost) FROM expense_records WHERE vehicleId = :vehicleId AND date LIKE :year || '%'")
    suspend fun getYearlyExpenseTotal(vehicleId: Long, year: String): Double?
}
