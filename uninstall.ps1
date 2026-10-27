$ErrorActionPreference = 'Stop'
$config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime.json') -Raw | ConvertFrom-Json
$expected = [IO.Path]::GetFullPath((Join-Path $config.codexHome 'token-monitor'))
if ([IO.Path]::GetFullPath($PSScriptRoot) -ne $expected) { throw 'Run uninstall.ps1 from the installed token-monitor folder.' }
& (Join-Path $PSScriptRoot 'control.ps1') -Action off | Out-Null
$skill = Join-Path $config.codexHome 'skills\usage-bar'
foreach ($file in @('SKILL.md','agents\openai.yaml')) {
    $target = Join-Path $skill $file
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target }
}
foreach ($file in @('monitor.py','windows_host.py','control.ps1','README.md','runtime.json','position.json','uninstall.ps1')) {
    $target = Join-Path $PSScriptRoot $file
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target }
}
Write-Output 'Uninstalled the bar and agent skill. Codex sessions and unrelated files were preserved. Empty folders/cache files may remain.'
