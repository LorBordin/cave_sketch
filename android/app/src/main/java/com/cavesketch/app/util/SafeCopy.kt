package com.cavesketch.app.util

import android.content.Context
import android.net.Uri
import java.io.File

/**
 * Core of [safeCopyUriToDir], split out for unit testing: runs [copy], and on any
 * throwable invokes [onError] with a friendly message and returns null.
 */
internal inline fun runCopy(copy: () -> String, onError: (String) -> Unit): String? =
    try {
        copy()
    } catch (t: Throwable) {
        onError(friendlyError(t))
        null
    }

/**
 * Copies a picked document like [copyUriToDir], but converts failures (e.g. no
 * free space) into a friendly [onError] callback and a null return instead of a
 * crash.
 */
fun safeCopyUriToDir(
    context: Context,
    uri: Uri,
    dir: File,
    fileName: String,
    onError: (String) -> Unit,
): String? = runCopy({ copyUriToDir(context, uri, dir, fileName) }, onError)
