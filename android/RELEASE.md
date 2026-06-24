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
Rename for distribution: `CaveSketch-1.0.0.apk`.

## Publish to GitHub Releases

1. Go to https://github.com/LorBordin/cave_sketch/releases → "Draft a new release".
2. Tag: `v1.0.0` (matches `versionName`). Title: `CaveSketch 1.0.0`.
3. Attach `CaveSketch-1.0.0.apk` as a release asset.
4. Publish.

## Installing on a phone (for users)

1. Download `CaveSketch-1.0.0.apk` from the Releases page.
2. Tap it; Android asks to allow installs from this source — enable it
   (Settings → Apps → Special access → Install unknown apps).
3. Tap Install.
4. **Upgrades:** download a newer `CaveSketch-x.y.z.apk` and install it over the
   top — settings and the app are preserved (same signing key required).

## Releasing a new version

Bump `versionCode` (must increase) and `versionName` in
`android/app/build.gradle`, rebuild, and attach the new APK to a new Release.
