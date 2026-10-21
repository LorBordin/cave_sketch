# Spec: CaveSketch v1.2.0 Android Release

## Overview

Build and publish the third Android release of CaveSketch (v1.2.0), bundling all improvements made since the v1.1.0 release (commit `863734f`, 2026-07-06). This is a **minor version** bump reflecting new features and bug fixes with no breaking changes. User documentation is audited and updated, and the user is guided step by step through publishing on GitHub Releases.

### Included Tracks (since v1.1.0)

| Track ID | Type | Summary |
|---|---|---|
| `dxf_icon_elements_20260930` | Feature | Water-flow, continuation and entrance icons now rendered; B_blocks fixed (PDF, satellite map, KMZ) |
| `magnetic_variation_20260930` | Feature | Magnetic declination correction to true north (backend) |
| `android_save_artifacts_20260930` | Feature | Save/Share menu: "Save to Device" (Storage Access Framework) or "Share" for all exports |
| `title_block_metadata_20261009` | Feature | Extended title block (drawer, municipality, coordinates, elevation, declination) with adaptive placement; Android inputs incl. magnetic variation |
| `entrance_symbol_orientation_20261014` | Bug Fix | Entrance/point symbol orientation and declination rotation fixed |
| `map_merge_protocol_20261014` | Feature | Map merge protocol Simple / Displacement (non-overlapping child map + connector line) |
| `snow_icon_20261014` | Bug Fix | B_snow now rendered in the KMZ export (white `*`, like TopoDroid) |
| `survey_csv_export_20261014` | Feature | Save/Share Map & Section CSVs to support iterative merging of >2 sub-surveys |

## Functional Requirements

### FR-1: Version Bump
- Update `android/app/build.gradle`: `versionCode` `2` → `3`, `versionName` `"1.1.0"` → `"1.2.0"`.

### FR-2: Documentation Audit & Update (EN + IT kept in sync)
- In-app guide: `android/app/src/main/assets/guide/guide_en.md` + `guide_it.md`
- `docs/android/README.md` + `README.it.md`
- Root `README.md` / `README.it.md` (version / feature references)
- `conductor/product.md` (only if out of date)
- Must cover: Save to Device / Share, Map & Section CSV export and iterative merge, map merge protocol (Simple / Displacement), title block fields, magnetic variation, new DXF icons.

### FR-3: Verification
- `uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest` pass.
- `cd android && ./gradlew :app:testDebugUnitTest` passes.

### FR-4: APK Build
- `./gradlew assembleRelease` from `android/`, signed with the same keystore as v1.0.0/v1.1.0.
- Rename `app-release.apk` → `CaveSketch-v1.2.0.apk`.

### FR-5: Device Check (user)
- Install the APK over v1.1.0; confirm upgrade preserves data and new features work.

### FR-6: Git Tag
- Annotated tag `v1.2.0` on the release commit.

### FR-7: GitHub Release Notes
- English markdown mirroring the v1.1.0 format and tone (⛰️ title, 🌟 New Features, 🛠️ Bug Fixes, 📲 How to Install), saved as a deliverable ready to paste.

### FR-8: Update RELEASE.md
- Update `android/RELEASE.md` to v1.2.0 and add a step-by-step GitHub Releases guide (push tag, draft release, attach APK, paste notes, publish, verify download).

### FR-9: DEVLOG
- Release entry in `android/DEVLOG.md`; root `DEVLOG.md` entry for documentation changes.

## Non-Functional Requirements

- The APK must be signed with the same keystore used for previous releases (required for in-place upgrades).
- Release notes concise and scannable.

## Acceptance Criteria

1. `build.gradle` shows `versionCode 3` and `versionName "1.2.0"`.
2. All Python gates and Gradle unit tests pass; `assembleRelease` succeeds.
3. `CaveSketch-v1.2.0.apk` exists and upgrades over v1.1.0 on a device.
4. Docs (EN + IT) describe all included features.
5. Tag `v1.2.0` exists; release notes ready to paste; `RELEASE.md` contains the guide.
6. DEVLOG entries appended.

## Out of Scope

- New feature development
- Google Play Store publishing
- Automated GitHub Actions release workflow
- Italian release notes
