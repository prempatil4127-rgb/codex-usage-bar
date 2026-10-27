param([ValidateSet('on','off','status')][string]$Action = 'status', [switch]$NoStart, [switch]$NoStartup)
$ErrorActionPreference = 'Stop'
$meterScript = Join-Path $PSScriptRoot 'monitor.py'
$config = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'runtime.json') -Raw | ConvertFrom-Json
$meterPython = $config.pythonw
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'Codex Usage Companion.lnk'
function Get-MeterProcess {
    Get-CimInstance Win32_Process -Filter "Name = 'pythonw.exe'" | Where-Object {
        $_.ExecutablePath -eq $meterPython -and $_.CommandLine -match ([regex]::Escape($meterScript) + '("|\s|$)')
    }
}
if ($Action -eq 'on') {
    if (!(Test-Path -LiteralPath $meterPython)) { throw 'Python runtime moved or was removed. Run the installer again.' }
    if (!$NoStartup) {
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $meterPython
        $shortcut.Arguments = '"' + $meterScript + '"'
        $shortcut.WorkingDirectory = $PSScriptRoot
        $shortcut.Description = 'Codex Usage Bar'
        $shortcut.Save()
    }
    if (!$NoStart -and !(Get-MeterProcess)) {
        $started = Start-Process -FilePath $meterPython -ArgumentList ('"' + $meterScript + '"') -WindowStyle Hidden -PassThru
        if ($started.WaitForExit(1000)) { throw "Usage bar exited during startup: $($started.ExitCode)" }
    }
} elseif ($Action -eq 'off') {
    if (Test-Path -LiteralPath $shortcutPath) {
        $shell = New-Object -ComObject WScript.Shell
        if ($shell.CreateShortcut($shortcutPath).Arguments -eq ('"' + $meterScript + '"')) { Remove-Item -LiteralPath $shortcutPath }
    }
    Get-MeterProcess | ForEach-Object { Stop-Process -Id $_.ProcessId }
}
$processes = @(Get-MeterProcess)
$enabled = $false
if (Test-Path -LiteralPath $shortcutPath) {
    $shell = New-Object -ComObject WScript.Shell
    $enabled = $shell.CreateShortcut($shortcutPath).Arguments -eq ('"' + $meterScript + '"')
}
[pscustomobject]@{ startupEnabled = $enabled; running = $processes.Count -gt 0; instances = $processes.Count } | ConvertTo-Json
