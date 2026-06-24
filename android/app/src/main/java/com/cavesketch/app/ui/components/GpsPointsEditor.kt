package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.GpsPoint

/** Mirror of cave_sketch.geo.coordinates.parse_coordinate (decimal, '.'/',' separator). */
fun parsesAsCoordinate(value: String): Boolean =
    value.trim().replace(",", ".").toDoubleOrNull() != null

@Composable
fun GpsPointsEditor(
    points: List<GpsPoint>,
    onUpdate: (Int, GpsPoint) -> Unit,
    onAdd: () -> Unit,
    onRemove: () -> Unit,
) {
    Column(Modifier.fillMaxWidth()) {
        points.forEachIndexed { i, p ->
            Row(Modifier.fillMaxWidth().padding(vertical = 4.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = p.station,
                    onValueChange = { onUpdate(i, p.copy(station = it)) },
                    label = { Text("Station") },
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = p.lat,
                    onValueChange = { onUpdate(i, p.copy(lat = it)) },
                    label = { Text("Lat") },
                    isError = p.lat.isNotBlank() && !parsesAsCoordinate(p.lat),
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = p.lon,
                    onValueChange = { onUpdate(i, p.copy(lon = it)) },
                    label = { Text("Lon") },
                    isError = p.lon.isNotBlank() && !parsesAsCoordinate(p.lon),
                    modifier = Modifier.weight(1f),
                )
            }
        }
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = onAdd, shape = RoundedCornerShape(12.dp)) { Text("➕ Add point") }
            Button(onClick = onRemove, shape = RoundedCornerShape(12.dp)) { Text("➖ Remove last") }
        }
    }
}
