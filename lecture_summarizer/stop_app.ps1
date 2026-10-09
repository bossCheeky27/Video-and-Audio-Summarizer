# Stops the Lecture Summarizer Flask app listening on port 5000.
# Flask debug mode runs a reloader parent + a server child, so the whole tree is killed.
param([int]$Port = 5000)
$port = $Port

$conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if (-not $conns) {
    Write-Host "Lecture Summarizer is not running (nothing listening on port $port)."
    exit 0
}

foreach ($procId in ($conns.OwningProcess | Sort-Object -Unique)) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$procId"
    if (-not $proc -or $proc.CommandLine -notmatch 'app\.py') {
        Write-Host "Port $port is used by PID $procId ($($proc.Name)), which is not the Lecture Summarizer. Leaving it alone."
        continue
    }

    # Kill from the reloader parent if there is one, so it can't respawn the server
    $target = $proc
    $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.ParentProcessId)"
    if ($parent -and $parent.CommandLine -match 'app\.py') { $target = $parent }

    Write-Host "Stopping Lecture Summarizer (PID $($target.ProcessId))..."
    taskkill /PID $target.ProcessId /T /F | Out-Null
}

Write-Host "Done."
