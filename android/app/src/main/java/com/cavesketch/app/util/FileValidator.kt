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
     * Validates if a file has the standard DXF signature:
     * Line 1 is "0" and Line 2 is "SECTION" (after trimming whitespace).
     */
    fun isDxfHeaderValid(file: File): Boolean {
        if (!file.exists() || !file.isFile) return false
        return try {
            file.bufferedReader().use { reader ->
                val line1 = reader.readLine()?.trim() ?: return false
                val line2 = reader.readLine()?.trim() ?: return false
                line1 == "0" && line2 == "SECTION"
            }
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Validates file extension, copies the file, validates the DXF structure if applicable,
     * and triggers onSuccess on success. Shows Snackbars on validation errors.
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
        if (isDxf) {
            val file = File(copiedPath)
            if (!isDxfHeaderValid(file)) {
                if (file.exists()) {
                    file.delete()
                }
                showSnackbar("The selected file is not a valid DXF file.")
                return
            }
        }
        onSuccess(copiedPath)
    }
}
