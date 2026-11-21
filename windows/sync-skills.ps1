$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$lockPath = Join-Path $repoRoot 'vendir.lock.yml'
$tempLockPath = Join-Path ([IO.Path]::GetTempPath()) ('vendir-windows-' + [guid]::NewGuid().ToString('N') + '.lock.yml')

try {
    $lockContent = Get-Content -LiteralPath $lockPath -Raw
    $windowsLockContent = [regex]::Replace(
        $lockContent,
        '(?m)^(?<indent>[ \t]*path:[ \t]*)(?<path>\.agents/[^\r\n]+)',
        {
            param($match)
            $match.Groups['indent'].Value + ($match.Groups['path'].Value -replace '/', '\')
        }
    )

    if ($windowsLockContent -eq $lockContent) {
        throw "No Windows vendir directory paths were converted in '$lockPath'."
    }

    Set-Content -LiteralPath $tempLockPath -Value $windowsLockContent -Encoding utf8NoBOM
    & aqua -c (Join-Path $repoRoot 'aqua.yaml') exec -- vendir sync --locked --lock-file $tempLockPath
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}
finally {
    if (Test-Path -LiteralPath $tempLockPath) {
        Remove-Item -LiteralPath $tempLockPath
    }
}
