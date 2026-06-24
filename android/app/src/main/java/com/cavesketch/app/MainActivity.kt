package com.cavesketch.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val initState = (application as CaveSketchApplication).initState
        setContent {
            com.cavesketch.app.ui.theme.CaveSketchTheme {
                val status by initState.status.collectAsState()
                when (val s = status) {
                    is InitStatus.Failed -> InitErrorScreen(s.message)
                    else -> App()
                }
            }
        }
    }
}

@Composable
fun InitErrorScreen(message: String) {
    Surface(modifier = androidx.compose.ui.Modifier.fillMaxSize()) {
        Column(
            modifier = androidx.compose.ui.Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = androidx.compose.ui.Alignment.CenterHorizontally,
            verticalArrangement = androidx.compose.foundation.layout.Arrangement.Center,
        ) {
            Text("CaveSketch couldn’t start", style = androidx.compose.material3.MaterialTheme.typography.headlineSmall)
            androidx.compose.foundation.layout.Spacer(androidx.compose.ui.Modifier.height(12.dp))
            Text(message)
        }
    }
}

@Composable
fun App() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val store = androidx.compose.runtime.remember { com.cavesketch.app.data.SurveyResultStore() }
    val bridge = androidx.compose.runtime.remember {
        com.cavesketch.app.bridge.PythonBridge(kotlinx.coroutines.Dispatchers.IO)
    }
    val filesDir = context.filesDir.absolutePath

    val surveyViewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SurveyPlotViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SurveyPlotViewModel(
                    bridge, filesDir, kotlinx.coroutines.Dispatchers.IO, store,
                ) as T
        }
    )
    val satelliteViewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SatelliteViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SatelliteViewModel(
                    bridge, store, filesDir, kotlinx.coroutines.Dispatchers.IO,
                ) { com.cavesketch.app.util.isOnline(context) } as T
        }
    )
    com.cavesketch.app.ui.AppNavHost(
        surveyViewModel,
        satelliteViewModel,
        com.cavesketch.app.BuildConfig.VERSION_NAME,
    )
}
