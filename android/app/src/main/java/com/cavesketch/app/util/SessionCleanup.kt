package com.cavesketch.app.util

/** Fixed-name intermediate + output artifacts written during a session. */
val SESSION_FILES: List<String> = listOf(
    "map.csv", "section.csv", "child_map.csv", "child_section.csv",
    "merged_map.csv", "survey.pdf", "survey.html", "survey.json", "survey.kmz",
)

/** Prefix for imported additional JSON maps (`additional_0.json`, …). */
const val ADDITIONAL_PREFIX: String = "additional_"

/**
 * Given the file names currently in app storage, returns those that are last-run
 * artifacts safe to delete on launch: the fixed [SESSION_FILES] plus any
 * `additional_*` imports.
 */
fun filesToDelete(names: List<String>): List<String> =
    names.filter { it in SESSION_FILES || it.startsWith(ADDITIONAL_PREFIX) }
