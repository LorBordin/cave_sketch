package com.cavesketch.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cavesketch.app.bridge.SatelliteBridge
import com.cavesketch.app.data.SurveyResultStore
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

sealed interface SatelliteState {
    data object Idle : SatelliteState
    data object NoMap : SatelliteState
    data class Generating(val phase: String) : SatelliteState
    data class Success(
        val htmlPath: String,
        val jsonPath: String,
        val kmzPath: String,
        val online: Boolean,
    ) : SatelliteState
    data class Error(val message: String) : SatelliteState
}

data class GpsPoint(val station: String = "", val lat: String = "", val lon: String = "")

class SatelliteViewModel(
    private val bridge: SatelliteBridge,
    private val store: SurveyResultStore,
    private val workDir: String,
    private val io: CoroutineDispatcher,
    private val isOnline: () -> Boolean,
) : ViewModel() {
    private val _state = MutableStateFlow<SatelliteState>(SatelliteState.NoMap)
    val state: StateFlow<SatelliteState> = _state.asStateFlow()

    private val _points = MutableStateFlow(listOf(GpsPoint()))
    val points: StateFlow<List<GpsPoint>> = _points.asStateFlow()

    private val _rotation = MutableStateFlow(0.0)
    val rotation: StateFlow<Double> = _rotation.asStateFlow()

    private val _jsonMaps = MutableStateFlow<List<String>>(emptyList())
    val jsonMaps: StateFlow<List<String>> = _jsonMaps.asStateFlow()

    init {
        viewModelScope.launch {
            store.result.collect { result ->
                // Only the gating states reflect map availability; never clobber a
                // Generating/Success/Error result.
                if (_state.value is SatelliteState.Idle || _state.value is SatelliteState.NoMap) {
                    _state.value = if (result == null) SatelliteState.NoMap else SatelliteState.Idle
                }
            }
        }
    }

    fun suggestedSurveyName(): String = store.result.value?.surveyName ?: "MySurvey"

    fun addPoint() { _points.value = _points.value + GpsPoint() }
    fun removeLastPoint() {
        if (_points.value.size > 1) _points.value = _points.value.dropLast(1)
    }
    fun updatePoint(index: Int, point: GpsPoint) {
        _points.value = _points.value.toMutableList().also { it[index] = point }
    }
    fun setRotation(value: Double) { _rotation.value = value }
    fun addJsonMap(path: String) { _jsonMaps.value = _jsonMaps.value + path }

    fun generate(surveyName: String) {
        val map = store.result.value ?: run { _state.value = SatelliteState.NoMap; return }
        _state.value = SatelliteState.Generating("Building map…")
        viewModelScope.launch {
            try {
                val resultJson = bridge.generateSatellite(buildJson(map.mapCsvPath, surveyName), workDir)
                val obj = JSONObject(resultJson)
                _state.value = if (obj.has("html_path")) {
                    SatelliteState.Success(
                        obj.getString("html_path"),
                        obj.getString("json_path"),
                        obj.getString("kmz_path"),
                        isOnline(),
                    )
                } else {
                    SatelliteState.Error(obj.optString("detail", obj.optString("error", "Unknown error")))
                }
            } catch (e: Throwable) {
                _state.value = SatelliteState.Error(e.message ?: "Generation failed")
            }
        }
    }

    private fun buildJson(mapCsvPath: String, surveyName: String): String {
        val pts = JSONArray()
        _points.value.forEach { p ->
            pts.put(JSONObject().put("station", p.station).put("lat", p.lat).put("lon", p.lon))
        }
        val maps = JSONArray()
        _jsonMaps.value.forEach { maps.put(it) }
        return JSONObject()
            .put("map_path", mapCsvPath)
            .put("gps_points", pts)
            .put("survey_name", surveyName)
            .put("rotation_angle", _rotation.value)
            .put("additional_json_maps", maps)
            .toString()
    }
}
