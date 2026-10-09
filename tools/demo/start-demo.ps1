<#
  Runs one of the two CapitUp demos on your Android phone over Wi-Fi.

  Examples (PowerShell, from the repo folder):
    .\tools\demo\start-demo.ps1 -Variant v2
    .\tools\demo\start-demo.ps1 -Variant v1 -Connect 192.168.1.50:41234

  v2 = the modern UI (this branch), v1 = the CoverSure-style UI (folder ..\App-claude-v1, see docs\DEMO.md).
  Start the backend first (docs\DEMO.md, step 2).
#>
param(
  [ValidateSet('v1', 'v2')][string]$Variant = 'v2',
  # The phone's "IP address & Port" from Developer options > Wireless debugging. Optional if already connected.
  [string]$Connect = ''
)

$ErrorActionPreference = 'Stop'
$adb = Join-Path $env:LOCALAPPDATA 'Android\sdk\platform-tools\adb.exe'
if (-not (Test-Path $adb)) { throw "adb not found at $adb. Install the Android SDK platform-tools via Android Studio." }

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$appRoot = if ($Variant -eq 'v1') { Join-Path (Split-Path $root -Parent) 'App-claude-v1' } else { $root }
if (-not (Test-Path (Join-Path $appRoot 'mobile\pubspec.yaml'))) {
  throw "Cannot find the $Variant app at $appRoot. For v1, create it first: see docs\DEMO.md step 1."
}

if ($Connect) { & $adb connect $Connect | Out-Host }

# Find the phone: the one connected device that is not an emulator.
$phones = @(& $adb devices | Select-Object -Skip 1 |
  Where-Object { $_ -match '\sdevice$' -and $_ -notmatch '^emulator-' } |
  ForEach-Object { ($_ -split '\s+')[0] })
if ($phones.Count -ne 1) {
  & $adb devices | Out-Host
  throw "Expected exactly one phone, found $($phones.Count). Pair/connect the phone first (docs\DEMO.md, step 3)."
}
$serial = $phones[0]
Write-Host "Using phone: $serial"

# Lets the phone reach the backend running on this PC at 127.0.0.1:8000.
& $adb -s $serial reverse tcp:8000 tcp:8000 | Out-Host

Set-Location (Join-Path $appRoot 'mobile')
flutter pub get
flutter run -d $serial --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
