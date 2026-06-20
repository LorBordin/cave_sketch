package com.cavesketch.app.ui.components

import android.webkit.WebView
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import java.io.File

/** Renders a local folium HTML file. Reads the HTML content and loads it with a secure
 * https base URL to avoid CORS/file origin restrictions. */
@Composable
fun MapWebView(htmlPath: String, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            WebView(ctx).apply {
                @Suppress("SetJavaScriptEnabled")
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                
                try {
                    val file = File(htmlPath)
                    if (file.exists()) {
                        val htmlContent = file.readText()
                        loadDataWithBaseURL(
                            "https://appassets.androidplatform.net/",
                            htmlContent,
                            "text/html",
                            "UTF-8",
                            null
                        )
                    } else {
                        loadData("Map file not found.", "text/html", "UTF-8")
                    }
                } catch (e: Exception) {
                    loadData("Error loading map: ${e.message}", "text/html", "UTF-8")
                }
            }
        },
        update = { webView ->
            try {
                val file = File(htmlPath)
                if (file.exists()) {
                    val htmlContent = file.readText()
                    webView.loadDataWithBaseURL(
                        "https://appassets.androidplatform.net/",
                        htmlContent,
                        "text/html",
                        "UTF-8",
                        null
                    )
                } else {
                    webView.loadData("Map file not found.", "text/html", "UTF-8")
                }
            } catch (e: Exception) {
                webView.loadData("Error loading map: ${e.message}", "text/html", "UTF-8")
            }
        },
    )
}
