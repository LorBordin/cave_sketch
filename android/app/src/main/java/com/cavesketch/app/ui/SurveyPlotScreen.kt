package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.components.FilePickerRow
import com.cavesketch.app.ui.components.SettingsForm
import com.cavesketch.app.util.copyUriToDir
import com.cavesketch.app.util.extensionOf

@Composable
fun SurveyPlotScreen(viewModel: SurveyPlotViewModel) {
    val context = LocalContext.current
    var inputs by remember { mutableStateOf(SurveyInputs()) }
    val state by viewModel.state.collectAsState()
    val canGenerate = inputs.mapPath != null || inputs.sectionPath != null

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
            modifier = Modifier.fillMaxWidth()
        )
        OutlinedTextField(
            value = inputs.surveyorName,
            onValueChange = { inputs = inputs.copy(surveyorName = it) },
            label = { Text("Surveyor name") },
            modifier = Modifier.fillMaxWidth()
        )

        SettingsForm(inputs) { inputs = it }

        Spacer(Modifier.height(16.dp))

        Button(
            enabled = canGenerate && state !is PlotState.Generating,
            onClick = { viewModel.generate(inputs) },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Generate Survey Plot")
        }

        Spacer(Modifier.height(16.dp))

        when (val s = state) {
            is PlotState.Generating -> {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is PlotState.Error -> {
                Text(
                    "⚠️ ${s.message}",
                    color = androidx.compose.material3.MaterialTheme.colorScheme.error
                )
            }
            is PlotState.Success -> {
                PdfPreview(s.pdfPath)
                Spacer(Modifier.height(8.dp))
                Button(
                    onClick = {
                        val name = inputs.surveyName.ifBlank { "survey" } + ".pdf"
                        com.cavesketch.app.util.sharePdf(context, s.pdfPath, name)
                    },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Save / Share PDF")
                }
            }
            PlotState.Idle -> {}
        }
    }
}

private fun extOf(path: String) = if (path.lowercase().endsWith(".dxf")) ".dxf" else ".csv"

