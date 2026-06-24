package com.cavesketch.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val CaveDarkColors = darkColorScheme(
    primary = CaveCyan,
    onPrimary = CaveOnCyan,
    secondary = CaveAmber,
    onSecondary = CaveOnAmber,
    background = CaveBackground,
    onBackground = CaveOnSurface,
    surface = CaveSurface,
    onSurface = CaveOnSurface,
    surfaceVariant = CaveSurfaceVariant,
    onSurfaceVariant = CaveOnSurfaceVariant,
    outline = CaveOutline,
    error = CaveError,
    onError = CaveOnError,
)

@Composable
fun CaveSketchTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = CaveDarkColors, content = content)
}
