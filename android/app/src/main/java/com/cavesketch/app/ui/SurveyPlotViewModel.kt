package com.cavesketch.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.cavesketch.app.bridge.SurveyBridge
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import org.json.JSONObject

sealed interface PlotState {
    data object Idle : PlotState
    data class Generating(val phase: String) : PlotState
    data class Success(val pdfPath: String) : PlotState
    data class Error(val message: String) : PlotState
}

/** Parses a user-typed decimal, accepting a comma as the decimal separator. */
fun parseDecimalOrNull(value: String): Double? = value.trim().replace(",", ".").toDoubleOrNull()

data class SurveyInputs(
    val mapPath: String? = null,
    val sectionPath: String? = null,
    val childMapPath: String? = null,
    val childSectionPath: String? = null,
    val surveyName: String = "",
    val surveyorName: String = "",
    val drawerName: String = "",
    val municipality: String = "",
    val latitude: String = "",
    val longitude: String = "",
    val elevationM: String = "",
    val parentStation: String = "",
    val childStation: String = "",
    val sectionProtocol: String = "simple",
    val ruleLength: Int = 100,
    val rotationDeg: Int = 0,
    val showDetails: Boolean = true,
    val showGrid: Boolean = true,
    val markerZoom: Double = 0.0,
    val textZoom: Double = 0.0,
    val lineWidthZoom: Double = 0.0,
    val showCenterline: Boolean = true,
    val magneticVariationDeg: String = "",
) {
    /** First validation error for title block / variation inputs, or null. Mirrors TitleBlockInfo (Python). */
    fun titleBlockError(): String? {
        if (latitude.isBlank() != longitude.isBlank()) return "Enter both latitude and longitude, or neither."
        if (latitude.isNotBlank()) {
            val lat = parseDecimalOrNull(latitude)
            if (lat == null || lat !in -90.0..90.0) return "Latitude must be a number between -90 and 90."
            val lon = parseDecimalOrNull(longitude)
            if (lon == null || lon !in -180.0..180.0) return "Longitude must be a number between -180 and 180."
        }
        if (elevationM.isNotBlank() && parseDecimalOrNull(elevationM) == null) return "Elevation must be a number."
        if (magneticVariationDeg.isNotBlank()) {
            val mv = parseDecimalOrNull(magneticVariationDeg)
            if (mv == null || mv !in -180.0..180.0) return "Magnetic variation must be a number between -180 and 180."
        }
        return null
    }

    fun toJson(): String {
        val settings = JSONObject()
            .put("rule_length", ruleLength)
            .put("rotation_deg", rotationDeg)
            .put("show_details", showDetails)
            .put("show_grid", showGrid)
            .put("marker_zoom", markerZoom)
            .put("text_zoom", textZoom)
            .put("line_width_zoom", lineWidthZoom)
            .put("show_centerline", showCenterline)
            .put("magnetic_variation_deg", parseDecimalOrNull(magneticVariationDeg) ?: 0.0)
        return JSONObject()
            .put("map_path", mapPath ?: JSONObject.NULL)
            .put("section_path", sectionPath ?: JSONObject.NULL)
            .put("child_map_path", childMapPath ?: JSONObject.NULL)
            .put("child_section_path", childSectionPath ?: JSONObject.NULL)
            .put("survey_name", surveyName)
            .put("surveyor_name", surveyorName)
            .put("drawer_name", drawerName)
            .put("municipality", municipality)
            .put("latitude", parseDecimalOrNull(latitude) ?: JSONObject.NULL)
            .put("longitude", parseDecimalOrNull(longitude) ?: JSONObject.NULL)
            .put("elevation_m", parseDecimalOrNull(elevationM) ?: JSONObject.NULL)
            .put("parent_station", parentStation)
            .put("child_station", childStation)
            .put("section_protocol", sectionProtocol)
            .put("settings", settings)
            .toString()
    }
}

class SurveyPlotViewModel(
    private val bridge: SurveyBridge,
    private val workDir: String,
    private val io: CoroutineDispatcher,
    private val store: com.cavesketch.app.data.SurveyResultStore,
) : ViewModel() {
    private val _state = MutableStateFlow<PlotState>(PlotState.Idle)
    val state: StateFlow<PlotState> = _state.asStateFlow()

    fun generate(inputs: SurveyInputs) {
        _state.value = PlotState.Generating("Starting engine…")
        viewModelScope.launch {
            try {
                _state.value = PlotState.Generating("Rendering survey…")
                val resultJson = bridge.generate(inputs.toJson(), workDir)
                val obj = JSONObject(resultJson)
                _state.value = if (obj.has("pdf_path")) {
                    if (obj.has("map_csv_path")) {
                        store.publish(
                            com.cavesketch.app.data.SurveyResult(
                                obj.getString("map_csv_path"), inputs.surveyName
                            )
                        )
                    }
                    PlotState.Success(obj.getString("pdf_path"))
                } else {
                    PlotState.Error(obj.optString("detail", obj.optString("error", "Unknown error")))
                }
            } catch (e: Throwable) {
                _state.value = PlotState.Error(com.cavesketch.app.util.friendlyError(e))
            }
        }
    }
}
