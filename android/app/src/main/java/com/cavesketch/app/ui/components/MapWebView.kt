package com.cavesketch.app.ui.components

import android.webkit.WebView
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView

/** Renders a local folium HTML file. Requires connectivity to fetch satellite tiles;
 * the caller decides whether to show this (online) or the offline banner. */
@Composable
fun MapWebView(htmlPath: String, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            WebView(ctx).apply {
                @Suppress("SetJavaScriptEnabled")
                settings.javaScriptEnabled = true
                settings.allowFileAccess = true
                loadUrl("file://$htmlPath")
            }
        },
        update = { it.loadUrl("file://$htmlPath") },
    )
}
