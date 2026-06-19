package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.components.FilePickerRow
import com.cavesketch.app.ui.components.SettingsForm
import com.cavesketch.app.util.copyUriToDir
import com.cavesketch.app.util.extensionOf

@Composable
fun SurveyPlotScreen() {
    val context = LocalContext.current
    var inputs by remember { mutableStateOf(SurveyInputs()) }

    Column(Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {
        Text("Survey Plot")

        FilePickerRow("Pick Cave Map", inputs.mapPath?.let { "map" + extOf(it) }) { uri ->
            val path = copyUriToDir(context, uri, context.filesDir, "map" + extensionOf(context, uri))
            inputs = inputs.copy(mapPath = path)
        }
        FilePickerRow("Pick Cave Section", inputs.sectionPath?.let { "section" + extOf(it) }) { uri ->
            val path = copyUriToDir(context, uri, context.filesDir, "section" + extensionOf(context, uri))
            inputs = inputs.copy(sectionPath = path)
        }

        com.cavesketch.app.ui.components.MergeControls(inputs, context) { inputs = it }

        OutlinedTextField(
            value = inputs.surveyName,
            onValueChange = { inputs = inputs.copy(surveyName = it) },
            label = { Text("Survey name") },
        )
        OutlinedTextField(
            value = inputs.surveyorName,
            onValueChange = { inputs = inputs.copy(surveyorName = it) },
            label = { Text("Surveyor name") },
        )

        SettingsForm(inputs) { inputs = it }
    }
}

private fun extOf(path: String) = if (path.lowercase().endsWith(".dxf")) ".dxf" else ".csv"
