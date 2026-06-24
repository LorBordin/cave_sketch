package com.cavesketch.app.util

/**
 * Maps a low-level [Throwable] to a short, non-technical message suitable for the
 * UI. Known field failures (no storage, Python runtime) get tailored copy; anything
 * else falls back to the throwable's own message, then a generic line.
 */
fun friendlyError(t: Throwable): String {
    val raw = (t.message ?: "") + " " + (t.cause?.message ?: "")
    return when {
        raw.contains("ENOSPC", ignoreCase = true) ||
            raw.contains("No space left", ignoreCase = true) ->
            "Not enough free space on the device. Free up some storage and try again."
        raw.contains("chaquo", ignoreCase = true) ||
            raw.contains("PyException", ignoreCase = true) ->
            "The CaveSketch engine hit a problem while processing. Please try again."
        else -> t.message ?: "Something went wrong. Please try again."
    }
}
