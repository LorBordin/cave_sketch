# GEMINI.md — agy/conductor instructions for the CaveSketch Mobile App

You (Antigravity CLI, `agy`, running the **conductor** workflow) are working
inside the **CaveSketch Mobile App** initiative. This file tells you how this
initiative is organized and what rules apply. It does **not** replace the
repo-root `GEMINI.md` or `conductor/workflow.md` — it sits on top of them.

## Read first (every session, in order)

1. Repo-root `GEMINI.md` — project context, code standards, mandatory
   verification, DEVLOG protocol.
2. `conductor/workflow.md` — task lifecycle (TDD, `plan.md` as source of truth,
   git-notes checkpoints, phase checkpointing).
3. `docs/mobile-app/umbrella-spec.md` — the **source of truth** for this
   initiative's architecture, scope, risks, and phase boundaries.
4. The current phase's `spec.md` + `plan.md` under `docs/mobile-app/phases/`.
5. Both DEVLOGs — decisions from previous sessions override specs on conflict.
   Root `DEVLOG.md` (Python project) for shared-core context, and
   `android/DEVLOG.md` for mobile-app history (exists from Phase 0 onward).

## What we are building

A native Android app (Kotlin + Jetpack Compose) that embeds CPython via
**Chaquopy** and calls the **untouched** `cave_sketch` package, giving cavers an
offline `.apk` with full feature parity to the Streamlit web app. The web app
and `cave_sketch` keep working unchanged. Full rationale: `umbrella-spec.md`.

## Spec/plan structure (two levels)

- **Level 1:** `umbrella-spec.md` — stable roadmap. Change only with the user's
  agreement; it defines the phase boundaries.
- **Level 2:** one folder per phase under `phases/` (e.g. `phases/phase-0-spike/`)
  containing that phase's `spec.md` and `plan.md`. These are written
  **just-in-time**, right before the phase is built, and may incorporate
  findings from earlier phases. Do **not** pre-write later phases' specs.

## Mapping to conductor

- Treat **each phase as one conductor track.** The track's working `spec.md` and
  `plan.md` live in this initiative's `phases/<phase>/` folder (keep the
  initiative self-contained), while you still follow `conductor/workflow.md` for
  the task lifecycle, checkpoints, and git notes, and register the track in
  `conductor/tracks.md` as usual.
- Apply the conductor **Phase Completion Verification & Checkpointing Protocol**
  at the end of each phase.
- For on-device behaviour that cannot be checked by automated tests, the manual
  verification plan must be performed on a **real Android phone**, not an
  emulator-only check.

## Hard constraints (do not violate)

- `cave_sketch/` stays **untouched and free of any UI/Streamlit/Android imports.**
  It is the shared core for both web and mobile. If a Streamlit-free helper is
  genuinely needed by the app, add it **to `cave_sketch`** — never duplicate
  logic in the Android layer.
- Do **not** change the Streamlit web app's behaviour.
- Python is managed with **`uv`** (`uv sync`, `uv run`, `uv add`). Never bare
  `pip`. Commit `uv.lock`.
- The Android app lives in a new top-level `android/` directory. Kotlin/Gradle
  code is built/tested with the Android toolchain; Python core code keeps using
  the existing `uv` + pytest gates.
- Mandatory Python gates before "done": `uv run ruff check .`,
  `uv run mypy cave_sketch/`, `uv run pytest` all pass.
- Append a DEVLOG entry after each meaningful change (root `GEMINI.md` format).
  **Mobile-app work goes in `android/DEVLOG.md`, not the root `DEVLOG.md`.** The
  root log is for the Python project (`cave_sketch` core + Streamlit web app).

## Notes specific to this initiative

- The main early risk is dependency build compatibility under Chaquopy
  (`numpy`/`pandas`/`matplotlib` versions may differ from `pyproject.toml`
  pins). Phase 0 exists to resolve this before any UI work. Record the
  discovered versions and render times in Phase 0's `spec.md`/`DEVLOG.md`.
- Offline is a hard requirement for PDF + KMZ/JSON. Only the satellite *preview*
  may require internet, and must degrade gracefully (see umbrella spec §8).
