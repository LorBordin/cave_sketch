package com.cavesketch.app

import com.cavesketch.app.bridge.SatelliteBridge
import com.cavesketch.app.data.SurveyResult
import com.cavesketch.app.data.SurveyResultStore
import com.cavesketch.app.ui.GpsPoint
import com.cavesketch.app.ui.SatelliteState
import com.cavesketch.app.ui.SatelliteViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class SatelliteViewModelTest {
    private val testDispatcher = StandardTestDispatcher()

    @Before fun setUp() = Dispatchers.setMain(testDispatcher)
    @After fun tearDown() = Dispatchers.resetMain()

    private fun vm(
        store: SurveyResultStore,
        online: Boolean = true,
        bridge: SatelliteBridge = SatelliteBridge { _, _ -> "{}" },
    ) = SatelliteViewModel(bridge, store, "/tmp", testDispatcher) { online }

    @Test
    fun empty_store_is_no_map() = runTest(testDispatcher) {
        val model = vm(SurveyResultStore())
        advanceUntilIdle()
        assertEquals(SatelliteState.NoMap, model.state.value)
    }

    @Test
    fun publishing_map_makes_it_idle() = runTest(testDispatcher) {
        val store = SurveyResultStore()
        val model = vm(store)
        advanceUntilIdle()
        store.publish(SurveyResult("/tmp/map.csv", "Cave"))
        advanceUntilIdle()
        assertEquals(SatelliteState.Idle, model.state.value)
    }

    @Test
    fun generate_success_emits_success_with_online_flag() = runTest(testDispatcher) {
        val store = SurveyResultStore().apply { publish(SurveyResult("/tmp/map.csv", "Cave")) }
        val model = vm(store, online = false, bridge = { _, _ ->
            """{"html_path":"/tmp/survey.html","json_path":"/tmp/survey.json","kmz_path":"/tmp/survey.kmz"}"""
        })
        advanceUntilIdle()
        model.addPoint()
        model.updatePoint(0, GpsPoint("st1", "45.0", "7.0"))
        model.generate("Cave")
        advanceUntilIdle()
        val s = model.state.value as SatelliteState.Success
        assertEquals("/tmp/survey.kmz", s.kmzPath)
        assertEquals(false, s.online)
    }

    @Test
    fun generate_error_emits_error_with_detail() = runTest(testDispatcher) {
        val store = SurveyResultStore().apply { publish(SurveyResult("/tmp/map.csv", "Cave")) }
        val model = vm(store, bridge = { _, _ ->
            """{"error":"no_anchor_match","detail":"no match"}"""
        })
        advanceUntilIdle()
        model.generate("Cave")
        advanceUntilIdle()
        assertTrue((model.state.value as SatelliteState.Error).message.contains("no match"))
    }

    @Test
    fun add_and_remove_points() = runTest(testDispatcher) {
        val model = vm(SurveyResultStore())
        advanceUntilIdle()
        assertEquals(1, model.points.value.size)
        model.addPoint()
        assertEquals(2, model.points.value.size)
        model.removeLastPoint()
        assertEquals(1, model.points.value.size)
        model.removeLastPoint() // never drops below one row
        assertEquals(1, model.points.value.size)
    }
}
