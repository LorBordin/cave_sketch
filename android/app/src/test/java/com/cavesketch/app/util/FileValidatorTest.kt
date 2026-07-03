package com.cavesketch.app.util

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class FileValidatorTest {

    @Rule
    @JvmField
    val tempFolder = TemporaryFolder()

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

    @Test
    fun testIsDxfHeaderValid_validHeader() {
        val file = tempFolder.newFile("valid.dxf")
        file.writeText("0\nSECTION\n2\nHEADER\n")
        assertTrue(FileValidator.isDxfHeaderValid(file))
    }

    @Test
    fun testIsDxfHeaderValid_validHeaderWindowsNewlines() {
        val file = tempFolder.newFile("valid_win.dxf")
        file.writeText("0\r\nSECTION\r\n2\r\nHEADER\r\n")
        assertTrue(FileValidator.isDxfHeaderValid(file))
    }

    @Test
    fun testIsDxfHeaderValid_emptyFile() {
        val file = tempFolder.newFile("empty.dxf")
        assertFalse(FileValidator.isDxfHeaderValid(file))
    }

    @Test
    fun testIsDxfHeaderValid_plainTextInvalid() {
        val file = tempFolder.newFile("invalid.txt")
        file.writeText("This is some text\nthat does not match DXF.")
        assertFalse(FileValidator.isDxfHeaderValid(file))
    }

    @Test
    fun testIsDxfHeaderValid_binaryFile() {
        val file = tempFolder.newFile("binary.bin")
        file.writeBytes(byteArrayOf(0x00, 0x01, 0x02, 0x03, 0x0A, 0x0B))
        assertFalse(FileValidator.isDxfHeaderValid(file))
    }
}
