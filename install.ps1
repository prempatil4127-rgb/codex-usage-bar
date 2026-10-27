param([string]$PythonExe, [switch]$NoStart, [switch]$NoStartup)
$ErrorActionPreference = 'Stop'
if (!$PythonExe) {
    if (Get-Command py -ErrorAction SilentlyContinue) { $PythonExe = (& py -3 -c 'import sys; print(sys.executable)') }
    elseif (Get-Command python -ErrorAction SilentlyContinue) { $PythonExe = (& python -c 'import sys; print(sys.executable)') }
}
if (!$PythonExe -or !(Test-Path -LiteralPath $PythonExe)) { throw 'Install Python 3.10+ (64-bit, with Tcl/Tk), or pass -PythonExe C:\path\python.exe.' }
& $PythonExe -c 'import sys, tkinter, struct; assert sys.version_info >= (3,10); assert struct.calcsize("P") == 8; assert sys.platform == "win32"'
if ($LASTEXITCODE -ne 0) { throw 'Python must be Windows 64-bit version 3.10+ with tkinter.' }
$pythonw = Join-Path (Split-Path $PythonExe) 'pythonw.exe'
if (!(Test-Path -LiteralPath $pythonw)) { throw 'pythonw.exe is missing from this Python installation.' }
$usageHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$destination = Join-Path $usageHome 'token-monitor'
if ([IO.Path]::GetFullPath($destination) -eq [IO.Path]::GetFullPath($PSScriptRoot)) { throw 'Run install.ps1 from the downloaded source folder, not the installation folder.' }
$files = @('monitor.py','windows_host.py','control.ps1','uninstall.ps1','README.md')
foreach ($file in $files) { if (!(Test-Path -LiteralPath (Join-Path $PSScriptRoot $file))) { throw "Missing package file: $file" } }
if (Test-Path -LiteralPath (Join-Path $destination 'control.ps1')) { & (Join-Path $destination 'control.ps1') -Action off | Out-Null }
New-Item -ItemType Directory -Force -Path $destination | Out-Null
foreach ($file in $files) { Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination $destination -Force }
@{ pythonw = $pythonw; codexHome = [IO.Path]::GetFullPath($usageHome) } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $destination 'runtime.json') -Encoding UTF8
$skillPath = Join-Path $usageHome 'skills\usage-bar'
New-Item -ItemType Directory -Force -Path (Join-Path $skillPath 'agents') | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'skills\usage-bar\SKILL.md') -Destination $skillPath -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'skills\usage-bar\agents\openai.yaml') -Destination (Join-Path $skillPath 'agents') -Force
& (Join-Path $destination 'control.ps1') -Action on -NoStart:$NoStart -NoStartup:$NoStartup
Write-Output "Installed in $destination. Agent command: `$usage-bar status"
