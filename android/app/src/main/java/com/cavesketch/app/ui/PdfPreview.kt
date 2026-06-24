package com.cavesketch.app.ui

import android.graphics.Bitmap
import android.graphics.Color
import android.graphics.pdf.PdfRenderer
import android.os.ParcelFileDescriptor
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import java.io.File

/** Renders page 1 of [pdfPath] to a fit-to-width bitmap (2× for legibility). */
fun renderPdfFirstPage(pdfPath: String): Bitmap {
    val pfd = ParcelFileDescriptor.open(File(pdfPath), ParcelFileDescriptor.MODE_READ_ONLY)
    PdfRenderer(pfd).use { renderer ->
        renderer.openPage(0).use { page ->
            val bmp = Bitmap.createBitmap(page.width * 2, page.height * 2, Bitmap.Config.ARGB_8888)
            bmp.eraseColor(Color.WHITE)
            page.render(bmp, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY)
            return bmp
        }
    }
}

@Composable
fun PdfPreview(pdfPath: String) {
    val bitmap = remember(pdfPath) { renderPdfFirstPage(pdfPath) }
    Image(
        bitmap.asImageBitmap(),
        contentDescription = "Survey plot preview",
        modifier = Modifier.fillMaxWidth()
    )
}
