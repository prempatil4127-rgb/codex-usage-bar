---
name: usage-bar
description: Enable, disable, or check the installed Codex Usage Bar companion on Windows.
---

Resolve the installed companion and run its PowerShell control:

```powershell
$usageHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
& (Join-Path $usageHome 'token-monitor\control.ps1') -Action status
```

Use `on` to launch the bar and enable Windows startup, `off` to stop it and
disable startup, and `status` to inspect it without changing anything. An
invocation without an action means `status`. Report the returned `running`
and `startupEnabled` values; surface errors rather than claiming success.

This controls a companion overlay, not Codex's native Settings or prompt bar.
It appears only while Codex is foregrounded. Tokens follow the latest active
local session; quotas are recorded account-wide 5-hour and weekly usage.
There is no daily percentage. If the script is missing, report that the
companion needs installation; the skill alone does not install it.
