# Plan: CaveSketch v1.1.0 Android Release

## Phase 1: Version Bump & Build Preparation

- [x] Task: Bump version in `build.gradle` (863734f)
    - [x] Update `versionCode` from `1` to `2`
    - [x] Update `versionName` from `"1.0.0"` to `"1.1.0"`
    - [x] Commit: `chore(android): Bump version to v1.1.0 (versionCode 2)`

- [x] Task: Verify all track code is present on the build branch (e615590)
    - [x] Confirm the 6 included tracks' changes exist in the working tree
    - [x] Run `./gradlew test` to verify Android unit tests pass

- [ ] Task: Conductor - User Manual Verification 'Phase 1: Version Bump & Build Preparation' (Protocol in workflow.md)

## Phase 2: Build & Package

- [ ] Task: Build the release APK
    - [ ] Run `./gradlew assembleRelease` from the `android/` directory
    - [ ] Verify the APK is produced at `android/app/build/outputs/apk/release/app-release.apk`

- [ ] Task: Rename the APK for distribution
    - [ ] Copy/rename `app-release.apk` to `CaveSketch-v1.1.0.apk`

- [ ] Task: Conductor - User Manual Verification 'Phase 2: Build & Package' (Protocol in workflow.md)

## Phase 3: Tag, Release Notes & Documentation

- [ ] Task: Create annotated git tag
    - [ ] Create tag `v1.1.0` with a descriptive message on the release commit

- [ ] Task: Draft GitHub Release notes
    - [ ] Write markdown release notes with: version title, feature list, bug fix list, installation instructions
    - [ ] Tone: friendly, action-oriented, aimed at field cavers
    - [ ] Save as a deliverable artifact for the user to copy into GitHub Releases

- [ ] Task: Update `android/RELEASE.md`
    - [ ] Update version references from v1.0.0 to include v1.1.0
    - [ ] Commit: `docs(android): Update RELEASE.md for v1.1.0`

- [ ] Task: Append release entry to `android/DEVLOG.md`
    - [ ] Add a `## [YYYY-MM-DD HH:MM] Release — v1.1.0 APK Build` entry
    - [ ] Commit: `docs(android): Add v1.1.0 release DEVLOG entry`

- [ ] Task: Conductor - User Manual Verification 'Phase 3: Tag, Release Notes & Documentation' (Protocol in workflow.md)
