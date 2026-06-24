# Phase 3 — Polish & Release — Spec

**Initiative:** CaveSketch Mobile App
**Phase:** 3 · Polish & Release
**Status:** Approved (design)
**Date:** 2026-06-23
**Level:** 2 (per-phase). See `../../umbrella-spec.md` for the roadmap.

---

## 1. Goal

Turn the working app (Phases 0–2) into a downloadable, installable product: a
**release-signed `.apk`** published on **GitHub Releases**, branded with an app
icon and splash, given a light brand theme, and hardened against the few ways it
can fail in the field. No new survey/map features — parity with today's screens
is preserved; this phase is packaging, branding, robustness, and release.

This realises the umbrella's one-line Phase 3 ("App icon, error states, session
cleanup, build a distributable `.apk`"), expanded with light theming and the
splash/About polish agreed during design.

## 2. Scope

In scope:

- Adaptive launcher icon derived from `imgs/logo.png`.
- Branded splash held until the Python runtime is ready.
- Light brand theme (Material3 color scheme + typography), no screen redesign.
- About tab (third bottom-nav destination) showing the app version.
- Loading/progress polish on the two existing screens.
- Crash/init hardening (Python init, low storage, uncaught errors).
- Session-cleanup hardening (the basics already exist).
- Release signing + versioning + a smaller release build.
- Build and publish the `.apk` to GitHub Releases with install instructions.

## 3. Non-goals

- **No structural UI redesign** — re-layout of screens, custom components,
  animations, and illustrations are deferred to a future **Phase 4 — Visual
  redesign** (its own brainstorm/spec). Phase 3 stays shippable.
- **No new survey/map features** — parity only.
- **No Google Play Store** distribution — sideload via GitHub Releases only.
- **No offline satellite tiles**, no CI/automated build pipeline (a future
  phase may add CI; Phase 3 builds the `.apk` locally via Gradle).
- **No changes to the Streamlit web app's behaviour.**

## 4. Branding & identity

### 4.1 Adaptive launcher icon

- Source: `imgs/logo.png` (centered circular emblem on a light background).
- Produce an **adaptive icon**: foreground = the emblem, background = a solid
  light/brand color, plus the legacy `mipmap-*` density fallbacks and a round
  variant. Wire `android:icon` and `android:roundIcon` in the manifest.
- App label stays **"CaveSketch"**.

### 4.2 Branded splash

- Use **`androidx.core:core-splashscreen`** (the official SplashScreen API).
- Shows the logo on a solid brand background on cold start.
- **Held on-screen until the Python/Chaquopy runtime is initialized**, so the
  user never sees a dead/blank UI while Python boots. Use a `keepOnScreen`
  condition driven by an app-level "python ready" flag; release the splash once
  initialization completes (or fails — see §6). If init is already warm, the
  splash shows for the default minimal duration.

## 5. Theming & UI polish

### 5.1 Light brand theme

- Replace the stock `@android:style/Theme.Material.Light.NoActionBar` with a
  Material3 theme:
  - A brand **color scheme** derived from the logo palette (cyan/blue tones),
    light variant (dark variant optional, not required for exit).
  - Consistent typography and default component styling (buttons, cards, text
    fields) so the two screens read as a coherent product.
- **No layout changes** to the screens beyond what the theme applies globally.

### 5.2 About tab

- Add a **third bottom-nav destination** (info icon) in `AppNavHost`, reusing
  the existing `NavigationBar`/`NavigationBarItem` pattern — no new top app bar,
  no nav restructuring of the existing two destinations.
- Content (static, no logic): the CaveSketch logo, the **app version** read from
  `BuildConfig` (`versionName`), a one-line credit, and a link to the project
  repository (opens externally).

### 5.3 Loading / progress polish

- Audit the existing `Generating…` states on **Survey Plot** and **Satellite**
  screens. Ensure, on both: a visible progress indicator while a bridge call is
  in flight, the **Generate** button disabled during work, and clear staged
  messages. Fix gaps only — much of this already exists; do not rebuild working
  state machines.

## 6. Crash / init hardening

Convert the realistic failure modes into friendly UI instead of silent death or
a raw stack trace:

- **Python/Chaquopy fails to start** — if runtime initialization throws, release
  the splash and show a clear, non-technical error screen ("CaveSketch couldn’t
  start its engine…") rather than a blank app. Both generation screens remain
  guarded so they cannot call the bridge when the runtime is unavailable.
- **Device storage full** — copying picked inputs or writing outputs can fail
  with an `IOException`. Catch at the bridge/IO boundary and surface the existing
  structured `Error` state with a "not enough free space" message.
- **Uncaught generation error** — any unexpected error during generation surfaces
  via the existing per-screen `Error` state (already the pattern in Phases 1–2);
  verify no path bypasses it.
- **Global uncaught-exception path** — install a last-resort handler so a truly
  unexpected crash is logged and shown as a graceful "something went wrong"
  message rather than a system "app keeps stopping" dialog where feasible.

## 7. Session-cleanup hardening

`CaveSketchApplication` already deletes the previous run's intermediate and
output files on launch (`CaveSketchApplication.kt:11`). For Phase 3:

- **Verify coverage** of every current intermediate/output name: parsed CSVs,
  `merged_map.csv`, `survey.pdf`, `survey.html`, the satellite JSON + KMZ, and
  `additional_*` imports.
- Tidy the list/logic so it stays correct as a single source of truth. No
  redesign of the cleanup approach; nothing leaves the device.

## 8. Release & distribution

### 8.1 Signing

- Generate a **release keystore** once. The keystore file and its passwords are
  **kept out of git** (`.gitignore`); credentials are read from
  `local.properties` / `gradle.properties` (uncommitted) or environment, never
  hard-coded or committed.
- Add a release `signingConfig` in `android/app/build.gradle` and apply it to the
  `release` build type. The signed release `.apk` is **upgradeable** (a later
  version installs over the top without uninstall).

### 8.2 Build configuration

- Enable `minifyEnabled true` and resource shrinking for the `release` build to
  reduce `.apk` size; add ProGuard/R8 keep rules as needed so Chaquopy/Python and
  reflection-using libraries are not stripped. Verify the release build still
  runs end-to-end on device (shrinking must not break Python).
- Bump version to **`versionName "1.0.0"`, `versionCode 1`**.

### 8.3 Distribution

- `./gradlew assembleRelease` produces the signed
  `CaveSketch-1.0.0.apk`.
- Add **`android/RELEASE.md`** documenting: how to generate the keystore, how to
  build the release `.apk`, and how to publish it to a **GitHub Release** with
  end-user install instructions (download the `.apk` → allow installs from
  unknown sources → tap to install → future versions install over the top).

## 9. Testing

- **Kotlin (JVM unit tests):** version string shown by the About screen matches
  `BuildConfig.VERSION_NAME`; any new hardening helper (e.g. the storage-full /
  python-not-ready guard) returns the expected state. Keep existing ViewModel
  tests green.
- **Python:** existing bridge/core tests stay green (no core changes intended in
  this phase).
- **Manual device verification (release build):**
  1. Install the **release-signed** `.apk` on a real phone.
  2. Confirm the launcher icon and the branded splash appear.
  3. Confirm both screens still work end-to-end (PDF; KMZ/JSON + online preview).
  4. Confirm the About tab shows `1.0.0`.
  5. Confirm an **over-the-top upgrade** (build a `versionCode 2` test build,
     install over the top) succeeds without uninstall.
  6. Confirm a forced failure (e.g. airplane-mode preview, or a deliberately
     broken input) shows a friendly message, not a crash.

## 10. Verification gates (before "done")

- `uv run ruff check .`
- `uv run mypy cave_sketch/` (must stay green)
- `uv run pytest`
- Kotlin unit tests pass.
- Release `.apk` builds and installs on a real device (the manual checks above).
- Log the phase to `android/DEVLOG.md` (existing entry format).

## 11. Exit criteria

A release-signed **`CaveSketch-1.0.0.apk`** that installs from a **GitHub
Release** on a real Android device, featuring:

- the branded adaptive launcher icon and held-until-ready splash,
- the light brand theme and an About tab showing the version,
- hardened error/init paths (no silent crashes for the known failure modes),
- verified session cleanup,

with all verification gates passing and the phase logged to `android/DEVLOG.md`.

## 12. Notes on prior deviations (for an honest record)

- The umbrella §12 states `cave_sketch/` stays **untouched and Streamlit-free**.
  Latency-optimization work done outside the phase structure modified several
  core files (`cave_sketch/dxf/parser.py`, `cave_sketch/features/render_features.py`,
  `cave_sketch/backend_renders/matplotlib.py`,
  `cave_sketch/survey/graphics/survey_plot.py`) — see `android/DEVLOG.md`
  (2026-06-23). Phase 3 does **not** revert this; it is recorded here so the
  roadmap and the code stay reconciled. Any further core changes should still be
  avoided.

## 13. Future — Phase 4 (out of scope, for context)

A structural **Visual redesign** — screen re-layout, custom components,
animations, empty-state illustrations, micro-interactions — is deferred to a
future Phase 4 with its own brainstorm and spec. Phase 3 deliberately keeps the
visual change to light theming so the release stays low-risk.
