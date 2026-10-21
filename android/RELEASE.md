# CaveSketch Android — Building & Releasing

## One-time setup: signing keystore

The release `.apk` is signed with a keystore kept **out of git**.

```bash
keytool -genkeypair -v -keystore android/app/release.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias cavesketch
cp android/keystore.properties.template android/keystore.properties
# edit android/keystore.properties with your passwords
```

Keep `release.jks` and `keystore.properties` safe and private. Losing the
keystore means future versions can no longer upgrade installed apps.

## Build the release APK

```bash
cd android
./gradlew assembleRelease
```

Output: `android/app/build/outputs/apk/release/app-release.apk`.
Rename for distribution: `CaveSketch-v1.2.0.apk` (or `CaveSketch-v1.1.0.apk` / `CaveSketch-1.0.0.apk` for earlier releases).

```bash
cp android/app/build/outputs/apk/release/app-release.apk CaveSketch-v1.2.0.apk
```

## Step-by-Step Guide: Publishing to GitHub Releases

1. **Ensure the annotated Git tag exists and is pushed to GitHub:**
   ```bash
   git tag -a v1.2.0 -m "CaveSketch v1.2.0 Android Release"
   git push origin main --tags
   ```
2. **Draft a new release on GitHub:**
   - Open [https://github.com/LorBordin/cave_sketch/releases/new](https://github.com/LorBordin/cave_sketch/releases/new) (or go to [Releases](https://github.com/LorBordin/cave_sketch/releases) → **Draft a new release**).
3. **Select tag and set release title:**
   - **Choose a tag:** Select `v1.2.0` (must match `versionName` in `android/app/build.gradle`).
   - **Release title:** `⛰️ CaveSketch v1.2.0 for Android` (or `CaveSketch v1.2.0`).
4. **Paste the release notes:**
   - Copy the markdown release notes (from `conductor/tracks/release_v120_20261021/release_notes_v1.2.0.md`) into the **Describe this release** text box.
   - Use the **Preview** tab to verify that the headings, bullet points, and emojis render cleanly.
5. **Attach the signed APK binary:**
   - Drag and drop `CaveSketch-v1.2.0.apk` (from the repository root) into the **Attach binaries by dropping them here or selecting them** area at the bottom of the form.
   - Wait until the ~98 MB upload progress bar completes.
6. **Publish the release:**
   - Ensure **Set as the latest release** is checked.
   - Click **Publish release**.
7. **Verify the published release:**
   - Confirm that `v1.2.0` is badged as **Latest** on [https://github.com/LorBordin/cave_sketch/releases](https://github.com/LorBordin/cave_sketch/releases).
   - Click `CaveSketch-v1.2.0.apk` under **Assets** to verify that the download starts cleanly.

## Installing on a phone (for users)

1. Download `CaveSketch-v1.2.0.apk` (or the latest version) from the Releases page.
2. Tap it; Android asks to allow installs from this source — enable it
   (Settings → Apps → Special access → Install unknown apps).
3. Tap Install.
4. **Upgrades:** download a newer `CaveSketch-vX.Y.Z.apk` and install it over the
   top — settings and the app are preserved (same signing key required).

## Releasing a new version

1. Audit and update user documentation (`android/app/src/main/assets/guide/`, `docs/android/`, `README.md`, `README.it.md`).
2. Bump `versionCode` (must increase) and `versionName` in `android/app/build.gradle`.
3. Run quality gates (`uv run ruff check .`, `uv run mypy cave_sketch/`, `uv run pytest`, `cd android && ./gradlew :app:testDebugUnitTest`).
4. Rebuild (`cd android && ./gradlew assembleRelease`), rename the APK to `CaveSketch-vX.Y.Z.apk`, test upgrading on a physical device, tag `vX.Y.Z`, and follow the GitHub Releases guide above.
