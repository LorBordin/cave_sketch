package com.cavesketch.app.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Text
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class SectionCardTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_title_and_content() {
        composeTestRule.setContent {
            SectionCard("Input files", Icons.Filled.Settings) {
                Text("inner content")
            }
        }
        composeTestRule.onNodeWithText("Input files").assertExists()
        composeTestRule.onNodeWithText("inner content").assertExists()
    }
}
