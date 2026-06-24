# Phase 4 — Visual Redesign (Dark Theme) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the CaveSketch Android app into a single dark theme with a cyan + amber identity, a top app bar, and controls grouped into section cards — full feature parity with Phase 3.

**Architecture:** Replace the Material 3 light scheme with an always-on dark `darkColorScheme`. Add three small reusable composables (`SectionCard`, `PrimaryCta`, `StateBanner`) and a per-route `TopAppBar` in `AppNavHost`. Each screen keeps its existing ViewModel wiring and controls; only grouping and styling change. `StepperControl` is restyled in place to a single row, preserving its test contract.

**Tech Stack:** Kotlin, Jetpack Compose, Material 3 (`compose-bom:2024.06.00`), `material-icons-extended`, Robolectric + Compose UI test (`createComposeRule`) for unit tests, Gradle (Groovy).

## Global Constraints

- `cave_sketch/` stays **untouched and Streamlit-free**; the Streamlit web app is unaffected (Android-only change).
- **Full feature parity** with Phase 3 — no control, screen, input, or behavior added or removed.
- **Dark-only.** No light scheme; ignore the system light/dark setting.
- **One amber CTA per screen, maximum.** Cyan for all other actions/highlights.
- Dark palette (exact hex, from spec §4):
  - `background #0F171A`, `surface #1A262C`, `surfaceVariant #22323A`
  - `primary(cyan) #2BD4E6`, `onPrimary #062227`
  - `secondary(amber) #FFB74D`, `onSecondary #1A1200`
  - `onSurface/onBackground #E6EDEF`, `onSurfaceVariant #9AA9AF`
  - `outline #3A4A52`, `error #FF6B6B`, `onError #3A0000`
- Existing tests must stay green: `SettingsFormTest` (StepperControl testTags `"${label}_+"`, `"${label}_−"`; `contentDescription` `"+"`/`"−"`; label `Text`; formatted-value `Text`; rule-length slider range) and `AboutScreenTest` (`aboutVersionLine`).
- Run unit tests with: `cd android && ./gradlew testDebugUnitTest`.
- Build the APK with: `cd android && ./gradlew assembleDebug`.
- Log the work in `android/DEVLOG.md` using the existing entry format.

---

## File Structure

**Created:**
- `android/app/src/main/java/com/cavesketch/app/ui/components/SectionCard.kt` — rounded card with icon + title header wrapping grouped controls.
- `android/app/src/main/java/com/cavesketch/app/ui/components/PrimaryCta.kt` — amber, full-width, 56dp primary CTA button.
- `android/app/src/main/java/com/cavesketch/app/ui/components/StateBanner.kt` — soft rounded banner for idle/error messages.
- `android/app/src/test/java/com/cavesketch/app/ui/theme/ThemeTest.kt` — asserts the dark palette.
- `android/app/src/test/java/com/cavesketch/app/ui/components/SectionCardTest.kt`
- `android/app/src/test/java/com/cavesketch/app/ui/components/PrimaryCtaTest.kt`
- `android/app/src/test/java/com/cavesketch/app/ui/components/StateBannerTest.kt`

**Modified:**
- `android/app/src/main/java/com/cavesketch/app/ui/theme/Color.kt` — dark tokens.
- `android/app/src/main/java/com/cavesketch/app/ui/theme/Theme.kt` — single dark scheme, always on.
- `android/app/src/main/res/values/colors.xml` — dark background + surface colors.
- `android/app/src/main/res/values/themes.xml` — dark window/status/nav bars.
- `android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt` — single-row `StepperControl`; drop internal header.
- `android/app/src/main/java/com/cavesketch/app/ui/components/FilePickerRow.kt` — 12dp button corners.
- `android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt` — drop internal header text.
- `android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt` — drop internal header text.
- `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt` — per-route `TopAppBar` + nav-bar colors.
- `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt` — group into cards + amber CTA + state banners.
- `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt` — group into cards + amber CTA + state banners.
- `android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt` — logo, version chip, cyan button.
- `android/DEVLOG.md` — Phase 4 entry.

---

### Task 1: Dark theme tokens & always-dark scheme (534b3ed)

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/theme/Color.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/theme/Theme.kt`
- Modify: `android/app/src/main/res/values/colors.xml`
- Modify: `android/app/src/main/res/values/themes.xml`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/theme/ThemeTest.kt`

**Interfaces:**
- Produces: `CaveSketchTheme(content: @Composable () -> Unit)` (the `darkTheme` parameter is removed). Color tokens: `CaveBackground`, `CaveSurface`, `CaveSurfaceVariant`, `CaveCyan`, `CaveOnCyan`, `CaveAmber`, `CaveOnAmber`, `CaveOnSurface`, `CaveOnSurfaceVariant`, `CaveOutline`, `CaveError`, `CaveOnError`.
- Consumes: `MainActivity` already calls `CaveSketchTheme { ... }` with no argument — unaffected by removing the parameter.

- [x] **Step 1: Confirm no other references to the old color tokens**

Run: `cd android && grep -rn "BrandCyan\|BrandCyanDark\|BrandSlate\|BrandSlateLight\|BrandBackground\|Color_White" app/src/main/java`
Expected: matches **only** in `ui/theme/Color.kt` and `ui/theme/Theme.kt`. If any other file references them, that file must be updated to a new token in this task too.

- [x] **Step 2: Write the failing theme test**

Create `android/app/src/test/java/com/cavesketch/app/ui/theme/ThemeTest.kt`:

```kotlin
package com.cavesketch.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class ThemeTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun theme_uses_dark_cyan_amber_palette() {
        var background = Color.Unspecified
        var primary = Color.Unspecified
        var secondary = Color.Unspecified
        var surface = Color.Unspecified
        composeTestRule.setContent {
            CaveSketchTheme {
                background = MaterialTheme.colorScheme.background
                primary = MaterialTheme.colorScheme.primary
                secondary = MaterialTheme.colorScheme.secondary
                surface = MaterialTheme.colorScheme.surface
            }
        }
        assertEquals(CaveBackground, background)
        assertEquals(CaveCyan, primary)
        assertEquals(CaveAmber, secondary)
        assertEquals(CaveSurface, surface)
    }
}
```

- [x] **Step 3: Run the test to verify it fails**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.theme.ThemeTest"`
Expected: FAIL to compile / unresolved references `CaveBackground`, `CaveCyan`, `CaveAmber`, `CaveSurface`.

- [x] **Step 4: Replace the color tokens**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/theme/Color.kt`:

```kotlin
package com.cavesketch.app.ui.theme

import androidx.compose.ui.graphics.Color

// Phase 4 dark palette — cyan + amber "headlamp" identity on deep cave slate.
val CaveBackground = Color(0xFF0F171A)
val CaveSurface = Color(0xFF1A262C)
val CaveSurfaceVariant = Color(0xFF22323A)
val CaveCyan = Color(0xFF2BD4E6)
val CaveOnCyan = Color(0xFF062227)
val CaveAmber = Color(0xFFFFB74D)
val CaveOnAmber = Color(0xFF1A1200)
val CaveOnSurface = Color(0xFFE6EDEF)
val CaveOnSurfaceVariant = Color(0xFF9AA9AF)
val CaveOutline = Color(0xFF3A4A52)
val CaveError = Color(0xFFFF6B6B)
val CaveOnError = Color(0xFF3A0000)
```

- [x] **Step 5: Replace the theme with an always-dark scheme**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/theme/Theme.kt`:

```kotlin
package com.cavesketch.app.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val CaveDarkColors = darkColorScheme(
    primary = CaveCyan,
    onPrimary = CaveOnCyan,
    secondary = CaveAmber,
    onSecondary = CaveOnAmber,
    background = CaveBackground,
    onBackground = CaveOnSurface,
    surface = CaveSurface,
    onSurface = CaveOnSurface,
    surfaceVariant = CaveSurfaceVariant,
    onSurfaceVariant = CaveOnSurfaceVariant,
    outline = CaveOutline,
    error = CaveError,
    onError = CaveOnError,
)

@Composable
fun CaveSketchTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = CaveDarkColors, content = content)
}
```

- [x] **Step 6: Update XML colors**

Replace the entire contents of `android/app/src/main/res/values/colors.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="brand_cyan">#FF2BD4E6</color>
    <color name="cave_background">#FF0F171A</color>
    <color name="cave_surface">#FF1A262C</color>
    <color name="ic_launcher_background">#FF0F171A</color>
</resources>
```

- [x] **Step 7: Update the Android window/status/splash theme to dark**

Replace the entire contents of `android/app/src/main/res/values/themes.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.CaveSketch" parent="android:Theme.Material.NoActionBar">
        <item name="android:windowBackground">@color/cave_background</item>
        <item name="android:statusBarColor">@color/cave_surface</item>
        <item name="android:navigationBarColor">@color/cave_surface</item>
        <item name="android:windowLightStatusBar">false</item>
    </style>

    <style name="Theme.CaveSketch.Splash" parent="Theme.SplashScreen">
        <item name="windowSplashScreenBackground">@color/cave_background</item>
        <item name="windowSplashScreenAnimatedIcon">@drawable/ic_launcher_foreground</item>
        <item name="postSplashScreenTheme">@style/Theme.CaveSketch</item>
    </style>
</resources>
```

- [x] **Step 8: Run the test to verify it passes**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.theme.ThemeTest"`
Expected: PASS.

- [x] **Step 9: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/theme/ android/app/src/main/res/values/colors.xml android/app/src/main/res/values/themes.xml android/app/src/test/java/com/cavesketch/app/ui/theme/ThemeTest.kt
git commit -m "feat(android): Phase 4 dark theme tokens and always-dark scheme"
```

---

### Task 2: SectionCard reusable composable (b9e6a79)

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/SectionCard.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/components/SectionCardTest.kt`

**Interfaces:**
- Produces: `SectionCard(title: String, icon: ImageVector, modifier: Modifier = Modifier, content: @Composable () -> Unit)` — a `surface`-colored 16dp-rounded card with an icon+title header above `content`.

- [x] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/ui/components/SectionCardTest.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Text
import androidx.compose.ui.test.assertExists
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class SectionCardTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_title_and_content() {
        composeTestRule.setContent {
            SectionCard("Input files", Icons.Filled.Settings) {
                Text("inner content")
            }
        }
        composeTestRule.onNodeWithText("Input files").assertExists()
        composeTestRule.onNodeWithText("inner content").assertExists()
    }
}
```

- [x] **Step 2: Run the test to verify it fails**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.SectionCardTest"`
Expected: FAIL — unresolved reference `SectionCard`.

- [x] **Step 3: Implement SectionCard**

Create `android/app/src/main/java/com/cavesketch/app/ui/components/SectionCard.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp

@Composable
fun SectionCard(
    title: String,
    icon: ImageVector,
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Card(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
            contentColor = MaterialTheme.colorScheme.onSurface,
        ),
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Icon(icon, contentDescription = null, tint = MaterialTheme.colorScheme.primary)
                Text(title, style = MaterialTheme.typography.titleMedium)
            }
            content()
        }
    }
}
```

- [x] **Step 4: Run the test to verify it passes**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.SectionCardTest"`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/SectionCard.kt android/app/src/test/java/com/cavesketch/app/ui/components/SectionCardTest.kt
git commit -m "feat(android): add SectionCard composable"
```

---

### Task 3: PrimaryCta reusable composable (amber) (012942e)

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/PrimaryCta.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/components/PrimaryCtaTest.kt`

**Interfaces:**
- Produces: `PrimaryCta(text: String, icon: ImageVector, enabled: Boolean, onClick: () -> Unit, modifier: Modifier = Modifier)` — full-width 56dp amber (`secondary`) button with a leading icon; respects `enabled`.

- [x] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/ui/components/PrimaryCtaTest.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import org.junit.Assert.assertTrue
import org.junit.Assert.assertFalse
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class PrimaryCtaTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_label_and_invokes_click_when_enabled() {
        var clicked = false
        composeTestRule.setContent {
            PrimaryCta("Generate Survey Plot", Icons.Filled.PlayArrow, enabled = true) { clicked = true }
        }
        composeTestRule.onNodeWithText("Generate Survey Plot").assertExists()
        composeTestRule.onNodeWithText("Generate Survey Plot").performClick()
        assertTrue(clicked)
    }

    @Test
    fun does_not_invoke_click_when_disabled() {
        var clicked = false
        composeTestRule.setContent {
            PrimaryCta("Generate Survey Plot", Icons.Filled.PlayArrow, enabled = false) { clicked = true }
        }
        composeTestRule.onNodeWithText("Generate Survey Plot").assertIsNotEnabled()
        composeTestRule.onNodeWithText("Generate Survey Plot").performClick()
        assertFalse(clicked)
    }
}
```

- [x] **Step 2: Run the test to verify it fails**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.PrimaryCtaTest"`
Expected: FAIL — unresolved reference `PrimaryCta`.

- [x] **Step 3: Implement PrimaryCta**

Create `android/app/src/main/java/com/cavesketch/app/ui/components/PrimaryCta.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp

@Composable
fun PrimaryCta(
    text: String,
    icon: ImageVector,
    enabled: Boolean,
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = modifier.fillMaxWidth().height(56.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = MaterialTheme.colorScheme.secondary,
            contentColor = MaterialTheme.colorScheme.onSecondary,
        ),
    ) {
        Icon(icon, contentDescription = null)
        Spacer(Modifier.width(8.dp))
        Text(text)
    }
}
```

- [x] **Step 4: Run the test to verify it passes**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.PrimaryCtaTest"`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/PrimaryCta.kt android/app/src/test/java/com/cavesketch/app/ui/components/PrimaryCtaTest.kt
git commit -m "feat(android): add amber PrimaryCta composable"
```

---

### Task 4: StateBanner reusable composable (71d4963)

**Files:**
- Create: `android/app/src/main/java/com/cavesketch/app/ui/components/StateBanner.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/components/StateBannerTest.kt`

**Interfaces:**
- Produces: `StateBanner(message: String, isError: Boolean, modifier: Modifier = Modifier)` — a rounded full-width banner; soft-red tint when `isError`, muted `surfaceVariant` otherwise.

- [x] **Step 1: Write the failing test**

Create `android/app/src/test/java/com/cavesketch/app/ui/components/StateBannerTest.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithText
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [28], application = android.app.Application::class)
class StateBannerTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun renders_idle_message() {
        composeTestRule.setContent {
            StateBanner("Pick your files and tap Generate", isError = false)
        }
        composeTestRule.onNodeWithText("Pick your files and tap Generate").assertExists()
    }

    @Test
    fun renders_error_message() {
        composeTestRule.setContent {
            StateBanner("Something went wrong", isError = true)
        }
        composeTestRule.onNodeWithText("Something went wrong").assertExists()
    }
}
```

- [x] **Step 2: Run the test to verify it fails**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.StateBannerTest"`
Expected: FAIL — unresolved reference `StateBanner`.

- [x] **Step 3: Implement StateBanner**

Create `android/app/src/main/java/com/cavesketch/app/ui/components/StateBanner.kt`:

```kotlin
package com.cavesketch.app.ui.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

@Composable
fun StateBanner(
    message: String,
    isError: Boolean,
    modifier: Modifier = Modifier,
) {
    val container = if (isError) {
        MaterialTheme.colorScheme.error.copy(alpha = 0.15f)
    } else {
        MaterialTheme.colorScheme.surfaceVariant
    }
    val contentColor = if (isError) {
        MaterialTheme.colorScheme.error
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant
    }
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        color = container,
    ) {
        Text(message, color = contentColor, modifier = Modifier.padding(16.dp))
    }
}
```

- [x] **Step 4: Run the test to verify it passes**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.StateBannerTest"`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/StateBanner.kt android/app/src/test/java/com/cavesketch/app/ui/components/StateBannerTest.kt
git commit -m "feat(android): add StateBanner composable"
```

---

### Task 5: Restyle StepperControl to a single row & FilePickerRow buttons (0415990)

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/FilePickerRow.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/components/SettingsFormTest.kt` (existing — must stay green)

**Interfaces:**
- Produces: `StepperControl(...)` keeps the **same signature** and the same test contract: label `Text`, formatted-value `Text`, `IconButton`s with `contentDescription` `"+"`/`"−"` and `testTag` `"${label}_+"` / `"${label}_−"`, container `testTag(label)`.
- `SettingsForm(inputs, onChange)` signature unchanged; its internal `Text("Survey settings")` header is removed (the wrapping `SectionCard` from Task 7 supplies the header).
- `FilePickerRow(label, fileName, onPick)` signature unchanged.

- [x] **Step 1: Restyle StepperControl into a single row**

In `android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt`, replace the `Column(Modifier.testTag(label)) { ... }` block at the end of `StepperControl` (the layout, **not** the value/clamp logic above it) with:

```kotlin
    Row(
        modifier = Modifier.fillMaxWidth().testTag(label),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(label, modifier = Modifier.weight(1f))
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(
                onClick = { updateValue(false) },
                enabled = canDecrease,
                modifier = Modifier
                    .semantics { contentDescription = "−" }
                    .testTag("${label}_−")
            ) {
                Icon(Icons.Filled.Remove, contentDescription = "Decrease")
            }
            Text(text = formatter(value))
            IconButton(
                onClick = { updateValue(true) },
                enabled = canIncrease,
                modifier = Modifier
                    .semantics { contentDescription = "+" }
                    .testTag("${label}_+")
            ) {
                Icon(Icons.Filled.Add, contentDescription = "Increase")
            }
        }
    }
```

(The imports `Row`, `fillMaxWidth`, `Alignment`, `testTag`, `semantics`, `contentDescription`, `Icons.Filled.Add`, `Icons.Filled.Remove` are already present in this file.)

- [x] **Step 2: Remove the SettingsForm internal header**

In the same file, in `SettingsForm`, delete the line:

```kotlin
        Text("Survey settings")
```

Leave the rest of `SettingsForm` (rule-length slider, the four `StepperControl` calls, the two checkbox rows) unchanged.

- [x] **Step 3: Restyle FilePickerRow buttons**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/components/FilePickerRow.kt`:

```kotlin
package com.cavesketch.app.ui.components

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier

@Composable
fun FilePickerRow(label: String, fileName: String?, onPick: (Uri) -> Unit) {
    val launcher = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri -> if (uri != null) onPick(uri) }
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Button(
            onClick = { launcher.launch(arrayOf("*/*")) },
            shape = RoundedCornerShape(12.dp),
        ) { Text(label) }
        Text(
            fileName ?: "none",
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}
```

Add the missing import at the top of the file:

```kotlin
import androidx.compose.ui.unit.dp
```

- [x] **Step 4: Run the existing settings tests to verify they stay green**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.components.SettingsFormTest"`
Expected: PASS (all stepper testTags, content descriptions, label/value text, and the rule-length slider range still resolve).

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/components/SettingsForm.kt android/app/src/main/java/com/cavesketch/app/ui/components/FilePickerRow.kt
git commit -m "feat(android): single-row stepper and rounded file-picker buttons"
```

---

### Task 6: Top app bar + styled bottom navigation in AppNavHost (f6b97cd)

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt`

**Interfaces:**
- Consumes: route strings `"survey_plot"`, `"satellite"`, `"about"` (unchanged); drawable `R.drawable.splash_icon` (existing cyan triangle mark).
- Produces: a `Scaffold` with a per-route `TopAppBar` (logo + title) and the existing bottom `NavigationBar` restyled with cyan active items. `AppNavHost(surveyViewModel, satelliteViewModel, versionName)` signature unchanged.

- [x] **Step 1: Add the top app bar and nav styling**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt`:

```kotlin
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
```

- [x] **Step 2: Build to verify it compiles**

Run: `cd android && ./gradlew assembleDebug`
Expected: BUILD SUCCESSFUL.

- [x] **Step 3: Manual verification**

Install the APK (`./gradlew installDebug` or sideload `app/build/outputs/apk/debug/app-debug.apk`) and confirm: each tab shows a dark top app bar with the cyan triangle mark and the correct title ("Survey Plot" / "Satellite Map" / "About"); the bottom nav has a cyan active item with a pill indicator on the dark surface; the status bar is dark with light icons.

- [x] **Step 4: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/AppNavHost.kt
git commit -m "feat(android): per-route top app bar and styled bottom nav"
```

---

### Task 7: Survey Plot screen — group into cards + amber CTA (7d5f399)

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt`

**Interfaces:**
- Consumes: `SectionCard` (Task 2), `PrimaryCta` (Task 3), `StateBanner` (Task 4), `SettingsForm`/`FilePickerRow` (Task 5), `MergeControls` (this task), existing `SurveyPlotViewModel`, `SurveyInputs`, `PlotState`, `PdfPreview`.
- `SurveyPlotScreen(viewModel: SurveyPlotViewModel)` signature unchanged.

- [x] **Step 1: Drop the internal header in MergeControls**

In `android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt`, delete the first line of the composable body:

```kotlin
    Text("Merge another survey (optional)")
```

Leave the rest (child file pickers, station fields, protocol radios) unchanged. (The `Text` import stays — it is still used by the protocol section.)

- [x] **Step 2: Rewrite SurveyPlotScreen with cards + CTA + banners**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt`:

```kotlin
package com.cavesketch.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Description
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Tune
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.components.FilePickerRow
import com.cavesketch.app.ui.components.MergeControls
import com.cavesketch.app.ui.components.PrimaryCta
import com.cavesketch.app.ui.components.SectionCard
import com.cavesketch.app.ui.components.SettingsForm
import com.cavesketch.app.ui.components.StateBanner
import com.cavesketch.app.util.extensionOf

@Composable
fun SurveyPlotScreen(viewModel: SurveyPlotViewModel) {
    val context = LocalContext.current
    val showError: (String) -> Unit = { msg ->
        android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show()
    }
    var inputs by remember { mutableStateOf(SurveyInputs()) }
    val state by viewModel.state.collectAsState()
    val canGenerate = inputs.mapPath != null || inputs.sectionPath != null

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard("Input files", Icons.Filled.Description) {
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
        }

        SectionCard("Merge survey (optional)", Icons.Filled.Link) {
            MergeControls(inputs, context) { inputs = it }
        }

        SectionCard("Survey details", Icons.Filled.Edit) {
            OutlinedTextField(
                value = inputs.surveyName,
                onValueChange = { inputs = inputs.copy(surveyName = it) },
                label = { Text("Survey name") },
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = inputs.surveyorName,
                onValueChange = { inputs = inputs.copy(surveyorName = it) },
                label = { Text("Surveyor name") },
                modifier = Modifier.fillMaxWidth(),
            )
        }

        SectionCard("Settings", Icons.Filled.Tune) {
            SettingsForm(inputs) { inputs = it }
        }

        PrimaryCta(
            text = "Generate Survey Plot",
            icon = Icons.Filled.PlayArrow,
            enabled = canGenerate && state !is PlotState.Generating,
            onClick = { viewModel.generate(inputs) },
        )

        when (val s = state) {
            is PlotState.Generating -> {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is PlotState.Error -> StateBanner("⚠️ ${s.message}", isError = true)
            is PlotState.Success -> {
                PdfPreview(s.pdfPath)
                Button(
                    onClick = {
                        val name = inputs.surveyName.ifBlank { "survey" } + ".pdf"
                        com.cavesketch.app.util.sharePdf(context, s.pdfPath, name)
                    },
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("Save / Share PDF")
                }
            }
            PlotState.Idle -> StateBanner("Pick your files and tap Generate.", isError = false)
        }
    }
}

private fun extOf(path: String) = if (path.lowercase().endsWith(".dxf")) ".dxf" else ".csv"
```

- [x] **Step 3: Build to verify it compiles**

Run: `cd android && ./gradlew assembleDebug`
Expected: BUILD SUCCESSFUL.

- [x] **Step 4: Manual verification**

On device: the Survey Plot screen shows four cards (Input files / Merge survey / Survey details / Settings), an amber "Generate Survey Plot" button with a play icon, an idle banner before generating, and — after generating with a sample DXF — the PDF preview and a cyan "Save / Share PDF" button. Confirm full parity: file pickers, merge fields/protocol, all settings (slider + four single-row steppers + two toggles) work exactly as before.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/SurveyPlotScreen.kt android/app/src/main/java/com/cavesketch/app/ui/components/MergeControls.kt
git commit -m "feat(android): card-grouped Survey Plot screen with amber CTA"
```

---

### Task 8: Satellite Map screen — group into cards + amber CTA (7904a5a)

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt`
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt`

**Interfaces:**
- Consumes: `SectionCard`, `PrimaryCta`, `StateBanner`, `GpsPointsEditor` (this task), existing `SatelliteViewModel`, `SatelliteState`, `MapWebView`, `parsesAsCoordinate`, `shareFile`.
- `SatelliteScreen(viewModel: SatelliteViewModel)` signature unchanged.

- [x] **Step 1: Drop the internal header in GpsPointsEditor**

In `android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt`, delete the line:

```kotlin
        Text("📍 Known GPS Points")
```

Leave the point rows and the Add/Remove buttons unchanged.

- [x] **Step 2: Rewrite SatelliteScreen with cards + CTA + banners**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt`:

```kotlin
package com.cavesketch.app.ui

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Folder
import androidx.compose.material.icons.filled.Place
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.cavesketch.app.ui.components.GpsPointsEditor
import com.cavesketch.app.ui.components.MapWebView
import com.cavesketch.app.ui.components.PrimaryCta
import com.cavesketch.app.ui.components.SectionCard
import com.cavesketch.app.ui.components.StateBanner
import com.cavesketch.app.ui.components.parsesAsCoordinate
import com.cavesketch.app.util.shareFile

@Composable
fun SatelliteScreen(viewModel: SatelliteViewModel) {
    val context = LocalContext.current
    val state by viewModel.state.collectAsState()
    val points by viewModel.points.collectAsState()
    val jsonMaps by viewModel.jsonMaps.collectAsState()

    var surveyName by remember { mutableStateOf(viewModel.suggestedSurveyName()) }
    var rotationText by remember { mutableStateOf("0") }

    val jsonPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenMultipleDocuments()
    ) { uris ->
        uris.forEachIndexed { idx, uri ->
            com.cavesketch.app.util.safeCopyUriToDir(
                context, uri, context.filesDir, "additional_${jsonMaps.size + idx}.json",
                { msg -> android.widget.Toast.makeText(context, msg, android.widget.Toast.LENGTH_LONG).show() },
            )?.let { viewModel.addJsonMap(it) }
        }
    }

    if (state is SatelliteState.NoMap) {
        Box(Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
            StateBanner(
                "Generate a survey plot first — the Satellite Map needs a cave map.",
                isError = false,
            )
        }
        return
    }

    val pointsValid = points.all {
        it.station.isNotBlank() && parsesAsCoordinate(it.lat) && parsesAsCoordinate(it.lon)
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        SectionCard("GPS points", Icons.Filled.Place) {
            GpsPointsEditor(
                points = points,
                onUpdate = viewModel::updatePoint,
                onAdd = viewModel::addPoint,
                onRemove = viewModel::removeLastPoint,
            )
        }

        SectionCard("Map details", Icons.Filled.Edit) {
            OutlinedTextField(
                value = surveyName,
                onValueChange = { surveyName = it },
                label = { Text("Survey name") },
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = rotationText,
                onValueChange = {
                    rotationText = it
                    it.trim().replace(",", ".").toDoubleOrNull()?.let(viewModel::setRotation)
                },
                label = { Text("Map rotation angle (°)") },
                isError = rotationText.isNotBlank() && rotationText.trim().replace(",", ".").toDoubleOrNull() == null,
                modifier = Modifier.fillMaxWidth(),
            )
        }

        SectionCard("Additional maps", Icons.Filled.Folder) {
            Button(onClick = { jsonPicker.launch(arrayOf("application/json", "*/*")) }) {
                Text("📁 Import JSON maps (${jsonMaps.size})")
            }
        }

        PrimaryCta(
            text = "Generate Satellite Map",
            icon = Icons.Filled.PlayArrow,
            enabled = pointsValid && state !is SatelliteState.Generating,
            onClick = { viewModel.generate(surveyName) },
        )

        when (val s = state) {
            is SatelliteState.Generating -> {
                Column(Modifier.fillMaxWidth(), horizontalAlignment = Alignment.CenterHorizontally) {
                    CircularProgressIndicator()
                    Spacer(Modifier.height(8.dp))
                    Text(s.phase)
                }
            }
            is SatelliteState.Error -> StateBanner("⚠️ ${s.message}", isError = true)
            is SatelliteState.Success -> {
                if (s.online) {
                    MapWebView(s.htmlPath, Modifier.fillMaxWidth().height(360.dp))
                } else {
                    StateBanner(
                        "No connection — satellite preview unavailable. " +
                            "KMZ & JSON are ready to save/share.",
                        isError = true,
                    )
                }
                Spacer(Modifier.height(8.dp))
                val name = surveyName.ifBlank { "survey" }
                Button(
                    onClick = { shareFile(context, s.htmlPath, "text/html", "$name.html") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share HTML") }
                Button(
                    onClick = { shareFile(context, s.jsonPath, "application/json", "$name.json") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share JSON") }
                Button(
                    onClick = { shareFile(context, s.kmzPath, "application/vnd.google-earth.kmz", "$name.kmz") },
                    modifier = Modifier.fillMaxWidth(),
                ) { Text("Save / Share KMZ") }
            }
            else -> {}
        }
    }
}
```

- [x] **Step 3: Build to verify it compiles**

Run: `cd android && ./gradlew assembleDebug`
Expected: BUILD SUCCESSFUL.

- [x] **Step 4: Manual verification**

On device: the Satellite Map screen shows three cards (GPS points / Map details / Additional maps), the amber "Generate Satellite Map" CTA, and (after generating) the WebView map online or the soft offline banner. Confirm parity: add/remove GPS points, lat/lon validation, JSON import counter, rotation field, and the three Save/Share buttons all behave as before.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/SatelliteScreen.kt android/app/src/main/java/com/cavesketch/app/ui/components/GpsPointsEditor.kt
git commit -m "feat(android): card-grouped Satellite Map screen with amber CTA"
```

---

### Task 9: About screen — logo, version chip, cyan button (5dc414a)

**Files:**
- Modify: `android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt`
- Test: `android/app/src/test/java/com/cavesketch/app/ui/AboutScreenTest.kt` (existing — must stay green)

**Interfaces:**
- Consumes: drawable `R.drawable.splash_icon`; existing `aboutVersionLine(versionName)` helper (kept unchanged so `AboutScreenTest` passes).
- `AboutScreen(versionName: String)` signature unchanged.

- [x] **Step 1: Rewrite AboutScreen with logo, chip, and cyan button**

Replace the entire contents of `android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt`:

```kotlin
package com.cavesketch.app.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.cavesketch.app.R

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
        Image(
            painter = painterResource(R.drawable.splash_icon),
            contentDescription = null,
            modifier = Modifier.size(96.dp),
        )
        Spacer(Modifier.height(16.dp))
        Text("CaveSketch", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "Cave survey plotting & georeferencing",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(16.dp))
        Surface(
            shape = RoundedCornerShape(12.dp),
            color = MaterialTheme.colorScheme.surfaceVariant,
        ) {
            Text(
                aboutVersionLine(versionName),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
            )
        }
        Spacer(Modifier.height(24.dp))
        Button(onClick = {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(REPO_URL)))
        }) {
            Text("Project on GitHub")
        }
    }
}
```

- [x] **Step 2: Run the About test to verify it stays green**

Run: `cd android && ./gradlew testDebugUnitTest --tests "com.cavesketch.app.ui.AboutScreenTest"`
Expected: PASS (`aboutVersionLine` is unchanged).

- [x] **Step 3: Build to verify it compiles**

Run: `cd android && ./gradlew assembleDebug`
Expected: BUILD SUCCESSFUL.

- [x] **Step 4: Manual verification**

On device: the About screen is centered on the dark background with the cyan triangle logo, "CaveSketch" title, muted tagline, a rounded "Version 1.0.0" chip, and a cyan "Project on GitHub" button that opens the repo.

- [x] **Step 5: Commit**

```bash
git add android/app/src/main/java/com/cavesketch/app/ui/AboutScreen.kt
git commit -m "feat(android): branded dark About screen with logo and version chip"
```

---

### Task 10: Full verification gates + DEVLOG

**Files:**
- Modify: `android/DEVLOG.md`

- [ ] **Step 1: Run the full unit-test suite**

Run: `cd android && ./gradlew testDebugUnitTest`
Expected: BUILD SUCCESSFUL — all tests pass (`ThemeTest`, `SectionCardTest`, `PrimaryCtaTest`, `StateBannerTest`, `SettingsFormTest`, `AboutScreenTest`).

- [ ] **Step 2: Build the release-style debug APK**

Run: `cd android && ./gradlew assembleDebug`
Expected: BUILD SUCCESSFUL; APK at `android/app/build/outputs/apk/debug/app-debug.apk`.

- [ ] **Step 3: Full-device parity smoke test**

Sideload the APK and walk all three screens end-to-end: generate a survey PDF from a sample DXF (incl. a merge), generate a satellite map (online and with connectivity off), and open the About link. Confirm dark theme throughout, cyan + amber identity, top app bar, and card grouping — with **no behavior changed** from Phase 3.

- [ ] **Step 4: Add the DEVLOG entry**

Append a Phase 4 entry to `android/DEVLOG.md` using the existing entry format (match the heading style, date `2026-06-24`, and sections used by prior entries). Summarize: dark-only theme with cyan + amber palette, top app bar, section-card layout, restyled stepper/buttons, new `SectionCard`/`PrimaryCta`/`StateBanner` composables; full feature parity preserved; tests + build green.

- [ ] **Step 5: Commit**

```bash
git add android/DEVLOG.md
git commit -m "docs(android): Phase 4 visual redesign DEVLOG entry"
```

---

## Self-Review

**Spec coverage:**
- Dark-only theme (§3.1, §4) → Task 1.
- Cyan + amber identity, one amber CTA per screen (§3.2, §5 buttons) → `PrimaryCta` (Task 3), used in Tasks 7–8; cyan elsewhere via theme.
- Top app bar (§5) → Task 6.
- Section cards (§5, §6) → `SectionCard` (Task 2), applied in Tasks 7–9.
- Restyled buttons/inputs (§5) → Tasks 5, 7, 8, 9.
- Single-row stepper (§5) → Task 5.
- Styled bottom nav (§5) → Task 6.
- State banners / idle / error (§5) → `StateBanner` (Task 4), applied in Tasks 7–8.
- Per-screen layouts (§6.1–6.3) → Tasks 7, 8, 9.
- System bar tint (§4) → Task 1 (themes.xml).
- Files affected (§7) → all covered; the four suggested composables become `SectionCard`, `PrimaryCta`, `StateBanner` (the suggested `StepperRow` is realized by restyling `StepperControl` in place to preserve its test contract — noted as an intentional deviation).
- Tests stay green (§8) → Tasks 5, 9 re-run existing tests; Task 10 runs the full suite.
- DEVLOG (§8) → Task 10.
- Success criteria (§9) → Task 10 device smoke test.

**Placeholder scan:** No TBD/TODO; every code step contains full file or block contents; every command has an expected result.

**Type consistency:** `SectionCard(title, icon, modifier, content)`, `PrimaryCta(text, icon, enabled, onClick, modifier)`, `StateBanner(message, isError, modifier)`, and `CaveSketchTheme(content)` are used with matching signatures across Tasks 2–9. `StepperControl` keeps its original signature and test contract. `AppNavHost` and all three screen composables keep their existing public signatures.
