package com.cavesketch.app.ui.components

import android.content.Context
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.selection.selectable
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.cavesketch.app.ui.SurveyInputs
import com.cavesketch.app.util.extensionOf

@Composable
fun MergeControls(inputs: SurveyInputs, context: Context, onChange: (SurveyInputs) -> Unit) {
    Text("Merge another survey (optional)")

    FilePickerRow("Pick Child Map", inputs.childMapPath?.let { "child_map" }) { uri ->
        val p = com.cavesketch.app.util.safeCopyUriToDir(
            context, uri, context.filesDir, "child_map" + extensionOf(context, uri),
            { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
        )
        if (p != null) {
            onChange(inputs.copy(childMapPath = p))
        }
    }
    FilePickerRow("Pick Child Section", inputs.childSectionPath?.let { "child_section" }) { uri ->
        val p = com.cavesketch.app.util.safeCopyUriToDir(
            context, uri, context.filesDir, "child_section" + extensionOf(context, uri),
            { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
        )
        if (p != null) {
            onChange(inputs.copy(childSectionPath = p))
        }
    }

    val hasChild = inputs.childMapPath != null || inputs.childSectionPath != null
    if (hasChild) {
        OutlinedTextField(
            value = inputs.parentStation,
            onValueChange = { onChange(inputs.copy(parentStation = it)) },
            label = { Text("Main station ID (e.g. 30)") },
        )
        OutlinedTextField(
            value = inputs.childStation,
            onValueChange = { onChange(inputs.copy(childStation = it)) },
            label = { Text("Child station ID (e.g. 47)") },
        )
        if (inputs.childSectionPath != null) {
            Text("Section merge protocol")
            listOf("simple", "mirror", "displacement").forEach { proto ->
                Row(Modifier.selectable(
                    selected = inputs.sectionProtocol == proto,
                    onClick = { onChange(inputs.copy(sectionProtocol = proto)) },
                )) {
                    RadioButton(inputs.sectionProtocol == proto, null)
                    Text(proto.replaceFirstChar { it.uppercase() })
                }
            }
        }
    }
}
