# build-fabric.ps1 -- ASR Fabric cog cells. cog-gen -> gradlew clean build -> copy jar to dist/.
# Pre-26 cells build from their own gradle.properties; the 26 cell is parameterized per 26.x version.
# Usage: pwsh scripts/build-fabric.ps1 [-Only 1.21.8,1.20.1] [-M26 26.1,26.2,26.3]
param([string[]]$Only, [string[]]$M26)
$ErrorActionPreference = 'Stop'
$repo   = Split-Path $PSScriptRoot -Parent
$root   = Join-Path $repo 'Fabric'
$dist   = Join-Path $repo 'dist'
$cogGen = Join-Path $PSScriptRoot 'cog-gen.ps1'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$env:JAVA_HOME = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot'

$m26 = [ordered]@{
  '26.1' = @{ mc='26.1.2'; api='0.145.3+26.1.1'; loader='0.18.6'; lo='26.1-'; hi='26.2';         modmenu='17.0.0-beta.1' }
  '26.2' = @{ mc='26.2';   api='0.152.1+26.2';   loader='0.19.3'; lo='26.2-'; hi='26.3';         modmenu='18.0.0-beta.1' }
  '26.3' = @{ mc='26.3-snapshot-5'; api='0.155.3+26.3'; loader='0.19.3'; lo='26.3-alpha.5'; hi='26.3-alpha.6'; modmenu='18.0.0-beta.1' }
}

function Copy-Jar($cell, $label) {
  $jar = Get-ChildItem (Join-Path $cell 'build\libs') -Filter 'autoshield-reborn-*.jar' -EA SilentlyContinue |
         Where-Object { $_.Name -notmatch 'sources|dev|slim' } | Sort-Object LastWriteTime | Select-Object -Last 1
  if (-not $jar) { throw "No jar for Fabric/$label" }
  Copy-Item $jar.FullName (Join-Path $dist $jar.Name) -Force
  Write-Host "  -> dist $($jar.Name)"
}

function Build-Pre($v) {
  $cell = Join-Path $root $v
  if (-not (Test-Path $cell)) { throw "no cell Fabric/$v" }
  Write-Host "=== ASR Fabric/$v (pre-26) ==="
  & $cogGen -Cell "Fabric/$v" -McVer $v -Loader Fabric
  if ($LASTEXITCODE -ne 0) { throw "cog-gen FAILED $v" }
  Push-Location $cell
  & .\gradlew.bat clean build --no-daemon
  $rc = $LASTEXITCODE; Pop-Location
  if ($rc -ne 0) { throw "build FAILED $v" }
  Copy-Jar $cell $v
}

function Build-26($v) {
  $cell = Join-Path $root '26'; $m = $m26[$v]
  Write-Host "=== ASR Fabric/26 -> $v (mc=$($m.mc)) ==="
  & $cogGen -Cell 'Fabric/26' -McVer $m.mc -Loader Fabric
  if ($LASTEXITCODE -ne 0) { throw "cog-gen FAILED 26/$v" }
  Push-Location $cell
  & .\gradlew.bat clean build "-Pmod_version=1.1.0+$v" "-Pminecraft_version=$($m.mc)" "-Pfabric_api_version=$($m.api)" "-Ploader_version=$($m.loader)" "-Pminecraft_range=>=$($m.lo) <$($m.hi)" "-Pmodmenu_version=$($m.modmenu)" --no-daemon
  $rc = $LASTEXITCODE; Pop-Location
  if ($rc -ne 0) { throw "build FAILED 26/$v" }
  Copy-Jar $cell $v
}

$pre = @(Get-ChildItem $root -Directory -EA SilentlyContinue | Where-Object { $_.Name -ne '26' } | Select-Object -ExpandProperty Name | Sort-Object)
if ($Only)  { foreach ($v in $Only) { Build-Pre $v } }
elseif ($M26) { foreach ($v in $M26) { Build-26 $v } }
else { foreach ($v in $pre) { Build-Pre $v }; foreach ($v in $m26.Keys) { Build-26 $v } }
Write-Host 'Fabric builds complete.'
