<#
.SYNOPSIS
    Đóng gói K-TOOL để chép sang máy khác: <gốc>\_dist\K-TOOL_<yyyyMMdd>\ + file .zip cùng tên.

.DESCRIPTION
    Gói giữ cấu trúc thư mục AI\... như máy này (chép thư mục AI vào gốc ổ bất kỳ là chạy):
      AI\scripts\lisp\       K-TOOL.dll (đã nhúng LISP), K-TOOL.lsp, các file .lsp gốc (dùng cho AutoCAD 2025/2026)
      AI\_tools\CHONGTHAM_python\   Python mang theo cho lệnh CHONGTHAM
      AI\.claude\skills\truc-lo-mo-mep\assets\A-MEP_thu_vien.dwg   thư viện block A-MEP (LOMO)
      HUONG_DAN.txt
    Chạy build.ps1 trước để DLL có bản LISP mới nhất. Không ghi đè gói đã có (thêm giờ phút vào tên).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dong_goi.ps1
#>
$ErrorActionPreference = 'Stop'
$goc = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$ten = "K-TOOL_$(Get-Date -Format 'yyyyMMdd')"
$dist = Join-Path $goc '_dist'
if ((Test-Path -LiteralPath (Join-Path $dist $ten)) -or (Test-Path -LiteralPath (Join-Path $dist "$ten.zip"))) {
    $ten = "K-TOOL_$(Get-Date -Format 'yyyyMMdd_HHmm')"
}
$out = Join-Path $dist $ten
$ai = Join-Path $out 'AI'

$lisp = @('K-TOOL.dll', 'K-TOOL.lsp', 'VK.lsp', 'VKMD.lsp', 'Lomo.lsp', 'fire_stop_shaft.lsp', 'CHONGTHAM.lsp')
$nguonLisp = Join-Path $goc 'scripts\lisp'
foreach ($f in $lisp) { if (-not (Test-Path -LiteralPath (Join-Path $nguonLisp $f))) { throw "Thieu $f trong $nguonLisp (chay build.ps1 truoc)" } }
$py = Join-Path $goc '_tools\CHONGTHAM_python'
if (-not (Test-Path -LiteralPath (Join-Path $py 'python.exe'))) { throw "Thieu goi Python mang theo: $py" }
$amep = Join-Path $goc '.claude\skills\truc-lo-mo-mep\assets\A-MEP_thu_vien.dwg'

New-Item -ItemType Directory -Force -Path (Join-Path $ai 'scripts\lisp') | Out-Null
foreach ($f in $lisp) { Copy-Item -LiteralPath (Join-Path $nguonLisp $f) -Destination (Join-Path $ai 'scripts\lisp') }
Copy-Item -LiteralPath $py -Destination (Join-Path $ai '_tools\CHONGTHAM_python') -Recurse
if (Test-Path -LiteralPath $amep) {
    $d = Join-Path $ai '.claude\skills\truc-lo-mo-mep\assets'
    New-Item -ItemType Directory -Force -Path $d | Out-Null
    Copy-Item -LiteralPath $amep -Destination $d
} else { Write-Warning "Khong thay thu vien A-MEP ($amep): LOMO se dung block tinh" }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'HUONG_DAN.txt') -Destination $out

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = Join-Path $dist "$ten.zip"
[System.IO.Compression.ZipFile]::CreateFromDirectory($out, $zip, [System.IO.Compression.CompressionLevel]::Optimal, $true)

$so = (Get-ChildItem -LiteralPath $out -Recurse -File | Measure-Object Length -Sum)
Write-Output "Thu muc goi: $out ($($so.Count) file, $([math]::Round($so.Sum / 1MB, 1)) MB)"
Write-Output "File zip:    $zip ($([math]::Round((Get-Item -LiteralPath $zip).Length / 1MB, 1)) MB)"
