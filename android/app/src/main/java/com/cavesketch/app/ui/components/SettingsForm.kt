package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.IconButton
import androidx.compose.material3.Icon
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Remove
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
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

@Composable
fun StepperControl(
    label: String,
    value: Number,
    min: Number,
    max: Number,
    step: Number,
    formatter: (Number) -> String,
    onChange: (Number) -> Unit
) {
    val valDouble = value.toDouble()
    val minDouble = min.toDouble()
    val maxDouble = max.toDouble()
    val stepDouble = step.toDouble()

    val canDecrease = valDouble > minDouble + 0.0001
    val canIncrease = valDouble < maxDouble - 0.0001

    fun updateValue(isIncrement: Boolean) {
        val delta = if (isIncrement) stepDouble else -stepDouble
        var nextVal = valDouble + delta
        if (isIncrement) {
            if (nextVal > maxDouble) {
                nextVal = maxDouble
            }
        } else {
            if (nextVal < minDouble) {
                nextVal = minDouble
            }
        }

        val castedValue: Number = when (value) {
            is Int -> nextVal.toInt()
            is Long -> nextVal.toLong()
            is Float -> nextVal.toFloat()
            else -> nextVal
        }
        onChange(castedValue)
    }

    Column {
        Text(label)
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            IconButton(
                onClick = { updateValue(false) },
                enabled = canDecrease,
                modifier = Modifier.semantics { contentDescription = "−" }
            ) {
                Icon(Icons.Filled.Remove, contentDescription = "Decrease")
            }
            Text(
                text = formatter(value),
                modifier = Modifier.align(Alignment.CenterVertically)
            )
            IconButton(
                onClick = { updateValue(true) },
                enabled = canIncrease,
                modifier = Modifier.semantics { contentDescription = "+" }
            ) {
                Icon(Icons.Filled.Add, contentDescription = "Increase")
            }
        }
    }
}
