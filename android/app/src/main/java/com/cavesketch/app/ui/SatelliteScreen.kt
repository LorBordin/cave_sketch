package com.cavesketch.app.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
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
import androidx.compose.material3.MaterialTheme
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
import com.cavesketch.app.ui.components.GpsPointsEditor
import com.cavesketch.app.ui.components.MapWebView
import com.cavesketch.app.ui.components.parsesAsCoordinate
import com.cavesketch.app.util.shareFile

@Composable
fun SatelliteScreen(viewModel: SatelliteViewModel) {
    val context = LocalContext.current
    val state by viewModel.state.collectAsState()
    val points by viewModel.points.collectAsState()
    val jsonMaps by viewModel.jsonMaps.collectAsState()

    var surveyName by remember { mutableStateOf(viewModel.suggestedSurveyName()) }
    var rotationText by remember { mutableStateOf("0") }

    val jsonPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        uris.forEachIndexed { idx, uri ->
            com.cavesketch.app.util.safeCopyUriToDir(
                context, uri, context.filesDir, "additional_${jsonMaps.size + idx}.json",
                { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
            )?.let { viewModel.addJsonMap(it) }
        }
    }

    if (state is SatelliteState.NoMap) {
        Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            Text("Generate a survey plot first — the Satellite Map needs a cave map.")
        }
        return
    }

    val pointsValid = points.all {
        it.station.isNotBlank() && parsesAsCoordinate(it.lat) && parsesAsCoordinate(it.lon)
    }

    Column(Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState())) {
        Text("🌍 Satellite Map")

        GpsPointsEditor(
            points = points,
            onUpdate = viewModel::updatePoint,
            onAdd = viewModel::addPoint,
            onRemove = viewModel::removeLastPoint,
        )

        OutlinedTextField(
            value = surveyName,
            onValueChange = { surveyName = it },
            label = { Text("Survey name") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = rotationText,
            onValueChange = {
                rotationText = it
                it.trim().replace(",", ".").toDoubleOrNull()?.let(viewModel::setRotation)
            },
            label = { Text("Map rotation angle (°)") },
            isError = rotationText.isNotBlank() && rotationText.trim().replace(",", ".").toDoubleOrNull() == null,
            modifier = Modifier.fillMaxWidth(),
        )

        Spacer(Modifier.height(8.dp))
        Button(onClick = { jsonPicker.launch(arrayOf("application/json", "*/*")) }) {
            Text("📁 Import JSON maps (${jsonMaps.size})")
        }

        Spacer(Modifier.height(16.dp))
        Button(
            enabled = pointsValid && state !is SatelliteState.Generating,
            onClick = { viewModel.generate(surveyName) },
            modifier = Modifier.fillMaxWidth(),
        ) { Text("Generate Satellite Map") }

        Spacer(Modifier.height(16.dp))

        when (val s = state) {
            is SatelliteState.Generating -> {
                Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is SatelliteState.Error -> {
                Text("⚠️ ${s.message}", color = MaterialTheme.colorScheme.error)
            }
            is SatelliteState.Success -> {
                if (s.online) {
                    MapWebView(s.htmlPath, Modifier.fillMaxWidth().height(360.dp))
                } else {
                    Text(
                        "No connection — satellite preview unavailable. " +
                            "KMZ & JSON are ready to save/share.",
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                Spacer(Modifier.height(8.dp))
                val name = surveyName.ifBlank { "survey" }
                Button(
                    onClick = { shareFile(context, s.htmlPath, "text/html", "$name.html") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share HTML") }
                Button(
                    onClick = { shareFile(context, s.jsonPath, "application/json", "$name.json") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share JSON") }
                Button(
                    onClick = { shareFile(context, s.kmzPath, "application/vnd.google-earth.kmz", "$name.kmz") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share KMZ") }
            }
            else -> {}
        }
    }
}
