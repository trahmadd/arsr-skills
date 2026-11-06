# Run a JSX file in the installed InDesign through COM (Windows PowerShell). No pip, no manual double-click.
#   powershell -ExecutionPolicy Bypass -File tools\indesign_run.ps1 <project>\build\run_build.jsx
#   powershell -ExecutionPolicy Bypass -File tools\indesign_run.ps1 <project>\build\run_qa.jsx
# Starts InDesign if it is not running. The call returns when the script ends. Results are in <project>\logs\.
param([Parameter(Mandatory=$true)][string]$Script)
$ErrorActionPreference = 'Stop'
$path = (Resolve-Path -LiteralPath $Script).Path
$JS = 1246973031        # ScriptLanguage.JAVASCRIPT
$NEVER = 1699640946     # UserInteractionLevels.NEVER_INTERACT (no dialog can block the run)
try {
    $app = New-Object -ComObject InDesign.Application
} catch {
    Write-Output "ERROR: cannot start InDesign through COM ($($_.Exception.Message)). Run the .jsx from the Scripts panel instead."
    exit 2
}
$old = $app.ScriptPreferences.UserInteractionLevel
try {
    $app.ScriptPreferences.UserInteractionLevel = $NEVER
    [void]$app.DoScript($path, $JS)
    Write-Output "OK: ran $path. Read the logs folder of the project."
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
    exit 1
} finally {
    try { $app.ScriptPreferences.UserInteractionLevel = $old } catch {}
}
