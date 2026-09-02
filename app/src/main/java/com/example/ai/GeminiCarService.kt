package com.example.ai

import android.graphics.Bitmap
import com.example.data.ai.GeminiService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.ByteArrayOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class GeminiCarService {
    private val service = GeminiService()

    suspend fun parseNaturalText(userInput: String): Result<AiParsedRecord> {
        val result = service.parseNaturalLanguageText(userInput)
        return result.map { data ->
            AiParsedRecord(
                type = data.type,
                date = data.date ?: SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date()),
                odometer = data.odometer,
                liters = data.liters,
                pricePerLiter = data.pricePerLiter,
                totalCost = data.totalCost,
                fuelType = data.fuelType,
                gasStation = data.station,
                category = data.category,
                description = data.description,
                workshop = data.workshop
            )
        }
    }

    suspend fun analyzeReceipt(bitmap: Bitmap): Result<AiParsedRecord> = withContext(Dispatchers.IO) {
        val stream = ByteArrayOutputStream()
        bitmap.compress(Bitmap.CompressFormat.JPEG, 80, stream)
        val bytes = stream.toByteArray()
        val result = service.analyzeReceipt(bytes, null)
        result.map { data ->
            AiParsedRecord(
                type = data.type,
                date = data.date ?: SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date()),
                odometer = data.odometer,
                liters = data.liters,
                pricePerLiter = data.pricePerLiter,
                totalCost = data.totalCost,
                fuelType = data.fuelType,
                gasStation = data.station,
                category = data.category,
                description = data.description,
                workshop = data.workshop
            )
        }
    }
}
