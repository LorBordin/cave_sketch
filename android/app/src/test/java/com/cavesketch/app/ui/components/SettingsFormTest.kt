package com.cavesketch.app.ui.components

import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithContentDescription
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
class SettingsFormTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun stepper_displays_label_and_formatted_value() {
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 5.0,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { "${it.toDouble() * 2}" },
                onChange = {}
            )
        }

        // Verify label is displayed
        composeTestRule.onNodeWithText("Test Label").assertExists()
        // Verify formatted value is displayed (5.0 * 2 = 10.0)
        composeTestRule.onNodeWithText("10.0").assertExists()
    }

    @Test
    fun tapping_plus_increases_value_by_step() {
        var newValue: Number? = null
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 5.0,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { it.toString() },
                onChange = { newValue = it }
            )
        }

        composeTestRule.onNodeWithContentDescription("+").performClick()
        assertEquals(6.0, newValue?.toDouble() ?: 0.0, 0.001)
    }

    @Test
    fun tapping_minus_decreases_value_by_step() {
        var newValue: Number? = null
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 5.0,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { it.toString() },
                onChange = { newValue = it }
            )
        }

        composeTestRule.onNodeWithContentDescription("−").performClick()
        assertEquals(4.0, newValue?.toDouble() ?: 0.0, 0.001)
    }

    @Test
    fun plus_button_disabled_at_max_boundary() {
        var onChangeCalled = false
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 10.0,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { it.toString() },
                onChange = { onChangeCalled = true }
            )
        }

        composeTestRule.onNodeWithContentDescription("+").assertIsNotEnabled()
        composeTestRule.onNodeWithContentDescription("+").performClick()
        org.junit.Assert.assertFalse(onChangeCalled)
    }

    @Test
    fun minus_button_disabled_at_min_boundary() {
        var onChangeCalled = false
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 0.0,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { it.toString() },
                onChange = { onChangeCalled = true }
            )
        }

        composeTestRule.onNodeWithContentDescription("−").assertIsNotEnabled()
        composeTestRule.onNodeWithContentDescription("−").performClick()
        org.junit.Assert.assertFalse(onChangeCalled)
    }

    @Test
    fun value_clamps_to_max_and_does_not_exceed_bounds() {
        var newValue: Number? = null
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 9.5,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { it.toString() },
                onChange = { newValue = it }
            )
        }

        composeTestRule.onNodeWithContentDescription("+").performClick()
        assertEquals(10.0, newValue?.toDouble() ?: 0.0, 0.001)
    }

    @Test
    fun value_clamps_to_min_and_does_not_exceed_bounds() {
        var newValue: Number? = null
        composeTestRule.setContent {
            StepperControl(
                label = "Test Label",
                value = 0.5,
                min = 0.0,
                max = 10.0,
                step = 1.0,
                formatter = { it.toString() },
                onChange = { newValue = it }
            )
        }

        composeTestRule.onNodeWithContentDescription("−").performClick()
        assertEquals(0.0, newValue?.toDouble() ?: 0.0, 0.001)
    }
}
