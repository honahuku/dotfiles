$ErrorActionPreference = 'Stop'
$source = Join-Path (Split-Path -Parent $PSScriptRoot) '.agents\AGENTS.md'
$codexRoot = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$destination = Join-Path $codexRoot 'AGENTS.md'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "Missing source: $source" }
New-Item -ItemType Directory -Path $codexRoot -Force | Out-Null
$existing = Get-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
if ($existing -and $existing.LinkType -eq 'SymbolicLink' -and $existing.Target -eq $source) {
    Write-Output "Already linked: $destination"
    return
}
$backup = $null
if ($existing) {
    $backup = "$destination.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    while (Test-Path -LiteralPath $backup) { $backup += '.bak' }
    Move-Item -LiteralPath $destination -Destination $backup
}
try {
    New-Item -ItemType SymbolicLink -Path $destination -Target $source | Out-Null
} catch {
    if ($backup) { Move-Item -LiteralPath $backup -Destination $destination }
    throw
}
Write-Output "Linked: $destination -> $source"
if ($backup) { Write-Output "Backup: $backup" }
