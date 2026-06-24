package com.cavesketch.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = BrandCyan,
    onPrimary = Color_White,
    secondary = BrandSlate,
    background = BrandBackground,
    surface = Color_White,
)

private val DarkColors = darkColorScheme(
    primary = BrandCyan,
    secondary = BrandSlateLight,
)

@Composable
fun CaveSketchTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}
