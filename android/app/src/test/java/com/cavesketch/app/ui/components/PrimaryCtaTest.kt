package com.cavesketch.app.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Assert.assertTrue
import org.junit.Assert.assertFalse
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class PrimaryCtaTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_label_and_invokes_click_when_enabled() {
        var clicked = false
        composeTestRule.setContent {
            PrimaryCta("Generate Survey Plot", Icons.Filled.PlayArrow, enabled = true) { clicked = true }
        }
        composeTestRule.onNodeWithText("Generate Survey Plot").assertExists()
        composeTestRule.onNodeWithText("Generate Survey Plot").performClick()
        assertTrue(clicked)
    }

    @Test
    fun does_not_invoke_click_when_disabled() {
        var clicked = false
        composeTestRule.setContent {
            PrimaryCta("Generate Survey Plot", Icons.Filled.PlayArrow, enabled = false) { clicked = true }
        }
        composeTestRule.onNodeWithText("Generate Survey Plot").assertIsNotEnabled()
        composeTestRule.onNodeWithText("Generate Survey Plot").performClick()
        assertFalse(clicked)
    }
}
