package com.example

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels
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
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.DirectionsCar
import androidx.compose.material.icons.filled.LocalGasStation
import androidx.compose.material.icons.filled.Payments
import androidx.compose.material3.Icon
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.ui.screens.AppDialogsHost
import com.example.ui.screens.ExpensesScreen
import com.example.ui.screens.FuelScreen
import com.example.ui.screens.HomeScreen
import com.example.ui.screens.MaintenanceScreen
import com.example.ui.screens.OnboardingScreen
import com.example.ui.theme.DarkBackground
import com.example.ui.theme.DarkBorder
import com.example.ui.theme.DarkSurface
import com.example.ui.theme.MyApplicationTheme
import com.example.ui.theme.TealAccent
import com.example.ui.theme.TextSecondary
import com.example.ui.viewmodel.ActiveDialog
import com.example.ui.viewmodel.CarViewModel

class MainActivity : ComponentActivity() {

    private val viewModel: CarViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MyApplicationTheme {
                MeuCarroApp(viewModel = viewModel)
            }
        }
    }
}

@Composable
fun MeuCarroApp(viewModel: CarViewModel) {
    val vehicle by viewModel.vehicle.collectAsState()
    val selectedTab by viewModel.selectedTab.collectAsState()

    if (vehicle == null) {
        OnboardingScreen(viewModel = viewModel)
        return
    }

    Scaffold(
        modifier = Modifier.fillMaxSize().background(DarkBackground),
        containerColor = DarkBackground,
        bottomBar = {
            SophisticatedBottomBar(
                selectedTab = selectedTab,
                onTabSelected = { viewModel.selectTab(it) },
                onQuickAction = { viewModel.openDialog(ActiveDialog.QUICK_ACTION) }
            )
        }
    ) { innerPadding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .padding(bottom = innerPadding.calculateBottomPadding())
        ) {
            when (selectedTab) {
                0 -> HomeScreen(viewModel = viewModel)
                1 -> FuelScreen(viewModel = viewModel)
                2 -> MaintenanceScreen(viewModel = viewModel)
                3 -> ExpensesScreen(viewModel = viewModel)
            }
        }
    }

    AppDialogsHost(viewModel = viewModel)
}

@Composable
fun SophisticatedBottomBar(
    selectedTab: Int,
    onTabSelected: (Int) -> Unit,
    onQuickAction: () -> Unit
) {
    Surface(
        color = DarkSurface,
        modifier = Modifier
            .fillMaxWidth()
            .border(width = 1.dp, color = DarkBorder)
            .navigationBarsPadding(),
        tonalElevation = 8.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(68.dp)
                .padding(horizontal = 8.dp),
            horizontalArrangement = Arrangement.SpaceAround,
            verticalAlignment = Alignment.CenterVertically
        ) {
            NavTabItem("Início", Icons.Default.DirectionsCar, selectedTab == 0, "nav_tab_home") { onTabSelected(0) }
            NavTabItem("Combustível", Icons.Default.LocalGasStation, selectedTab == 1, "nav_tab_fuel") { onTabSelected(1) }

            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(CircleShape)
                    .background(TealAccent)
                    .clickable { onQuickAction() }
                    .testTag("nav_quick_action"),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = Icons.Default.Add,
                    contentDescription = "Ação rápida",
                    tint = Color(0xFF111111),
                    modifier = Modifier.size(26.dp)
                )
            }

            NavTabItem("Manutenção", Icons.Default.Build, selectedTab == 2, "nav_tab_maintenance") { onTabSelected(2) }
            NavTabItem("Gastos", Icons.Default.Payments, selectedTab == 3, "nav_tab_expenses") { onTabSelected(3) }
        }
    }
}

@Composable
private fun NavTabItem(
    title: String,
    icon: ImageVector,
    isSelected: Boolean,
    testTag: String,
    onClick: () -> Unit
) {
    Column(
        modifier = Modifier
            .clip(RoundedCornerShape(12.dp))
            .clickable { onClick() }
            .padding(horizontal = 10.dp, vertical = 6.dp)
            .testTag(testTag),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            imageVector = icon,
            contentDescription = title,
            tint = if (isSelected) TealAccent else TextSecondary,
            modifier = Modifier.size(22.dp)
        )
        Spacer(modifier = Modifier.height(3.dp))
        Text(
            text = title,
            fontSize = 11.sp,
            fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
            color = if (isSelected) TealAccent else TextSecondary
        )
    }
}
