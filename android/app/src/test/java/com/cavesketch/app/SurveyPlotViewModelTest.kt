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
}
