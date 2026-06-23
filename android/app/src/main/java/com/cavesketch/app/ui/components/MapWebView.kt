package com.cavesketch.app.ui.components

import android.util.Log
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
                // Enable remote debugging for chrome://inspect
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
                        // Probe body size and .folium-map computed size
                        view?.evaluateJavascript(
                            """
                            (function() {
                                var bodyW = document.body ? document.body.clientWidth : -1;
                                var bodyH = document.body ? document.body.clientHeight : -1;
                                var mapEl = document.querySelector('.folium-map');
                                var mapW = mapEl ? mapEl.clientWidth : -1;
                                var mapH = mapEl ? mapEl.clientHeight : -1;
                                var mapCompH = -1;
                                if (mapEl) {
                                    mapCompH = parseInt(window.getComputedStyle(mapEl).height, 10);
                                }
                                return JSON.stringify({
                                    bodyW: bodyW,
                                    bodyH: bodyH,
                                    mapW: mapW,
                                    mapH: mapH,
                                    mapCompH: mapCompH
                                });
                            })()
                            """.trimIndent()
                        ) { result ->
                            Log.d(TAG, "probeResult: $result")
                        }
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
