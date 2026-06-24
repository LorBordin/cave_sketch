package com.cavesketch.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AppInitStateTest {
    @Test
    fun starts_initializing() {
        assertTrue(AppInitState().status.value is InitStatus.Initializing)
    }

    @Test
    fun mark_ready_transitions_to_ready() {
        val s = AppInitState()
        s.markReady()
        assertTrue(s.status.value is InitStatus.Ready)
    }

    @Test
    fun mark_failed_carries_message() {
        val s = AppInitState()
        s.markFailed("nope")
        assertEquals("nope", (s.status.value as InitStatus.Failed).message)
    }
}
