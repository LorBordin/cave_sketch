# Plan: CaveSketch v1.2.0 Android Release

## Phase 1: Documentation Audit & Update [checkpoint: bf284a0]

- [x] Task: Audit docs against included tracks (790a83a)
    - [x] Diff each doc vs. the 8 included tracks; list gaps
- [x] Task: Update in-app guide (`guide_en.md` + `guide_it.md`) (790a83a)
    - [x] Save to Device / Share, Map & Section CSV + iterative merge, map merge protocol, DXF icons
- [x] Task: Update `docs/android/README.md` + `README.it.md` (790a83a)
- [x] Task: Update root `README.md` / `README.it.md` and `conductor/product.md` (if stale) (790a83a)
- [x] Task: Append root `DEVLOG.md` entry; commit `docs: Update user docs for v1.2.0` (790a83a)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Documentation Audit & Update' (Protocol in workflow.md) (bf284a0)

## Phase 2: Version Bump & Verification [checkpoint: bd94bbe]

- [x] Task: Bump version in `build.gradle` (6d6d106)
    - [x] `versionCode` 2 → 3, `versionName` "1.1.0" → "1.2.0"
    - [x] Commit: `chore(android): Bump version to v1.2.0 (versionCode 3)`
- [x] Task: Run gates (6d6d106)
    - [x] `uv run ruff check .` / `uv run mypy cave_sketch/` / `uv run pytest`
    - [x] `cd android && ./gradlew :app:testDebugUnitTest`
- [x] Task: Conductor - User Manual Verification 'Phase 2: Version Bump & Verification' (Protocol in workflow.md) (bd94bbe)

## Phase 3: Build & Package [checkpoint: aef61b9]

- [x] Task: Build release APK (6d6d106)
    - [x] `./gradlew assembleRelease`; verify signed with the release keystore
- [x] Task: Rename to `CaveSketch-v1.2.0.apk` (6d6d106)
- [x] Task: User installs APK over v1.1.0 on device and confirms upgrade + new features (6d6d106)
- [x] Task: Conductor - User Manual Verification 'Phase 3: Build & Package' (Protocol in workflow.md) (aef61b9)

## Phase 4: Tag, Release Notes & Release Guide [checkpoint: 8a32b16]

- [x] Task: Draft GitHub release notes (English, v1.1.0 format) as deliverable (3726c82)
- [x] Task: Update `android/RELEASE.md` with v1.2.0 + step-by-step GitHub Releases guide (3726c82)
- [x] Task: Append `android/DEVLOG.md` release entry (3726c82)
- [x] Task: Create annotated tag `v1.2.0` on the release commit (3726c82)
- [x] Task: Guide user through publishing (`git push origin main --tags`, draft release, attach APK, paste notes, publish, verify) (3726c82)
- [x] Task: Conductor - User Manual Verification 'Phase 4: Tag, Release Notes & Release Guide' (Protocol in workflow.md) (8a32b16)
