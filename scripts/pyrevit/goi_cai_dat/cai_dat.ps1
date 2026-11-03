<#
.SYNOPSIS
    Cai tab ARV Tools (pyRevit) tren may nay: dang ky thu muc ARVTools\ canh file nay vao Extension Search Path cua pyRevit.

.DESCRIPTION
    - Tim pyrevit.exe (PATH, %APPDATA%\pyRevit-Master, %ProgramData%\pyRevit-Master). Chua co thi hoi cai bang bo cai di kem.
    - Bo chan file tai tu Internet (Unblock-File) trong goi.
    - Them <thu muc goi>\ARVTools vao Extension Search Path (da co thi bo qua).
    - Duong dan khac cung chua ARVTools.extension (ban cu) thi hoi go dang ky (chi go dang ky, khong xoa file).
    -Go : go dang ky thu muc ARVTools cua goi nay (khong xoa file).
    Khong chuyen thu muc goi sau khi cai; chuyen roi thi chay lai.

.EXAMPLE
    CAI_DAT.bat
    powershell -NoProfile -ExecutionPolicy Bypass -File cai_dat.ps1 -Go
#>
param([switch]$Go)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$extDir = Join-Path $here 'ARVTools'
if (-not (Test-Path -LiteralPath (Join-Path $extDir 'ARVTools.extension'))) {
    throw "Khong thay $extDir\ARVTools.extension (giai nen du goi roi chay lai)"
}

function Find-PyRevit {
    $c = Get-Command pyrevit -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    foreach ($d in @($env:APPDATA, $env:ProgramData)) {
        if (-not $d) { continue }
        $p = Join-Path $d 'pyRevit-Master\bin\pyrevit.exe'
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function Get-SearchPaths($pr) {
    # Dong sau "==> Extension Search Paths" la cac duong dan da dang ky
    $ds = @(); $vao = $false
    foreach ($l in (& $pr extensions paths 2>$null)) {
        if ($l -match '^==> Extension Search Paths') { $vao = $true; continue }
        if ($l -match '^==>') { $vao = $false; continue }
        if ($vao -and $l.Trim()) { $ds += $l.Trim() }
    }
    return $ds
}

$pr = Find-PyRevit
if (-not $pr) {
    Write-Host 'Chua co pyRevit tren may nay.'
    $setup = Get-ChildItem -LiteralPath $here -Filter 'pyRevit_*.exe' -File | Select-Object -First 1
    if ($setup) {
        $a = Read-Host "Cai $($setup.Name) ngay bay gio? Dong Revit truoc khi cai. (Y/N)"
        if ($a -match '^[Yy]') { Start-Process -FilePath $setup.FullName -Wait; $pr = Find-PyRevit }
    }
    if (-not $pr) { Write-Host 'Cai pyRevit >= 6.5.5 (ban cho user) roi chay lai CAI_DAT.bat'; exit 1 }
}
Write-Host "pyRevit CLI: $pr"

$ver = (& $pr --version 2>$null | Select-Object -First 1)
if ($ver -match 'v(\d+)\.(\d+)\.(\d+)') {
    $v = [version]"$($Matches[1]).$($Matches[2]).$($Matches[3])"
    Write-Host "Phien ban: $v"
    if ($v -lt [version]'6.5.5') { Write-Warning 'pyRevit < 6.5.5: nut CPython loi tren Revit 2027 ("3.12.3 was not in a correct format"). Nen cai ban di kem.' }
}

$daCo = Get-SearchPaths $pr
$cungCho = $daCo | Where-Object { $_.TrimEnd('\') -ieq $extDir.TrimEnd('\') }

if ($Go) {
    if ($cungCho) { & $pr extensions paths forget $extDir; Write-Host "Da go dang ky: $extDir (file van con)" }
    else { Write-Host "Chua dang ky: $extDir" }
    exit 0
}

foreach ($p in $daCo) {
    if ($p.TrimEnd('\') -ieq $extDir.TrimEnd('\')) { continue }
    if (Test-Path -LiteralPath (Join-Path $p 'ARVTools.extension')) {
        $a = Read-Host "Da co ARVTools.extension khac o '$p' (2 ban se trung tab). Go dang ky duong dan do? Khong xoa file. (Y/N)"
        if ($a -match '^[Yy]') { & $pr extensions paths forget $p }
    }
}

if ($cungCho) { Write-Host "Da dang ky tu truoc: $extDir" }
else { & $pr extensions paths add $extDir; Write-Host "Da dang ky: $extDir" }

Write-Host 'Unblock file trong goi...'
Get-ChildItem -LiteralPath $here -Recurse -File | Unblock-File

Write-Host ''
& $pr attached
Write-Host ''
Write-Host 'Xong. Mo lai Revit (dang mo thi bam pyRevit -> Reload) se thay tab ARV Tools.'
Write-Host 'Khong thay dong "Attachments" nao o tren: chay  pyrevit attach master default --installed'
