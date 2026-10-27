# Codex Usage Bar

A small, quiet Windows companion for the Codex desktop app. See recorded token
usage and account quota percentages without opening a dashboard.

```text
  [sprout]  1.24M          5-hour  29%       Weekly  15%
            latest chat   ━━━───────        ━─────────
```

The preview above uses example numbers. This is an independent community tool,
not an OpenAI product or a native prompt-bar extension.

## What it does

- Compact 362 × 44 logical-pixel bar with muted green accents.
- Follows the Codex window; hides when Codex is closed, minimized or inactive.
- Shows the latest active local chat's cumulative tokens and recorded account
  quota percentages. Hover for input/output totals, cached input and update time.
- Drag to move it; the relative position is saved. Right-click to quit.
- Starts at Windows sign-in and waits quietly for Codex to become active.
- Includes `$usage-bar on`, `$usage-bar off`, and `$usage-bar status` agent controls.
- Uses only Python's standard library and Windows APIs. No pip packages, API key,
  telemetry, remote server, or administrator access required.

## Requirements

- Windows 10/11, 64-bit. Developed and manually checked on Windows 11.
- Microsoft Store Codex desktop installation (`OpenAI.Codex_*` package).
  Other distribution paths, macOS, Linux and the terminal-only CLI are unsupported.
- Python **3.10 or newer**, 64-bit, with **Tcl/Tk and IDLE** enabled in the installer.
  Get Python from [python.org](https://www.python.org/downloads/windows/).
- Local Codex session logs under `%USERPROFILE%\.codex\sessions`, or `CODEX_HOME`.

## Easy installation

1. [Download the source ZIP](https://github.com/prempatil4127-rgb/codex-usage-bar/archive/refs/heads/main.zip)
   and extract it.
2. Open PowerShell in the extracted `codex-usage-bar-main` folder.
3. Run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

The execution-policy option applies only to this command. The installer does not
change your permanent PowerShell policy or download any dependencies. Inspect the
scripts before running them. The same command works after cloning with Git:

```powershell
git clone https://github.com/prempatil4127-rgb/codex-usage-bar.git
cd codex-usage-bar
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

Python not detected? Supply the path explicitly:

```powershell
.\install.ps1 -PythonExe 'C:\path\to\python.exe'
```

For installation without launching the bar or enabling startup:

```powershell
.\install.ps1 -NoStart -NoStartup
```

The installer copies the program to `<CODEX_HOME>\token-monitor` (default
`%USERPROFILE%\.codex\token-monitor`), installs the `usage-bar` skill, and creates
`Codex Usage Companion.lnk` in your Windows Startup folder. It replaces an older
installation's program files while retaining the saved bar position. No Codex
application files or session logs are modified.

## Controls

In a Codex chat, invoke `$usage-bar on`, `$usage-bar off`, or `$usage-bar status`.
If the skill does not appear immediately, start a new chat or restart Codex.
The skill is optional for operation; these commands also work directly:

```powershell
$usageHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
& (Join-Path $usageHome 'token-monitor\control.ps1') -Action status
& (Join-Path $usageHome 'token-monitor\control.ps1') -Action on
& (Join-Path $usageHome 'token-monitor\control.ps1') -Action off
```

`on` launches the bar and enables startup. `off` stops it and disables startup.
Right-clicking quits only the current run; it does not disable startup.
Only one companion instance can run in a Windows session.

## What the numbers mean

| Display | Meaning |
| --- | --- |
| Tokens | Cumulative input + output reported for the most recently modified local chat log. Includes repeated and cached input. Not a billing estimate. |
| 5-hour / Weekly | Percentage **used**, as recorded in Codex's account quota event. Shared across chats. Window labels come from the event duration. |
| Dash | Quota unavailable or its reset time passed without a fresh event. |

Codex does not supply a daily quota percentage. This tool does not invent one.
Updates are event-based, not token-by-token streaming. The visible bar checks for
new data every two seconds and selects the latest local session every ten seconds.
It cannot identify the currently viewed chat reliably: another active chat or
agent can become the displayed source. Hover to see the source suffix and timestamp.
Recorded account usage can be stale until Codex writes a new event.

## Performance and privacy

The companion reads local JSONL files and foreground-window process metadata.
It makes **no network requests**, reads no authentication credentials, and sends
nothing to GitHub or OpenAI. The program can encounter conversation text while
reading the tail of a session file, but only usage metadata is parsed/displayed.

Unchanged logs are not reread, unchanged values are not repainted, and stationary
windows are not repositioned. Log reads pause while the bar is hidden or dragged.
Dragging responds to mouse events. Foreground checks run every 100 ms while
Codex is active, or every 500 ms otherwise. No animations or AI polling jobs run.
Actual CPU/memory use depends on your machine; there is no universal zero-CPU claim.

## Troubleshooting

- **No bar:** bring the Store version of Codex to the foreground and check `status`.
  Confirm Python includes Tk. A second instance exits immediately by design.
- **No usage yet:** send a normal message in a local Codex chat. Cloud-only sessions
  or installations without local usage events may not provide usable data.
- **Old percentages:** hover to check the last recorded timestamp. The bar cannot
  refresh account quotas independently of Codex.
- **Overlap with your controls:** drag the bar to another place within the Codex
  window. Its location follows the window edge, not the prompt's internal layout.
- **Startup fails after moving Python:** rerun the installer with `-PythonExe`.
- **Need a visible traceback:** run `python monitor.py` from the installed folder.

## Update and uninstall

Download a fresh ZIP (or `git pull`) and rerun `install.ps1` to update.
To remove the installed program and skill:

```powershell
$usageHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
& (Join-Path $usageHome 'token-monitor\uninstall.ps1')
```

The uninstaller stops the bar, removes its own startup shortcut and named program/
skill files. Codex chats and unrelated files are preserved. Empty directories or
Python cache files may remain. Delete your downloaded source folder separately.

## Development

```powershell
python -m unittest discover -v
python monitor.py
```

`monitor.py` handles parsing and Tk UI; `windows_host.py` reads foreground metadata
and moves only the companion window. `install.ps1`, `control.ps1` and
`uninstall.ps1` manage the per-user installation. Tests cover partial log writes,
quota reset handling, positioning, application detection, latest-session selection
and avoiding redundant window calls. Windows CI runs Python tests and PowerShell
syntax checks. It does not replace manual UI, startup, or multi-monitor testing.

Session JSONL is an internal format and may change with Codex updates. The reader
scans at most the last 2 MB of a file; an unusually large trailing event can hide
the last usage record. Please report reproducible issues with Windows/Python/Codex
versions and sanitized error messages, **not raw chat logs or credentials**.

## License

[MIT](LICENSE). Contributions and focused bug reports are welcome.
