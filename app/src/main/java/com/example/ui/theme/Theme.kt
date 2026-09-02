package com.example.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val SophisticatedDarkColorScheme = darkColorScheme(
    primary = TealAccent,
    onPrimary = DarkBackground,
    primaryContainer = TealContainer,
    onPrimaryContainer = TealAccent,
    secondary = PurpleAccent,
    onSecondary = OnPurple,
    secondaryContainer = PurpleContainer,
    onSecondaryContainer = PurpleAccent,
    background = DarkBackground,
    onBackground = TextPrimary,
    surface = DarkSurface,
    onSurface = TextPrimary,
    surfaceVariant = DarkSurfaceVariant,
    onSurfaceVariant = TextSecondary,
    outline = DarkBorder,
    error = AlertRed,
    onError = DarkBackground,
    errorContainer = AlertRedContainer,
    onErrorContainer = AlertRed
)

@Composable
fun MyApplicationTheme(
    darkTheme: Boolean = true,
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = SophisticatedDarkColorScheme,
        typography = Typography,
        content = content
    )
}
