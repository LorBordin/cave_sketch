package com.cavesketch.app.ui

import org.junit.Assert.assertEquals
import org.junit.Test

class AboutScreenTest {
    @Test
    fun version_line_is_formatted() {
        assertEquals("Version 1.0.0", aboutVersionLine("1.0.0"))
    }

    @Test
    fun version_line_handles_blank() {
        assertEquals("Version unknown", aboutVersionLine(""))
    }
}
