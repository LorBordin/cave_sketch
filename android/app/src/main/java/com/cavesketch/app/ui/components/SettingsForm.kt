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
import androidx.compose.ui.platform.testTag
import com.cavesketch.app.ui.SurveyInputs

@Composable
fun SettingsForm(inputs: SurveyInputs, onChange: (SurveyInputs) -> Unit) {
    Column {

    // Rule length: 5..100, step 5. Keep as Slider.
    Text("Rule length (m): ${inputs.ruleLength}")
    Slider(
        value = inputs.ruleLength.toFloat(),
        onValueChange = { onChange(inputs.copy(ruleLength = (Math.round(it / 5f) * 5))) },
        valueRange = 5f..100f,
    )

    StepperControl(
        label = "Map rotation (°)",
        value = inputs.rotationDeg,
        min = -180,
        max = 180,
        step = 5,
        formatter = { "${it.toInt()}°" },
        onChange = { onChange(inputs.copy(rotationDeg = it.toInt())) }
    )

    StepperControl(
        label = "Marker zoom [-1, 1]",
        value = inputs.markerZoom,
        min = -1.0,
        max = 1.0,
        step = 0.1,
        formatter = { "%.1f".format(it.toDouble()) },
        onChange = { onChange(inputs.copy(markerZoom = it.toDouble())) }
    )

    StepperControl(
        label = "Text zoom [-1, 1]",
        value = inputs.textZoom,
        min = -1.0,
        max = 1.0,
        step = 0.1,
        formatter = { "%.1f".format(it.toDouble()) },
        onChange = { onChange(inputs.copy(textZoom = it.toDouble())) }
    )

    StepperControl(
        label = "Line width zoom [-1, 1]",
        value = inputs.lineWidthZoom,
        min = -1.0,
        max = 1.0,
        step = 0.1,
        formatter = { "%.1f".format(it.toDouble()) },
        onChange = { onChange(inputs.copy(lineWidthZoom = it.toDouble())) }
    )

    Row(Modifier.fillMaxWidth()) {
        Checkbox(inputs.showDetails, { onChange(inputs.copy(showDetails = it)) })
        Text("Show station markers")
    }
    Row(Modifier.fillMaxWidth()) {
        Checkbox(inputs.showGrid, { onChange(inputs.copy(showGrid = it)) })
        Text("Show grid")
    }
    }
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

    Row(
        modifier = Modifier.fillMaxWidth().testTag(label),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, modifier = Modifier.weight(1f))
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(
                onClick = { updateValue(false) },
                enabled = canDecrease,
                modifier = Modifier
                     .semantics { contentDescription = "−" }
                     .testTag("${label}_−")
            ) {
                Icon(Icons.Filled.Remove, contentDescription = "Decrease")
            }
            Text(text = formatter(value))
            IconButton(
                onClick = { updateValue(true) },
                enabled = canIncrease,
                modifier = Modifier
                     .semantics { contentDescription = "+" }
                     .testTag("${label}_+")
            ) {
                Icon(Icons.Filled.Add, contentDescription = "Increase")
            }
        }
    }
}
