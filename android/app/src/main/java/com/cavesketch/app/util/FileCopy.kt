package com.cavesketch.app.util

import android.content.Context
import android.net.Uri
import java.io.File

/** Copies a picked content:// document into [dir] as [fileName]; returns its path. */
fun copyUriToDir(context: Context, uri: Uri, dir: File, fileName: String): String {
    val out = File(dir, fileName)
    context.contentResolver.openInputStream(uri).use { input ->
        requireNotNull(input) { "Cannot open $uri" }
        out.outputStream().use { input.copyTo(it) }
    }
    return out.absolutePath
}

/** Queries the content resolver for the document's display name, fallback to lastPathSegment. */
fun getDisplayName(context: Context, uri: Uri): String {
    return context.contentResolver.query(uri, null, null, null, null)?.use { c ->
        val idx = c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
        if (idx >= 0 && c.moveToFirst()) c.getString(idx) else null
    } ?: uri.lastPathSegment ?: ""
}

/** Best-effort display name → extension (".dxf"/".csv"); defaults to the uri path. */
fun extensionOf(context: Context, uri: Uri): String {
    val name = getDisplayName(context, uri)
    return if (name.lowercase().endsWith(".dxf")) ".dxf" else ".csv"
}
