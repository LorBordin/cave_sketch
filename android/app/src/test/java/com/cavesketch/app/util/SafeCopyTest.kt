package com.cavesketch.app.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.io.IOException

class SafeCopyTest {
    @Test
    fun returns_path_on_success() {
        var err: String? = null
        val result = runCopy({ "/tmp/map.csv" }, { err = it })
        assertEquals("/tmp/map.csv", result)
        assertNull(err)
    }

    @Test
    fun reports_friendly_error_and_returns_null_on_failure() {
        var err: String? = null
        val result = runCopy(
            { throw IOException("ENOSPC (No space left on device)") },
            { err = it },
        )
        assertNull(result)
        assertEquals(
            "Not enough free space on the device. Free up some storage and try again.",
            err,
        )
    }
}
