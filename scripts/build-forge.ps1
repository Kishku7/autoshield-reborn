# build-forge.ps1 -- Auto-Shield Reborn: every Forge cell (cog-gen -> gradlew clean build -> dist).
#
# ASR was the only mod without a canonical Forge build script: its Forge cells had to be driven
# cell-by-cell through their own gradlew, which is exactly the "shooting from the hip" the build
# rules forbid. This is the peer of build-fabric.ps1 / build-neoforge.ps1.
#
# Usage: pwsh -File scripts\build-forge.ps1                 # every Forge cell
#        pwsh -File scripts\build-forge.ps1 -Only 1.21.8    # one or more cells
#
# JDK per MC line: 1.20.1/1.20.4 -> 17, everything else -> 21 (no Forge on 26.x; FG6 cannot build it).
param([string[]]$Only)
$ErrorActionPreference = 'Stop'
$repo   = Split-Path $PSScriptRoot -Parent
$root   = Join-Path $repo 'Forge'
$dist   = Join-Path $repo 'dist'
$cogGen = Join-Path $PSScriptRoot 'cog-gen.ps1'
New-Item -ItemType Directory -Force -Path $dist | Out-Null

$JDK17 = 'C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot'
$JDK21 = 'C:\Program Files\Eclipse Adoptium\jdk-21.0.9.10-hotspot'

function Jdk-For($v) {
    $p = $v.Split('.')
    if ($p[0] -eq '1' -and [int]$p[1] -eq 20 -and [int]($p[2] ?? 0) -le 4) { return $JDK17 }
    return $JDK21
}

$prog = Join-Path $PSScriptRoot '_build-forge-progress.txt'
Remove-Item $prog -ErrorAction SilentlyContinue

$cells = @(Get-ChildItem $root -Directory -EA SilentlyContinue | Select-Object -ExpandProperty Name | Sort-Object)
if ($Only) { $cells = $cells | Where-Object { $Only -contains $_ } }
if (-not $cells) { throw "no matching Forge cell in: $($Only -join ', ')" }

$failed = @()
foreach ($v in $cells) {
    $cell = Join-Path $root $v
    Add-Content $prog "=== $v START $(Get-Date -Format HH:mm:ss) ==="
    Write-Host "=== ASR Forge/$v ==="

    & pwsh -NoProfile -File $cogGen -Cell "Forge/$v" -McVer $v -Loader Forge *>> $prog
    if ($LASTEXITCODE -ne 0) { Add-Content $prog "$v COG-FAIL"; $failed += $v; continue }

    $prevJavaHome = $env:JAVA_HOME
    $env:JAVA_HOME = Jdk-For $v
    Push-Location $cell
    Get-ChildItem "$cell\build\libs\*.jar" -ErrorAction SilentlyContinue | Remove-Item -Force
    & "$cell\gradlew.bat" clean build --console=plain --no-daemon *> "$cell\_build_$v.log"
    $code = $LASTEXITCODE
    Pop-Location
    $env:JAVA_HOME = $prevJavaHome

    if ($code -ne 0) {
        Add-Content $prog "$v BUILD-FAIL (see $cell\_build_$v.log)"
        $failed += $v
        continue
    }

    $jar = Get-ChildItem "$cell\build\libs" -Filter 'autoshield-reborn-*.jar' -EA SilentlyContinue |
        Where-Object { $_.Name -notmatch 'sources|dev|slim' } | Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $jar) { Add-Content $prog "$v NO-JAR"; $failed += $v; continue }
    Copy-Item $jar.FullName (Join-Path $dist $jar.Name) -Force
    $warn = (Select-String -Path "$cell\_build_$v.log" -Pattern 'warning:' -EA SilentlyContinue | Measure-Object).Count
    Add-Content $prog "$v OK -> $($jar.Name) (javac warnings: $warn)"
    Write-Host "  -> dist $($jar.Name)"
}

Add-Content $prog "ALLDONE $(Get-Date -Format HH:mm:ss)"
if ($failed) { throw "Forge build FAILED for: $($failed -join ', ')" }
Write-Host 'Forge builds complete.'
