package com.cavesketch.app.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.PlayArrow
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
import com.cavesketch.app.ui.components.GpsPointsEditor
import com.cavesketch.app.ui.components.MapWebView
import com.cavesketch.app.ui.components.PrimaryCta
import com.cavesketch.app.ui.components.SectionCard
import com.cavesketch.app.ui.components.StateBanner
import com.cavesketch.app.ui.components.parsesAsCoordinate
import com.cavesketch.app.ui.components.SaveShareButton

import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.launch

@Composable
fun SatelliteScreen(viewModel: SatelliteViewModel) {
    val context = LocalContext.current
    val state by viewModel.state.collectAsState()
    val points by viewModel.points.collectAsState()
    val jsonMaps by viewModel.jsonMaps.collectAsState()

    var surveyName by remember { mutableStateOf(viewModel.suggestedSurveyName()) }
    var rotationText by remember { mutableStateOf("0") }

    val snackbarHostState = remember { SnackbarHostState() }
    val coroutineScope = rememberCoroutineScope()
    val showSnackbar: (String) -> Unit = { msg ->
        coroutineScope.launch {
            snackbarHostState.showSnackbar(msg)
        }
    }

    val jsonPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        uris.forEachIndexed { idx, uri ->
            val displayName = com.cavesketch.app.util.getDisplayName(context, uri)
            if (!com.cavesketch.app.util.FileValidator.isAcceptedJsonExtension(displayName)) {
                showSnackbar("Unsupported file format. Please select a .json file.")
            } else {
                com.cavesketch.app.util.safeCopyUriToDir(
                    context, uri, context.filesDir, "additional_${jsonMaps.size + idx}.json",
                    { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
                )?.let { viewModel.addJsonMap(it) }
            }
        }
    }

    if (state is SatelliteState.NoMap) {
        Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            StateBanner(
                "Generate a survey plot first — the Satellite Map needs a cave map.",
                isError = false,
            )
        }
        return
    }

    val pointsValid = points.all {
        it.station.isNotBlank() && parsesAsCoordinate(it.lat) && parsesAsCoordinate(it.lon)
    }

    Scaffold(
        snackbarHost = { SnackbarHost(hostState = snackbarHostState) }
    ) { contentPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(contentPadding)
                .padding(16.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
        SectionCard("GPS points", Icons.Filled.Place) {
            GpsPointsEditor(
                points = points,
                onUpdate = viewModel::updatePoint,
                onAdd = viewModel::addPoint,
                onRemove = viewModel::removeLastPoint,
            )
        }

        SectionCard("Map details", Icons.Filled.Edit) {
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
        }

        SectionCard("Additional maps", Icons.Filled.Folder) {
            Button(onClick = { jsonPicker.launch(arrayOf("application/json", "*/*")) }) {
                Text("📁 Import JSON maps (${jsonMaps.size})")
            }
        }

        PrimaryCta(
            text = "Generate Satellite Map",
            icon = Icons.Filled.PlayArrow,
            enabled = pointsValid && state !is SatelliteState.Generating,
            onClick = { viewModel.generate(surveyName) },
        )

        when (val s = state) {
            is SatelliteState.Generating -> {
                Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is SatelliteState.Error -> StateBanner("⚠️ ${s.message}", isError = true)
            is SatelliteState.Success -> {
                if (s.online) {
                    MapWebView(s.htmlPath, Modifier.fillMaxWidth().height(360.dp))
                } else {
                    StateBanner(
                        "No connection — satellite preview unavailable. " +
                            "KMZ & JSON are ready to save/share.",
                        isError = true,
                    )
                }
                Spacer(Modifier.height(8.dp))
                val name = surveyName.ifBlank { "survey" }
                SaveShareButton(
                    label = "Save / Share HTML",
                    path = s.htmlPath,
                    mimeType = "text/html",
                    displayName = "$name.html",
                    modifier = Modifier.fillMaxWidth(),
                    onError = showSnackbar,
                    onSaved = { showSnackbar("Saved $name.html") },
                )
                SaveShareButton(
                    label = "Save / Share JSON",
                    path = s.jsonPath,
                    mimeType = "application/json",
                    displayName = "$name.json",
                    modifier = Modifier.fillMaxWidth(),
                    onError = showSnackbar,
                    onSaved = { showSnackbar("Saved $name.json") },
                )
                SaveShareButton(
                    label = "Save / Share KMZ",
                    path = s.kmzPath,
                    mimeType = "application/vnd.google-earth.kmz",
                    displayName = "$name.kmz",
                    modifier = Modifier.fillMaxWidth(),
                    onError = showSnackbar,
                    onSaved = { showSnackbar("Saved $name.kmz") },
                )
            }
            else -> {}
        }
    }
}
}
