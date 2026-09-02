package com.example.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.DocumentScanner
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.LocalGasStation
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import com.example.data.model.AiParsedData
import com.example.data.model.Vehicle
import com.example.ui.viewmodel.ActiveDialog
import com.example.ui.viewmodel.CarViewModel
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun AppDialogsHost(viewModel: CarViewModel) {
    val activeDialog by viewModel.activeDialog.collectAsState()
    val aiParsedData by viewModel.aiParsedData.collectAsState()
    val isLoadingAi by viewModel.isLoadingAi.collectAsState()
    val vehicle by viewModel.vehicle.collectAsState()
    val errorMessage by viewModel.errorMessage.collectAsState()

    when (activeDialog) {
        ActiveDialog.QUICK_ACTION -> {
            QuickActionSheet(
                onDismiss = { viewModel.dismissDialog() },
                onSelectOption = { opt ->
                    viewModel.openDialog(opt)
                }
            )
        }
        ActiveDialog.ADD_FUEL -> {
            AddFuelDialog(
                currentVehicle = vehicle,
                errorMessage = errorMessage,
                onDismiss = { viewModel.dismissDialog() },
                onSave = { date, odo, liters, price, fuelType, station, notes, allowLower ->
                    viewModel.addFuel(date, odo, liters, price, fuelType, station, notes, allowLower) {}
                }
            )
        }
        ActiveDialog.ADD_MAINTENANCE -> {
            AddMaintenanceDialog(
                currentVehicle = vehicle,
                errorMessage = errorMessage,
                onDismiss = { viewModel.dismissDialog() },
                onSave = { date, odo, category, desc, workshop, cost, nextKm, nextDate, notes, allowLower ->
                    viewModel.addMaintenance(date, odo, category, desc, workshop, cost, nextKm, nextDate, notes, allowLower) {}
                }
            )
        }
        ActiveDialog.ADD_EXPENSE -> {
            AddExpenseDialog(
                errorMessage = errorMessage,
                onDismiss = { viewModel.dismissDialog() },
                onSave = { date, category, desc, cost, notes ->
                    viewModel.addExpense(date, category, desc, cost, notes) {}
                }
            )
        }
        ActiveDialog.AI_TEXT_INPUT -> {
            AiTextInputDialog(
                isLoading = isLoadingAi,
                errorMessage = errorMessage,
                onDismiss = { viewModel.dismissDialog() },
                onAnalyze = { input -> viewModel.processAiText(input) }
            )
        }
        ActiveDialog.RECEIPT_SCAN -> {
            ReceiptScanDialog(
                isLoading = isLoadingAi,
                errorMessage = errorMessage,
                onDismiss = { viewModel.dismissDialog() },
                onAnalyze = { text -> viewModel.processReceipt(null, text) }
            )
        }
        ActiveDialog.CONFIRM_AI_DATA -> {
            aiParsedData?.let { data ->
                ConfirmAiDataDialog(
                    initialData = data,
                    onDismiss = { viewModel.dismissDialog() },
                    onConfirm = { confirmed -> viewModel.confirmAiRecord(confirmed) }
                )
            }
        }
        ActiveDialog.EDIT_VEHICLE -> {
            vehicle?.let { v ->
                EditVehicleDialog(
                    vehicle = v,
                    onDismiss = { viewModel.dismissDialog() },
                    onSave = { updated -> viewModel.updateVehicle(updated) }
                )
            }
        }
        ActiveDialog.NONE -> {}
    }
}

@Composable
fun QuickActionSheet(
    onDismiss: () -> Unit,
    onSelectOption: (ActiveDialog) -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(8.dp)
                .testTag("quick_action_modal")
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "O que deseja registrar?",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onSurface
                    )
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar", tint = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                QuickActionRowItem(
                    icon = Icons.Default.LocalGasStation,
                    iconColor = Color(0xFF38BDF8),
                    title = "⛽ Abastecimento",
                    subtitle = "Litros, preço, odômetro e consumo",
                    tag = "action_fuel",
                    onClick = { onSelectOption(ActiveDialog.ADD_FUEL) }
                )

                QuickActionRowItem(
                    icon = Icons.Default.Build,
                    iconColor = Color(0xFFFBBF24),
                    title = "🔧 Manutenção",
                    subtitle = "Óleo, filtros, revisão, pneus e oficina",
                    tag = "action_maintenance",
                    onClick = { onSelectOption(ActiveDialog.ADD_MAINTENANCE) }
                )

                QuickActionRowItem(
                    icon = Icons.Default.Payments,
                    iconColor = Color(0xFF34D399),
                    title = "💰 Outro gasto",
                    subtitle = "Lavagem, pedágio, estacionamento, seguro",
                    tag = "action_expense",
                    onClick = { onSelectOption(ActiveDialog.ADD_EXPENSE) }
                )

                QuickActionRowItem(
                    icon = Icons.Default.AutoAwesome,
                    iconColor = Color(0xFFA78BFA),
                    title = "🤖 Registrar com IA",
                    subtitle = "Escreva naturalmente ou fale o que aconteceu",
                    tag = "action_ai_text",
                    onClick = { onSelectOption(ActiveDialog.AI_TEXT_INPUT) }
                )

                QuickActionRowItem(
                    icon = Icons.Default.DocumentScanner,
                    iconColor = Color(0xFFFB923C),
                    title = "🧾 Leitura de Recibo / Cupom",
                    subtitle = "Analise cupons fiscais com Gemini AI",
                    tag = "action_receipt",
                    onClick = { onSelectOption(ActiveDialog.RECEIPT_SCAN) }
                )
            }
        }
    }
}

@Composable
fun QuickActionRowItem(
    icon: ImageVector,
    iconColor: Color,
    title: String,
    subtitle: String,
    tag: String,
    onClick: () -> Unit
) {
    Card(
        shape = RoundedCornerShape(14.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
        modifier = Modifier
            .fillMaxWidth()
            .testTag(tag)
            .clickable { onClick() }
            .border(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.15f), RoundedCornerShape(14.dp))
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(42.dp)
                    .clip(CircleShape)
                    .background(iconColor.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(imageVector = icon, contentDescription = null, tint = iconColor, modifier = Modifier.size(22.dp))
            }
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(text = title, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
                Text(text = subtitle, style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

@Composable
fun AddFuelDialog(
    currentVehicle: Vehicle?,
    errorMessage: String?,
    onDismiss: () -> Unit,
    onSave: (date: String, odo: Int, liters: Double, price: Double, fuelType: String, station: String?, notes: String?, allowLower: Boolean) -> Unit
) {
    val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
    var date by remember { mutableStateOf(today) }
    var odometerStr by remember { mutableStateOf(currentVehicle?.currentOdometer?.toString() ?: "") }
    var litersStr by remember { mutableStateOf("") }
    var priceStr by remember { mutableStateOf("") }
    var fuelType by remember { mutableStateOf(currentVehicle?.fuelType ?: "Gasolina") }
    var station by remember { mutableStateOf("") }
    var notes by remember { mutableStateOf("") }
    var allowLowerOdometer by remember { mutableStateOf(false) }

    val liters = litersStr.replace(",", ".").toDoubleOrNull() ?: 0.0
    val price = priceStr.replace(",", ".").toDoubleOrNull() ?: 0.0
    val totalCalculated = liters * price

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .testTag("dialog_add_fuel")
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Registrar Abastecimento", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = date,
                        onValueChange = { date = it },
                        label = { Text("Data") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = odometerStr,
                        onValueChange = { odometerStr = it },
                        label = { Text("Km atual") },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("input_fuel_odometer"),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = litersStr,
                        onValueChange = { litersStr = it },
                        label = { Text("Litros") },
                        placeholder = { Text("40.0") },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("input_fuel_liters"),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = priceStr,
                        onValueChange = { priceStr = it },
                        label = { Text("Preço / Litro") },
                        placeholder = { Text("5.89") },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("input_fuel_price"),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        singleLine = true
                    )
                }

                // Total calculated display
                Card(
                    shape = RoundedCornerShape(10.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("Valor total calculado:", style = MaterialTheme.typography.bodySmall)
                        Text(
                            text = String.format(Locale.getDefault(), "R$ %.2f", totalCalculated),
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }

                OutlinedTextField(
                    value = station,
                    onValueChange = { station = it },
                    label = { Text("Posto (Opcional)") },
                    placeholder = { Text("Ex: Posto Ipiranga, Shell") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Observação (Opcional)") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                if (errorMessage != null) {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFFEF4444).copy(alpha = 0.1f)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(10.dp)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(Icons.Default.Warning, contentDescription = null, tint = Color(0xFFEF4444), modifier = Modifier.size(18.dp))
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(
                                    text = errorMessage,
                                    color = Color(0xFFEF4444),
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                            if (errorMessage.contains("menor")) {
                                Spacer(modifier = Modifier.height(6.dp))
                                OutlinedButton(
                                    onClick = { allowLowerOdometer = true },
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFEF4444))
                                ) {
                                    Text("Confirmar mesmo assim", style = MaterialTheme.typography.labelMedium)
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(6.dp))

                Button(
                    onClick = {
                        val odo = odometerStr.toIntOrNull() ?: 0
                        onSave(date, odo, liters, price, fuelType, station, notes, allowLowerOdometer)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .testTag("button_save_fuel"),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                ) {
                    Text("Salvar Abastecimento", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun AddMaintenanceDialog(
    currentVehicle: Vehicle?,
    errorMessage: String?,
    onDismiss: () -> Unit,
    onSave: (date: String, odo: Int, category: String, desc: String, workshop: String?, cost: Double, nextKm: Int?, nextDate: String?, notes: String?, allowLower: Boolean) -> Unit
) {
    val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
    var date by remember { mutableStateOf(today) }
    var odometerStr by remember { mutableStateOf(currentVehicle?.currentOdometer?.toString() ?: "") }
    var category by remember { mutableStateOf("Óleo") }
    var description by remember { mutableStateOf("") }
    var workshop by remember { mutableStateOf("") }
    var costStr by remember { mutableStateOf("") }
    var nextKmStr by remember { mutableStateOf("") }
    var nextDate by remember { mutableStateOf("") }
    var notes by remember { mutableStateOf("") }
    var allowLowerOdometer by remember { mutableStateOf(false) }

    val categories = listOf("Óleo", "Filtros", "Pneus", "Freios", "Suspensão", "Motor", "Elétrica", "Revisão", "Outro")
    var catExpanded by remember { mutableStateOf(false) }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .testTag("dialog_add_maintenance")
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Registrar Manutenção", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = date,
                        onValueChange = { date = it },
                        label = { Text("Data") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = odometerStr,
                        onValueChange = { odometerStr = it },
                        label = { Text("Km atual") },
                        modifier = Modifier.weight(1f),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                }

                Box(modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = category,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Categoria") },
                        trailingIcon = {
                            Icon(Icons.Default.KeyboardArrowDown, contentDescription = null, modifier = Modifier.clickable { catExpanded = !catExpanded })
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { catExpanded = true }
                    )
                    DropdownMenu(expanded = catExpanded, onDismissRequest = { catExpanded = false }) {
                        categories.forEach { c ->
                            DropdownMenuItem(text = { Text(c) }, onClick = { category = c; catExpanded = false })
                        }
                    }
                }

                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Descrição do Serviço") },
                    placeholder = { Text("Ex: Troca de óleo 5W30 e filtro") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("input_maint_desc"),
                    singleLine = true
                )

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = costStr,
                        onValueChange = { costStr = it },
                        label = { Text("Valor (R$)") },
                        placeholder = { Text("350.00") },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("input_maint_cost"),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = workshop,
                        onValueChange = { workshop = it },
                        label = { Text("Oficina") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                }

                Text("Previsão da Próxima Manutenção", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = nextKmStr,
                        onValueChange = { nextKmStr = it },
                        label = { Text("Próximo Km") },
                        placeholder = { Text("Ex: 82430") },
                        modifier = Modifier.weight(1f),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = nextDate,
                        onValueChange = { nextDate = it },
                        label = { Text("Próxima Data") },
                        placeholder = { Text("YYYY-MM-DD") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                }

                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Observação") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                if (errorMessage != null) {
                    Text(text = errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }

                Button(
                    onClick = {
                        val odo = odometerStr.toIntOrNull() ?: 0
                        val cost = costStr.replace(",", ".").toDoubleOrNull() ?: 0.0
                        val nextKm = nextKmStr.toIntOrNull()
                        onSave(date, odo, category, description, workshop, cost, nextKm, nextDate, notes, allowLowerOdometer)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .testTag("button_save_maintenance"),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("Salvar Manutenção", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun AddExpenseDialog(
    errorMessage: String?,
    onDismiss: () -> Unit,
    onSave: (date: String, category: String, desc: String, cost: Double, notes: String?) -> Unit
) {
    val today = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
    var date by remember { mutableStateOf(today) }
    var category by remember { mutableStateOf("lavagem") }
    var description by remember { mutableStateOf("") }
    var costStr by remember { mutableStateOf("") }
    var notes by remember { mutableStateOf("") }

    val categories = listOf("lavagem", "estacionamento", "pedágio", "seguro", "documentação", "acessórios", "outros")
    var catExpanded by remember { mutableStateOf(false) }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .testTag("dialog_add_expense")
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Registrar Outro Gasto", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = date,
                        onValueChange = { date = it },
                        label = { Text("Data") },
                        modifier = Modifier.weight(1f),
                        singleLine = true
                    )
                    OutlinedTextField(
                        value = costStr,
                        onValueChange = { costStr = it },
                        label = { Text("Valor (R$)") },
                        placeholder = { Text("65.00") },
                        modifier = Modifier
                            .weight(1f)
                            .testTag("input_expense_cost"),
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal),
                        singleLine = true
                    )
                }

                Box(modifier = Modifier.fillMaxWidth()) {
                    OutlinedTextField(
                        value = category.replaceFirstChar { it.uppercase() },
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Categoria") },
                        trailingIcon = {
                            Icon(Icons.Default.KeyboardArrowDown, contentDescription = null, modifier = Modifier.clickable { catExpanded = !catExpanded })
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable { catExpanded = true }
                    )
                    DropdownMenu(expanded = catExpanded, onDismissRequest = { catExpanded = false }) {
                        categories.forEach { c ->
                            DropdownMenuItem(text = { Text(c.replaceFirstChar { it.uppercase() }) }, onClick = { category = c; catExpanded = false })
                        }
                    }
                }

                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    label = { Text("Descrição") },
                    placeholder = { Text("Ex: Lavagem completa com cera") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .testTag("input_expense_desc"),
                    singleLine = true
                )

                OutlinedTextField(
                    value = notes,
                    onValueChange = { notes = it },
                    label = { Text("Observação") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                if (errorMessage != null) {
                    Text(text = errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }

                Button(
                    onClick = {
                        val cost = costStr.replace(",", ".").toDoubleOrNull() ?: 0.0
                        onSave(date, category, description, cost, notes)
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .testTag("button_save_expense"),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text("Salvar Gasto", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
fun AiTextInputDialog(
    isLoading: Boolean,
    errorMessage: String?,
    onDismiss: () -> Unit,
    onAnalyze: (String) -> Unit
) {
    var textInput by remember { mutableStateOf("") }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .testTag("dialog_ai_text")
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.AutoAwesome, contentDescription = null, tint = Color(0xFFA78BFA))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Registrar com IA", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    }
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                Text(
                    text = "Escreva naturalmente o que aconteceu e o Gemini irá estruturar os dados para você conferir antes de salvar.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                OutlinedTextField(
                    value = textInput,
                    onValueChange = { textInput = it },
                    label = { Text("O que aconteceu?") },
                    placeholder = { Text("Ex: Abasteci hoje. Foram 40 litros de gasolina a 6,19 e o carro estava com 72.430 km.") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(110.dp)
                        .testTag("input_ai_text"),
                    maxLines = 4
                )

                // Quick chips
                Text("Exemplos rápidos:", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedButton(
                        onClick = { textInput = "Abasteci hoje. Foram 40 litros de gasolina a 6,19 e o carro estava com 72.430 km." },
                        modifier = Modifier.weight(1f),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 4.dp, vertical = 2.dp)
                    ) {
                        Text("Abastecimento", fontSize = 11.sp)
                    }
                    OutlinedButton(
                        onClick = { textInput = "Fiz troca de óleo hoje aos 73 mil km e paguei 380 reais." },
                        modifier = Modifier.weight(1f),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 4.dp, vertical = 2.dp)
                    ) {
                        Text("Óleo 73k km", fontSize = 11.sp)
                    }
                    OutlinedButton(
                        onClick = { textInput = "Fiz lavagem completa hoje por 60 reais." },
                        modifier = Modifier.weight(1f),
                        contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 4.dp, vertical = 2.dp)
                    ) {
                        Text("Lavagem", fontSize = 11.sp)
                    }
                }

                if (errorMessage != null) {
                    Text(text = errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }

                Button(
                    onClick = { onAnalyze(textInput) },
                    enabled = !isLoading && textInput.isNotBlank(),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .testTag("button_analyze_ai"),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFA78BFA))
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White)
                    } else {
                        Text("Analisar com IA", fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            }
        }
    }
}

@Composable
fun ReceiptScanDialog(
    isLoading: Boolean,
    errorMessage: String?,
    onDismiss: () -> Unit,
    onAnalyze: (String) -> Unit
) {
    var receiptText by remember { mutableStateOf("") }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .testTag("dialog_receipt_scan")
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.DocumentScanner, contentDescription = null, tint = Color(0xFFFB923C))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Leitura de Recibo", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    }
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                Text(
                    text = "O Gemini extrai os dados do comprovante. Cole o texto do recibo ou use os dados de teste para ver a extração:",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                OutlinedTextField(
                    value = receiptText,
                    onValueChange = { receiptText = it },
                    label = { Text("Texto ou dados do cupom fiscal") },
                    placeholder = { Text("Ex: POSTO SHELL - 02/09/2026 - GASOLINA ADITIVADA 40,000L x R$ 6,19 = TOTAL R$ 247,60 - KM 72430") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(110.dp)
                        .testTag("input_receipt_text"),
                    maxLines = 4
                )

                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    OutlinedButton(
                        onClick = { receiptText = "POSTO SHELL 02/09/2026 - GASOLINA 40,00 L x 6,19 - TOTAL R$ 247,60 - ODÔMETRO: 72.430 KM" },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Recibo Posto", fontSize = 11.sp)
                    }
                    OutlinedButton(
                        onClick = { receiptText = "OFICINA AUTO TECH 02/09/2026 - TROCA DE ÓLEO SINTÉTICO 5W30 - TOTAL R$ 380,00 - KM 73000" },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Recibo Oficina", fontSize = 11.sp)
                    }
                }

                if (errorMessage != null) {
                    Text(text = errorMessage, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                }

                Button(
                    onClick = { onAnalyze(receiptText) },
                    enabled = !isLoading && receiptText.isNotBlank(),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(48.dp)
                        .testTag("button_analyze_receipt"),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFB923C))
                ) {
                    if (isLoading) {
                        CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color.White)
                    } else {
                        Text("Analisar Recibo", fontWeight = FontWeight.Bold, color = Color.White)
                    }
                }
            }
        }
    }
}

@Composable
fun ConfirmAiDataDialog(
    initialData: AiParsedData,
    onDismiss: () -> Unit,
    onConfirm: (AiParsedData) -> Unit
) {
    var editableData by remember { mutableStateOf(initialData) }
    var isEditing by remember { mutableStateOf(false) }

    var date by remember { mutableStateOf(editableData.date ?: "") }
    var odoStr by remember { mutableStateOf(editableData.odometer?.toString() ?: "") }
    var litersStr by remember { mutableStateOf(editableData.liters?.toString() ?: "") }
    var priceStr by remember { mutableStateOf(editableData.pricePerLiter?.toString() ?: "") }
    var totalCostStr by remember { mutableStateOf(editableData.totalCost?.toString() ?: "") }
    var fuelType by remember { mutableStateOf(editableData.fuelType ?: "Gasolina") }
    var desc by remember { mutableStateOf(editableData.description ?: "") }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
                .testTag("dialog_confirm_ai_data")
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Confira os dados", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                Text(
                    text = "A IA interpretou os seguintes dados. Revise antes de confirmar:",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                if (!isEditing) {
                    // Visual confirmation card
                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.4f)),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(14.dp),
                            verticalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            DataConfirmationRow("Tipo de Registro", editableData.type.replaceFirstChar { it.uppercase() })
                            DataConfirmationRow("Data", editableData.date ?: "Não identificada")
                            if (editableData.totalCost != null) {
                                DataConfirmationRow("Valor Total", String.format(Locale.getDefault(), "R$ %.2f", editableData.totalCost))
                            }
                            if (editableData.liters != null) {
                                DataConfirmationRow("Litros", "${editableData.liters} L")
                            }
                            if (editableData.pricePerLiter != null) {
                                DataConfirmationRow("Preço por Litro", String.format(Locale.getDefault(), "R$ %.2f", editableData.pricePerLiter))
                            }
                            if (editableData.fuelType != null) {
                                DataConfirmationRow("Combustível", editableData.fuelType ?: "")
                            }
                            if (editableData.odometer != null) {
                                DataConfirmationRow("Quilometragem", "${editableData.odometer} km")
                            }
                            if (!editableData.description.isNullOrBlank()) {
                                DataConfirmationRow("Descrição", editableData.description ?: "")
                            }
                        }
                    }
                } else {
                    // Inline editor
                    OutlinedTextField(value = date, onValueChange = { date = it }, label = { Text("Data") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(value = totalCostStr, onValueChange = { totalCostStr = it }, label = { Text("Valor Total (R$)") }, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(value = odoStr, onValueChange = { odoStr = it }, label = { Text("Km") }, modifier = Modifier.fillMaxWidth())
                    if (editableData.type == "fuel") {
                        OutlinedTextField(value = litersStr, onValueChange = { litersStr = it }, label = { Text("Litros") }, modifier = Modifier.fillMaxWidth())
                        OutlinedTextField(value = priceStr, onValueChange = { priceStr = it }, label = { Text("Preço / L") }, modifier = Modifier.fillMaxWidth())
                    } else {
                        OutlinedTextField(value = desc, onValueChange = { desc = it }, label = { Text("Descrição") }, modifier = Modifier.fillMaxWidth())
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    OutlinedButton(
                        onClick = {
                            if (isEditing) {
                                editableData = editableData.copy(
                                    date = date.ifBlank { null },
                                    totalCost = totalCostStr.replace(",", ".").toDoubleOrNull(),
                                    odometer = odoStr.toIntOrNull(),
                                    liters = litersStr.replace(",", ".").toDoubleOrNull(),
                                    pricePerLiter = priceStr.replace(",", ".").toDoubleOrNull(),
                                    description = desc.ifBlank { null }
                                )
                                isEditing = false
                            } else {
                                isEditing = true
                            }
                        },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text(if (isEditing) "Concluir" else "Editar")
                    }

                    Button(
                        onClick = {
                            val finalData = if (isEditing) {
                                editableData.copy(
                                    date = date.ifBlank { null },
                                    totalCost = totalCostStr.replace(",", ".").toDoubleOrNull(),
                                    odometer = odoStr.toIntOrNull(),
                                    liters = litersStr.replace(",", ".").toDoubleOrNull(),
                                    pricePerLiter = priceStr.replace(",", ".").toDoubleOrNull(),
                                    description = desc.ifBlank { null }
                                )
                            } else editableData
                            onConfirm(finalData)
                        },
                        modifier = Modifier
                            .weight(1.3f)
                            .testTag("button_confirm_ai_data"),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Text("Confirmar", fontWeight = FontWeight.Bold)
                    }
                }
            }
        }
    }
}

@Composable
private fun DataConfirmationRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(text = label, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        Text(text = value, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface)
    }
}

@Composable
fun EditVehicleDialog(
    vehicle: Vehicle,
    onDismiss: () -> Unit,
    onSave: (Vehicle) -> Unit
) {
    var brand by remember { mutableStateOf(vehicle.brand) }
    var model by remember { mutableStateOf(vehicle.model) }
    var yearStr by remember { mutableStateOf(vehicle.year.toString()) }
    var odoStr by remember { mutableStateOf(vehicle.currentOdometer.toString()) }
    var fuelType by remember { mutableStateOf(vehicle.fuelType) }
    var plate by remember { mutableStateOf(vehicle.licensePlate ?: "") }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp)
        ) {
            Column(
                modifier = Modifier
                    .padding(20.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Editar Meu Carro", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.Bold)
                    IconButton(onClick = onDismiss, modifier = Modifier.size(28.dp)) {
                        Icon(Icons.Default.Close, contentDescription = "Fechar")
                    }
                }

                OutlinedTextField(value = brand, onValueChange = { brand = it }, label = { Text("Marca") }, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(value = model, onValueChange = { model = it }, label = { Text("Modelo") }, modifier = Modifier.fillMaxWidth())
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = yearStr, onValueChange = { yearStr = it }, label = { Text("Ano") }, modifier = Modifier.weight(1f))
                    OutlinedTextField(value = odoStr, onValueChange = { odoStr = it }, label = { Text("Km") }, modifier = Modifier.weight(1.2f))
                }
                OutlinedTextField(value = plate, onValueChange = { plate = it }, label = { Text("Placa (Privada)") }, modifier = Modifier.fillMaxWidth())

                Button(
                    onClick = {
                        val year = yearStr.toIntOrNull() ?: vehicle.year
                        val odo = odoStr.toIntOrNull() ?: vehicle.currentOdometer
                        onSave(vehicle.copy(brand = brand, model = model, year = year, currentOdometer = odo, fuelType = fuelType, licensePlate = plate.ifBlank { null }))
                    },
                    modifier = Modifier.fillMaxWidth().height(48.dp)
                ) {
                    Text("Atualizar Dados", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
