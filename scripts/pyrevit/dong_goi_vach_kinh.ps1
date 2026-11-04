<#
.SYNOPSIS
    Đóng gói RIÊNG nút Vách kính (tab Archivina, pyRevit) để chép sang máy khác:
    <gốc>\_dist\ARVVachKinh_<yyyyMMdd>\ + file .zip cùng tên.

.DESCRIPTION
    Lấy từ ARVTools.extension đúng phần nút Vách kính cần (không gồm các nút khác):
      ARVVachKinh\ARVVachKinh.extension\
        startup.py                                   updater chia lại đố khi đổi dài / cao vách
        Archivina.tab\VachKinh.panel\...            nút Vách kính (bundle, icon, script.py)
        lib\arv_vach_kinh.py, lib\arv_vach_kinh_bang.py
        lib\vach_kinh\                               2 file XAML + 3 family .rfa + ARV_VachKinh_Nguon.rvt
                                                     (5 kiểu đố / vách ARV + panel kính + vật liệu), Revit 2027
      CAI_DAT.bat, cai_dat.ps1, HUONG_DAN.txt        nguồn: goi_vach_kinh\
      pyRevit_*.exe                                  bộ cài pyRevit (lấy ở <gốc>\_tmp\pyrevit_setup\ nếu có; -KhongKemPyRevit để bỏ)
    Không sửa file nguồn. Không ghi đè gói đã có (thêm giờ phút vào tên).
    startup.py của ARVTools.extension chỉ dùng arv_vach_kinh: nếu sau này thêm việc khác vào startup.py thì kiểm lại.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dong_goi_vach_kinh.ps1
#>
param([switch]$KhongKemPyRevit)
$ErrorActionPreference = 'Stop'
$goc = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ten = "ARVVachKinh_$(Get-Date -Format 'yyyyMMdd')"
$dist = Join-Path $goc '_dist'
if ((Test-Path -LiteralPath (Join-Path $dist $ten)) -or (Test-Path -LiteralPath (Join-Path $dist "$ten.zip"))) {
    $ten = "ARVVachKinh_$(Get-Date -Format 'yyyyMMdd_HHmm')"
}
$out = Join-Path $dist $ten

$ext = Join-Path $PSScriptRoot 'ARVTools.extension'
$nguon = Join-Path $PSScriptRoot 'goi_vach_kinh'
$canCo = @(
    'startup.py',
    'Archivina.tab\VachKinh.panel\bundle.yaml',
    'Archivina.tab\VachKinh.panel\VachKinh.pushbutton\script.py',
    'lib\arv_vach_kinh.py',
    'lib\arv_vach_kinh_bang.py',
    'lib\vach_kinh\BangVachKinh.xaml',
    'lib\vach_kinh\ChuDe.xaml',
    'lib\vach_kinh\CuaSoVK_A_loai2.rfa',
    'lib\vach_kinh\Door-Curtain-Wall-Double-Glass.rfa',
    'lib\vach_kinh\Kinh_goc_6_trai.rfa',
    'lib\vach_kinh\ARV_VachKinh_Nguon.rvt'
)
foreach ($f in $canCo) {
    if (-not (Test-Path -LiteralPath (Join-Path $ext $f))) { throw "Thieu $ext\$f" }
}
foreach ($f in @('cai_dat.ps1', 'CAI_DAT.bat', 'HUONG_DAN.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $nguon $f))) { throw "Thieu $nguon\$f" }
}
# startup.py chỉ được nạp lib của vách kính, không thì gói thiếu module
$imp = Select-String -LiteralPath (Join-Path $ext 'startup.py') -Pattern '^\s*import (arv_\w+)' -AllMatches |
    ForEach-Object { $_.Matches.Groups[1].Value } | Where-Object { $_ -ne 'arv_vach_kinh' }
if ($imp) { throw "startup.py nap them module ngoai goi: $($imp -join ', ')" }

$dich = Join-Path $out 'ARVVachKinh\ARVVachKinh.extension'
New-Item -ItemType Directory -Force -Path (Join-Path $dich 'lib') | Out-Null
Copy-Item -LiteralPath (Join-Path $ext 'startup.py') -Destination $dich
Copy-Item -LiteralPath (Join-Path $ext 'lib\arv_vach_kinh.py') -Destination (Join-Path $dich 'lib')
Copy-Item -LiteralPath (Join-Path $ext 'lib\arv_vach_kinh_bang.py') -Destination (Join-Path $dich 'lib')
foreach ($d in @('Archivina.tab\VachKinh.panel', 'lib\vach_kinh')) {
    robocopy (Join-Path $ext $d) (Join-Path $dich $d) /E /XD __pycache__ /XF *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy loi ($LASTEXITCODE): $d" }
}
$global:LASTEXITCODE = 0

# cmd cần CRLF
$bat = (Get-Content -LiteralPath (Join-Path $nguon 'CAI_DAT.bat') -Raw) -replace "`r?`n", "`r`n"
[IO.File]::WriteAllText((Join-Path $out 'CAI_DAT.bat'), $bat, [Text.Encoding]::ASCII)
Copy-Item -LiteralPath (Join-Path $nguon 'cai_dat.ps1') -Destination $out
# Notepad đời cũ cần BOM mới nhận UTF-8
$hd = Get-Content -LiteralPath (Join-Path $nguon 'HUONG_DAN.txt') -Raw -Encoding UTF8
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
