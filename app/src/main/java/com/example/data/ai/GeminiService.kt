package com.example.data.ai

import android.util.Base64
import com.example.BuildConfig
import com.example.data.model.AiParsedData
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit
import java.util.regex.Pattern

class GeminiService {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    private fun getApiKey(): String {
        return try {
            val field = BuildConfig::class.java.getField("GEMINI_API_KEY")
            val key = field.get(null) as? String
            key?.trim()?.takeIf { it.isNotEmpty() && !it.startsWith("MY_") } ?: ""
        } catch (_: Throwable) {
            ""
        }
    }

    suspend fun parseNaturalLanguageText(userInput: String): Result<AiParsedData> = withContext(Dispatchers.IO) {
        val apiKey = getApiKey()
        if (apiKey.isNotBlank()) {
            try {
                val prompt = """
                    Você é o assistente inteligente do app 'Meu Carro'.
                    Analise o texto do usuário e extraia as informações estruturadas em JSON estrito.
                    Não invente valores ausentes, use null.
                    
                    Hoje é ${SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())}.
                    
                    Estrutura JSON obrigatória:
                    {
                      "type": "fuel" | "maintenance" | "expense",
                      "date": "YYYY-MM-DD" ou null,
                      "odometer": int ou null,
                      "liters": float ou null,
                      "price_per_liter": float ou null,
                      "total_cost": float ou null,
                      "fuel_type": "gasoline" | "ethanol" | "diesel" | "flex" | "electric" | "hybrid" ou null,
                      "category": "oil" | "filters" | "tires" | "brakes" | "suspension" | "engine" | "electrical" | "revision" | "wash" | "parking" | "toll" | "insurance" | "taxes" | "other" ou null,
                      "description": "breve resumo" ou null,
                      "station": "nome do posto" ou null,
                      "workshop": "nome da oficina" ou null
                    }
                    
                    Texto do usuário: "$userInput"
                """.trimIndent()

                val requestJson = JSONObject().apply {
                    val contents = JSONArray().apply {
                        val contentObj = JSONObject().apply {
                            val parts = JSONArray().apply {
                                put(JSONObject().apply { put("text", prompt) })
                            }
                            put("parts", parts)
                        }
                        put(contentObj)
                    }
                    put("contents", contents)
                    val genConfig = JSONObject().apply {
                        put("responseMimeType", "application/json")
                        put("temperature", 0.1)
                    }
                    put("generationConfig", genConfig)
                }

                val url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$apiKey"
                val request = Request.Builder()
                    .url(url)
                    .post(requestJson.toString().toRequestBody("application/json".toMediaType()))
                    .build()

                val response = client.newCall(request).execute()
                if (response.isSuccessful) {
                    val bodyString = response.body?.string() ?: ""
                    val root = JSONObject(bodyString)
                    val candidates = root.optJSONArray("candidates")
                    if (candidates != null && candidates.length() > 0) {
                        val content = candidates.getJSONObject(0).optJSONObject("content")
                        val parts = content?.optJSONArray("parts")
                        val text = parts?.getJSONObject(0)?.optString("text") ?: ""
                        val cleanJson = text.substringAfter("```json").substringBeforeLast("```").trim()
                        val parsed = JSONObject(if (cleanJson.startsWith("{")) cleanJson else text)
                        return@withContext Result.success(parseJsonObjectToData(parsed))
                    }
                }
            } catch (e: Exception) {
                // Fallback para parser determinístico offline
            }
        }

        // Fallback determinístico inteligente
        val fallback = parseTextHeuristically(userInput)
        Result.success(fallback)
    }

    suspend fun analyzeReceipt(imageBytes: ByteArray?, notesText: String? = null): Result<AiParsedData> = withContext(Dispatchers.IO) {
        val apiKey = getApiKey()
        if (apiKey.isNotBlank() && imageBytes != null && imageBytes.isNotEmpty()) {
            try {
                val prompt = """
                    Analise este cupom fiscal / recibo de veículo.
                    Extraia SOMENTE informações realmente presentes no recibo.
                    Se não encontrar determinada informação, use null. NUNCA INVENTE.
                    
                    Estrutura JSON obrigatória:
                    {
                      "type": "fuel" | "maintenance" | "expense",
                      "date": "YYYY-MM-DD" ou null,
                      "odometer": int ou null,
                      "liters": float ou null,
                      "price_per_liter": float ou null,
                      "total_cost": float ou null,
                      "fuel_type": "gasoline" | "ethanol" | "diesel" | "flex" ou null,
                      "category": "oil" | "filters" | "tires" | "brakes" | "suspension" | "engine" | "electrical" | "revision" | "other" ou null,
                      "description": "descrição do item/serviço" ou null,
                      "station": "nome do estabelecimento" ou null,
                      "workshop": "nome do estabelecimento" ou null
                    }
                """.trimIndent()

                val base64Data = Base64.encodeToString(imageBytes, Base64.NO_WRAP)
                val requestJson = JSONObject().apply {
                    val contents = JSONArray().apply {
                        val contentObj = JSONObject().apply {
                            val parts = JSONArray().apply {
                                put(JSONObject().apply { put("text", prompt) })
                                put(JSONObject().apply {
                                    val inlineData = JSONObject().apply {
                                        put("mimeType", "image/jpeg")
                                        put("data", base64Data)
                                    }
                                    put("inlineData", inlineData)
                                })
                            }
                            put("parts", parts)
                        }
                        put(contentObj)
                    }
                    put("contents", contents)
                    val genConfig = JSONObject().apply {
                        put("responseMimeType", "application/json")
                        put("temperature", 0.0)
                    }
                    put("generationConfig", genConfig)
                }

                val url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$apiKey"
                val request = Request.Builder()
                    .url(url)
                    .post(requestJson.toString().toRequestBody("application/json".toMediaType()))
                    .build()

                val response = client.newCall(request).execute()
                if (response.isSuccessful) {
                    val bodyString = response.body?.string() ?: ""
                    val root = JSONObject(bodyString)
                    val candidates = root.optJSONArray("candidates")
                    if (candidates != null && candidates.length() > 0) {
                        val content = candidates.getJSONObject(0).optJSONObject("content")
                        val parts = content?.optJSONArray("parts")
                        val text = parts?.getJSONObject(0)?.optString("text") ?: ""
                        val cleanJson = text.substringAfter("```json").substringBeforeLast("```").trim()
                        val parsed = JSONObject(if (cleanJson.startsWith("{")) cleanJson else text)
                        return@withContext Result.success(parseJsonObjectToData(parsed))
                    }
                }
            } catch (e: Exception) {
                // Fallback amigável
            }
        }

        // Se não foi possível ou sem API Key, tenta extrair de notas ou retorna estrutura vazia para preenchimento
        val fallback = if (!notesText.isNullOrBlank()) {
            parseTextHeuristically(notesText)
        } else {
            AiParsedData(
                type = "fuel",
                date = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date()),
                odometer = null,
                liters = null,
                pricePerLiter = null,
                totalCost = null,
                fuelType = "Gasolina",
                category = null,
                description = "Recibo escaneado"
            )
        }
        Result.success(fallback)
    }

    private fun parseJsonObjectToData(json: JSONObject): AiParsedData {
        val type = when (json.optString("type").lowercase()) {
            "maintenance", "manutencao" -> "maintenance"
            "expense", "gasto", "despesa" -> "expense"
            else -> "fuel"
        }

        val fuelType = when (json.optString("fuel_type").lowercase()) {
            "ethanol", "etanol" -> "Etanol"
            "diesel" -> "Diesel"
            "flex" -> "Flex"
            "electric", "eletrico" -> "Elétrico"
            "hybrid", "hibrido" -> "Híbrido"
            else -> "Gasolina"
        }

        val category = when (json.optString("category").lowercase()) {
            "oil", "oleo" -> "Óleo"
            "filters", "filtros" -> "Filtros"
            "tires", "pneus" -> "Pneus"
            "brakes", "freios" -> "Freios"
            "suspension", "suspensao" -> "Suspensão"
            "engine", "motor" -> "Motor"
            "electrical", "eletrica" -> "Elétrica"
            "revision", "revisao" -> "Revisão"
            "wash", "lavagem" -> "lavagem"
            "parking", "estacionamento" -> "estacionamento"
            "toll", "pedagio" -> "pedágio"
            "insurance", "seguro" -> "seguro"
            "taxes", "documentacao" -> "documentação"
            else -> "Outro"
        }

        return AiParsedData(
            type = type,
            date = json.optString("date").takeIf { it.isNotBlank() && it != "null" }
                ?: SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date()),
            odometer = if (json.has("odometer") && !json.isNull("odometer")) json.optInt("odometer") else null,
            liters = if (json.has("liters") && !json.isNull("liters")) json.optDouble("liters") else null,
            pricePerLiter = if (json.has("price_per_liter") && !json.isNull("price_per_liter")) json.optDouble("price_per_liter") else null,
            totalCost = if (json.has("total_cost") && !json.isNull("total_cost")) json.optDouble("total_cost") else null,
            fuelType = fuelType,
            category = category,
            description = json.optString("description").takeIf { it.isNotBlank() && it != "null" },
            station = json.optString("station").takeIf { it.isNotBlank() && it != "null" },
            workshop = json.optString("workshop").takeIf { it.isNotBlank() && it != "null" }
        )
    }

    private fun parseTextHeuristically(text: String): AiParsedData {
        val lower = text.lowercase()
        val isMaintenance = lower.contains("troca") || lower.contains("revis") || lower.contains("oficina") || lower.contains("oleo") || lower.contains("óleo") || lower.contains("freio") || lower.contains("pneu")
        val isExpense = lower.contains("lavagem") || lower.contains("estacionamento") || lower.contains("pedágio") || lower.contains("pedagio") || lower.contains("seguro") || lower.contains("ipva")

        val type = if (isMaintenance) "maintenance" else if (isExpense) "expense" else "fuel"

        // Extrair quilometragem: "72.430 km" ou "72430km" ou "73 mil km"
        var odometer: Int? = null
        val odoMilMatch = Pattern.compile("(\\d+)\\s*(mil|k)\\s*km").matcher(lower)
        if (odoMilMatch.find()) {
            odometer = (odoMilMatch.group(1)?.toIntOrNull() ?: 0) * 1000
        } else {
            val odoMatch = Pattern.compile("(\\d{1,3}(?:\\.\\d{3})*|\\d{2,6})\\s*(?:km|quilometros)").matcher(lower)
            if (odoMatch.find()) {
                odometer = odoMatch.group(1)?.replace(".", "")?.toIntOrNull()
            }
        }

        // Extrair litros: "40 litros", "40l"
        var liters: Double? = null
        val litersMatch = Pattern.compile("(\\d+(?:[,.]\\d+)?)\\s*(?:litros|litro|l\\b)").matcher(lower)
        if (litersMatch.find()) {
            liters = litersMatch.group(1)?.replace(",", ".")?.toDoubleOrNull()
        }

        // Extrair preço por litro ou valor: "a 6,19", "6.19", "paguei 380 reais", "R$ 247,60"
        var pricePerLiter: Double? = null
        var totalCost: Double? = null

        val priceMatch = Pattern.compile("a\\s*(\\d+[,.]\\d{2})").matcher(lower)
        if (priceMatch.find()) {
            pricePerLiter = priceMatch.group(1)?.replace(",", ".")?.toDoubleOrNull()
        }

        val totalMatch = Pattern.compile("(?:paguei|custou|total|r\\$)\\s*(\\d+(?:[,.]\\d{2})?)").matcher(lower)
        if (totalMatch.find()) {
            totalCost = totalMatch.group(1)?.replace(",", ".")?.toDoubleOrNull()
        }

        if (liters != null && pricePerLiter != null && totalCost == null) {
            totalCost = (liters * pricePerLiter * 100.0).toInt() / 100.0
        }

        var fuelType = "Gasolina"
        if (lower.contains("etanol") || lower.contains("álcool") || lower.contains("alcool")) fuelType = "Etanol"
        else if (lower.contains("diesel")) fuelType = "Diesel"
        else if (lower.contains("flex")) fuelType = "Flex"

        var category = "Outro"
        if (lower.contains("óleo") || lower.contains("oleo")) category = "Óleo"
        else if (lower.contains("pneu")) category = "Pneus"
        else if (lower.contains("freio")) category = "Freios"
        else if (lower.contains("revis")) category = "Revisão"
        else if (lower.contains("lavagem")) category = "lavagem"
        else if (lower.contains("estacionamento")) category = "estacionamento"
        else if (lower.contains("pedágio") || lower.contains("pedagio")) category = "pedágio"

        val description = if (isMaintenance) {
            if (lower.contains("óleo") || lower.contains("oleo")) "Troca de óleo" else "Manutenção do veículo"
        } else if (isExpense) {
            category
        } else {
            "Abastecimento"
        }

        return AiParsedData(
            type = type,
            date = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date()),
            odometer = odometer,
            liters = liters,
            pricePerLiter = pricePerLiter,
            totalCost = totalCost,
            fuelType = fuelType,
            category = category,
            description = description
        )
    }
}
