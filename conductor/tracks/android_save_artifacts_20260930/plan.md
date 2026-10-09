# Plan: Save Exported Artifacts to Device Storage (Android)

> Design spec: `./spec.md`. Follow the standard task workflow in
> `conductor/workflow.md` (Red → Green → verify → commit → git note → mark
> `[x]`), including the Phase Completion Verification and Checkpointing
> Protocol at the end of each phase below.

## Global Constraints

- No new Android permissions or manifest changes — the save path uses
  Storage Access Framework (`ActivityResultContracts.CreateDocument`), which
  needs none at `minSdk 24`+.
- `shareFile`/`sharePdf` in `util/Share.kt` are reused unchanged.
- `runCopy`/`friendlyError` in `util/SafeCopy.kt` are reused unchanged — new
  code wraps them, doesn't modify them.
- One button per artifact, same label as today ("Save / Share `<X>`") — no
  second button is added to either screen.
- Test commands: `cd android && ./gradlew :app:testDebugUnitTest` (unit +
  Robolectric/Compose tests) and `./gradlew :app:assembleDebug` (compile
  check) after each phase.

---

## Phase 1: Save-to-Device Building Blocks (utility + component) [checkpoint: c31f949]

- [x] Task: Write tests — `copyFileToUri` / `safeCopyFileToUri` [775f060]
    - [x] In `android/app/src/test/java/com/cavesketch/app/util/SafeCopyTest.kt`
      (or a new `FileCopyTest.kt` alongside it), add tests covering:
      - `copyFileToUri` copies the exact bytes of a source file to a target
        `file://` URI and returns the URI's string form.
      - `safeCopyFileToUri` returns the same value on success, with `onError`
        never invoked.
      - `safeCopyFileToUri` returns `null` and calls `onError` with a
        friendly message when the source path doesn't exist (reusing
        `runCopy`, so this exercises the existing `friendlyError` mapping —
        no new error-message logic to test).
    - [x] Run `./gradlew :app:testDebugUnitTest --tests "*FileCopy*" --tests "*SafeCopy*"`;
      confirm the new tests fail (Red) — `copyFileToUri`/`safeCopyFileToUri`
      don't exist yet.
- [x] Task: Implement `copyFileToUri` / `safeCopyFileToUri` [775f060]
    - [x] In `util/FileCopy.kt`, add
      `copyFileToUri(context: Context, sourcePath: String, targetUri: Uri): String`:
      open `File(sourcePath).inputStream()`, copy into
      `context.contentResolver.openOutputStream(targetUri)` (`requireNotNull`
      it, matching `copyUriToDir`'s null-check style), return
      `targetUri.toString()`.
    - [x] In `util/SafeCopy.kt`, add
      `safeCopyFileToUri(context, sourcePath, targetUri, onError): String? = runCopy({ copyFileToUri(context, sourcePath, targetUri) }, onError)`.
    - [x] Re-run the tests from the previous task; confirm they pass (Green).
- [x] Task: Write tests — `SaveShareButton` [20a9cd4]
    - [x] New `android/app/src/test/java/com/cavesketch/app/ui/components/SaveShareButtonTest.kt`,
      Robolectric + `createComposeRule` (same style as `PrimaryCtaTest.kt`).
      Cover:
      - The button renders with the given `label` text.
      - Tapping it reveals two menu items, "Save to Device" and "Share".
      - Tapping "Share" results in an `ACTION_SEND` intent having been
        started (assert via Robolectric's `Shadows.shadowOf(application).nextStartedActivity`)
        with the expected `type` (mimeType).
    - [x] Run `./gradlew :app:testDebugUnitTest --tests "*SaveShareButton*"`;
      confirm it fails (Red) — the composable doesn't exist yet.
- [x] Task: Implement `SaveShareButton` [c31f949]
    - [x] New `android/app/src/main/java/com/cavesketch/app/ui/components/SaveShareButton.kt`:
      `@Composable fun SaveShareButton(label: String, path: String, mimeType: String, displayName: String, modifier: Modifier = Modifier, onError: (String) -> Unit = {}, onSaved: () -> Unit = {})`.
      - `var expanded by remember { mutableStateOf(false) }`.
      - `rememberLauncherForActivityResult(ActivityResultContracts.CreateDocument(mimeType))`
        callback: on non-null `Uri`, call `safeCopyFileToUri(context, path, uri, onError)?.let { onSaved() }`.
      - `Box(modifier) { Button(onClick = { expanded = true }, Modifier.fillMaxWidth()) { Text(label) }; DropdownMenu(expanded, { expanded = false }) { DropdownMenuItem("Save to Device") { expanded = false; launcher.launch(displayName) }; DropdownMenuItem("Share") { expanded = false; shareFile(context, path, mimeType, displayName) } } }`.
    - [x] Re-run the tests from the previous task; confirm they pass (Green).
- [x] Task: Conductor - User Manual Verification 'Phase 1: Save-to-Device Building Blocks' (Protocol in workflow.md)
    - [x] Run `./gradlew :app:testDebugUnitTest`; confirm the full unit test
      suite passes (no regressions).
    - [x] Run `./gradlew :app:assembleDebug`; confirm `BUILD SUCCESSFUL`.
    - [x] No user-visible change yet at this checkpoint (the component isn't
      wired into any screen) — present this as a code-only checkpoint and
      confirm with the user before proceeding to Phase 2.
- [x] Commit: `test(util): add tests for copyFileToUri and safeCopyFileToUri`,
  `feat(util): add copyFileToUri and safeCopyFileToUri`,
  `test(ui): add SaveShareButtonTest`,
  `feat(ui): add SaveShareButton composable with save/share menu`
  (one commit per Red/Green pair, per `conductor/workflow.md`).

## Phase 2: Wire `SaveShareButton` into Both Screens [checkpoint: ab0a8d2]

- [x] Task: Implement — `SatelliteScreen.kt` [ab0a8d2]
    - [x] Replace the three `Button(onClick = { shareFile(...) })` blocks
      (HTML, JSON, KMZ) with `SaveShareButton(...)`, passing
      `Modifier.fillMaxWidth()`, `onError = showSnackbar`, and
      `onSaved = { showSnackbar("Saved $name.<ext>") }` for each.
    - [x] Remove the now-unused `import com.cavesketch.app.util.shareFile`
      and add `import com.cavesketch.app.ui.components.SaveShareButton`.
- [x] Task: Implement — `SurveyPlotScreen.kt` [ab0a8d2]
    - [x] Replace the "Save / Share PDF" `Button` with `SaveShareButton(...)`
      the same way, using the screen's existing `showSnackbar`.
    - [x] Add `import com.cavesketch.app.ui.components.SaveShareButton`.
- [x] Task: Regression-test and verify [ab0a8d2]
    - [x] Run `./gradlew :app:testDebugUnitTest`; confirm the full suite
      passes.
    - [x] Run `./gradlew :app:assembleDebug`; confirm `BUILD SUCCESSFUL`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Wire SaveShareButton into Both Screens' (Protocol in workflow.md)
    - [x] Install on device/emulator: `./gradlew :app:installDebug`.
    - [x] Generate a Survey Plot PDF; tap "Save / Share PDF"; confirm the
      menu shows "Save to Device" / "Share".
    - [x] Tap "Save to Device"; pick a location (e.g. Downloads) in the
      system picker; confirm the PDF appears there and opens correctly.
    - [x] Tap "Share" on the same button; confirm the Android share sheet
      opens as it does today.
    - [x] Generate a Satellite Map; repeat both checks ("Save to Device" +
      "Share") for the HTML, JSON, and KMZ buttons.
    - [x] Force a save failure (e.g. cancel the system picker mid-flow, or
      fill the device storage) and confirm a friendly snackbar message
      appears rather than a crash.
    - [x] **Does this meet your expectations? Please confirm with yes or
      provide feedback on what needs to be changed.**
- [x] Commit: `feat(ui): wire SaveShareButton into SatelliteScreen and SurveyPlotScreen`.
