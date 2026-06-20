package com.cavesketch.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { MaterialTheme { App() } }
    }
}

@Composable
fun App() {
    val context = androidx.compose.ui.platform.LocalContext.current
    val store = androidx.compose.runtime.remember { com.cavesketch.app.data.SurveyResultStore() }
    val viewModel = androidx.lifecycle.viewmodel.compose.viewModel<com.cavesketch.app.ui.SurveyPlotViewModel>(
        factory = object : androidx.lifecycle.ViewModelProvider.Factory {
            @Suppress("UNCHECKED_CAST")
            override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T =
                com.cavesketch.app.ui.SurveyPlotViewModel(
                    com.cavesketch.app.bridge.PythonBridge(kotlinx.coroutines.Dispatchers.IO),
                    context.filesDir.absolutePath,
                    kotlinx.coroutines.Dispatchers.IO,
                    store,
                ) as T
        }
    )
    com.cavesketch.app.ui.AppNavHost(viewModel)
}
