package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.testTag
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.SurveyInputs

/** Optional metadata printed in the PDF title block. */
@Composable
fun TitleBlockFields(inputs: SurveyInputs, onChange: (SurveyInputs) -> Unit) {
    val decimal = KeyboardOptions(keyboardType = KeyboardType.Decimal)
    val error = inputs.titleBlockError()
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedTextField(
            value = inputs.surveyorName,
            onValueChange = { onChange(inputs.copy(surveyorName = it)) },
            label = { Text("Surveyor name") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = inputs.drawerName,
            onValueChange = { onChange(inputs.copy(drawerName = it)) },
            label = { Text("Drawer name") },
            modifier = Modifier.fillMaxWidth().testTag("drawer_field"),
        )
        OutlinedTextField(
            value = inputs.municipality,
            onValueChange = { onChange(inputs.copy(municipality = it)) },
            label = { Text("Municipality") },
            modifier = Modifier.fillMaxWidth().testTag("municipality_field"),
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = inputs.latitude,
                onValueChange = { onChange(inputs.copy(latitude = it)) },
                label = { Text("Latitude (° N)") },
                keyboardOptions = decimal,
                modifier = Modifier.weight(1f).testTag("latitude_field"),
            )
            OutlinedTextField(
                value = inputs.longitude,
                onValueChange = { onChange(inputs.copy(longitude = it)) },
                label = { Text("Longitude (° E)") },
                keyboardOptions = decimal,
                modifier = Modifier.weight(1f).testTag("longitude_field"),
            )
        }
        OutlinedTextField(
            value = inputs.elevationM,
            onValueChange = { onChange(inputs.copy(elevationM = it)) },
            label = { Text("Elevation (m a.s.l.)") },
            keyboardOptions = decimal,
            modifier = Modifier.fillMaxWidth().testTag("elevation_field"),
        )
        if (error != null) {
            Text(
                error,
                color = MaterialTheme.colorScheme.error,
                style = MaterialTheme.typography.bodySmall,
                modifier = Modifier.testTag("title_block_error"),
            )
        }
    }
}
