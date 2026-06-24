package com.cavesketch.app.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SessionCleanupTest {
    @Test
    fun fixed_outputs_are_selected_for_deletion() {
        val present = listOf("map.csv", "survey.pdf", "survey.kmz", "keep_me.txt")
        val toDelete = filesToDelete(present)
        assertTrue(toDelete.contains("map.csv"))
        assertTrue(toDelete.contains("survey.pdf"))
        assertTrue(toDelete.contains("survey.kmz"))
        assertFalse(toDelete.contains("keep_me.txt"))
    }

    @Test
    fun additional_json_imports_are_selected() {
        val toDelete = filesToDelete(listOf("additional_0.json", "additional_12.json", "notes.json"))
        assertTrue(toDelete.contains("additional_0.json"))
        assertTrue(toDelete.contains("additional_12.json"))
        assertFalse(toDelete.contains("notes.json"))
    }

    @Test
    fun known_output_set_covers_all_current_artifacts() {
        // Guards against an artifact being added elsewhere without updating cleanup.
        val expected = listOf(
            "map.csv", "section.csv", "child_map.csv", "child_section.csv",
            "merged_map.csv", "survey.pdf", "survey.html", "survey.json", "survey.kmz",
        )
        assertEquals(expected.toSet(), SESSION_FILES.toSet())
    }
}
