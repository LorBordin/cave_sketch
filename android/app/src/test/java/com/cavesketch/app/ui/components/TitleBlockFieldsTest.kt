package com.cavesketch.app.ui.components

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performTextInput
import com.cavesketch.app.ui.SurveyInputs
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class TitleBlockFieldsTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun typing_updates_inputs() {
        var latest = SurveyInputs()
        composeTestRule.setContent { TitleBlockFields(latest) { latest = it } }
        composeTestRule.onNodeWithTag("drawer_field").performTextInput("Bob")
        assertEquals("Bob", latest.drawerName)
        composeTestRule.onNodeWithTag("latitude_field").performTextInput("43,4")
        assertEquals("43,4", latest.latitude)
    }

    @Test
    fun shows_error_when_only_latitude_entered() {
        composeTestRule.setContent { TitleBlockFields(SurveyInputs(latitude = "43.4")) {} }
        composeTestRule.onNodeWithTag("title_block_error").assertExists()
    }

    @Test
    fun no_error_for_valid_inputs() {
        composeTestRule.setContent {
            TitleBlockFields(SurveyInputs(latitude = "43.4", longitude = "12.9")) {}
        }
        composeTestRule.onNodeWithTag("title_block_error").assertDoesNotExist()
    }
}
