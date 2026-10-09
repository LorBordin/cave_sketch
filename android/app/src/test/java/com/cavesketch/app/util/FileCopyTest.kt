package com.cavesketch.app.util

import android.content.Context
import android.net.Uri
import androidx.test.core.app.ApplicationProvider
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.io.File

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class FileCopyTest {
    @get:Rule
    val tempFolder = TemporaryFolder()

    @Test
    fun copyFileToUri_copies_exact_bytes_and_returns_uri_string() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val sourceFile = tempFolder.newFile("source.txt").apply { writeText("Hello CaveSketch!") }
        val targetFile = tempFolder.newFile("target.txt")
        val targetUri = Uri.fromFile(targetFile)

        val resultUriString = copyFileToUri(context, sourceFile.absolutePath, targetUri)

        assertEquals(targetUri.toString(), resultUriString)
        assertEquals("Hello CaveSketch!", targetFile.readText())
    }

    @Test
    fun safeCopyFileToUri_returns_uri_string_on_success_without_error() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val sourceFile = tempFolder.newFile("source_safe.txt").apply { writeText("Safe content") }
        val targetFile = tempFolder.newFile("target_safe.txt")
        val targetUri = Uri.fromFile(targetFile)
        var errorReported: String? = null

        val result = safeCopyFileToUri(context, sourceFile.absolutePath, targetUri) { errorReported = it }

        assertEquals(targetUri.toString(), result)
        assertEquals("Safe content", targetFile.readText())
        assertNull(errorReported)
    }

    @Test
    fun safeCopyFileToUri_returns_null_and_invokes_onError_when_source_missing() {
        val context = ApplicationProvider.getApplicationContext<Context>()
        val missingPath = File(tempFolder.root, "non_existent.txt").absolutePath
        val targetFile = tempFolder.newFile("target_missing.txt")
        val targetUri = Uri.fromFile(targetFile)
        var errorReported: String? = null

        val result = safeCopyFileToUri(context, missingPath, targetUri) { errorReported = it }

        assertNull(result)
        assertTrue(errorReported != null && errorReported!!.isNotBlank())
    }
}
