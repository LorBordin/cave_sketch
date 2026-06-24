package com.cavesketch.app.ui

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.Terrain
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.cavesketch.app.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppNavHost(
    surveyViewModel: SurveyPlotViewModel,
    satelliteViewModel: SatelliteViewModel,
    versionName: String,
) {
    val nav = rememberNavController()
    val current = nav.currentBackStackEntryAsState().value?.destination?.route
    val title = when (current) {
        "satellite" -> "Satellite Map"
        "about" -> "About"
        else -> "Survey Plot"
    }
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(title) },
                navigationIcon = {
                    Image(
                        painter = painterResource(R.drawable.splash_icon),
                        contentDescription = null,
                        modifier = Modifier.padding(start = 12.dp).size(28.dp),
                    )
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface,
                    titleContentColor = MaterialTheme.colorScheme.onSurface,
                ),
            )
        },
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                val navColors = NavigationBarItemDefaults.colors(
                    selectedIconColor = MaterialTheme.colorScheme.primary,
                    selectedTextColor = MaterialTheme.colorScheme.primary,
                    indicatorColor = MaterialTheme.colorScheme.primary.copy(alpha = 0.18f),
                    unselectedIconColor = MaterialTheme.colorScheme.onSurfaceVariant,
                    unselectedTextColor = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                NavigationBarItem(
                    selected = current == "survey_plot",
                    onClick = { nav.navigate("survey_plot") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Terrain, null) },
                    label = { Text("Survey") },
                    colors = navColors,
                )
                NavigationBarItem(
                    selected = current == "satellite",
                    onClick = { nav.navigate("satellite") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Map, null) },
                    label = { Text("Satellite") },
                    colors = navColors,
                )
                NavigationBarItem(
                    selected = current == "about",
                    onClick = { nav.navigate("about") { launchSingleTop = true } },
                    icon = { Icon(Icons.Filled.Info, null) },
                    label = { Text("About") },
                    colors = navColors,
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
