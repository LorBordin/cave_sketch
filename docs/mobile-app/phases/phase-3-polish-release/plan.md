# Phase 3 — Polish & Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the working CaveSketch Android app (Phases 0–2) into a downloadable, release-signed `.apk` — branded (icon, splash, light theme), hardened against the realistic field failures, with an About screen — published to GitHub Releases.

**Architecture:** Additive polish over the existing Kotlin/Compose + Chaquopy app. New pure-logic helpers are TDD'd as plain JVM unit tests (`app/src/test`). UI, theming, splash, icon, and Gradle release config are implemented then verified by compile/build and manual device checks. The shared Python `cave_sketch/` core is **not** touched.

**Tech Stack:** Kotlin, Jetpack Compose (Material3), AndroidX Navigation, `androidx.core:core-splashscreen`, Chaquopy (CPython on device), Gradle (AGP 8.5.0, Kotlin 1.9.24), JUnit4 + kotlinx-coroutines-test + Robolectric for tests, Pillow (`uv run python`) for icon asset generation.

## Global Constraints

- `cave_sketch/` stays **untouched and Streamlit-free** — no edits to any file under `cave_sketch/`.
- Streamlit web app behaviour unchanged — no edits under `app/` (the Python web UI).
- Python project managed with **`uv`** (never bare `pip`); commit `uv.lock` if it changes.
- App display name stays **"CaveSketch"**.
- Release version: **`versionName "1.0.0"`, `versionCode 1`**.
- Distribution: **GitHub Releases** sideload only — no Play Store, no CI pipeline.
- Repo URL (for About link / RELEASE.md): `https://github.com/LorBordin/cave_sketch`.
- Verification gates before "done": `uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest`, and Kotlin unit tests (`./gradlew :app:testDebugUnitTest`) all pass. Log the phase to `android/DEVLOG.md`.
- All Gradle commands run from the `android/` directory using `./gradlew`.

---

### Task 1: Friendly error-message helper

Maps low-level throwables (out-of-space, Python/runtime failures) to non-technical messages, used by both generation ViewModels' catch blocks instead of the raw `e.message`.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/util/ErrorMessages.kt`
- Create: `android/app/src/test/java/com/cavesketch/app/util/ErrorMessagesTest.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt:90-92`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt:90-92`

**Interfaces:**
- Produces: `fun com.cavesketch.app.util.friendlyError(t: Throwable): String`

- [x] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/util/ErrorMessagesTest.kt`:

```kotlin
package com.cavesketch.app.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.IOException

class ErrorMessagesTest {
    @Test
    fun no_space_message_is_friendly() {
        val msg = friendlyError(IOException("write failed: ENOSPC (No space left on device)"))
        assertTrue(msg.contains("space", ignoreCase = true))
        assertTrue(msg.contains("free up", ignoreCase = true))
    }

    @Test
    fun python_runtime_failure_is_friendly() {
        val msg = friendlyError(RuntimeException("com.chaquo.python.PyException: boom"))
        assertTrue(msg.contains("engine", ignoreCase = true))
    }

    @Test
    fun unknown_error_falls_back_to_message() {
        assertEquals("boom", friendlyError(IllegalStateException("boom")))
    }

    @Test
    fun null_message_has_generic_fallback() {
        assertEquals("Something went wrong. Please try again.", friendlyError(RuntimeException()))
    }
}
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.util.ErrorMessagesTest"`
Expected: FAIL — `friendlyError` unresolved reference (compilation error).

- [x] **Step 3: Write minimal implementation**

Create `android/app/src/main/java/com/cavesketch/app/util/ErrorMessages.kt`:

```kotlin
package com.cavesketch.app.util

/**
 * Maps a low-level [Throwable] to a short, non-technical message suitable for the
 * UI. Known field failures (no storage, Python runtime) get tailored copy; anything
 * else falls back to the throwable's own message, then a generic line.
 */
fun friendlyError(t: Throwable): String {
    val raw = (t.message ?: "") + " " + (t.cause?.message ?: "")
    return when {
        raw.contains("ENOSPC", ignoreCase = true) ||
            raw.contains("No space left", ignoreCase = true) ->
            "Not enough free space on the device. Free up some storage and try again."
        raw.contains("chaquo", ignoreCase = true) ||
            raw.contains("PyException", ignoreCase = true) ->
            "The CaveSketch engine hit a problem while processing. Please try again."
        else -> t.message ?: "Something went wrong. Please try again."
    }
}
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.util.ErrorMessagesTest"`
Expected: PASS (4 tests).

- [x] **Step 5: Wire into both ViewModels**

In `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt`, change the catch block (lines ~90-92):

```kotlin
            } catch (e: Throwable) {
                _state.value = PlotState.Error(com.cavesketch.app.util.friendlyError(e))
            }
```

In `android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt`, change the catch block (lines ~90-92):

```kotlin
            } catch (e: Throwable) {
                _state.value = SatelliteState.Error(com.cavesketch.app.util.friendlyError(e))
            }
```

- [x] **Step 6: Run the full unit-test suite to verify nothing broke**

Run: `cd android && ./gradlew :app:testDebugUnitTest`
Expected: PASS (existing ViewModel/SettingsForm tests still green — note the existing `error_path_emits_error_with_detail` test asserts the message *contains* "boom", which `friendlyError` preserves via the fallback branch).

- [x] **Step 7: Commit** [4ec8fe9]

```bash
git add android/app/src/main/java/com/cavesketch/app/util/ErrorMessages.kt \
        android/app/src/test/java/com/cavesketch/app/util/ErrorMessagesTest.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotViewModel.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SatelliteViewModel.kt
git commit -m "feat(android): friendly error messages for generation failures"
```

---

### Task 2: Session-cleanup single source of truth

Extracts the launch-time cleanup file list (currently inline in `CaveSketchApplication`) into a tested pure function so coverage of all intermediate/output names is explicit and verifiable.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/util/SessionCleanup.kt`
- Create: `android/app/src/test/java/com/cavesketch/app/util/SessionCleanupTest.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt:11-17`

**Interfaces:**
- Produces: `val com.cavesketch.app.util.SESSION_FILES: List<String>`
- Produces: `fun com.cavesketch.app.util.filesToDelete(names: List<String>): List<String>`

- [x] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/util/SessionCleanupTest.kt`:

```kotlin
package com.cavesketch.app.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SessionCleanupTest {
    @Test
    fun fixed_outputs_are_selected_for_deletion() {
        val present = listOf("map.csv", "survey.pdf", "survey.kmz", "keep_me.txt")
        val toDelete = filesToDelete(present)
        assertTrue(toDelete.contains("map.csv"))
        assertTrue(toDelete.contains("survey.pdf"))
        assertTrue(toDelete.contains("survey.kmz"))
        assertFalse(toDelete.contains("keep_me.txt"))
    }

    @Test
    fun additional_json_imports_are_selected() {
        val toDelete = filesToDelete(listOf("additional_0.json", "additional_12.json", "notes.json"))
        assertTrue(toDelete.contains("additional_0.json"))
        assertTrue(toDelete.contains("additional_12.json"))
        assertFalse(toDelete.contains("notes.json"))
    }

    @Test
    fun known_output_set_covers_all_current_artifacts() {
        // Guards against an artifact being added elsewhere without updating cleanup.
        val expected = listOf(
            "map.csv", "section.csv", "child_map.csv", "child_section.csv",
            "merged_map.csv", "survey.pdf", "survey.html", "survey.json", "survey.kmz",
        )
        assertEquals(expected.toSet(), SESSION_FILES.toSet())
    }
}
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.util.SessionCleanupTest"`
Expected: FAIL — `filesToDelete` / `SESSION_FILES` unresolved.

- [x] **Step 3: Write minimal implementation**

Create `android/app/src/main/java/com/cavesketch/app/util/SessionCleanup.kt`:

```kotlin
package com.cavesketch.app.util

/** Fixed-name intermediate + output artifacts written during a session. */
val SESSION_FILES: List<String> = listOf(
    "map.csv", "section.csv", "child_map.csv", "child_section.csv",
    "merged_map.csv", "survey.pdf", "survey.html", "survey.json", "survey.kmz",
)

/** Prefix for imported additional JSON maps (`additional_0.json`, …). */
const val ADDITIONAL_PREFIX: String = "additional_"

/**
 * Given the file names currently in app storage, returns those that are last-run
 * artifacts safe to delete on launch: the fixed [SESSION_FILES] plus any
 * `additional_*` imports.
 */
fun filesToDelete(names: List<String>): List<String> =
    names.filter { it in SESSION_FILES || it.startsWith(ADDITIONAL_PREFIX) }
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.util.SessionCleanupTest"`
Expected: PASS (3 tests).

- [x] **Step 5: Wire into the Application**

In `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt`, replace the inline cleanup block (lines ~11-17) with:

```kotlin
        // Per-session cleanup: remove last run's intermediate + output files.
        val present = filesDir.list()?.toList() ?: emptyList()
        com.cavesketch.app.util.filesToDelete(present).forEach {
            java.io.File(filesDir, it).delete()
        }
```

- [x] **Step 6: Run unit tests + compile**

Run: `cd android && ./gradlew :app:testDebugUnitTest`
Expected: PASS.

- [x] **Step 7: Commit** [456ad74]

```bash
git add android/app/src/main/java/com/cavesketch/app/util/SessionCleanup.kt \
        android/app/src/test/java/com/cavesketch/app/util/SessionCleanupTest.kt \
        android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt
git commit -m "refactor(android): single source of truth for session cleanup"
```

---

### Task 3: Light brand theme (Material3)

Replaces the bare `MaterialTheme {}` with a branded Compose theme (cyan/blue palette from the logo) and switches the manifest window theme to an app-owned style.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/theme/Color.kt`
- Create: `android/app/src/main/java/com/cavesketch/app/ui/theme/Theme.kt`
- Create: `android/app/src/main/res/values/colors.xml`
- Create: `android/app/src/main/res/values/themes.xml`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt:14`
- Modify: `android/app/src/main/AndroidManifest.xml` (`<application android:theme=...>`)

**Interfaces:**
- Produces: `@Composable fun com.cavesketch.app.ui.theme.CaveSketchTheme(content: @Composable () -> Unit)`

- [x] **Step 1: Create the color palette**

Create `android/app/src/main/java/com/cavesketch/app/ui/theme/Color.kt`:

```kotlin
package com.cavesketch.app.ui.theme

import androidx.compose.ui.graphics.Color

// Brand palette derived from the CaveSketch logo (cyan scanner + slate cave).
val BrandCyan = Color(0xFF00B8D4)
val BrandCyanDark = Color(0xFF0091A7)
val BrandSlate = Color(0xFF37474F)
val BrandSlateLight = Color(0xFFCFD8DC)
val BrandBackground = Color(0xFFF7FBFC)
```

- [x] **Step 2: Create the theme**

Create `android/app/src/main/java/com/cavesketch/app/ui/theme/Theme.kt`:

```kotlin
package com.cavesketch.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColors = lightColorScheme(
    primary = BrandCyan,
    onPrimary = Color_White,
    secondary = BrandSlate,
    background = BrandBackground,
    surface = Color_White,
)

private val DarkColors = darkColorScheme(
    primary = BrandCyan,
    secondary = BrandSlateLight,
)

@Composable
fun CaveSketchTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}
```

Add to `Color.kt` the white constant referenced above:

```kotlin
val Color_White = Color(0xFFFFFFFF)
```

- [x] **Step 3: Create XML colors + window theme**

Create `android/app/src/main/res/values/colors.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="brand_cyan">#FF00B8D4</color>
    <color name="brand_background">#FFF7FBFC</color>
    <color name="ic_launcher_background">#FFFFFFFF</color>
</resources>
```

Create `android/app/src/main/res/values/themes.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.CaveSketch" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:windowBackground">@color/brand_background</item>
    </style>
</resources>
```

- [x] **Step 4: Apply the Compose theme**

In `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`, replace line 14:

```kotlin
        setContent { com.cavesketch.app.ui.theme.CaveSketchTheme { App() } }
```

- [x] **Step 5: Point the manifest at the app theme**

In `android/app/src/main/AndroidManifest.xml`, change the `<application>` `android:theme`:

```xml
        android:theme="@style/Theme.CaveSketch">
```

- [x] **Step 6: Compile and run unit tests**

Run: `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest`
Expected: BUILD SUCCESSFUL; tests PASS.

- [x] **Step 7: Commit** [a5019e8]

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/theme/ \
        android/app/src/main/res/values/colors.xml \
        android/app/src/main/res/values/themes.xml \
        android/app/src/main/java/com/cavesketch/app/MainActivity.kt \
        android/app/src/main/AndroidManifest.xml
git commit -m "feat(android): light brand Material3 theme"
```

---

### Task 4: About screen + third nav tab

Adds an About destination to the bottom nav showing the app version (from `BuildConfig`) and a repo link. Requires enabling `BuildConfig` generation.

**Files:**
- Modify: `android/app/build.gradle` (`buildFeatures`, `versionName`/`versionCode`)
- Create: `android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt`
- Create: `android/app/src/test/java/com/cavesketch/app/ui/AboutScreenTest.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt:45`

**Interfaces:**
- Consumes: `CaveSketchTheme` (Task 3).
- Produces: `fun com.cavesketch.app.ui.aboutVersionLine(versionName: String): String`
- Produces: `@Composable fun com.cavesketch.app.ui.AboutScreen(versionName: String)`
- Produces: `AppNavHost(surveyViewModel, satelliteViewModel, versionName: String)` (signature gains a `versionName` param).

- [x] **Step 1: Enable BuildConfig + set release version**

In `android/app/build.gradle`, set the version in `defaultConfig`:

```gradle
        versionCode 1
        versionName "1.0.0"
```

And add `buildConfig` next to `compose` in `buildFeatures`:

```gradle
    buildFeatures {
        compose true
        buildConfig true
    }
```

- [x] **Step 2: Write the failing test for the version line**

Create `android/app/src/test/java/com/cavesketch/app/ui/AboutScreenTest.kt`:

```kotlin
package com.cavesketch.app.ui

import org.junit.Assert.assertEquals
import org.junit.Test

class AboutScreenTest {
    @Test
    fun version_line_is_formatted() {
        assertEquals("Version 1.0.0", aboutVersionLine("1.0.0"))
    }

    @Test
    fun version_line_handles_blank() {
        assertEquals("Version unknown", aboutVersionLine(""))
    }
}
```

- [x] **Step 3: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.ui.AboutScreenTest"`
Expected: FAIL — `aboutVersionLine` unresolved.

- [x] **Step 4: Implement the About screen**

Create `android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt`:

```kotlin
package com.cavesketch.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp

private const val REPO_URL = "https://github.com/LorBordin/cave_sketch"

/** Human-readable version line, tolerant of a blank/missing version name. */
fun aboutVersionLine(versionName: String): String =
    "Version " + versionName.ifBlank { "unknown" }

@Composable
fun AboutScreen(versionName: String) {
    val context = LocalContext.current
    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text("CaveSketch", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text("Cave survey plotting & georeferencing", style = MaterialTheme.typography.bodyMedium)
        Spacer(Modifier.height(16.dp))
        Text(aboutVersionLine(versionName), style = MaterialTheme.typography.bodyLarge)
        Spacer(Modifier.height(24.dp))
        TextButton(onClick = {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(REPO_URL)))
        }) {
            Text("Project on GitHub")
        }
    }
}
```

- [x] **Step 5: Run test to verify it passes**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.ui.AboutScreenTest"`
Expected: PASS (2 tests).

- [x] **Step 6: Add the About destination to the nav host**

Replace the body of `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt` with:

```kotlin
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
```

- [x] **Step 7: Pass the version into the nav host**

In `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`, replace line 45:

```kotlin
    com.cavesketch.app.ui.AppNavHost(
        surveyViewModel,
        satelliteViewModel,
        com.cavesketch.app.BuildConfig.VERSION_NAME,
    )
```

- [x] **Step 8: Compile and test**

Run: `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest`
Expected: BUILD SUCCESSFUL; tests PASS.

- [x] **Step 9: Commit** [1f72236]

```bash
git add android/app/build.gradle \
        android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt \
        android/app/src/test/java/com/cavesketch/app/ui/AboutScreenTest.kt \
        android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt \
        android/app/src/main/java/com/cavesketch/app/MainActivity.kt
git commit -m "feat(android): About screen with version + repo link, bump to 1.0.0"
```

---

### Task 5: App init readiness + init-failure handling

Refactors Python startup so the app exposes an observable init status (Initializing → Ready / Failed). Drives the splash hold (Task 6) and shows a friendly error screen if the Python runtime can't start. Also installs a global uncaught-exception logger.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/AppInitState.kt`
- Create: `android/app/src/test/java/com/cavesketch/app/AppInitStateTest.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`

**Interfaces:**
- Consumes: `friendlyError` (Task 1); `CaveSketchTheme` (Task 3).
- Produces: `sealed interface com.cavesketch.app.InitStatus { Initializing; Ready; data class Failed(message: String) }`
- Produces: `class com.cavesketch.app.AppInitState` with `val status: StateFlow<InitStatus>`, `fun markReady()`, `fun markFailed(message: String)`.
- Produces: `CaveSketchApplication.initState: AppInitState` (public property).

- [x] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/AppInitStateTest.kt`:

```kotlin
package com.cavesketch.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class AppInitStateTest {
    @Test
    fun starts_initializing() {
        assertTrue(AppInitState().status.value is InitStatus.Initializing)
    }

    @Test
    fun mark_ready_transitions_to_ready() {
        val s = AppInitState()
        s.markReady()
        assertTrue(s.status.value is InitStatus.Ready)
    }

    @Test
    fun mark_failed_carries_message() {
        val s = AppInitState()
        s.markFailed("nope")
        assertEquals("nope", (s.status.value as InitStatus.Failed).message)
    }
}
```

- [x] **Step 2: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.AppInitStateTest"`
Expected: FAIL — `AppInitState` / `InitStatus` unresolved.

- [x] **Step 3: Implement the init-state holder**

Create `android/app/src/main/java/com/cavesketch/app/AppInitState.kt`:

```kotlin
package com.cavesketch.app

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/** Lifecycle of the on-device Python runtime startup. */
sealed interface InitStatus {
    data object Initializing : InitStatus
    data object Ready : InitStatus
    data class Failed(val message: String) : InitStatus
}

/** Observable holder for the app's one-time initialization status. */
class AppInitState {
    private val _status = MutableStateFlow<InitStatus>(InitStatus.Initializing)
    val status: StateFlow<InitStatus> = _status.asStateFlow()

    fun markReady() { _status.value = InitStatus.Ready }
    fun markFailed(message: String) { _status.value = InitStatus.Failed(message) }
}
```

- [x] **Step 4: Run test to verify it passes**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.AppInitStateTest"`
Expected: PASS (3 tests).

- [x] **Step 5: Drive readiness from the Application + add uncaught handler**

Replace `android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt` with:

```kotlin
package com.cavesketch.app

import android.app.Application
import android.util.Log
import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform

class CaveSketchApplication : Application() {
    val initState = AppInitState()

    override fun onCreate() {
        super.onCreate()

        // Last-resort logger so an unexpected crash leaves a breadcrumb.
        val previous = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Log.e("CaveSketch", "Uncaught exception on ${thread.name}", throwable)
            previous?.uncaughtException(thread, throwable)
        }

        // Per-session cleanup: remove last run's intermediate + output files.
        val present = filesDir.list()?.toList() ?: emptyList()
        com.cavesketch.app.util.filesToDelete(present).forEach {
            java.io.File(filesDir, it).delete()
        }

        // Start + pre-warm the Python runtime off the UI thread; publish readiness.
        Thread {
            try {
                if (!Python.isStarted()) {
                    Python.start(AndroidPlatform(this))
                }
                // Pay the one-time heavy import + matplotlib font-cache cost here.
                Python.getInstance().getModule("survey_bridge").callAttr("prewarm")
                initState.markReady()
            } catch (t: Throwable) {
                Log.e("CaveSketch", "Python init failed", t)
                initState.markFailed(com.cavesketch.app.util.friendlyError(t))
            }
        }.start()
    }
}
```

Note: `Python.start` moved into the background thread so a failure becomes a `Failed` status instead of crashing `onCreate`.

- [x] **Step 6: Show init status in MainActivity**

In `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`, replace the `MainActivity` class and add an init-error composable. Update `onCreate` and add the status gate inside `setContent`:

```kotlin
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
            Text("CaveSketch couldn’t start", style = MaterialTheme.typography.headlineSmall)
            androidx.compose.foundation.layout.Spacer(androidx.compose.ui.Modifier.height(12.dp))
            Text(message)
        }
    }
}
```

Add these imports at the top of `MainActivity.kt` (alongside the existing ones):

```kotlin
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.unit.dp
```

- [x] **Step 7: Compile and test**

Run: `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest`
Expected: BUILD SUCCESSFUL; tests PASS.

- [x] **Step 8: Commit** [386b133]

```bash
git add android/app/src/main/java/com/cavesketch/app/AppInitState.kt \
        android/app/src/test/java/com/cavesketch/app/AppInitStateTest.kt \
        android/app/src/main/java/com/cavesketch/app/CaveSketchApplication.kt \
        android/app/src/main/java/com/cavesketch/app/MainActivity.kt
git commit -m "feat(android): observable Python init status + init-failure screen"
```

---

### Task 6: Branded splash held until Python is ready

Adds `core-splashscreen`, a splash theme, and holds the splash on cold start until `AppInitState` leaves `Initializing`.

**Files:**
- Modify: `android/app/build.gradle` (dependency)
- Modify: `android/app/src/main/res/values/themes.xml`
- Modify: `android/app/src/main/AndroidManifest.xml`
- Modify: `android/app/src/main/java/com/cavesketch/app/MainActivity.kt:onCreate`

**Interfaces:**
- Consumes: `CaveSketchApplication.initState` + `InitStatus` (Task 5); `@drawable/ic_launcher_foreground` (created in Task 7 — see Step 3 fallback).

- [ ] **Step 1: Add the dependency**

In `android/app/build.gradle`, add to `dependencies`:

```gradle
    implementation "androidx.core:core-splashscreen:1.0.1"
```

- [ ] **Step 2: Add the splash theme**

In `android/app/src/main/res/values/themes.xml`, add a splash style (sibling of `Theme.CaveSketch`):

```xml
    <style name="Theme.CaveSketch.Splash" parent="Theme.SplashScreen">
        <item name="windowSplashScreenBackground">@color/brand_background</item>
        <item name="windowSplashScreenAnimatedIcon">@drawable/splash_icon</item>
        <item name="postSplashScreenTheme">@style/Theme.CaveSketch</item>
    </style>
```

- [ ] **Step 3: Add a splash icon drawable**

Until the launcher foreground exists (Task 7), create a simple vector so the build resolves. Create `android/app/src/main/res/drawable/splash_icon.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#00B8D4"
        android:pathData="M54,30 L78,72 L30,72 Z" />
</vector>
```

(Task 7 may repoint `windowSplashScreenAnimatedIcon` to the real launcher foreground if desired; this vector keeps Task 6 self-contained and buildable.)

- [ ] **Step 4: Point the manifest at the splash theme**

In `android/app/src/main/AndroidManifest.xml`, change the `<application android:theme=...>` to the splash theme:

```xml
        android:theme="@style/Theme.CaveSketch.Splash">
```

- [ ] **Step 5: Install + hold the splash**

In `android/app/src/main/java/com/cavesketch/app/MainActivity.kt`, update `onCreate` to install the splash before `super.onCreate` and hold it while initializing:

```kotlin
    override fun onCreate(savedInstanceState: Bundle?) {
        val splash = androidx.core.splashscreen.SplashScreen.installSplashScreen(this)
        super.onCreate(savedInstanceState)
        val initState = (application as CaveSketchApplication).initState
        splash.setKeepOnScreenCondition { initState.status.value is InitStatus.Initializing }
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
```

- [ ] **Step 6: Compile and test**

Run: `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest`
Expected: BUILD SUCCESSFUL; tests PASS.

- [ ] **Step 7: Manual device check**

Install on a real device (`./gradlew installDebug`), cold-start the app. Expected: branded splash shows on the `brand_background` color and remains until the screens are interactive (no blank/dead UI while Python warms up).

- [ ] **Step 8: Commit**

```bash
git add android/app/build.gradle \
        android/app/src/main/res/values/themes.xml \
        android/app/src/main/res/drawable/splash_icon.xml \
        android/app/src/main/AndroidManifest.xml \
        android/app/src/main/java/com/cavesketch/app/MainActivity.kt
git commit -m "feat(android): branded splash held until Python runtime is ready"
```

---

### Task 7: Adaptive launcher icon from logo.png

Generates launcher icon assets from `imgs/logo.png` with a Pillow script, adds the adaptive-icon XML, and wires the manifest icon.

**Files:**
- Create: `android/tools/gen_launcher_icons.py`
- Create (generated): `android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml`
- Create (generated): `android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml`
- Create (generated): `android/app/src/main/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher.png`, `ic_launcher_round.png`
- Create (generated): `android/app/src/main/res/drawable-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/ic_launcher_foreground.png`
- Modify: `android/app/src/main/AndroidManifest.xml` (`android:icon`, `android:roundIcon`)

**Interfaces:**
- Consumes: `@color/ic_launcher_background` (defined in Task 3 `colors.xml`).

- [ ] **Step 1: Write the icon generator**

Create `android/tools/gen_launcher_icons.py`:

```python
"""Generate Android launcher icon assets from imgs/logo.png.

Run from the repo root with the project env:
    uv run python android/tools/gen_launcher_icons.py
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO_ROOT, "imgs", "logo.png")
RES = os.path.join(REPO_ROOT, "android", "app", "src", "main", "res")

# Legacy square launcher sizes (px) and adaptive foreground sizes (px).
LEGACY = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
FOREGROUND = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}
BG = (255, 255, 255, 255)  # matches @color/ic_launcher_background


def load_emblem() -> Image.Image:
    """Load the logo and tightly crop to the non-white/non-transparent emblem."""
    img = Image.open(SRC).convert("RGBA")
    # Build a mask of "ink" pixels (not near-white, not transparent).
    px = img.load()
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    mdraw = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 20 and not (r > 245 and g > 245 and b > 245):
                mdraw[x, y] = 255
    bbox = mask.getbbox()
    return img.crop(bbox) if bbox else img


def square_canvas(emblem: Image.Image, size: int, scale: float, bg) -> Image.Image:
    """Center the emblem on a square RGBA canvas at the given fractional scale."""
    canvas = Image.new("RGBA", (size, size), bg)
    target = int(size * scale)
    e = emblem.copy()
    e.thumbnail((target, target), Image.LANCZOS)
    ox = (size - e.width) // 2
    oy = (size - e.height) // 2
    canvas.alpha_composite(e, (ox, oy))
    return canvas


def round_mask(size: int) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size - 1, size - 1), fill=255)
    return m


def write(img: Image.Image, folder: str, name: str) -> None:
    d = os.path.join(RES, folder)
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, name))


def main() -> None:
    emblem = load_emblem()
    for dens, size in LEGACY.items():
        sq = square_canvas(emblem, size, 0.82, BG)
        write(sq, f"mipmap-{dens}", "ic_launcher.png")
        rnd = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        rnd.paste(sq, (0, 0), round_mask(size))
        write(rnd, f"mipmap-{dens}", "ic_launcher_round.png")
    for dens, size in FOREGROUND.items():
        # Transparent foreground; emblem within the ~66% adaptive safe zone.
        fg = square_canvas(emblem, size, 0.60, (0, 0, 0, 0))
        write(fg, f"drawable-{dens}", "ic_launcher_foreground.png")
    print("Launcher icons generated under", RES)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the generator**

Run: `uv run python android/tools/gen_launcher_icons.py`
Expected: prints "Launcher icons generated…"; PNGs appear under `mipmap-*` and `drawable-*`.

- [ ] **Step 3: Add the adaptive-icon XML**

Create `android/app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
```

Create `android/app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml` with identical content.

- [ ] **Step 4: Wire the manifest icon**

In `android/app/src/main/AndroidManifest.xml`, add to `<application>`:

```xml
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
```

- [ ] **Step 5: (Optional) point the splash at the real foreground**

In `android/app/src/main/res/values/themes.xml`, you may change the splash icon to the launcher foreground:

```xml
        <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
```

- [ ] **Step 6: Build and verify**

Run: `cd android && ./gradlew :app:assembleDebug`
Expected: BUILD SUCCESSFUL.

- [ ] **Step 7: Manual device check**

`./gradlew installDebug` and confirm the launcher icon shows the CaveSketch emblem (square and round/adaptive launchers).

- [ ] **Step 8: Commit**

```bash
git add android/tools/gen_launcher_icons.py \
        android/app/src/main/res/mipmap-anydpi-v26/ \
        android/app/src/main/res/mipmap-mdpi/ android/app/src/main/res/mipmap-hdpi/ \
        android/app/src/main/res/mipmap-xhdpi/ android/app/src/main/res/mipmap-xxhdpi/ \
        android/app/src/main/res/mipmap-xxxhdpi/ \
        android/app/src/main/res/drawable-mdpi/ android/app/src/main/res/drawable-hdpi/ \
        android/app/src/main/res/drawable-xhdpi/ android/app/src/main/res/drawable-xxhdpi/ \
        android/app/src/main/res/drawable-xxxhdpi/ \
        android/app/src/main/res/values/themes.xml \
        android/app/src/main/AndroidManifest.xml
git commit -m "feat(android): adaptive launcher icon from logo"
```

---

### Task 8: Storage-full handling on file import

Wraps the picked-file copy call sites so an `IOException` (e.g. disk full) shows a friendly toast via `friendlyError` instead of crashing the picker callback.

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/util/SafeCopy.kt`
- Create: `android/app/src/test/java/com/cavesketch/app/util/SafeCopyTest.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt:40-47`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt:21-25`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt:48-51`

**Interfaces:**
- Consumes: `friendlyError` (Task 1); `copyUriToDir` (existing, `FileCopy.kt`).
- Produces: `fun com.cavesketch.app.util.safeCopyUriToDir(context, uri, dir, fileName, onError: (String) -> Unit): String?` — returns the path on success, or `null` after invoking `onError` with a friendly message.

- [ ] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/util/SafeCopyTest.kt`:

```kotlin
package com.cavesketch.app.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.io.IOException

class SafeCopyTest {
    @Test
    fun returns_path_on_success() {
        var err: String? = null
        val result = runCopy({ "/tmp/map.csv" }, { err = it })
        assertEquals("/tmp/map.csv", result)
        assertNull(err)
    }

    @Test
    fun reports_friendly_error_and_returns_null_on_failure() {
        var err: String? = null
        val result = runCopy(
            { throw IOException("ENOSPC (No space left on device)") },
            { err = it },
        )
        assertNull(result)
        assertEquals(
            "Not enough free space on the device. Free up some storage and try again.",
            err,
        )
    }
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.util.SafeCopyTest"`
Expected: FAIL — `runCopy` unresolved.

- [ ] **Step 3: Implement the safe-copy helper**

Create `android/app/src/main/java/com/cavesketch/app/util/SafeCopy.kt`:

```kotlin
package com.cavesketch.app.util

import android.content.Context
import android.net.Uri
import java.io.File

/**
 * Core of [safeCopyUriToDir], split out for unit testing: runs [copy], and on any
 * throwable invokes [onError] with a friendly message and returns null.
 */
internal inline fun runCopy(copy: () -> String, onError: (String) -> Unit): String? =
    try {
        copy()
    } catch (t: Throwable) {
        onError(friendlyError(t))
        null
    }

/**
 * Copies a picked document like [copyUriToDir], but converts failures (e.g. no
 * free space) into a friendly [onError] callback and a null return instead of a
 * crash.
 */
fun safeCopyUriToDir(
    context: Context,
    uri: Uri,
    dir: File,
    fileName: String,
    onError: (String) -> Unit,
): String? = runCopy({ copyUriToDir(context, uri, dir, fileName) }, onError)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd android && ./gradlew :app:testDebugUnitTest --tests "com.cavesketch.app.util.SafeCopyTest"`
Expected: PASS (2 tests).

- [ ] **Step 5: Use safe copy in SurveyPlotScreen**

In `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`, add a toast helper and update the two picker callbacks (lines ~40-47). Add near the top of the composable (after `val context = LocalContext.current`):

```kotlin
    val showError: (String) -> Unit = { msg ->
        android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show()
    }
```

Replace the two `FilePickerRow` callbacks:

```kotlin
        FilePickerRow("Pick Cave Map", inputs.mapPath?.let { "map" + extOf(it) }) { uri ->
            com.cavesketch.app.util.safeCopyUriToDir(
                context, uri, context.filesDir, "map" + extensionOf(context, uri), showError,
            )?.let { inputs = inputs.copy(mapPath = it) }
        }
        FilePickerRow("Pick Cave Section", inputs.sectionPath?.let { "section" + extOf(it) }) { uri ->
            com.cavesketch.app.util.safeCopyUriToDir(
                context, uri, context.filesDir, "section" + extensionOf(context, uri), showError,
            )?.let { inputs = inputs.copy(sectionPath = it) }
        }
```

- [ ] **Step 6: Use safe copy in MergeControls**

In `android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt`, replace the two `copyUriToDir` calls (lines ~21-25) with `safeCopyUriToDir`, surfacing errors via a Toast. For each picker callback, replace:

```kotlin
        val p = copyUriToDir(context, uri, context.filesDir, "child_map" + extensionOf(context, uri))
```

with:

```kotlin
        val p = com.cavesketch.app.util.safeCopyUriToDir(
            context, uri, context.filesDir, "child_map" + extensionOf(context, uri),
            { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
        ) ?: return@/* keep the existing lambda label */
```

If the existing lambda has no label to `return@`, instead guard with a local:

```kotlin
        val p = com.cavesketch.app.util.safeCopyUriToDir(
            context, uri, context.filesDir, "child_map" + extensionOf(context, uri),
            { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
        )
        if (p != null) { /* existing assignment using p */ }
```

Apply the same to the `child_section` callback. (Read the current file before editing; preserve the existing assignment logic — only the copy call and the null-guard change.)

- [ ] **Step 7: Use safe copy in SatelliteScreen**

In `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt`, replace the copy inside the `jsonPicker` callback (lines ~48-51):

```kotlin
        uris.forEachIndexed { idx, uri ->
            com.cavesketch.app.util.safeCopyUriToDir(
                context, uri, context.filesDir, "additional_${jsonMaps.size + idx}.json",
                { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
            )?.let { viewModel.addJsonMap(it) }
        }
```

- [ ] **Step 8: Compile and test**

Run: `cd android && ./gradlew :app:assembleDebug :app:testDebugUnitTest`
Expected: BUILD SUCCESSFUL; tests PASS.

- [ ] **Step 9: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/util/SafeCopy.kt \
        android/app/src/test/java/com/cavesketch/app/util/SafeCopyTest.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt \
        android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt \
        android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt
git commit -m "feat(android): friendly handling of storage-full on file import"
```

---

### Task 9: Release signing, minify, and version config

Adds a release `signingConfig` reading credentials from an uncommitted `keystore.properties`, enables R8 minify + resource shrink with Chaquopy keep rules, and ignores the keystore artifacts.

**Files:**
- Modify: `android/app/build.gradle`
- Create: `android/app/proguard-rules.pro`
- Create: `android/keystore.properties.template`
- Modify: `.gitignore`

**Interfaces:** none (build configuration).

- [ ] **Step 1: Ignore keystore artifacts**

In `.gitignore`, under the "Android build and local files" section, add:

```
android/keystore.properties
android/app/*.jks
android/app/*.keystore
```

- [ ] **Step 2: Add a keystore.properties template**

Create `android/keystore.properties.template`:

```properties
# Copy to android/keystore.properties (gitignored) and fill in.
# storeFile is resolved relative to the android/app module directory.
storeFile=release.jks
storePassword=CHANGE_ME
keyAlias=cavesketch
keyPassword=CHANGE_ME
```

- [ ] **Step 3: Add ProGuard keep rules**

Create `android/app/proguard-rules.pro`:

```proguard
# Chaquopy / embedded CPython runtime — keep reflectively-used classes.
-keep class com.chaquo.python.** { *; }
-dontwarn com.chaquo.python.**

# App entry points referenced via Compose/AndroidX reflection are kept by AGP's
# default rules; nothing else app-specific needs keeping.
```

- [ ] **Step 4: Wire signing + release build type**

In `android/app/build.gradle`, add near the top (after the `plugins { }` block, before `android { }`):

```gradle
def keystorePropsFile = rootProject.file("keystore.properties")
def keystoreProps = new Properties()
if (keystorePropsFile.exists()) {
    keystoreProps.load(new FileInputStream(keystorePropsFile))
}
```

Inside `android { }`, add a `signingConfigs` block (before `buildTypes`) and a `buildTypes` block (the project currently has none, so add it):

```gradle
    signingConfigs {
        release {
            if (keystorePropsFile.exists()) {
                storeFile file(keystoreProps['storeFile'])
                storePassword keystoreProps['storePassword']
                keyAlias keystoreProps['keyAlias']
                keyPassword keystoreProps['keyPassword']
            }
        }
    }

    buildTypes {
        release {
            if (keystorePropsFile.exists()) {
                signingConfig signingConfigs.release
            }
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
```

Note: resource shrinking only touches `res/`; Chaquopy's Python lives in `assets/` and is unaffected.

- [ ] **Step 5: Generate a keystore locally (one time)**

Run from the repo root (interactive — answer the prompts; remember the passwords):

```bash
keytool -genkeypair -v -keystore android/app/release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias cavesketch
```

Then copy the template and fill in the passwords:

```bash
cp android/keystore.properties.template android/keystore.properties
# edit android/keystore.properties with the real passwords
```

- [ ] **Step 6: Build the signed release APK**

Run: `cd android && ./gradlew assembleRelease`
Expected: BUILD SUCCESSFUL; APK at `android/app/build/outputs/apk/release/app-release.apk`.

Verify it is signed (not "unsigned"):

```bash
$ANDROID_HOME/build-tools/*/apksigner verify --print-certs android/app/build/outputs/apk/release/app-release.apk
```
Expected: prints a signing certificate (no "DOES NOT VERIFY").

- [ ] **Step 7: Manual device check (release build with minify)**

Install the release APK on a real device and run a full generation on each screen:

```bash
adb install -r android/app/build/outputs/apk/release/app-release.apk
```
Expected: app launches; Survey Plot produces a PDF; Satellite produces KMZ/JSON (and online preview). This confirms R8/minify did not strip anything Chaquopy/Python needs.

- [ ] **Step 8: Commit (config only — never the keystore or properties)**

```bash
git add .gitignore android/app/build.gradle android/app/proguard-rules.pro \
        android/keystore.properties.template
git status   # CONFIRM release.jks and keystore.properties are NOT staged
git commit -m "build(android): release signing, R8 minify + resource shrink"
```

---

### Task 10: Release docs, final gates, and DEVLOG

Documents the build/publish flow for GitHub Releases and runs every verification gate.

**Files:**
- Create: `android/RELEASE.md`
- Modify: `android/DEVLOG.md`

**Interfaces:** none.

- [ ] **Step 1: Write the release guide**

Create `android/RELEASE.md`:

````markdown
# CaveSketch Android — Building & Releasing

## One-time setup: signing keystore

The release `.apk` is signed with a keystore kept **out of git**.

```bash
keytool -genkeypair -v -keystore android/app/release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias cavesketch
cp android/keystore.properties.template android/keystore.properties
# edit android/keystore.properties with your passwords
```

Keep `release.jks` and `keystore.properties` safe and private. Losing the
keystore means future versions can no longer upgrade installed apps.

## Build the release APK

```bash
cd android
./gradlew assembleRelease
```

Output: `android/app/build/outputs/apk/release/app-release.apk`.
Rename for distribution: `CaveSketch-1.0.0.apk`.

## Publish to GitHub Releases

1. Go to https://github.com/LorBordin/cave_sketch/releases → "Draft a new release".
2. Tag: `v1.0.0` (matches `versionName`). Title: `CaveSketch 1.0.0`.
3. Attach `CaveSketch-1.0.0.apk` as a release asset.
4. Publish.

## Installing on a phone (for users)

1. Download `CaveSketch-1.0.0.apk` from the Releases page.
2. Tap it; Android asks to allow installs from this source — enable it
   (Settings → Apps → Special access → Install unknown apps).
3. Tap Install.
4. **Upgrades:** download a newer `CaveSketch-x.y.z.apk` and install it over the
   top — settings and the app are preserved (same signing key required).

## Releasing a new version

Bump `versionCode` (must increase) and `versionName` in
`android/app/build.gradle`, rebuild, and attach the new APK to a new Release.
````

- [ ] **Step 2: Append the DEVLOG entry**

Append to `android/DEVLOG.md` (match the existing entry format; use today's date `2026-06-23`):

```markdown
## [2026-06-23] Phase 3 — Polish & Release
**Files:**
- android/app/build.gradle (release signing, minify, version 1.0.0, buildConfig, splashscreen dep)
- android/app/src/main/java/com/cavesketch/app/ (AppInitState, MainActivity, CaveSketchApplication, AboutScreen, AppNavHost, theme/, util/{ErrorMessages,SessionCleanup,SafeCopy})
- android/app/src/main/res/ (theme, colors, splash, adaptive launcher icons)
- android/tools/gen_launcher_icons.py, android/RELEASE.md, android/app/proguard-rules.pro

**Deviations from spec:** None

**Assumptions:** Splash uses core-splashscreen with the launcher foreground as the splash icon; About link points at the public repo.

**Next session notes:** Phase 4 (visual redesign) is the next roadmap item.
```

- [ ] **Step 3: Run all verification gates**

```bash
uv run ruff check .
uv run mypy cave_sketch/
uv run pytest
cd android && ./gradlew :app:testDebugUnitTest && ./gradlew assembleRelease
```
Expected: ruff clean; mypy clean; pytest passes; Kotlin unit tests pass; release APK builds.

- [ ] **Step 4: Commit**

```bash
git add android/RELEASE.md android/DEVLOG.md
git commit -m "docs(android): Phase 3 release guide + DEVLOG entry"
```

---

## Self-Review

**Spec coverage** (against `docs/mobile-app/phases/phase-3-polish-release/spec.md`):
- §4.1 Adaptive launcher icon → Task 7.
- §4.2 Branded splash held until ready → Tasks 5 (readiness) + 6 (splash).
- §5.1 Light brand theme → Task 3.
- §5.2 About tab with version → Task 4.
- §5.3 Loading/progress polish → existing `Generating` UI already shows spinner + disabled button (verified in `SurveyPlotScreen.kt:68-88`, `SatelliteScreen.kt:98-113`); no rebuild needed. Error copy improved via Task 1.
- §6 Crash/init hardening → Python init failure (Task 5), storage-full (Tasks 1 + 8), uncaught generation error (existing catch, now via `friendlyError`), global uncaught handler (Task 5).
- §7 Session-cleanup hardening → Task 2.
- §8.1 Signing → Task 9. §8.2 minify + version → Tasks 9 + 4. §8.3 build + distribute → Tasks 9 + 10.
- §9 Testing → unit tests in Tasks 1,2,4,5,8; manual device checks in Tasks 6,7,9. §10 gates → Task 10. §11 exit criteria → Task 10.

**Placeholder scan:** No TBD/TODO; every code step shows full content. The one "read the current file before editing" note (Task 8 Step 6, MergeControls) is a real instruction because the surrounding assignment varies — the copy-call replacement and null-guard are shown explicitly.

**Type consistency:** `friendlyError(Throwable): String` (Task 1) consumed unchanged in Tasks 5 & 8. `AppInitState`/`InitStatus` (Task 5) consumed in Task 6. `AppNavHost(.., versionName)` (Task 4) called with `BuildConfig.VERSION_NAME` in MainActivity; MainActivity is further edited in Tasks 5 & 6 (later tasks supersede earlier `onCreate` bodies — the Task 6 `onCreate` is the final form and includes the Task 5 status gate). `safeCopyUriToDir` signature matches its three call sites.
