package com.cavesketch.app.ui.components

import android.content.Intent
import java.io.File
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.Shadows
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class SaveShareButtonTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_label_and_opens_menu_on_click() {
        val context = ApplicationProvider.getApplicationContext<android.app.Application>()
        val testFile = File(context.cacheDir, "test.pdf").apply { writeText("pdf") }

        composeTestRule.setContent {
            SaveShareButton(
                label = "Save / Share PDF",
                path = testFile.absolutePath,
                mimeType = "application/pdf",
                displayName = "test.pdf",
            )
        }

        // Button label is displayed
        composeTestRule.onNodeWithText("Save / Share PDF").assertExists()

        // Click button to open menu
        composeTestRule.onNodeWithText("Save / Share PDF").performClick()
        composeTestRule.waitForIdle()

        // Both options exist in menu
        composeTestRule.onNodeWithText("Save to Device").assertExists()
        composeTestRule.onNodeWithText("Share").assertExists()
    }

    @Test
    fun tapping_share_launches_action_send_intent() {
        val context = ApplicationProvider.getApplicationContext<android.app.Application>()
        val testFile = File(context.cacheDir, "test.pdf").apply { writeText("pdf") }

        composeTestRule.setContent {
            SaveShareButton(
                label = "Save / Share PDF",
                path = testFile.absolutePath,
                mimeType = "application/pdf",
                displayName = "test.pdf",
            )
        }


        // Open menu and tap Share
        composeTestRule.onNodeWithText("Save / Share PDF").performClick()
        composeTestRule.waitForIdle()
        composeTestRule.onNodeWithText("Share").performClick()
        composeTestRule.waitForIdle()

        val application = ApplicationProvider.getApplicationContext<android.app.Application>()
        val nextStartedActivity = Shadows.shadowOf(application).nextStartedActivity
        assertNotNull("Expected an intent to be launched when tapping Share", nextStartedActivity)

        // shareFile uses Intent.createChooser(intent, chooserTitle)
        val targetIntent = if (Intent.ACTION_CHOOSER == nextStartedActivity.action) {
            nextStartedActivity.getParcelableExtra(Intent.EXTRA_INTENT) as? Intent
        } else {
            nextStartedActivity
        }

        assertNotNull("Expected target intent inside chooser", targetIntent)
        assertEquals(Intent.ACTION_SEND, targetIntent?.action)
        assertEquals("application/pdf", targetIntent?.type)
    }
}
