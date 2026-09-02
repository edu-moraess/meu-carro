package com.example.ai

data class AiParsedRecord(
    val type: String, // "fuel", "maintenance", "expense"
    val date: String,
    val odometer: Int? = null,
    val liters: Double? = null,
    val pricePerLiter: Double? = null,
    val totalCost: Double? = null,
    val fuelType: String? = null,
    val gasStation: String? = null,
    val category: String? = null,
    val description: String? = null,
    val workshop: String? = null,
    val confidence: String? = null
)
