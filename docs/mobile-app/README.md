# CaveSketch Mobile App — Initiative Home

This folder is the single, tool-neutral home for the **CaveSketch Mobile App**
initiative: turning the existing Streamlit web app into an installable,
offline-capable Android `.apk` while keeping the web app and the shared
`cave_sketch` core untouched.

It is used by **both** agent workflows in this repo:
- **Claude Code / superpowers** (brainstorm → spec → plan → implement).
- **Antigravity CLI (`agy`) / conductor** (tracks, `plan.md` as source of truth,
  TDD, git-notes checkpoints). See `GEMINI.md` in this folder.

## Layout

```
docs/mobile-app/
├── README.md          ← you are here (index + status)
├── GEMINI.md          ← instructions for agy/conductor
├── umbrella-spec.md   ← Level 1: the roadmap (architecture, phases, risks)
└── phases/
    ├── phase-0-spike/        (spec.md + plan.md, created just-in-time)
    ├── phase-1-survey-plot/
    ├── phase-2-satellite-map/
    └── phase-3-polish/
```

## How to work here

1. Read `umbrella-spec.md` — the stable contract for architecture & scope.
2. Pick the current phase; create/read its `spec.md` + `plan.md` under `phases/`.
   Per-phase specs are written **just-in-time**, not all up front, so each can
   use findings from earlier phases.
3. Obey the hard constraints in §12 of the umbrella spec and the root
   `GEMINI.md` (uv, ruff/mypy/pytest gates, `cave_sketch` stays Streamlit-free,
   `DEVLOG.md` entries).

## Status

| Phase | Description | Status |
|-------|-------------|--------|
| Umbrella spec | Roadmap & architecture | ✅ Approved |
| Phase 0 | Spike: prove Python stack runs on device | ⬜ Not started |
| Phase 1 | Survey Plot screen | ⬜ Not started |
| Phase 2 | Satellite Map screen | ⬜ Not started |
| Phase 3 | Polish & release `.apk` | ⬜ Not started |
