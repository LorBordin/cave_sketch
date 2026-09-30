# Spec: Save Exported Artifacts to Device Storage (Android)

## Overview

The Android app generates several export artifacts — a Survey Plot PDF, and
a Satellite Map's HTML/JSON/KMZ — and every screen labels its export button
**"Save / Share `<X>`"**. In reality, every one of these buttons only calls
`util/Share.kt`'s `shareFile`/`sharePdf`, which launches
`Intent.ACTION_SEND` (the Android share sheet). There is no path that writes
the file directly to device storage — if the user backs out of the share
sheet, or has no installed app that saves shared files locally, the artifact
cannot be kept on the device at all.

This track makes the existing "Save / Share" label true: tapping the button
opens a small menu offering **"Save to Device"** (writes the file to a
location the user picks, via the standard Android file picker) or **"Share"**
(unchanged, today's behavior). One button, one label — no new button is
added to the screens.

## Decisions (locked with maintainer)

| Decision | Choice |
|----------|--------|
| UI shape | Keep the single existing button per artifact; tapping it opens a dropdown menu with two choices, "Save to Device" and "Share". No second button. |
| Save mechanism | Android Storage Access Framework (`ActivityResultContracts.CreateDocument(mimeType)`) — the same "system picker" pattern already used for importing files (`FilePickerRow.kt`, `SatelliteScreen.kt`'s JSON picker). No new runtime permissions: SAF does not require `WRITE_EXTERNAL_STORAGE` at `minSdk 24`+. |
| Error handling | Reuse the existing `runCopy`/`friendlyError` pattern from `util/SafeCopy.kt` so a failed save (e.g. no space) surfaces the same kind of friendly message as a failed import, via each screen's existing `SnackbarHostState`. |
| Scope | All 4 existing export buttons: HTML, JSON, KMZ (`SatelliteScreen.kt`) and PDF (`SurveyPlotScreen.kt`). All four get the same new component. |

## Functional Requirements

### FR-1: Save-to-Uri copy utility
- `util/FileCopy.kt`: add `copyFileToUri(context: Context, sourcePath: String, targetUri: Uri): String`, which opens `sourcePath` and writes its bytes to `targetUri` via `context.contentResolver.openOutputStream(targetUri)`. Mirrors the existing (reverse-direction) `copyUriToDir`. Returns `targetUri.toString()` on success, to fit the existing `runCopy` helper's `() -> String` shape.
- `util/SafeCopy.kt`: add `safeCopyFileToUri(context, sourcePath, targetUri, onError): String?`, wrapping `copyFileToUri` with the existing `runCopy` helper — no changes to `runCopy`/`friendlyError` themselves.

### FR-2: `SaveShareButton` composable
- New `ui/components/SaveShareButton.kt`. Public signature:
  `SaveShareButton(label: String, path: String, mimeType: String, displayName: String, modifier: Modifier = Modifier, onError: (String) -> Unit = {}, onSaved: () -> Unit = {})`.
- Renders a single `Button(label)`. Tapping it opens a Material3 `DropdownMenu`
  anchored to the button with two `DropdownMenuItem`s:
  - **"Save to Device"** — launches an `ActivityResultContracts.CreateDocument(mimeType)` launcher with `displayName` as the suggested file name; on a non-null result `Uri`, calls `safeCopyFileToUri(...)`, invoking `onSaved()` on success or `onError(message)` on failure.
  - **"Share"** — calls the existing `shareFile(context, path, mimeType, displayName)`, unchanged behavior.
- Follows the same `rememberLauncherForActivityResult` idiom already used by `FilePickerRow.kt` and `SatelliteScreen.kt`.

### FR-3: Wire into `SatelliteScreen.kt`
- Replace the three existing "Save / Share HTML/JSON/KMZ" `Button`s with `SaveShareButton` calls, using the screen's existing `showSnackbar` for `onError`, and a short success message for `onSaved` (e.g. `"Saved $name.html"`).
- Remove the now-unused direct `import com.cavesketch.app.util.shareFile` (share is called from inside `SaveShareButton` now).

### FR-4: Wire into `SurveyPlotScreen.kt`
- Replace the "Save / Share PDF" `Button` the same way, using the screen's existing `showSnackbar`.

## Non-Functional Requirements

- No new Android permissions or manifest changes.
- No change to `shareFile`/`sharePdf`'s existing behavior or signatures — both are reused as-is from inside `SaveShareButton`.
- Kotlin/Compose code follows existing project conventions (see `FilePickerRow.kt`, `SafeCopy.kt`).

## Testing Plan

- Unit tests for `copyFileToUri`/`safeCopyFileToUri` (JVM + Robolectric `Context`, using `file://` URIs as stand-ins for a real SAF-returned `content://` URI — `ContentResolver` handles the `file` scheme directly without needing a registered provider).
- A Robolectric + Compose UI test for `SaveShareButton` (same style as `PrimaryCtaTest.kt`): the button renders with its label; tapping it reveals both menu items; tapping "Share" results in a `ACTION_SEND` intent being started with the expected `mimeType`.
- Manual verification on-device/emulator (see plan) for the actual SAF save flow, since a real system file-picker result can't be driven from a Robolectric unit test.

## Out of Scope

- Choosing or remembering a default save directory — the user picks the location every time via the system picker (standard SAF behavior).
- Any change to what gets exported or its format/content.
- A "save all" / batch action across multiple artifacts.
- Any doc updates to `docs/android/architecture.md` — that document doesn't describe the share/export flow today, and this track doesn't change the app's architecture.
