package com.cavesketch.spike

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.os.Bundle
import android.os.ParcelFileDescriptor
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import com.chaquo.python.Python
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { SpikeScreen() } }
    }

    @Composable
    fun SpikeScreen() {
        val scope = rememberCoroutineScope()
        var status by remember { mutableStateOf("Tap to run the spike") }
        var bitmap by remember { mutableStateOf<Bitmap?>(null) }
        var running by remember { mutableStateOf(false) }

        Column(
            modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Button(
                enabled = !running,
                onClick = {
                    running = true
                    status = "Running…"
                    bitmap = null
                    scope.launch {
                        try {
                            val result = withContext(Dispatchers.IO) { runSpike() }
                            bitmap = result.first
                            status = "OK: ${result.second}"
                        } catch (e: Throwable) {
                            status = "FAILED: ${e.message}"
                        } finally {
                            running = false
                        }
                    }
                }
            ) { Text("Run spike") }

            Spacer(Modifier.height(12.dp))
            Text(status)
            Spacer(Modifier.height(12.dp))
            bitmap?.let { Image(it.asImageBitmap(), contentDescription = "Survey PDF page 1") }
        }
    }

    /** Copies the sample DXF out of assets, calls Python to make the PDF,
     *  renders page 1 to a Bitmap. Returns (bitmap, timingsJson). */
    private fun runSpike(): Pair<Bitmap, String> {
        val dxf = File(filesDir, "sample.dxf")
        assets.open("sample.dxf").use { input -> dxf.outputStream().use { input.copyTo(it) } }

        val py = Python.getInstance()
        val resultJson = py.getModule("spike")
            .callAttr("render_sample_pdf_timed", dxf.absolutePath, filesDir.absolutePath)
            .toString()
        android.util.Log.i("SpikeTiming", resultJson)
        val pdfPath = org.json.JSONObject(resultJson).getString("pdf_path")

        val pfd = ParcelFileDescriptor.open(File(pdfPath), ParcelFileDescriptor.MODE_READ_ONLY)
        PdfRenderer(pfd).use { renderer ->
            renderer.openPage(0).use { page ->
                val bmp = Bitmap.createBitmap(page.width * 2, page.height * 2, Bitmap.Config.ARGB_8888)
                bmp.eraseColor(Color.WHITE)
                page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
                return Pair(bmp, resultJson)
            }
        }
    }
}
