package com.cavesketch.app.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Terrain
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController

@Composable
fun AppNavHost(
    surveyViewModel: SurveyPlotViewModel,
    satelliteViewModel: SatelliteViewModel,
    versionName: String,
) {
    val nav = rememberNavController()
    val current = nav.currentBackStackEntryAsState().value?.destination?.route
    Scaffold(
        bottomBar = {
            NavigationBar {
                NavigationBarItem(
                    selected = current == "survey_plot",
                    onClick = { nav.navigate("survey_plot") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Terrain, null) },
                    label = { Text("Survey") },
                )
                NavigationBarItem(
                    selected = current == "satellite",
                    onClick = { nav.navigate("satellite") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Map, null) },
                    label = { Text("Satellite") },
                )
                NavigationBarItem(
                    selected = current == "about",
                    onClick = { nav.navigate("about") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Info, null) },
                    label = { Text("About") },
                )
            }
        }
    ) { padding ->
        NavHost(nav, startDestination = "survey_plot", modifier = Modifier.padding(padding)) {
            composable("survey_plot") { SurveyPlotScreen(surveyViewModel) }
            composable("satellite") { SatelliteScreen(satelliteViewModel) }
            composable("about") { AboutScreen(versionName) }
        }
    }
}
