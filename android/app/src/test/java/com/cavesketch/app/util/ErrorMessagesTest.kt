package com.cavesketch.app.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.IOException

class ErrorMessagesTest {
    @Test
    fun no_space_message_is_friendly() {
        val msg = friendlyError(IOException("write failed: ENOSPC (No space left on device)"))
        assertTrue(msg.contains("space", ignoreCase = true))
        assertTrue(msg.contains("free up", ignoreCase = true))
    }

    @Test
    fun python_runtime_failure_is_friendly() {
        val msg = friendlyError(RuntimeException("com.chaquo.python.PyException: boom"))
        assertTrue(msg.contains("engine", ignoreCase = true))
    }

    @Test
    fun unknown_error_falls_back_to_message() {
        assertEquals("boom", friendlyError(IllegalStateException("boom")))
    }

    @Test
    fun null_message_has_generic_fallback() {
        assertEquals("Something went wrong. Please try again.", friendlyError(RuntimeException()))
    }
}
