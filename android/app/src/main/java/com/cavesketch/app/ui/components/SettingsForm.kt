package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.cavesketch.app.ui.SurveyInputs

@Composable
fun SettingsForm(inputs: SurveyInputs, onChange: (SurveyInputs) -> Unit) {
    Text("Survey settings")

    // Rule length: 5..1000, step 5 (multiple-of-5 constraint).
    Text("Rule length (m): ${inputs.ruleLength}")
    Slider(
        value = inputs.ruleLength.toFloat(),
        onValueChange = { onChange(inputs.copy(ruleLength = (Math.round(it / 5f) * 5))) },
        valueRange = 5f..1000f,
    )

    // Map rotation: -180..180, step 1.
    Text("Map rotation (°): ${inputs.rotationDeg}")
    Slider(
        value = inputs.rotationDeg.toFloat(),
        onValueChange = { onChange(inputs.copy(rotationDeg = Math.round(it))) },
        valueRange = -180f..180f,
    )

    ZoomSlider("Marker zoom", inputs.markerZoom) { onChange(inputs.copy(markerZoom = it)) }
    ZoomSlider("Text zoom", inputs.textZoom) { onChange(inputs.copy(textZoom = it)) }
    ZoomSlider("Line width zoom", inputs.lineWidthZoom) { onChange(inputs.copy(lineWidthZoom = it)) }

    Row(Modifier.fillMaxWidth()) {
        Checkbox(inputs.showDetails, { onChange(inputs.copy(showDetails = it)) })
        Text("Show station markers")
    }
    Row(Modifier.fillMaxWidth()) {
        Checkbox(inputs.showGrid, { onChange(inputs.copy(showGrid = it)) })
        Text("Show grid")
    }
}

@Composable
private fun ZoomSlider(label: String, value: Double, onChange: (Double) -> Unit) {
    Text("$label [-1, 1]: ${"%.1f".format(value)}")
    Slider(
        value = value.toFloat(),
        onValueChange = { onChange((Math.round(it * 10f) / 10f).toDouble()) },
        valueRange = -1f..1f,
    )
}
