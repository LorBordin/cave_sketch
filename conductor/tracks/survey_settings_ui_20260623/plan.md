# Plan: Survey Settings UI Refinement

## Phase 1: Stepper Composable

- [ ] Task: Write Tests — StepperControl composable
    - [ ] Create `app/src/test/java/com/cavesketch/app/ui/components/SettingsFormTest.kt`
    - [ ] Test: stepper displays label and formatted value
    - [ ] Test: tapping `+` increases value by step
    - [ ] Test: tapping `−` decreases value by step
    - [ ] Test: `+` button disabled at max boundary
    - [ ] Test: `−` button disabled at min boundary
    - [ ] Test: value clamps to min/max and does not exceed bounds

- [ ] Task: Implement — StepperControl composable
    - [ ] Create a reusable `StepperControl` `@Composable` in `SettingsForm.kt`
    - [ ] Parameters: label (`String`), value (`Number`), min, max, step, formatter (`(Number) -> String`), onChange
    - [ ] Layout: `Label` row above, `[−] value [+]` compact inline row below
    - [ ] Use Material 3 `IconButton` with `Icons.Filled.Remove` / `Icons.Filled.Add`
    - [ ] Disable `−` when value ≤ min, `+` when value ≥ max
    - [ ] Ensure touch targets ≥ 44dp

- [ ] Task: Conductor - User Manual Verification 'Stepper Composable' (Protocol in workflow.md)

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
