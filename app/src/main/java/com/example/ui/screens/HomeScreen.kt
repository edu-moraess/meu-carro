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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.LocalGasStation
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material.icons.filled.Speed
import androidx.compose.material.icons.filled.TrendingUp
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.data.model.Vehicle
import com.example.ui.components.ActivityItemRow
import com.example.ui.components.MetricCard
import com.example.ui.components.SectionHeader
import com.example.ui.viewmodel.ActiveDialog
import com.example.ui.viewmodel.CarViewModel
import java.text.NumberFormat
import java.util.Locale

@Composable
fun HomeScreen(viewModel: CarViewModel) {
    val vehicle by viewModel.vehicle.collectAsState()
    val dashboard by viewModel.dashboard.collectAsState()

    val currentVehicle = vehicle ?: return

    val formatter = NumberFormat.getNumberInstance(Locale("pt", "BR"))

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .background(MaterialTheme.colorScheme.background)
            .padding(horizontal = 16.dp)
            .testTag("home_screen"),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Top Header - Meu Carro
        item {
            Spacer(modifier = Modifier.height(8.dp))
            Card(
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.2f), RoundedCornerShape(20.dp))
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(48.dp)
                                .clip(CircleShape)
                                .background(MaterialTheme.colorScheme.primary.copy(alpha = 0.15f)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.DirectionsCar,
                                contentDescription = null,
                                tint = MaterialTheme.colorScheme.primary,
                                modifier = Modifier.size(28.dp)
                            )
                        }
                        Spacer(modifier = Modifier.width(12.dp))
                        Column {
                            Text(
                                text = "Meu carro",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = "${currentVehicle.brand} ${currentVehicle.model} ${currentVehicle.year}",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = MaterialTheme.colorScheme.onSurface
                            )
                            Text(
                                text = "${formatter.format(currentVehicle.currentOdometer)} km",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.primary,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }

                    IconButton(
                        onClick = { viewModel.openDialog(ActiveDialog.EDIT_VEHICLE) },
                        modifier = Modifier.testTag("button_edit_vehicle")
                    ) {
                        Icon(
                            imageVector = Icons.Default.Edit,
                            contentDescription = "Editar veículo",
                            tint = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }

        // 4 Main Metric Cards (Gastos este mês, Consumo médio, Custo por km, Próxima manutenção)
        item {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    val monthExp = dashboard?.monthExpenses ?: 0.0
                    MetricCard(
                        title = "Gastos este mês",
                        value = String.format(Locale.getDefault(), "R$ %.2f", monthExp),
                        subtitle = "Combustível, manutenção e outros",
                        icon = Icons.Default.Payments,
                        accentColor = Color(0xFF38BDF8),
                        modifier = Modifier.weight(1f),
                        onClick = { viewModel.selectTab(3) }
                    )

                    val avgCons = dashboard?.averageConsumption
                    MetricCard(
                        title = "Consumo médio",
                        value = if (avgCons != null) "${String.format(Locale.getDefault(), "%.1f", avgCons)} km/L" else "--",
                        subtitle = if (avgCons != null) "Cálculo real de abastecimentos" else "Dados insuficientes",
                        icon = Icons.Default.LocalGasStation,
                        accentColor = Color(0xFF34D399),
                        modifier = Modifier.weight(1f),
                        onClick = { viewModel.selectTab(1) }
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    val costPerKm = dashboard?.costPerKm
                    MetricCard(
                        title = "Custo por km",
                        value = if (costPerKm != null) String.format(Locale.getDefault(), "R$ %.2f", costPerKm) else "--",
                        subtitle = "Gasto médio rodado",
                        icon = Icons.Default.Speed,
                        accentColor = Color(0xFFA78BFA),
                        modifier = Modifier.weight(1f)
                    )

                    val nextMaintKm = dashboard?.nextMaintenanceKmRemaining
                    MetricCard(
                        title = "Próx. manutenção",
                        value = if (nextMaintKm != null) "${formatter.format(nextMaintKm)} km" else "--",
                        subtitle = dashboard?.nextMaintenanceTitle ?: "Sem agendamentos",
                        icon = Icons.Default.Build,
                        accentColor = Color(0xFFFBBF24),
                        modifier = Modifier.weight(1f),
                        onClick = { viewModel.selectTab(2) }
                    )
                }
            }
        }

        // Seção Resumo
        item {
            val monthExp = dashboard?.monthExpenses ?: 0.0
            val fuelPct = dashboard?.fuelExpensePercentage ?: 0.0

            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.2f), RoundedCornerShape(16.dp))
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Default.TrendingUp,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Resumo do Mês",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurface
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = if (monthExp > 0) {
                            "Você gastou ${String.format(Locale.getDefault(), "R$ %.2f", monthExp)} este mês. Combustível representa ${fuelPct.toInt()}% dos seus gastos."
                        } else {
                            "Nenhum gasto registrado neste mês ainda. Toque em '+ Registrar' para começar."
                        },
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        lineHeight = 20.sp
                    )
                }
            }
        }

        // Seção Insights
        item {
            val insights = dashboard?.insights ?: emptyList()
            if (insights.isNotEmpty()) {
                Column {
                    SectionHeader(title = "Insights")
                    insights.forEach { insight ->
                        Card(
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 3.dp)
                                .border(1.dp, MaterialTheme.colorScheme.outline.copy(alpha = 0.15f), RoundedCornerShape(12.dp))
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Box(
                                    modifier = Modifier
                                        .size(32.dp)
                                        .clip(CircleShape)
                                        .background(Color(0xFF818CF8).copy(alpha = 0.15f)),
                                    contentAlignment = Alignment.Center
                                ) {
                                    Icon(
                                        imageVector = Icons.Default.AutoAwesome,
                                        contentDescription = null,
                                        tint = Color(0xFF818CF8),
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                                Spacer(modifier = Modifier.width(10.dp))
                                Text(
                                    text = insight,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurface,
                                    modifier = Modifier.weight(1f)
                                )
                            }
                        }
                    }
                }
            }
        }

        // Seção Últimas Atividades
        item {
            val activities = dashboard?.recentActivities ?: emptyList()
            SectionHeader(
                title = "Últimas atividades",
                actionText = if (activities.isNotEmpty()) "Ver todas" else null,
                onAction = { viewModel.selectTab(3) }
            )
            if (activities.isEmpty()) {
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Icon(
                            imageVector = Icons.Default.Info,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f),
                            modifier = Modifier.size(32.dp)
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Nenhuma atividade registrada",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }

        val activities = dashboard?.recentActivities ?: emptyList()
        items(activities, key = { "${it.type}_${it.id}" }) { activity ->
            ActivityItemRow(activity = activity)
        }

        item {
            Spacer(modifier = Modifier.height(72.dp))
        }
    }
}
