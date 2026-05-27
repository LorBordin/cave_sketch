# Implementation Plan: North Symbol Visibility for Section Renders

## Key Files
- `cave_sketch/survey/config.py` — `SurveyConfig` dataclass (add `show_north` field here)
- `cave_sketch/survey/survey.py` — `draw_survey()` lines 60-63 (section-only reassignment, set `show_north=False` here)
- `cave_sketch/survey/renderer.py` — `render_survey()` (use `config.show_north` instead of hardcoded `True`; also fix subplot title)
- `tests/test_renderer.py` or `tests/test_survey.py` — write tests here

## Phase 1: Investigation and Testing [checkpoint: 0c532ac]
- [x] Task: Confirm the root cause — in `cave_sketch/survey/survey.py:60-63`, `section_survey` is reassigned to `survey` (losing section-only context), so `renderer.py` renders it as a plan subplot with `north_flag=True`. 717a6e2
- [x] Task: Write failing unit tests verifying section-only renders have no north symbol and title `"Sezione"`. 717a6e2
    - [x] Locate or create the test file (e.g., `tests/test_renderer.py` or `tests/test_survey.py`). 717a6e2
    - [x] Test 1: Call `draw_survey(csv_map_path=None, csv_section_path=<fixture_path>, rule_length=50, title="Test")`. Assert the returned figure's subplot title is `"Sezione"`. 717a6e2
    - [x] Test 2: Call `render_survey(survey=section_data, config=SurveyConfig(show_north=False), section_survey=None)`. Assert that `_add_north_arrow` is not called (mock it) or that no north arrow artist is present. 717a6e2
    - [x] Test 3: Regression — `draw_survey(csv_map_path=<path>, ...)` still renders with `north_flag=True` on plan subplot. 717a6e2
- [x] Task: Conductor - User Manual Verification 'Phase 1: Investigation and Testing' (Protocol in workflow.md) 0c532ac

## Phase 2: Implementation
- [x] Task: Add `show_north: bool = True` field to `SurveyConfig` in `cave_sketch/survey/config.py`. 01e61c3
- [x] Task: In `cave_sketch/survey/survey.py`, within the section-only branch (lines 60-63), set `show_north=False` on `render_config` after the `SurveyConfig` is constructed. dffefac
    - Note: `render_config` is built *after* this branch, so either move config construction above it, or pass `show_north` as a local flag and apply it to `render_config` before calling `render_survey()`.
- [x] Task: In `cave_sketch/survey/renderer.py`, replace the hardcoded `north_flag=True` on the plan subplot (line 72) with `north_flag=config.show_north`. 09718bd
- [x] Task: In `cave_sketch/survey/renderer.py`, when `section_survey` is `None` and `config.show_north` is `False`, set the subplot title to `"Sezione"` instead of `"Pianta"`. 09718bd
- [x] Task: Run all automated tests (`uv run pytest`) and ensure the newly written tests pass (Green Phase). 09718bd
- [x] Task: Run linting and static analysis (`uv run ruff check .` and `uv run mypy cave_sketch/`) to ensure code quality. 09718bd
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation' (Protocol in workflow.md)