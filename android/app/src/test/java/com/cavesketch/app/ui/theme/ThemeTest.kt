package com.cavesketch.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class ThemeTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun theme_uses_dark_cyan_amber_palette() {
        var background = Color.Unspecified
        var primary = Color.Unspecified
        var secondary = Color.Unspecified
        var surface = Color.Unspecified
        composeTestRule.setContent {
            CaveSketchTheme {
                background = MaterialTheme.colorScheme.background
                primary = MaterialTheme.colorScheme.primary
                secondary = MaterialTheme.colorScheme.secondary
                surface = MaterialTheme.colorScheme.surface
            }
        }
        assertEquals(CaveBackground, background)
        assertEquals(CaveCyan, primary)
        assertEquals(CaveAmber, secondary)
        assertEquals(CaveSurface, surface)
    }
}
