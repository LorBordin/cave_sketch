# Plan: Survey Settings UI Refinement

## Phase 1: Stepper Composable [checkpoint: eeea642]

- [x] Task: Write Tests — StepperControl composable [b0824cc]
    - [x] Create `app/src/test/java/com/cavesketch/app/ui/components/SettingsFormTest.kt`
    - [x] Test: stepper displays label and formatted value
    - [x] Test: tapping `+` increases value by step
    - [x] Test: tapping `−` decreases value by step
    - [x] Test: `+` button disabled at max boundary
    - [x] Test: `−` button disabled at min boundary
    - [x] Test: value clamps to min/max and does not exceed bounds

- [x] Task: Implement — StepperControl composable [b0824cc]
    - [x] Create a reusable `StepperControl` `@Composable` in `SettingsForm.kt`
    - [x] Parameters: label (`String`), value (`Number`), min, max, step, formatter (`(Number) -> String`), onChange
    - [x] Layout: `Label` row above, `[−] value [+]` compact inline row below
    - [x] Use Material 3 `IconButton` with `Icons.Filled.Remove` / `Icons.Filled.Add`
    - [x] Disable `−` when value ≤ min, `+` when value ≥ max
    - [x] Ensure touch targets ≥ 44dp

- [x] Task: Conductor - User Manual Verification 'Stepper Composable' (Protocol in workflow.md) [eeea642]

## Phase 2: Replace Sliders with Steppers

- [ ] Task: Write Tests — SettingsForm integration
    - [ ] Test: Rule Length slider has range 5–100 (not 1000)
    - [ ] Test: Map Rotation renders as stepper (not slider) with step 5
    - [ ] Test: Marker zoom renders as stepper with step 0.1
    - [ ] Test: Text zoom renders as stepper with step 0.1
    - [ ] Test: Line width zoom renders as stepper with step 0.1

- [ ] Task: Implement — Update SettingsForm
    - [ ] Change Rule Length slider `valueRange` from `5f..1000f` to `5f..100f`
    - [ ] Replace Map Rotation `Slider` with `StepperControl` (step=5, range=-180..180, formatter with °)
    - [ ] Replace the three `ZoomSlider` calls with `StepperControl` (step=0.1, range=-1.0..1.0, formatter with 1 decimal)
    - [ ] Remove the now-unused `ZoomSlider` private composable

- [ ] Task: Conductor - User Manual Verification 'Replace Sliders with Steppers' (Protocol in workflow.md)
