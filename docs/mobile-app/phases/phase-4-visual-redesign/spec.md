# CaveSketch Android — Phase 4 Visual Redesign (Dark Theme)

**Status:** Approved (design)
**Date:** 2026-06-24
**Scope:** Phase 4 of the mobile-app roadmap (`docs/mobile-app/umbrella-spec.md` §10).
**Level:** 2 (phase spec). Implements the "Visual redesign" phase.

---

## 1. Goal

Restyle the existing Android app into a single **dark theme** with a more
catchy, user-friendly appearance. The redesign is **themed + structured**: a
new top app bar, related controls grouped into cards, restyled components, and a
cyan + amber color identity — **without** custom illustrations or heavy
animation.

**Feature parity is preserved.** No control, input, screen, or behavior is
added or removed. This is purely an appearance/layout change over the screens
shipped in Phases 1–3 (Survey Plot, Satellite Map, About).

## 2. Non-goals

- No new features, settings, or screens; no change to the Python core
  (`cave_sketch/` stays untouched and Streamlit-free) or the bridge logic.
- No light theme. The app is **dark-only** and ignores the system light/dark
  setting.
- No custom empty-state illustrations, Lottie/animated assets, or bespoke
  motion design (deferred — out of the chosen scope).
- No change to navigation structure (the Survey / Satellite / About bottom nav
  stays).

## 3. Decisions (from brainstorming)

1. **Theme mode:** dark-only. Always dark, regardless of system setting.
2. **Accent:** cyan + amber "headlamp" duo — cyan for normal actions/highlights,
   amber reserved for the single primary CTA per screen.
3. **Redesign scope:** themed + structured (app bar + grouped cards + restyled
   components), no illustrations/heavy animation.

## 4. Color tokens (dark scheme)

Replace the current light scheme. `Theme.kt` always uses the dark scheme; the
`isSystemInDarkTheme()` branch is removed. Define tokens in `Color.kt`.

| Material role | Hex | Used for |
|---|---|---|
| `background` | `#0F171A` | app background |
| `surface` | `#1A262C` | cards, app bar, bottom nav |
| `surfaceVariant` | `#22323A` | input field fills, dividers |
| `primary` | `#2BD4E6` | buttons, active tab, sliders, focus rings, links |
| `onPrimary` | `#062227` | text/icons on cyan |
| `secondary` | `#FFB74D` | the one primary CTA per screen + key highlights |
| `onSecondary` | `#1A1200` | text/icons on amber |
| `onBackground` / `onSurface` | `#E6EDEF` | primary text |
| `onSurfaceVariant` | `#9AA9AF` | labels, hints, captions, inactive nav |
| `outline` | `#3A4A52` | input borders |
| `error` | `#FF6B6B` | error text / banners |
| `onError` | `#3A0000` | text on error surfaces |

Notes:
- `primary` is `#00B8D4` (the existing brand cyan) brightened for legible
  contrast on the dark background. Brand continuity preserved.
- System status bar and navigation bar are tinted to `surface` with light icons
  (replacing the current grey default).

## 5. Global component patterns

These are shared styling rules applied consistently across all screens.

- **Top app bar:** each screen wraps its content in a `Scaffold` with a
  `TopAppBar` (`surface` colored) showing a small CaveSketch logo mark on the
  left and the screen title ("Survey Plot" / "Satellite Map" / "About").
  Replaces today's bare `Text("Survey Plot")` heading.
- **Section card:** a reusable composable — rounded `Card` (16dp corners,
  `surface` fill, low elevation), with a header row (small icon + bold label)
  and the grouped controls below. Used to group related controls on each screen.
- **Buttons:**
  - Standard actions (file pickers, Add/Remove point) → cyan `Button`, **12dp
    corner radius** (replacing today's fully-rounded pill).
  - The single **Generate** CTA per screen → amber filled, full-width, ~56dp
    tall, with a leading action icon. One amber CTA per screen, maximum.
- **Inputs:** `OutlinedTextField` with `surfaceVariant` fill, 12dp corners, cyan
  focus border, optional leading icon. Keyboard types unchanged.
- **Bottom navigation:** `surface` bar; cyan active icon + label with the
  existing pill indicator; `onSurfaceVariant` for inactive items.
- **Stepper row:** label on the left, a compact `−  value  +` segmented control
  on the right, on a single aligned row (replacing the current label-above /
  controls-below stacking).
- **States in the result area:**
  - Idle/empty → a friendly muted message card ("Pick your files and tap
    Generate").
  - Generating → spinner + phase text inside a card.
  - Error → soft red inline banner card (replacing bare `⚠️ Text`).

## 6. Per-screen layout

Controls and behavior are identical to the current screens; only grouping,
ordering within a group, and styling change.

### 6.1 Survey Plot (`SurveyPlotScreen.kt`)

App bar + scrollable column of cards:
1. **Input files** — Pick Cave Map, Pick Cave Section (file picker rows with
   chosen-file labels).
2. **Merge survey (optional)** — child map/section pickers, Main station ID,
   Child station ID, section merge protocol (Simple / Mirror / Displacement).
3. **Survey details** — survey name, surveyor name.
4. **Settings** — rule length slider, rotation stepper, marker/text/line-width
   zoom steppers, "Show station markers" and "Show grid" toggles.
5. **Generate Survey Plot** — amber CTA.
6. **Result area** — idle/generating/error/success states; on success the PDF
   preview + a cyan "Save / Share PDF" button.

### 6.2 Satellite Map (`SatelliteScreen.kt`)

App bar + cards:
1. **GPS points** — Station / Lat / Lon entry row, `[+ Add point]`
   `[− Remove last]`.
2. **Map details** — survey name, map rotation angle.
3. **Additional maps** — Import JSON maps (N).
4. **Generate Satellite Map** — amber CTA.
5. **Result area** — WebView map preview when online; the offline "No
   connection — satellite preview unavailable" banner restyled as a soft card;
   Save/Share for HTML/JSON/KMZ.

### 6.3 About (`AboutScreen.kt`)

Centered on the dark background: CaveSketch logo mark, "CaveSketch" title,
"Cave survey plotting & georeferencing" tagline, "Version 1.0.0" in a muted
chip, and a cyan "Project on GitHub" button (replacing the plain link text).

## 7. Files affected

- `ui/theme/Color.kt` — replace palette with the dark tokens (§4).
- `ui/theme/Theme.kt` — single dark scheme, always-on; set system bar colors;
  remove the light/dark branch.
- `ui/SurveyPlotScreen.kt`, `ui/SatelliteScreen.kt`, `ui/AboutScreen.kt` — wrap
  in `Scaffold` + `TopAppBar`, regroup controls into section cards.
- `ui/AppNavHost.kt` — bottom-nav styling (colors/indicator) if not already
  derived from the theme.
- `ui/components/*` (`SettingsForm.kt`, `GpsPointsEditor.kt`, `MergeControls.kt`,
  `FilePickerRow.kt`) — apply card grouping, stepper-row, and button styling.
- New shared composables (suggested): `SectionCard`, `StepperRow`,
  `PrimaryCta` (amber), `StateBanner` — added under `ui/components/` to keep
  screens declarative and styling DRY.

## 8. Constraints & verification

- `cave_sketch/` untouched; Streamlit web app unaffected (this is Android-only).
- Existing instrumented/unit tests for the screens (`SettingsFormTest`,
  `AboutScreenTest`, etc.) must still pass; update assertions only where they
  reference the old heading `Text` that the app bar replaces.
- The app builds and the redesigned screens render on a real device with all
  controls reachable and functional (parity check against Phase 3 behavior).
- Log the redesign in `android/DEVLOG.md` per the project's DEVLOG convention.

## 9. Success criteria

- App is dark-only with the §4 palette; status/nav bars tinted to match.
- Each screen has a top app bar and groups its controls into cards; steppers are
  single-row; the one Generate CTA per screen is amber.
- Cyan + amber identity applied consistently (buttons, inputs, nav, links).
- Full feature parity with Phase 3 — no control, screen, or behavior changed.
- Tests pass; build produces an installable APK.
