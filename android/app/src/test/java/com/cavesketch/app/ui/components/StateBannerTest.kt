package com.cavesketch.app.ui.components

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class StateBannerTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_idle_message() {
        composeTestRule.setContent {
            StateBanner("Pick your files and tap Generate", isError = false)
        }
        composeTestRule.onNodeWithText("Pick your files and tap Generate").assertExists()
    }

    @Test
    fun renders_error_message() {
        composeTestRule.setContent {
            StateBanner("Something went wrong", isError = true)
        }
        composeTestRule.onNodeWithText("Something went wrong").assertExists()
    }
}
