$ErrorActionPreference = "Stop"
$scriptPath = "C:\Users\iwata\iCloudPhotos\Photos\fujisan_auto_post.py"
$patchPath = "C:\Users\iwata\Documents\GitHub\fujisanroku-rice\photo_selector_patch.py"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupPath = "$scriptPath.backup_$timestamp"
Copy-Item $scriptPath $backupPath -Force
Write-Host "OK backup: $backupPath" -ForegroundColor Green
$content = [System.IO.File]::ReadAllText($scriptPath, [System.Text.UTF8Encoding]::new($false))
Write-Host "OK read source: $($content.Length) chars" -ForegroundColor Green
$patchCode = [System.IO.File]::ReadAllText($patchPath, [System.Text.UTF8Encoding]::new($false))
Write-Host "OK read patch: $($patchCode.Length) chars" -ForegroundColor Green
$importMarker = "from pathlib import Path"
$newImports = "from pathlib import Path`r`nfrom astral import LocationInfo`r`nfrom astral.sun import sun`r`nimport pytz"
if ($content.Contains("from astral import LocationInfo")) {
    Write-Host "WARN astral import already exists" -ForegroundColor Yellow
} elseif ($content.Contains($importMarker)) {
    $content = $content.Replace($importMarker, $newImports)
    Write-Host "OK added astral, pytz imports" -ForegroundColor Green
} else {
    Write-Host "ERR import marker not found" -ForegroundColor Red
    exit 1
}
$pattern = "(?ms)^def find_todays_photo\(.*?(?=^def |^if __name__)"
if ($content -match $pattern) {
    $oldFunc = $matches[0]
    Write-Host "OK found existing find_todays_photo: $($oldFunc.Length) chars" -ForegroundColor Green
    $content = $content.Replace($oldFunc, $patchCode + "`r`n`r`n")
    Write-Host "OK replaced with patch code" -ForegroundColor Green
} else {
    Write-Host "ERR find_todays_photo not found" -ForegroundColor Red
    exit 1
}
[System.IO.File]::WriteAllText($scriptPath, $content, [System.Text.UTF8Encoding]::new($false))
Write-Host "OK wrote: $($content.Length) chars" -ForegroundColor Green
Write-Host ""
Write-Host "=== Python syntax check ===" -ForegroundColor Cyan
$pythonExe = "C:\Users\iwata\AppData\Local\Programs\Python\Python314\python.exe"
& $pythonExe -m py_compile $scriptPath
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK syntax check passed" -ForegroundColor Green
} else {
    Write-Host "ERR syntax error, restoring backup..." -ForegroundColor Red
    Copy-Item $backupPath $scriptPath -Force
    Write-Host "OK restored" -ForegroundColor Yellow
    exit 1
}
Write-Host ""
Write-Host "=== Function check ===" -ForegroundColor Cyan
Select-String -Path $scriptPath -Pattern "^def (find_todays_photo|_get_photo_datetime|_get_sun_times|_select_best_photo)" |
    ForEach-Object { Write-Host "  OK Line $($_.LineNumber): $($_.Line)" -ForegroundColor Green }
Write-Host ""
Write-Host "*** PATCH APPLIED ***" -ForegroundColor Green
Write-Host "Restore: Copy-Item '$backupPath' '$scriptPath' -Force" -ForegroundColor Yellow