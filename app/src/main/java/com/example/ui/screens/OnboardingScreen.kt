package com.example.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.KeyboardArrowDown
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.viewmodel.CarViewModel

@Composable
fun OnboardingScreen(viewModel: CarViewModel) {
    var brand by remember { mutableStateOf("") }
    var model by remember { mutableStateOf("") }
    var yearStr by remember { mutableStateOf("2022") }
    var odometerStr by remember { mutableStateOf("72430") }
    var fuelType by remember { mutableStateOf("Flex") }
    var licensePlate by remember { mutableStateOf("") }

    var fuelExpanded by remember { mutableStateOf(false) }
    val fuelOptions = listOf("Gasolina", "Etanol", "Diesel", "Flex", "Elétrico", "Híbrido")

    var formError by remember { mutableStateOf<String?>(null) }

    val scrollState = rememberScrollState()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 24.dp)
            .verticalScroll(scrollState),
        contentAlignment = Alignment.TopCenter
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(modifier = Modifier.height(16.dp))
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .clip(CircleShape)
                    .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.DirectionsCar,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.primary,
                    modifier = Modifier.size(36.dp)
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            Text(
                text = "Cadastre seu carro",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )

            Text(
                text = "Acompanhe abastecimentos, manutenções e custos em um só lugar.",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(top = 6.dp, bottom = 24.dp)
            )

            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.2f), RoundedCornerShape(20.dp))
            ) {
                Column(
                    modifier = Modifier.padding(20.dp),
                    verticalArrangement = Arrangement.spacedBy(14.dp)
                ) {
                    OutlinedTextField(
                        value = brand,
                        onValueChange = { brand = it; formError = null },
                        label = { Text("Marca") },
                        placeholder = { Text("Ex: Honda, Toyota, VW") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("input_brand"),
                        singleLine = true
                    )

                    OutlinedTextField(
                        value = model,
                        onValueChange = { model = it; formError = null },
                        label = { Text("Modelo") },
                        placeholder = { Text("Ex: Civic, Corolla, Polo") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("input_model"),
                        singleLine = true
                    )

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        OutlinedTextField(
                            value = yearStr,
                            onValueChange = { yearStr = it; formError = null },
                            label = { Text("Ano") },
                            modifier = Modifier
                                .weight(1f)
                                .testTag("input_year"),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            singleLine = true
                        )

                        OutlinedTextField(
                            value = odometerStr,
                            onValueChange = { odometerStr = it; formError = null },
                            label = { Text("Km atual") },
                            modifier = Modifier
                                .weight(1.2f)
                                .testTag("input_odometer"),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                            singleLine = true
                        )
                    }

                    // Combustível Dropdown
                    Box(modifier = Modifier.fillMaxWidth()) {
                        OutlinedTextField(
                            value = fuelType,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Combustível") },
                            trailingIcon = {
                                Icon(
                                    imageVector = Icons.Default.KeyboardArrowDown,
                                    contentDescription = null,
                                    modifier = Modifier.clickable { fuelExpanded = !fuelExpanded }
                                )
                            },
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { fuelExpanded = true }
                                .testTag("input_fuel_type")
                        )

                        DropdownMenu(
                            expanded = fuelExpanded,
                            onDismissRequest = { fuelExpanded = false }
                        ) {
                            fuelOptions.forEach { opt ->
                                DropdownMenuItem(
                                    text = { Text(opt) },
                                    onClick = {
                                        fuelType = opt
                                        fuelExpanded = false
                                    }
                                )
                            }
                        }
                    }

                    // Placa opcional
                    OutlinedTextField(
                        value = licensePlate,
                        onValueChange = { licensePlate = it },
                        label = { Text("Placa (Opcional - Dado privado)") },
                        placeholder = { Text("Ex: ABC-1D23") },
                        trailingIcon = {
                            Icon(
                                imageVector = Icons.Default.Lock,
                                contentDescription = "Privado",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                                modifier = Modifier.size(18.dp)
                            )
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .testTag("input_plate"),
                        singleLine = true
                    )

                    if (formError != null) {
                        Text(
                            text = formError ?: "",
                            color = MaterialTheme.colorScheme.error,
                            style = MaterialTheme.typography.bodySmall
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    Button(
                        onClick = {
                            val year = yearStr.toIntOrNull()
                            val odo = odometerStr.toIntOrNull()
                            if (brand.isBlank()) {
                                formError = "Por favor, informe a marca do veículo."
                            } else if (model.isBlank()) {
                                formError = "Por favor, informe o modelo do veículo."
                            } else if (year == null || year < 1920 || year > 2035) {
                                formError = "Informe um ano de fabricação válido."
                            } else if (odo == null || odo < 0) {
                                formError = "Informe uma quilometragem inicial válida."
                            } else {
                                viewModel.registerVehicle(brand, model, year, odo, fuelType, licensePlate)
                            }
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(52.dp)
                            .testTag("button_continue"),
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.primary)
                    ) {
                        Text(
                            text = "Continuar",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                    }
                }
            }
        }
    }
}
