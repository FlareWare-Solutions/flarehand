: << 'CMDBLOCK'
@echo off
REM flarehand hook launcher. One file, two languages.
REM cmd.exe runs this batch part. A POSIX shell skips it (the first line opens a heredoc that
REM ends at CMDBLOCK) and runs the part below. Either way it starts hooks\hook.py with Python,
REM passes the hook's standard input through, and exits 0 when Python or hook.py is missing,
REM so a hook can never block the agent.
REM Usage: run-hook.cmd <action>   action is session-start, prompt-submit, stop, pre-compact or session-end
setlocal
set "HOOK_DIR=%~dp0"
if not exist "%HOOK_DIR%hook.py" exit /b 0
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    py -3 "%HOOK_DIR%hook.py" %*
    exit /b 0
)
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python "%HOOK_DIR%hook.py" %*
    exit /b 0
)
exit /b 0
CMDBLOCK

# POSIX shell from here. Run it as `sh run-hook.cmd <action>`, so no executable bit is needed.
dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd) || exit 0
[ -f "$dir/hook.py" ] || exit 0
# Probe each candidate, because on Windows `python3` can be a store stub that only prints a hint.
for py in python3 python; do
    if command -v "$py" >/dev/null 2>&1 &&
        "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' </dev/null >/dev/null 2>&1; then
        exec "$py" "$dir/hook.py" "$@"
    fi
done
if command -v py >/dev/null 2>&1; then
    py -3 "$dir/hook.py" "$@"
fi
exit 0
