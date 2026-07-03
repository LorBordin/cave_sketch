package com.cavesketch.app.util

import android.content.Context
import android.net.Uri
import android.widget.Toast
import java.io.File

object FileValidator {
    val SURVEY_EXTENSIONS = setOf("dxf", "csv")
    val JSON_EXTENSIONS = setOf("json")

    /**
     * Checks if the given display name has an extension included in the allowed set (case-insensitive).
     */
    fun isAcceptedExtension(displayName: String, allowed: Set<String>): Boolean {
        val dotIndex = displayName.lastIndexOf('.')
        if (dotIndex == -1 || dotIndex == displayName.length - 1) return false
        val ext = displayName.substring(dotIndex + 1).lowercase()
        return allowed.map { it.lowercase() }.contains(ext)
    }

    /**
     * Checks if the given display name has a .json extension (case-insensitive).
     */
    fun isAcceptedJsonExtension(displayName: String): Boolean {
        return isAcceptedExtension(displayName, JSON_EXTENSIONS)
    }

    /**
     * Validates file extension, copies the file, and triggers onSuccess on success.
     * Shows Snackbars on validation errors.
     */
    fun validateAndCopySurveyFile(
        context: Context,
        uri: Uri,
        fileNamePrefix: String,
        showSnackbar: (String) -> Unit,
        onSuccess: (String) -> Unit
    ) {
        val displayName = getDisplayName(context, uri)
        if (!isAcceptedExtension(displayName, SURVEY_EXTENSIONS)) {
            showSnackbar("Unsupported file format. Please select a .dxf or .csv file.")
            return
        }
        val isDxf = displayName.lowercase().endsWith(".dxf")
        val targetExt = if (isDxf) ".dxf" else ".csv"
        val targetFileName = fileNamePrefix + targetExt
        val showError: (String) -> Unit = { msg ->
            Toast.makeText(context, msg, Toast.LENGTH_LONG).show()
        }
        val copiedPath = safeCopyUriToDir(context, uri, context.filesDir, targetFileName, showError) ?: return
        onSuccess(copiedPath)
    }
}
