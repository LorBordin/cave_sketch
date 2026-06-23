# Spec: Survey Settings UI Refinement

## Overview
Refine the Survey tab's settings controls in the Android app to make them simpler and more usable on mobile devices. The current implementation uses sliders for all numeric settings, which are imprecise on small screens and make fine-grained adjustments difficult. This track replaces most sliders with compact +/− stepper controls and reduces the rule-length range to a practical maximum.

## Functional Requirements

### FR-1: Reduce Rule Length Range
- Keep the Rule Length control as a **Slider**.
- Change the value range from `5–1000` to **`5–100`**.
- Keep the step size at **5 m**.
- The default value remains **100 m** (which is now the new maximum).

### FR-2: Map Rotation Stepper
- Replace the Map Rotation **Slider** with a **compact +/− stepper**.
- Range: **-180° to 180°**.
- Step size: **5°**.
- Display format: current integer value with ° suffix.
- Default: **0°**.

### FR-3: Zoom Steppers (Marker, Text, Line Width)
- Replace the three Zoom **Sliders** (Marker zoom, Text zoom, Line width zoom) with **compact +/− steppers**.
- Range: **-1.0 to 1.0**.
- Step size: **0.1**.
- Display format: value with 1 decimal place.
- Default: **0.0** for all three.

### FR-4: Stepper Widget Visual Design
- All steppers use a **compact inline layout**: `[−] value [+]`.
- The value is displayed centered between two small icon buttons.
- The `−` button is disabled at the minimum value; the `+` button is disabled at the maximum.
- The widget should be consistent with Material 3 theming.

### FR-5: Reusable Stepper Composable
- Extract the stepper as a **reusable `@Composable` function** (e.g., `StepperControl`) in the existing `SettingsForm.kt` file.
- Parameters: label, value, min, max, step, display formatter, onChange callback.

## Non-Functional Requirements
- The new controls must be easily tappable on mobile (touch target ≥ 44dp).
- No changes to the data model (`SurveyInputs`) or the Python bridge (`SurveyBridge`).
- No changes to the `SurveyPlotViewModel` logic.

## Acceptance Criteria
1. Rule Length slider range is 5–100m, step 5m.
2. Map Rotation is a stepper with step 5°, range -180–180.
3. Marker, Text, and Line Width zoom controls are steppers with step 0.1, range -1.0–1.0.
4. All steppers disable the appropriate button at boundary values.
5. The `SurveyInputs` data class is unchanged.
6. The app builds and runs correctly on API 28+.

## Out of Scope
- Changes to the Satellite tab.
- Changes to the Python backend or bridge layer.
- Addition of new settings or controls.
- Visual redesign of file-picker or merge controls.
