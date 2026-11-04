<#
.SYNOPSIS
    Đóng gói tab Archivina (pyRevit) để chép sang máy khác: <gốc>\_dist\ARVTools_<yyyyMMdd>\ + file .zip cùng tên.

.DESCRIPTION
    Gói gồm:
      ARVTools\ARVTools.extension\   extension (bỏ __pycache__ / .pyc), thư mục ARVTools\ là Extension Search Path
      CAI_DAT.bat, cai_dat.ps1       đăng ký vào pyRevit trên máy đích (nguồn: goi_cai_dat\)
      HUONG_DAN.txt
      pyRevit_*.exe                  bộ cài pyRevit (lấy ở <gốc>\_tmp\pyrevit_setup\ nếu có; -KhongKemPyRevit để bỏ)
    Không ghi đè gói đã có (thêm giờ phút vào tên).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dong_goi.ps1
#>
param([switch]$KhongKemPyRevit)
$ErrorActionPreference = 'Stop'
$goc = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ten = "ARVTools_$(Get-Date -Format 'yyyyMMdd')"
$dist = Join-Path $goc '_dist'
if ((Test-Path -LiteralPath (Join-Path $dist $ten)) -or (Test-Path -LiteralPath (Join-Path $dist "$ten.zip"))) {
    $ten = "ARVTools_$(Get-Date -Format 'yyyyMMdd_HHmm')"
}
$out = Join-Path $dist $ten

$ext = Join-Path $PSScriptRoot 'ARVTools.extension'
$caiDat = Join-Path $PSScriptRoot 'goi_cai_dat'
foreach ($f in @($ext, (Join-Path $caiDat 'cai_dat.ps1'), (Join-Path $caiDat 'CAI_DAT.bat'), (Join-Path $caiDat 'HUONG_DAN.txt'))) {
    if (-not (Test-Path -LiteralPath $f)) { throw "Thieu $f" }
}

New-Item -ItemType Directory -Force -Path (Join-Path $out 'ARVTools') | Out-Null
robocopy $ext (Join-Path $out 'ARVTools\ARVTools.extension') /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy loi ($LASTEXITCODE)" }
$global:LASTEXITCODE = 0

# cmd cần CRLF
$bat = (Get-Content -LiteralPath (Join-Path $caiDat 'CAI_DAT.bat') -Raw) -replace "`r?`n", "`r`n"
[IO.File]::WriteAllText((Join-Path $out 'CAI_DAT.bat'), $bat, [Text.Encoding]::ASCII)
Copy-Item -LiteralPath (Join-Path $caiDat 'cai_dat.ps1') -Destination $out
# Notepad đời cũ cần BOM mới nhận UTF-8
$hd = Get-Content -LiteralPath (Join-Path $caiDat 'HUONG_DAN.txt') -Raw -Encoding UTF8
[IO.File]::WriteAllText((Join-Path $out 'HUONG_DAN.txt'), ($hd -replace "`r?`n", "`r`n"), (New-Object Text.UTF8Encoding $true))

if (-not $KhongKemPyRevit) {
    $setup = Get-ChildItem -Path (Join-Path $goc '_tmp\pyrevit_setup') -Filter 'pyRevit_*.exe' -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($setup) { Copy-Item -LiteralPath $setup.FullName -Destination $out }
    else { Write-Warning "Khong thay bo cai pyRevit trong $goc\_tmp\pyrevit_setup: goi khong kem bo cai" }
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = Join-Path $dist "$ten.zip"
[System.IO.Compression.ZipFile]::CreateFromDirectory($out, $zip, [System.IO.Compression.CompressionLevel]::Optimal, $true)

$so = (Get-ChildItem -LiteralPath $out -Recurse -File | Measure-Object Length -Sum)
Write-Output "Thu muc goi: $out ($($so.Count) file, $([math]::Round($so.Sum / 1MB, 1)) MB)"
Write-Output "File zip:    $zip ($([math]::Round((Get-Item -LiteralPath $zip).Length / 1MB, 1)) MB)"
