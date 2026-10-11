param(
    [ValidateSet('Stable', 'Preview', 'Canary', 'Unpackaged')]
    [string]$Distribution = 'Stable'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$source = Join-Path $PSScriptRoot 'terminal\settings.json'
if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Missing source: $source"
}
$source = (Resolve-Path -LiteralPath $source).Path

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw 'LOCALAPPDATA is not set'
}

$destination = switch ($Distribution) {
    'Stable' {
        Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json'
    }
    'Preview' {
        Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalPreview_8wekyb3d8bbwe\LocalState\settings.json'
    }
    'Canary' {
        Join-Path $env:LOCALAPPDATA 'Packages\Microsoft.WindowsTerminalCanary_8wekyb3d8bbwe\LocalState\settings.json'
    }
    'Unpackaged' {
        Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json'
    }
}

$destinationParent = Split-Path -Parent $destination
New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null

$existing = Get-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
if ($existing -and $existing.LinkType -eq 'SymbolicLink' -and $existing.Target -eq $source) {
    Write-Output "Already linked: $destination"
    return
}

$backup = $null
if ($existing) {
    $backup = "$destination.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    while (Test-Path -LiteralPath $backup) {
        $backup += '.bak'
    }
    Move-Item -LiteralPath $destination -Destination $backup
}

try {
    New-Item -ItemType SymbolicLink -Path $destination -Target $source | Out-Null
} catch {
    if ($backup) {
        Move-Item -LiteralPath $backup -Destination $destination
    }
    throw
}

Write-Output "Linked: $destination -> $source"
if ($backup) {
    Write-Output "Backup: $backup"
}
