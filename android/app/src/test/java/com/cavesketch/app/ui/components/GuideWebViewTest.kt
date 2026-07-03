package com.cavesketch.app.ui.components

import android.webkit.WebView
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class GuideWebViewTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testGuideWebView_settingsAndLoading() {
        var capturedWebView: WebView? = null
        val testHtml = "<html><body>Hello Guide</body></html>"

        composeTestRule.setContent {
            GuideWebView(
                htmlContent = testHtml,
                onWebViewCreated = { webView ->
                    capturedWebView = webView
                }
            )
        }

        // Wait for Compose to render the WebView
        composeTestRule.waitForIdle()

        val webView = capturedWebView
        org.junit.Assert.assertNotNull("WebView should be created", webView)
        
        // Verify settings are correct (JavaScript disabled)
        assertFalse("JavaScript should be disabled", webView!!.settings.javaScriptEnabled)
        assertFalse("File access should be disabled for security", webView.settings.allowFileAccess)
        assertFalse("Content access should be disabled for security", webView.settings.allowContentAccess)
    }
}
