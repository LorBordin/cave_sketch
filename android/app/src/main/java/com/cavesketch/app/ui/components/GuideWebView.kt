package com.cavesketch.app.ui.components

import android.content.Intent
import android.net.Uri
import android.view.ViewGroup
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView

@Composable
fun GuideWebView(
    htmlContent: String,
    modifier: Modifier = Modifier,
    onWebViewCreated: ((WebView) -> Unit)? = null
) {
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )

                // Configure settings for offline-only operation and security
                @Suppress("SetJavaScriptEnabled")
                settings.javaScriptEnabled = false
                settings.allowFileAccess = false
                settings.allowContentAccess = false
                settings.allowFileAccessFromFileURLs = false
                settings.allowUniversalAccessFromFileURLs = false

                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(
                        view: WebView?,
                        request: WebResourceRequest?
                    ): Boolean {
                        val url = request?.url ?: return false
                        // Open external URLs in the system browser
                        val intent = Intent(Intent.ACTION_VIEW, url).apply {
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        context.startActivity(intent)
                        return true
                    }
                }

                onWebViewCreated?.invoke(this)
                loadDataWithBaseURL("file:///android_asset/guide/", htmlContent, "text/html", "UTF-8", null)
            }
        },
        update = { webView ->
            webView.loadDataWithBaseURL("file:///android_asset/guide/", htmlContent, "text/html", "UTF-8", null)
        }
    )
}
