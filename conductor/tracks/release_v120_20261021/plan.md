# Plan: CaveSketch v1.2.0 Android Release

## Phase 1: Documentation Audit & Update

- [ ] Task: Audit docs against included tracks
    - [ ] Diff each doc vs. the 8 included tracks; list gaps
- [ ] Task: Update in-app guide (`guide_en.md` + `guide_it.md`)
    - [ ] Save to Device / Share, Map & Section CSV + iterative merge, map merge protocol, DXF icons
- [ ] Task: Update `docs/android/README.md` + `README.it.md`
- [ ] Task: Update root `README.md` / `README.it.md` and `conductor/product.md` (if stale)
- [ ] Task: Append root `DEVLOG.md` entry; commit `docs: Update user docs for v1.2.0`
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Documentation Audit & Update' (Protocol in workflow.md)

## Phase 2: Version Bump & Verification

- [ ] Task: Bump version in `build.gradle`
    - [ ] `versionCode` 2 → 3, `versionName` "1.1.0" → "1.2.0"
    - [ ] Commit: `chore(android): Bump version to v1.2.0 (versionCode 3)`
- [ ] Task: Run gates
    - [ ] `uv run ruff check .` / `uv run mypy cave_sketch/` / `uv run pytest`
    - [ ] `cd android && ./gradlew :app:testDebugUnitTest`
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Version Bump & Verification' (Protocol in workflow.md)

## Phase 3: Build & Package

- [ ] Task: Build release APK
    - [ ] `./gradlew assembleRelease`; verify signed with the release keystore
- [ ] Task: Rename to `CaveSketch-v1.2.0.apk`
- [ ] Task: User installs APK over v1.1.0 on device and confirms upgrade + new features
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Build & Package' (Protocol in workflow.md)

## Phase 4: Tag, Release Notes & Release Guide

- [ ] Task: Draft GitHub release notes (English, v1.1.0 format) as deliverable
- [ ] Task: Update `android/RELEASE.md` with v1.2.0 + step-by-step GitHub Releases guide
- [ ] Task: Append `android/DEVLOG.md` release entry
- [ ] Task: Create annotated tag `v1.2.0` on the release commit
- [ ] Task: Guide user through publishing (`git push origin main --tags`, draft release, attach APK, paste notes, publish, verify)
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Tag, Release Notes & Release Guide' (Protocol in workflow.md)
