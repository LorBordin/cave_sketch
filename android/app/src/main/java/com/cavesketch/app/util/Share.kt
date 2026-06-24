package com.cavesketch.app.util

import android.content.Context
import android.content.Intent
import androidx.core.content.FileProvider
import java.io.File

/** Launches the Android share sheet for [path] with the given [mimeType], via the
 * app's FileProvider. */
fun shareFile(context: Context, path: String, mimeType: String, displayName: String) {
    val file = File(path)
    val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
    val intent = Intent(Intent.ACTION_SEND).apply {
        type = mimeType
        putExtra(Intent.EXTRA_STREAM, uri)
        putExtra(Intent.EXTRA_TITLE, displayName)
        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    }
    context.startActivity(Intent.createChooser(intent, "Share $displayName"))
}

/** Backwards-compatible PDF share (Phase 1 call sites). */
fun sharePdf(context: Context, pdfPath: String, displayName: String) =
    shareFile(context, pdfPath, "application/pdf", displayName)
