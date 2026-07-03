package com.cavesketch.app.ui

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class AboutScreenTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun version_line_is_formatted() {
        assertEquals("Version 1.0.0", aboutVersionLine("1.0.0"))
    }

    @Test
    fun version_line_handles_blank() {
        assertEquals("Version unknown", aboutVersionLine(""))
    }

    @Test
    fun testAboutScreen_userGuideAccordion() {
        composeTestRule.setContent {
            AboutScreen(versionName = "1.0.0")
        }

        // Verify User Guide header exists
        composeTestRule.onNodeWithText("User Guide").assertExists()

        // Click the header to expand
        composeTestRule.onNodeWithText("User Guide").performClick()
        composeTestRule.waitForIdle()

        // Verify English helper text exists
        composeTestRule.onNodeWithText("💡 Use two fingers to scroll the guide content").assertExists()

        // Toggle language to Italian
        composeTestRule.onNodeWithText("🇮🇹").performClick()
        composeTestRule.waitForIdle()
        
        // After clicking Italian flag, the header text should localize to "Guida Utente"
        composeTestRule.onNodeWithText("Guida Utente").assertExists()

        // Verify Italian helper text exists
        composeTestRule.onNodeWithText("💡 Usa due dita per scorrere la guida").assertExists()
    }
}
