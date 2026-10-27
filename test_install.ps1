param([Parameter(Mandatory=$true)][string]$PythonExe)
$ErrorActionPreference = 'Stop'
$testRoot = Join-Path ([IO.Path]::GetTempPath()) ('codex-usage-test-' + [guid]::NewGuid())
$previousHome = $env:CODEX_HOME
try {
    $env:CODEX_HOME = $testRoot
    & (Join-Path $PSScriptRoot 'install.ps1') -PythonExe $PythonExe -NoStart -NoStartup | Out-Null
    $control = Join-Path $testRoot 'token-monitor\control.ps1'
    $status = & $control -Action status | ConvertFrom-Json
    if ($status.running -or $status.startupEnabled) { throw 'Opt-out switches failed.' }
    if (!(Test-Path -LiteralPath (Join-Path $testRoot 'skills\usage-bar\SKILL.md'))) { throw 'Agent skill missing.' }
    & (Join-Path $PSScriptRoot 'install.ps1') -PythonExe $PythonExe -NoStart -NoStartup | Out-Null
    Set-Content -LiteralPath (Join-Path $testRoot 'token-monitor\keep-me.txt') -Value 'unrelated'
    & (Join-Path $testRoot 'token-monitor\uninstall.ps1') | Out-Null
    if (Test-Path -LiteralPath $control) { throw 'Uninstall left program files.' }
    if (!(Test-Path -LiteralPath (Join-Path $testRoot 'token-monitor\keep-me.txt'))) { throw 'Uninstall removed unrelated data.' }
    'PASS: install, opt-out switches, skill installation, update, uninstall, preservation'
} finally {
    $env:CODEX_HOME = $previousHome
    $resolved = [IO.Path]::GetFullPath($testRoot)
    $tempPrefix = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if (!$resolved.StartsWith($tempPrefix, [StringComparison]::OrdinalIgnoreCase) -or !(Split-Path $resolved -Leaf).StartsWith('codex-usage-test-')) { throw 'Unsafe cleanup path.' }
    if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
