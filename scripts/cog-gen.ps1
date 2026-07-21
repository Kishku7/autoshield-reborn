<#
.SYNOPSIS  Auto-Shield Reborn Cog code-generation for one (loader, MC-version) cell.
.DESCRIPTION
  Materialises <Cell>/gen/ from _codegen/cog_sources with all version+loader drift resolved by Cog
  (_codegen/compat.py). Loader-aware file placement; presence-gates the payload API + ClientNet out of
  1.20.1; regenerates autoshield_reborn.mixins.json (compatibilityLevel + Forge refmap). The cell's
  build.gradle srcDirs gen/src/main/{java,resources}.
.EXAMPLE  ./cog-gen.ps1 -Cell Fabric/1.21.8 -McVer 1.21.8 -Loader Fabric
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Cell,
    [Parameter(Mandatory = $true)][string]$McVer,
    [Parameter(Mandatory = $true)][ValidateSet('Fabric','NeoForge','Forge')][string]$Loader
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$codegen  = Join-Path $repoRoot '_codegen'
$cog      = Join-Path $codegen 'cog_sources'
$cellPath = if ([System.IO.Path]::IsPathRooted($Cell)) { $Cell } else { Join-Path $repoRoot $Cell }
if (-not (Test-Path $cellPath)) { throw "Cell not found: $cellPath" }
$gen      = Join-Path $cellPath 'gen'
$genJava  = Join-Path $gen 'src/main/java'
$genRes   = Join-Path $gen 'src/main/resources'
$pkg      = 'com/kishku7/autoshieldreborn'

Push-Location $codegen
try {
    $env:PYTHONPATH = $codegen
    $hasPayload  = (& python -c "import compat,sys;sys.stdout.write('1' if compat.has_payload_api('$McVer') else '0')")
    $compatLevel = (& python -c "import compat,sys;sys.stdout.write(compat.compat_level('$McVer'))")
    $forgeRefmap = (& python -c "import compat,sys;sys.stdout.write('1' if compat.forge_needs_refmap('$McVer') else '0')")
    if ($Loader -eq 'Forge') {
        $forgeOldMixin = (& python -c "import compat,sys;sys.stdout.write('1' if compat._parse('$McVer') < (1,21,0) else '0')")
        if ($forgeOldMixin -eq '1') { $compatLevel = 'JAVA_17' }   # classic Forge (<=1.20.x, Forge 50) bundles an old Mixin that rejects JAVA_21
        $dataFormat = (& python -c "import compat,sys;sys.stdout.write(str(compat.datapack_format('$McVer')))")
    }
} finally { Pop-Location }

Write-Host "[cog-gen] cell=$Cell mcver=$McVer loader=$Loader payload=$hasPayload compat=$compatLevel"

if (Test-Path $gen) { Remove-Item -Recurse -Force $gen }
New-Item -ItemType Directory -Force -Path $genJava | Out-Null
New-Item -ItemType Directory -Force -Path $genRes  | Out-Null

# shared invariants (ASRConfig + icon resources)
Copy-Item -Recurse -Force (Join-Path $cog 'shared/src/main/java/*') $genJava
if (Test-Path (Join-Path $cog 'shared/src/main/resources')) {
    Copy-Item -Recurse -Force (Join-Path $cog 'shared/src/main/resources/*') $genRes
}

function Place([string]$srcRel, [string]$dstRel) {
    $src = Join-Path $cog $srcRel
    $dst = Join-Path $genJava $dstRel
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    Copy-Item -Force $src $dst
    $dst
}

$cogTargets = @()
# loader-neutral cog files (present on every cell)
$cogTargets += Place 'mixin/AutoShieldMixin.java'      "$pkg/mixin/AutoShieldMixin.java"
$cogTargets += Place 'client/ASRConfigScreen.java'     "$pkg/client/ASRConfigScreen.java"
# payload API + ClientNet facade: payload era only (>=1.20.5)
if ($hasPayload -eq '1') {
    $cogTargets += Place 'net/SetDurabilityPayload.java'  "$pkg/net/SetDurabilityPayload.java"
    $cogTargets += Place 'net/SyncDurabilityPayload.java' "$pkg/net/SyncDurabilityPayload.java"
    Place 'client/ClientNet.java' "$pkg/client/ClientNet.java" | Out-Null
}
# loader-specific entry + client + manifest
if ($Loader -eq 'Fabric') {
    $cogTargets += Place 'entrypoints/fabric/AutoShieldReborn.java'    "$pkg/AutoShieldReborn.java"
    $cogTargets += Place 'net/ASRNetworking.java'                     "$pkg/net/ASRNetworking.java"
    $cogTargets += Place 'client/fabric/AutoShieldRebornClient.java'   "$pkg/client/AutoShieldRebornClient.java"
    Place 'client/fabric/ASRModMenu.java' "$pkg/client/ASRModMenu.java" | Out-Null
    Copy-Item -Force (Join-Path $cog 'manifests/fabric/fabric.mod.json') (Join-Path $genRes 'fabric.mod.json')
}
elseif ($Loader -eq 'NeoForge') {
    $cogTargets += Place 'entrypoints/neoforge/AutoShieldReborn.java'  "$pkg/AutoShieldReborn.java"
    $cogTargets += Place 'entrypoints/neoforge/AutoShieldRebornNeoForge.java' "$pkg/AutoShieldRebornNeoForge.java"
    $cogTargets += Place 'client/neoforge/AutoShieldRebornNeoForgeClient.java' "$pkg/client/AutoShieldRebornNeoForgeClient.java"
    New-Item -ItemType Directory -Force -Path (Join-Path $genRes 'META-INF') | Out-Null
    Copy-Item -Force (Join-Path $cog 'manifests/neoforge/neoforge.mods.toml') (Join-Path $genRes 'META-INF/neoforge.mods.toml')
}
elseif ($Loader -eq 'Forge') {
    $cogTargets += Place 'entrypoints/forge/AutoShieldReborn.java'       "$pkg/AutoShieldReborn.java"
    $cogTargets += Place 'entrypoints/forge/AutoShieldRebornForge.java'  "$pkg/AutoShieldRebornForge.java"
    $cogTargets += Place 'net/ASRForgeNetworking.java'                   "$pkg/net/ASRForgeNetworking.java"
    $cogTargets += Place 'client/forge/AutoShieldRebornForgeClient.java' "$pkg/client/AutoShieldRebornForgeClient.java"
    New-Item -ItemType Directory -Force -Path (Join-Path $genRes 'META-INF') | Out-Null
    Copy-Item -Force (Join-Path $cog 'manifests/forge/mods.toml') (Join-Path $genRes 'META-INF/mods.toml')
}

# run Cog over the placed cog files
Push-Location $codegen
try {
    $env:PYTHONPATH = $codegen
    & cog -r -D "mcver=$McVer" -D "loader=$Loader" @cogTargets
    if ($LASTEXITCODE -ne 0) { throw "cog failed (exit $LASTEXITCODE)" }
} finally { Pop-Location }

# regenerate mixins.json
$refmapLine = ''
if ($Loader -eq 'Forge' -and $forgeRefmap -eq '1') {
    $refmapLine = "  `"refmap`": `"autoshield_reborn.refmap.json`",`n"
}
$json = @"
{
  "required": true,
  "minVersion": "0.8",
  "package": "com.kishku7.autoshieldreborn.mixin",
  "compatibilityLevel": "$compatLevel",
$refmapLine  "mixins": [
    "AutoShieldMixin"
  ],
  "injectors": {
    "defaultRequire": 1
  }
}
"@
$json = $json -replace "`r`n", "`n"
[System.IO.File]::WriteAllText((Join-Path $genRes 'autoshield_reborn.mixins.json'), $json, (New-Object System.Text.UTF8Encoding($false)))
# Forge 56+/58 requires the mod to ship a pack.mcmeta (else its datapack never loads ->
# LootModifierManager world-tick crash on 1.21.8). Emit one for Forge cells.
if ($Loader -eq 'Forge') {
    # >=1.21.9 rewrote pack.mcmeta: old "supported_formats" is rejected (declares support newer
    # than 81, missing min_format/max_format). datapack_format is <=81, so a bare pack_format loads
    # clean there; keep supported_formats only on the <1.21.9 range where it is accepted.
    $packModern = (& python -c "import compat,sys;sys.stdout.write('1' if compat._parse('$McVer') >= (1,21,9) else '0')")
    if ($packModern -eq '1') {
        $mcmeta = @'
{
  "pack": {
    "description": "Auto-Shield Reborn",
    "pack_format": __FMT__
  }
}
'@ -replace '__FMT__', $dataFormat
    } else {
        $mcmeta = @'
{
  "pack": {
    "description": "Auto-Shield Reborn",
    "pack_format": __FMT__,
    "supported_formats": { "min_inclusive": 1, "max_inclusive": 9999 }
  }
}
'@ -replace '__FMT__', $dataFormat
    }
    $mcmeta = $mcmeta -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText((Join-Path $genRes 'pack.mcmeta'), $mcmeta, (New-Object System.Text.UTF8Encoding($false)))
    Write-Host "[cog-gen] wrote pack.mcmeta (pack_format=$dataFormat)"
}
Write-Host "[cog-gen] done: $Cell (compat=$compatLevel)"
