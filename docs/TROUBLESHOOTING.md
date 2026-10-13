# Troubleshooting: building and running the app on Windows

Written from the 13 Oct 2026 build session. Each entry: what you see, why, what to do.

## The toolchain this project expects

| Piece | Version | Where it is set |
|---|---|---|
| Flutter | 3.47.6 stable | `flutter --version` (CI uses the same) |
| Java for Gradle | 21 (JDK 17+ works) | `flutter config --jdk-dir="C:\Program Files\Java\jdk-21.0.10"` |
| Gradle | 9.3.1 | `mobile/android/gradle/wrapper/gradle-wrapper.properties` |
| Android Gradle Plugin | 9.1.0 | `mobile/android/settings.gradle.kts` |
| Kotlin Gradle Plugin | 2.4.0 | `mobile/android/settings.gradle.kts` |
| minSdk | Flutter default (24) | `mobile/android/app/build.gradle.kts` |

Do not change these to make one error go away; every push builds the APK on GitHub with exactly these
(CI job `android-build`), so if CI is green the problem is on the PC, not in the project.

## `:jni:compileDebugJavaWithJavac` / "Cannot query the value of this provider"

Cause: the `sentry_flutter` package (added 13 Oct, removed the same day) pulled in a native `jni` plugin that
needs CMake, the Android 35 platform, minSdk 26 and an older Android Gradle Plugin.

Fix: pull the latest `main`. If you changed Gradle files by hand while chasing this error, put them back:

```powershell
cd C:\Users\babua\Documents\App-claude
git status --short mobile/android
git checkout -- mobile/android/settings.gradle.kts mobile/android/gradle/wrapper/gradle-wrapper.properties mobile/android/app/build.gradle.kts
git pull
cd mobile
flutter clean
flutter pub get
```

## "This build uses a Java 8 JVM" / "Dependency requires at least JVM runtime version 11"

Cause: Gradle picked an old Java from `PATH` (Oracle's `javapath` shim points at Java 8).

Fix (once):

```powershell
flutter config --jdk-dir="C:\Program Files\Java\jdk-21.0.10"
cd mobile\android; .\gradlew.bat --stop; cd ..
```

Running `.\gradlew.bat` directly (outside `flutter run`) also needs `JAVA_HOME` set in that window:
`$env:JAVA_HOME = "C:\Program Files\Java\jdk-21.0.10"`.

## Gradle download times out

The wrapper downloads Gradle once into `%USERPROFILE%\.gradle\wrapper\dists`. If it times out but
`curl.exe -IL https://services.gradle.org/distributions/gradle-9.3.1-all.zip` works, retry on a different network
or set a longer timeout in `gradle-wrapper.properties` (`networkTimeout=60000`). Do not point the wrapper at a
file in Downloads; that breaks the build for everyone else and for CI.

## "Failed to find target with hash string 'android-XX'"

A plugin needs that Android platform. Install it from Android Studio: **Settings → Languages & Frameworks →
Android SDK → SDK Platforms**, tick it, Apply. Check it really landed:

```powershell
Test-Path "$env:LOCALAPPDATA\Android\Sdk\platforms\android-36\android.jar"
```

(`sdkmanager "platforms;android-35"` from the old command-line tools can fail with "Package not found"; the
Android Studio screen is the reliable way.)

## "Dart SDK is not configured" in Android Studio

Only the editor's code help is affected; `flutter run` still works. Fix: **File → Settings → Languages & Frameworks
→ Flutter** → Flutter SDK path `C:\Users\babua\flutter`, then **Dart** → Dart SDK path
`C:\Users\babua\flutter\bin\cache\dart-sdk`. Apply, restart. If it stays: **File → Invalidate Caches → Invalidate
and Restart**.

## Emulator: "System UI isn't responding"

An emulator problem, not the app. Tap **Wait** once. If it returns: **Device Manager → ⋮ → Cold Boot Now**; still
bad → **Wipe Data**. A real phone over wireless debugging (docs/DEMO.md) avoids emulator issues entirely.

## "Skipped 532 frames" on first launch

Normal for a debug build on a cold emulator (debug code is not optimised). Judge speed with
`flutter run --profile` on a real phone.

## `No supported devices found with name or id matching '--dart-define=…'`

`$phone` was empty (new terminal). Paste the two lines again before `flutter run`:

```powershell
$adb   = "C:\Users\babua\AppData\Local\Android\sdk\platform-tools\adb.exe"
$phone = "adb-10BF49245X0026E-aTofZl._adb-tls-connect._tcp"   # from: & $adb devices
```

## "Warning: Observed package id 'cmdline-tools;latest' in inconsistent location"

Harmless. To clean it: Android Studio **SDK Tools** tab → untick **Android SDK Command-line Tools (latest)** →
Apply → tick it again → Apply.

## A key or password appeared in a screenshot or chat

Treat it as leaked. Revoke it at the provider (Gemini: https://aistudio.google.com/apikey → delete the key),
create a new one, put it only in `backend\.env`. `.env` is in `.gitignore` and has never been committed
(checked 13 Oct 2026), so no Git cleanup is needed.
