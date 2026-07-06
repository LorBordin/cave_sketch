# Spec: CaveSketch v1.1.0 Android Release

## Overview

Build and publish the second Android release of CaveSketch (v1.1.0), bundling all improvements made since the v1.0.0 release (2026-06-24). This is a **minor version** bump reflecting 3 new features and 3 bug fixes with no breaking changes.

### Included Tracks (since v1.0.0)

| Track ID | Type | Summary |
|---|---|---|
| `section_rule_fix_20260630` | Bug Fix | Fixed section-view scale bar overlapping survey drawing via collision detection |
| `section_rule_snap_fix_20260630` | Bug Fix | Fixed grid-snap reintroducing scale bar collisions after collision-free placement |
| `show_polygonal_line_20260630` | Feature | Added toggle to show/hide the polygonal centerline on plan and section views |
| `dxf_version_compat_20260630` | Feature | Added support for DXF R14/R2000 files (LWPOLYLINE entities) |
| `input_validation_20260703` | Feature | Pre-flight file validation on Android with user-friendly error messages |
| `inapp_guide_20260703` | Feature | Embedded offline user guide (EN/IT) in the About screen |

## Functional Requirements

### FR-1: Version Bump
- Update `android/app/build.gradle`:
  - `versionCode` from `1` → `2`
  - `versionName` from `"1.0.0"` → `"1.1.0"`

### FR-2: APK Build
- Build the release APK locally via `./gradlew assembleRelease` from the `android/` directory
- **Prerequisite**: All code from the 6 included tracks must be present on the build branch
- Output: `android/app/build/outputs/apk/release/app-release.apk`

### FR-3: APK Rename
- Rename the output APK to `CaveSketch-v1.1.0.apk` for distribution

### FR-4: Git Tag
- Create an annotated git tag `v1.1.0` on the release commit

### FR-5: GitHub Release Notes
- Draft a markdown release notes document suitable for a GitHub Release page
- Must include: version name, summary of changes grouped by type (Features / Bug Fixes), installation instructions, and a link to the APK asset
- Tone: friendly, action-oriented, aimed at field cavers

### FR-6: Update RELEASE.md
- Update `android/RELEASE.md` to reference v1.1.0 alongside v1.0.0
- Ensure the "Releasing a new version" section still applies

### FR-7: DEVLOG Entry
- Append a release entry to `android/DEVLOG.md` documenting the v1.1.0 build

## Non-Functional Requirements

- The APK must be signed with the same keystore used for v1.0.0 (required for in-place upgrades)
- The release notes should be concise and scannable (bullet points, not paragraphs)

## Acceptance Criteria

1. `build.gradle` shows `versionCode 2` and `versionName "1.1.0"`
2. `./gradlew assembleRelease` completes successfully
3. Output APK exists and is renamed to `CaveSketch-v1.1.0.apk`
4. Git tag `v1.1.0` exists on the release commit
5. A markdown release notes document is produced, ready to paste into GitHub Releases
6. `RELEASE.md` references v1.1.0
7. `android/DEVLOG.md` has a v1.1.0 release entry

## Out of Scope

- GitHub Actions automated release workflow (manual upload via GitHub UI)
- Publishing to Google Play Store
- Any new feature development (all features already implemented on the build branch)
- Python library/web app changes (this track is Android-only)
