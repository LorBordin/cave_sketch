package com.cavesketch.app.ui.components

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.util.safeCopyFileToUri
import com.cavesketch.app.util.shareFile

@Composable
fun SaveShareButton(
    label: String,
    path: String,
    mimeType: String,
    displayName: String,
    modifier: Modifier = Modifier,
    onError: (String) -> Unit = {},
    onSaved: () -> Unit = {},
) {
    val context = LocalContext.current
    var expanded by remember { mutableStateOf(false) }

    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument(mimeType)
    ) { uri ->
        if (uri != null) {
            val result = safeCopyFileToUri(context, path, uri, onError)
            if (result != null) {
                onSaved()
            }
        }
    }

    Box(modifier = modifier) {
        Button(
            onClick = { expanded = true },
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
        ) {
            Text(label)
        }
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false },
        ) {
            DropdownMenuItem(
                text = { Text("Save to Device") },
                onClick = {
                    expanded = false
                    launcher.launch(displayName)
                },
            )
            DropdownMenuItem(
                text = { Text("Share") },
                onClick = {
                    expanded = false
                    shareFile(context, path, mimeType, displayName)
                },
            )
        }
    }
}
