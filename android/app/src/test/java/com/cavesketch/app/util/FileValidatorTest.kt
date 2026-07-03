package com.cavesketch.app.util

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FileValidatorTest {

    @Test
    fun testIsAcceptedExtension_validExtensions() {
        val allowed = setOf("dxf", "csv")
        assertTrue(FileValidator.isAcceptedExtension("survey.dxf", allowed))
        assertTrue(FileValidator.isAcceptedExtension("data.csv", allowed))
        assertTrue(FileValidator.isAcceptedExtension("SURVEY.DXF", allowed))
        assertTrue(FileValidator.isAcceptedExtension("data.Csv", allowed))
    }

    @Test
    fun testIsAcceptedExtension_invalidExtensions() {
        val allowed = setOf("dxf", "csv")
        assertFalse(FileValidator.isAcceptedExtension("survey.txt", allowed))
        assertFalse(FileValidator.isAcceptedExtension("document.pdf", allowed))
        assertFalse(FileValidator.isAcceptedExtension("image.png", allowed))
        assertFalse(FileValidator.isAcceptedExtension("survey.dxf.bak", allowed))
        assertFalse(FileValidator.isAcceptedExtension("noextension", allowed))
        assertFalse(FileValidator.isAcceptedExtension("", allowed))
    }

    @Test
    fun testIsAcceptedJsonExtension() {
        assertTrue(FileValidator.isAcceptedJsonExtension("map.json"))
        assertTrue(FileValidator.isAcceptedJsonExtension("MAP.JSON"))
        assertFalse(FileValidator.isAcceptedJsonExtension("map.txt"))
        assertFalse(FileValidator.isAcceptedJsonExtension("map.json.bak"))
        assertFalse(FileValidator.isAcceptedJsonExtension("noextension"))
        assertFalse(FileValidator.isAcceptedJsonExtension(""))
    }
}
