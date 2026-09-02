package com.example.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.example.data.ai.GeminiService
import com.example.data.database.AppDatabase
import com.example.data.model.AiParsedData
import com.example.data.model.DashboardSummary
import com.example.data.model.ExpenseRecord
import com.example.data.model.FuelRecord
import com.example.data.model.MaintenanceRecord
import com.example.data.model.Vehicle
import com.example.data.repository.CarRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

enum class ActiveDialog {
    NONE,
    QUICK_ACTION,
    ADD_FUEL,
    ADD_MAINTENANCE,
    ADD_EXPENSE,
    AI_TEXT_INPUT,
    RECEIPT_SCAN,
    CONFIRM_AI_DATA,
    EDIT_VEHICLE
}

class CarViewModel(application: Application) : AndroidViewModel(application) {

    private val db = AppDatabase.getDatabase(application)
    private val repository = CarRepository(
        db.vehicleDao(),
        db.fuelDao(),
        db.maintenanceDao(),
        db.expenseDao()
    )
    private val geminiService = GeminiService()

    val vehicle: StateFlow<Vehicle?> = repository.vehicleFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    val dashboard: StateFlow<DashboardSummary?> = vehicle.flatMapLatest { v ->
        if (v != null) {
            repository.getDashboardStream(v.id)
        } else {
            flowOf(null)
        }
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    val fuelRecords: StateFlow<List<FuelRecord>> = vehicle.flatMapLatest { v ->
        if (v != null) repository.getFuelRecords(v.id) else flowOf(emptyList())
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    val maintenanceRecords: StateFlow<List<MaintenanceRecord>> = vehicle.flatMapLatest { v ->
        if (v != null) repository.getMaintenanceRecords(v.id) else flowOf(emptyList())
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    val expenseRecords: StateFlow<List<ExpenseRecord>> = vehicle.flatMapLatest { v ->
        if (v != null) repository.getExpenseRecords(v.id) else flowOf(emptyList())
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    private val _selectedTab = MutableStateFlow(0)
    val selectedTab = _selectedTab.asStateFlow()

    private val _activeDialog = MutableStateFlow(ActiveDialog.NONE)
    val activeDialog = _activeDialog.asStateFlow()

    private val _aiParsedData = MutableStateFlow<AiParsedData?>(null)
    val aiParsedData = _aiParsedData.asStateFlow()

    private val _isLoadingAi = MutableStateFlow(false)
    val isLoadingAi = _isLoadingAi.asStateFlow()

    private val _errorMessage = MutableStateFlow<String?>(null)
    val errorMessage = _errorMessage.asStateFlow()

    fun selectTab(index: Int) {
        _selectedTab.value = index
    }

    fun openDialog(dialog: ActiveDialog) {
        _errorMessage.value = null
        _activeDialog.value = dialog
    }

    fun dismissDialog() {
        _activeDialog.value = ActiveDialog.NONE
        _errorMessage.value = null
    }

    fun clearError() {
        _errorMessage.value = null
    }

    fun registerVehicle(
        brand: String,
        model: String,
        year: Int,
        odometer: Int,
        fuelType: String,
        licensePlate: String?
    ) {
        if (brand.isBlank() || model.isBlank() || year < 1900 || odometer < 0) {
            _errorMessage.value = "Preencha todos os campos obrigatórios com valores válidos."
            return
        }

        viewModelScope.launch {
            repository.registerVehicle(brand, model, year, odometer, fuelType, licensePlate)
        }
    }

    fun updateVehicle(updated: Vehicle) {
        viewModelScope.launch {
            repository.updateVehicle(updated)
            dismissDialog()
        }
    }

    suspend fun validateOdometer(newOdometer: Int): String? {
        val current = vehicle.value ?: return null
        val maxRecorded = repository.getMaxRecordedOdometer(current.id)
        return if (newOdometer < maxRecorded) {
            "A quilometragem informada ($newOdometer km) é menor que o último registro ($maxRecorded km). Verifique o valor."
        } else {
            null
        }
    }

    fun addFuel(
        date: String,
        odometer: Int,
        liters: Double,
        pricePerLiter: Double,
        fuelType: String,
        station: String?,
        notes: String?,
        allowLowerOdometer: Boolean = false,
        onSuccess: () -> Unit
    ) {
        val v = vehicle.value ?: return
        if (liters <= 0 || pricePerLiter <= 0 || odometer < 0) {
            _errorMessage.value = "Valores de litros, preço e quilometragem devem ser maiores que zero."
            return
        }

        viewModelScope.launch {
            if (!allowLowerOdometer) {
                val odoWarning = validateOdometer(odometer)
                if (odoWarning != null) {
                    _errorMessage.value = odoWarning
                    return@launch
                }
            }
            repository.addFuelRecord(
                vehicleId = v.id,
                date = date,
                odometer = odometer,
                liters = liters,
                pricePerLiter = pricePerLiter,
                fuelType = fuelType,
                station = station,
                notes = notes
            )
            dismissDialog()
            onSuccess()
        }
    }

    fun addMaintenance(
        date: String,
        odometer: Int,
        category: String,
        description: String,
        workshop: String?,
        cost: Double,
        nextKm: Int?,
        nextDate: String?,
        notes: String?,
        allowLowerOdometer: Boolean = false,
        onSuccess: () -> Unit
    ) {
        val v = vehicle.value ?: return
        if (cost < 0 || description.isBlank() || odometer < 0) {
            _errorMessage.value = "Verifique os dados da manutenção (valor e descrição válidos)."
            return
        }

        viewModelScope.launch {
            if (!allowLowerOdometer) {
                val odoWarning = validateOdometer(odometer)
                if (odoWarning != null) {
                    _errorMessage.value = odoWarning
                    return@launch
                }
            }
            repository.addMaintenanceRecord(
                vehicleId = v.id,
                date = date,
                odometer = odometer,
                category = category,
                description = description,
                workshop = workshop,
                cost = cost,
                nextMaintenanceKm = nextKm,
                nextMaintenanceDate = nextDate,
                notes = notes
            )
            dismissDialog()
            onSuccess()
        }
    }

    fun addExpense(
        date: String,
        category: String,
        description: String,
        cost: Double,
        notes: String?,
        onSuccess: () -> Unit
    ) {
        val v = vehicle.value ?: return
        if (cost <= 0 || description.isBlank()) {
            _errorMessage.value = "Informe um valor e uma descrição válida."
            return
        }

        viewModelScope.launch {
            repository.addExpenseRecord(
                vehicleId = v.id,
                date = date,
                category = category,
                description = description,
                cost = cost,
                notes = notes
            )
            dismissDialog()
            onSuccess()
        }
    }

    fun deleteFuelRecord(id: Long) {
        viewModelScope.launch { repository.deleteFuelRecord(id) }
    }

    fun deleteMaintenanceRecord(id: Long) {
        viewModelScope.launch { repository.deleteMaintenance(id) }
    }

    fun deleteExpenseRecord(id: Long) {
        viewModelScope.launch { repository.deleteExpense(id) }
    }

    fun processAiText(input: String) {
        if (input.isBlank()) {
            _errorMessage.value = "Digite um texto para análise."
            return
        }
        _isLoadingAi.value = true
        _errorMessage.value = null

        viewModelScope.launch {
            try {
                val result = geminiService.parseNaturalLanguageText(input)
                result.onSuccess { parsed ->
                    _aiParsedData.value = parsed
                    _activeDialog.value = ActiveDialog.CONFIRM_AI_DATA
                }.onFailure {
                    _errorMessage.value = "Não foi possível analisar o texto. Registre os dados manualmente."
                }
            } finally {
                _isLoadingAi.value = false
            }
        }
    }

    fun processReceipt(bytes: ByteArray?, notes: String? = null) {
        _isLoadingAi.value = true
        _errorMessage.value = null

        viewModelScope.launch {
            try {
                val result = geminiService.analyzeReceipt(bytes, notes)
                result.onSuccess { parsed ->
                    _aiParsedData.value = parsed
                    _activeDialog.value = ActiveDialog.CONFIRM_AI_DATA
                }.onFailure {
                    _errorMessage.value = "Não foi possível analisar o recibo. Tente novamente ou registre os dados manualmente."
                }
            } finally {
                _isLoadingAi.value = false
            }
        }
    }

    fun confirmAiRecord(data: AiParsedData) {
        val v = vehicle.value ?: return
        viewModelScope.launch {
            val date = data.date ?: java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault()).format(java.util.Date())
            val odo = data.odometer ?: v.currentOdometer

            when (data.type.lowercase()) {
                "fuel" -> {
                    val liters = data.liters ?: 1.0
                    val price = data.pricePerLiter ?: if (data.totalCost != null && liters > 0) data.totalCost / liters else 5.89
                    repository.addFuelRecord(
                        vehicleId = v.id,
                        date = date,
                        odometer = odo,
                        liters = liters,
                        pricePerLiter = price,
                        fuelType = data.fuelType ?: v.fuelType,
                        station = data.station ?: "Posto",
                        notes = "Registrado via IA"
                    )
                }
                "maintenance" -> {
                    repository.addMaintenanceRecord(
                        vehicleId = v.id,
                        date = date,
                        odometer = odo,
                        category = data.category ?: "Outro",
                        description = data.description ?: "Manutenção via IA",
                        workshop = data.workshop,
                        cost = data.totalCost ?: 0.0,
                        nextMaintenanceKm = null,
                        nextMaintenanceDate = null,
                        notes = "Registrado via IA"
                    )
                }
                else -> {
                    repository.addExpenseRecord(
                        vehicleId = v.id,
                        date = date,
                        category = data.category ?: "outros",
                        description = data.description ?: "Gasto via IA",
                        cost = data.totalCost ?: 0.0,
                        notes = "Registrado via IA"
                    )
                }
            }
            _aiParsedData.value = null
            dismissDialog()
        }
    }
}
