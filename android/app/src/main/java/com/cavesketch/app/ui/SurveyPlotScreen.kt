package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Tune
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
import com.cavesketch.app.ui.components.MergeControls
import com.cavesketch.app.ui.components.PrimaryCta
import com.cavesketch.app.ui.components.SectionCard
import com.cavesketch.app.ui.components.SettingsForm
import com.cavesketch.app.ui.components.StateBanner
import com.cavesketch.app.util.extensionOf

@Composable
fun SurveyPlotScreen(viewModel: SurveyPlotViewModel) {
    val context = LocalContext.current
    val showError: (String) -> Unit = { msg ->
        android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show()
    }
    var inputs by remember { mutableStateOf(SurveyInputs()) }
    val state by viewModel.state.collectAsState()
    val canGenerate = inputs.mapPath != null || inputs.sectionPath != null

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard("Input files", Icons.Filled.Description) {
            FilePickerRow("Pick Cave Map", inputs.mapPath?.let { "map" + extOf(it) }) { uri ->
                com.cavesketch.app.util.safeCopyUriToDir(
                    context, uri, context.filesDir, "map" + extensionOf(context, uri), showError,
                )?.let { inputs = inputs.copy(mapPath = it) }
            }
            FilePickerRow("Pick Cave Section", inputs.sectionPath?.let { "section" + extOf(it) }) { uri ->
                com.cavesketch.app.util.safeCopyUriToDir(
                    context, uri, context.filesDir, "section" + extensionOf(context, uri), showError,
                )?.let { inputs = inputs.copy(sectionPath = it) }
            }
        }

        SectionCard("Merge survey (optional)", Icons.Filled.Link) {
            MergeControls(inputs, context) { inputs = it }
        }

        SectionCard("Survey details", Icons.Filled.Edit) {
            OutlinedTextField(
                value = inputs.surveyName,
                onValueChange = { inputs = inputs.copy(surveyName = it) },
                label = { Text("Survey name") },
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = inputs.surveyorName,
                onValueChange = { inputs = inputs.copy(surveyorName = it) },
                label = { Text("Surveyor name") },
                modifier = Modifier.fillMaxWidth(),
            )
        }

        SectionCard("Settings", Icons.Filled.Tune) {
            SettingsForm(inputs) { inputs = it }
        }

        PrimaryCta(
            text = "Generate Survey Plot",
            icon = Icons.Filled.PlayArrow,
            enabled = canGenerate && state !is PlotState.Generating,
            onClick = { viewModel.generate(inputs) },
        )

        when (val s = state) {
            is PlotState.Generating -> {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is PlotState.Error -> StateBanner("⚠️ ${s.message}", isError = true)
            is PlotState.Success -> {
                PdfPreview(s.pdfPath)
                Button(
                    onClick = {
                        val name = inputs.surveyName.ifBlank { "survey" } + ".pdf"
                        com.cavesketch.app.util.sharePdf(context, s.pdfPath, name)
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Save / Share PDF")
                }
            }
            PlotState.Idle -> StateBanner("Pick your files and tap Generate.", isError = false)
        }
    }
}

private fun extOf(path: String) = if (path.lowercase().endsWith(".dxf")) ".dxf" else ".csv"
