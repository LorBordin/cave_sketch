package com.cavesketch.app.ui.components

import android.util.Log
import android.view.ViewGroup
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import java.io.File

private const val TAG = "MapWebView"

/** Renders a local folium HTML file. Reads the HTML content and loads it with a secure
 * https base URL to avoid CORS/file origin restrictions. */
@Composable
fun MapWebView(htmlPath: String, modifier: Modifier = Modifier) {
    AndroidView(
        modifier = modifier,
        factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )

                // TODO: guard behind debug build
                WebView.setWebContentsDebuggingEnabled(true)

                @Suppress("SetJavaScriptEnabled")
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true

                webChromeClient = object : WebChromeClient() {
                    override fun onConsoleMessage(consoleMessage: ConsoleMessage?): Boolean {
                        val message = consoleMessage?.message() ?: ""
                        val line = consoleMessage?.lineNumber() ?: 0
                        val source = consoleMessage?.sourceId() ?: ""
                        Log.d(TAG, "JS Console: $message -- From line $line of $source")
                        return true
                    }
                }

                webViewClient = object : WebViewClient() {
                    override fun onReceivedError(
                        view: WebView?,
                        request: WebResourceRequest?,
                        error: WebResourceError?
                    ) {
                        val url = request?.url?.toString() ?: "unknown"
                        val desc = error?.description ?: "unknown"
                        val code = error?.errorCode ?: 0
                        Log.e(TAG, "onReceivedError: URL=$url, Code=$code, Description=$desc")
                    }

                    override fun onReceivedHttpError(
                        view: WebView?,
                        request: WebResourceRequest?,
                        errorResponse: WebResourceResponse?
                    ) {
                        val url = request?.url?.toString() ?: "unknown"
                        val statusCode = errorResponse?.statusCode ?: 0
                        val phrase = errorResponse?.reasonPhrase ?: "unknown"
                        Log.e(TAG, "onReceivedHttpError: URL=$url, StatusCode=$statusCode, Reason=$phrase")
                    }

                    override fun onPageFinished(view: WebView?, url: String?) {
                        Log.d(TAG, "onPageFinished: $url")
                        // Injects CSS and dispatches window resize event robustly
                        view?.evaluateJavascript(
                            """
                            (function() {
                                var style = document.createElement('style');
                                style.innerHTML = 'html, body { height: 100% !important; margin: 0; padding: 0; } .folium-map { position: absolute !important; top: 0; bottom: 0; left: 0; right: 0; height: 100% !important; width: 100% !important; }';
                                var target = document.head || document.body || document.documentElement;
                                if (target) {
                                    target.appendChild(style);
                                }
                                window.dispatchEvent(new Event('resize'));
                            })()
                            """.trimIndent(),
                            null
                        )
                    }
                }

                loadHtml(this, htmlPath)
            }
        },
        update = { webView ->
            loadHtml(webView, htmlPath)
        },
    )
}

private fun loadHtml(webView: WebView, htmlPath: String) {
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
}
