package com.cavesketch.app.util

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

/** Launches the Android share sheet for [pdfPath] via the app's FileProvider. */
fun sharePdf(context: Context, pdfPath: String, displayName: String) {
    val file = File(pdfPath)
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = "application/pdf"
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_TITLE, displayName)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Share survey PDF"))
}
