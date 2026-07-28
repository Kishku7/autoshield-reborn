# build-neoforge.ps1 -- Auto-Shield Reborn NeoForge 26-line builds (cog-gen -> gradle -> dist).
# Usage: pwsh -File scripts\build-neoforge.ps1 [26.1 26.2]   (no args = every 26.X target)
#
# The NeoForge/26 cell is PARAMETERIZED: one cell builds both 26.1 and 26.2 via -P overrides, exactly
# like the other mods' 26 cells. A bare `gradlew build` uses only the checked-in gradle.properties
# defaults AND a stale gen/ tree (gen/ is gitignored and produced by cog-gen) -- so ALWAYS build
# through this script. Pin doctrine + the do-not-normalize rule for neoRange: Memory/minecraft/version-gates.md.
param([Parameter(ValueFromRemainingArguments)][string[]]$Only)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$dist = Join-Path $repoRoot 'dist'
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$prog = Join-Path $PSScriptRoot '_build-neoforge-progress.txt'
Remove-Item $prog -ErrorAction SilentlyContinue

# 26-line matrix. pf column intentionally absent: ASR ships no pack.mcmeta in any cell.
$matrix26 = [ordered]@{
    '26.1' = @{ mc='26.1.2'; neo='26.1.2.87';      mcRange='[26.1,26.2)'; neoRange='[26.1.0-alpha,)' }
    '26.2' = @{ mc='26.2';   neo='26.2.0.35-beta'; mcRange='[26.2,26.3)'; neoRange='[26.2.0-alpha,)' }
}
$keys26 = if ($Only) { @($matrix26.Keys) | Where-Object { $Only -contains $_ } } else { @($matrix26.Keys) }
if (-not $keys26) { throw "no matching 26.X target in: $($Only -join ', ')" }

$cell26 = Join-Path $repoRoot 'NeoForge\26'
foreach ($v in $keys26) {
    $m = $matrix26[$v]
    Add-Content $prog "=== $v START $(Get-Date -Format HH:mm:ss) (mc=$($m.mc), neo=$($m.neo)) ==="

    & pwsh -NoProfile -File (Join-Path $PSScriptRoot 'cog-gen.ps1') `
        -Cell 'NeoForge/26' -McVer $m.mc -Loader NeoForge *>> $prog
    if ($LASTEXITCODE -ne 0) { Add-Content $prog "$v COG-FAIL"; continue }

    Push-Location $cell26
    Get-ChildItem "$cell26\build\libs\*.jar" -ErrorAction SilentlyContinue | Remove-Item -Force
    & "$cell26\gradlew.bat" clean build "-Pminecraft_version=$($m.mc)" "-Pneo_version=$($m.neo)" `
        "-Pmc_range=$($m.mcRange)" "-Pneoforge_range=$($m.neoRange)" `
        --console=plain *> "$cell26\_build_$v.log"
    $code = $LASTEXITCODE
    Pop-Location

    $jar = Get-ChildItem "$cell26\build\libs" -Filter 'autoshield-reborn-*.jar' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch 'sources|dev' } | Sort-Object LastWriteTime | Select-Object -Last 1
    $warn = (Select-String -Path "$cell26\_build_$v.log" -Pattern '\.java.*warning' -ErrorAction SilentlyContinue | Measure-Object).Count
    if ($code -eq 0 -and $jar) {
        Copy-Item $jar.FullName (Join-Path $dist $jar.Name) -Force
        Add-Content $prog "$v OK -> $($jar.Name) (javac warnings: $warn)"
    } else {
        Add-Content $prog "$v FAIL exit=$code (see NeoForge\26\_build_$v.log)"
    }
}
Add-Content $prog "ALLDONE $(Get-Date -Format HH:mm:ss)"
Get-Content $prog
