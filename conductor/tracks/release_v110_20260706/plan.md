# Plan: CaveSketch v1.1.0 Android Release

## Phase 1: Version Bump & Build Preparation [checkpoint: 0728cfd]

- [x] Task: Bump version in `build.gradle` (863734f)
    - [x] Update `versionCode` from `1` to `2`
    - [x] Update `versionName` from `"1.0.0"` to `"1.1.0"`
    - [x] Commit: `chore(android): Bump version to v1.1.0 (versionCode 2)`

- [x] Task: Verify all track code is present on the build branch (e615590)
    - [x] Confirm the 6 included tracks' changes exist in the working tree
    - [x] Run `./gradlew test` to verify Android unit tests pass

- [x] Task: Conductor - User Manual Verification 'Phase 1: Version Bump & Build Preparation' (Protocol in workflow.md) (0728cfd)

## Phase 2: Build & Package [checkpoint: 52b86dc]

- [x] Task: Build the release APK (e67596e)
    - [x] Run `./gradlew assembleRelease` from the `android/` directory
    - [x] Verify the APK is produced at `android/app/build/outputs/apk/release/app-release.apk`

- [x] Task: Rename the APK for distribution (7d4cc6f)
    - [x] Copy/rename `app-release.apk` to `CaveSketch-v1.1.0.apk`

- [x] Task: Conductor - User Manual Verification 'Phase 2: Build & Package' (Protocol in workflow.md) (52b86dc)

## Phase 3: Tag, Release Notes & Documentation

- [x] Task: Create annotated git tag (6b79d7d)
    - [x] Create tag `v1.1.0` with a descriptive message on the release commit

- [x] Task: Draft GitHub Release notes (988e2c4)
    - [x] Write markdown release notes with: version title, feature list, bug fix list, installation instructions
    - [x] Tone: friendly, action-oriented, aimed at field cavers
    - [x] Save as a deliverable artifact for the user to copy into GitHub Releases

- [x] Task: Update `android/RELEASE.md` (032d9c8)
    - [x] Update version references from v1.0.0 to include v1.1.0
    - [x] Commit: `docs(android): Update RELEASE.md for v1.1.0`

- [x] Task: Append release entry to `android/DEVLOG.md` (6292cfd)
    - [x] Add a `## [YYYY-MM-DD HH:MM] Release — v1.1.0 APK Build` entry
    - [x] Commit: `docs(android): Add v1.1.0 release DEVLOG entry`

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Tag, Release Notes & Documentation' (Protocol in workflow.md)
