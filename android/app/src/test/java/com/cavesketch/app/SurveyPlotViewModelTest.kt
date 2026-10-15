package com.cavesketch.app

import com.cavesketch.app.bridge.SurveyBridge
import com.cavesketch.app.ui.PlotState
import com.cavesketch.app.ui.SurveyInputs
import com.cavesketch.app.ui.SurveyPlotViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.coroutines.test.resetMain
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class SurveyPlotViewModelTest {
    private val testDispatcher = StandardTestDispatcher()

    private val store = com.cavesketch.app.data.SurveyResultStore()

    private fun vm(bridge: SurveyBridge) =
        SurveyPlotViewModel(bridge, "/tmp", testDispatcher, store)

    private val inputs = SurveyInputs(mapPath = "/tmp/map.csv")

    @org.junit.Before fun setUp() = kotlinx.coroutines.Dispatchers.setMain(testDispatcher)
    @org.junit.After fun tearDown() = kotlinx.coroutines.Dispatchers.resetMain()

    @Test
    fun success_path_emits_success_with_pdf_path() = runTest(testDispatcher) {
        val model = vm(object : SurveyBridge {
            override suspend fun generate(inputsJson: String, workDir: String) =
                """{"pdf_path":"/tmp/survey.pdf"}"""
        })
        model.generate(inputs)
        advanceUntilIdle()
        assertEquals(PlotState.Success("/tmp/survey.pdf"), model.state.value)
    }

    @Test
    fun error_path_emits_error_with_detail() = runTest(testDispatcher) {
        val model = vm(object : SurveyBridge {
            override suspend fun generate(inputsJson: String, workDir: String) =
                """{"error":"render_failed","detail":"boom"}"""
        })
        model.generate(inputs)
        advanceUntilIdle()
        assertTrue((model.state.value as PlotState.Error).message.contains("boom"))
    }

    @Test
    fun success_with_map_csv_publishes_to_store() = runTest(testDispatcher) {
        val model = vm(object : SurveyBridge {
            override suspend fun generate(inputsJson: String, workDir: String) =
                """{"pdf_path":"/tmp/survey.pdf","map_csv_path":"/tmp/map.csv"}"""
        })
        model.generate(SurveyInputs(mapPath = "/tmp/map.csv", surveyName = "Cave"))
        advanceUntilIdle()
        assertEquals(
            com.cavesketch.app.data.SurveyResult("/tmp/map.csv", "Cave"),
            store.result.value,
        )
    }

    @Test
    fun survey_inputs_to_json_includes_show_centerline() {
        val inputs = SurveyInputs(showCenterline = false)
        val json = inputs.toJson()
        assertTrue(json.contains("\"show_centerline\":false"))
    }

    @Test
    fun testFileValidator_surveyExtensions() {
        val allowed = com.cavesketch.app.util.FileValidator.SURVEY_EXTENSIONS
        assertTrue(com.cavesketch.app.util.FileValidator.isAcceptedExtension("survey.dxf", allowed))
        assertTrue(com.cavesketch.app.util.FileValidator.isAcceptedExtension("data.csv", allowed))
        org.junit.Assert.assertFalse(com.cavesketch.app.util.FileValidator.isAcceptedExtension("survey.txt", allowed))
    }

    @Test
    fun toJson_includes_title_block_fields_and_variation() {
        val json = org.json.JSONObject(
            SurveyInputs(
                surveyorName = "Alice", drawerName = "Bob", municipality = "Genga",
                latitude = "43,4", longitude = "12.9", elevationM = "320",
                magneticVariationDeg = "-1,5",
            ).toJson()
        )
        assertEquals("Bob", json.getString("drawer_name"))
        assertEquals("Genga", json.getString("municipality"))
        assertEquals(43.4, json.getDouble("latitude"), 1e-9)
        assertEquals(12.9, json.getDouble("longitude"), 1e-9)
        assertEquals(320.0, json.getDouble("elevation_m"), 1e-9)
        assertEquals(-1.5, json.getJSONObject("settings").getDouble("magnetic_variation_deg"), 1e-9)
    }

    @Test
    fun toJson_emits_null_for_empty_numbers_and_zero_variation() {
        val json = org.json.JSONObject(SurveyInputs().toJson())
        assertTrue(json.isNull("latitude"))
        assertTrue(json.isNull("longitude"))
        assertTrue(json.isNull("elevation_m"))
        assertEquals(0.0, json.getJSONObject("settings").getDouble("magnetic_variation_deg"), 0.0)
    }

    @Test
    fun titleBlockError_validates_inputs() {
        assertEquals(null, SurveyInputs().titleBlockError())
        assertEquals(null, SurveyInputs(latitude = "-90", longitude = "180").titleBlockError())
        assertEquals(null, SurveyInputs(latitude = "0", longitude = "0", elevationM = "0").titleBlockError())
        assertTrue(SurveyInputs(latitude = "45").titleBlockError()!!.contains("both"))
        assertTrue(SurveyInputs(latitude = "91", longitude = "0").titleBlockError()!!.contains("Latitude"))
        assertTrue(SurveyInputs(latitude = "0", longitude = "-181").titleBlockError()!!.contains("Longitude"))
        assertTrue(SurveyInputs(latitude = "abc", longitude = "0").titleBlockError()!!.contains("Latitude"))
        assertTrue(SurveyInputs(elevationM = "high").titleBlockError()!!.contains("Elevation"))
        assertTrue(SurveyInputs(magneticVariationDeg = "200").titleBlockError()!!.contains("Magnetic"))
    }
}

