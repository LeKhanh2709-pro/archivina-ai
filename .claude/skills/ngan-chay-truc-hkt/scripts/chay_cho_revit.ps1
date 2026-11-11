<#
.SYNOPSIS
    Chay nen cho nut Revit "Ngan chay lan" (ARVTools) khi mat bang co CAD link: DWG -> DXF tren ban sao, do truc / hop
    ky thuat -> <ten>_vung.json.

.DESCRIPTION
    Nut Revit (NganChay_TrucHKT.py, nguoi dung yeu cau 2026-11-11 "ap dung tuong tu chong tham": dua theo CAD link) goi
    script nay, cho xong roi doc <OutDir>\<ten>_vung.json (toa do DWG, mm) de ve Filled Region.
    Khong dong vao file DWG goc (dwg_to_dxf.ps1 chep ban sao vao thu muc tam).
    Ket qua: <ten>_vung.json / .png, <OutDir>\xong.txt ("OK" hoac "LOI ..."), <OutDir>\nhat_ky.txt.
    Python / AutoCAD tu tim tren may (moi_truong.ps1), khong gan cung duong dan.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chay_cho_revit.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDir "D:\AI\_tmp\nganchay_revit_x"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDir,
    # de trong: tu tim (moi_truong.ps1 / Find-Python)
    [string]$Python = '',
    [int]$TimeoutSec = 1800
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$xong = Join-Path $OutDir 'xong.txt'
try { Start-Transcript -LiteralPath (Join-Path $OutDir 'nhat_ky.txt') -Force | Out-Null } catch {}
try {
    . (Join-Path $PSScriptRoot 'moi_truong.ps1')
    $py = Find-Python -Python $Python -Goi @('ezdxf', 'shapely')
    Write-Host "Python: $py"
    Write-Host 'NGAN CHAY - buoc 1/2: DWG -> DXF tren ban sao...'
    $dxf = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($Dwg) + '.dxf')
    if (-not (Test-Path -LiteralPath $dxf)) {
        $kq = & (Join-Path $PSScriptRoot 'dwg_to_dxf.ps1') -Dwg $Dwg -OutDir $OutDir -TimeoutSec $TimeoutSec
        $kq | ForEach-Object { Write-Host $_ }
    }
    if (-not (Test-Path -LiteralPath $dxf)) { throw "Khong tao duoc DXF: $dxf" }
    Write-Host 'NGAN CHAY - buoc 2/2: do truc / hop ky thuat...'
    $env:PYTHONUTF8 = '1'
    # lan truoc loi giua chung con de lai <ten>_vung.json / .png: doi ten (khong xoa) de tim_truc_ky_thuat.py ghi moi
    $hau = Get-Date -Format 'HHmmss'
    foreach ($du in @('_vung.json', '_vung.png')) {
        $f = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($Dwg) + $du)
        if (Test-Path -LiteralPath $f) { Rename-Item -LiteralPath $f -NewName ((Split-Path $f -Leaf) + '.loi_' + $hau) }
    }
    # khong Excel (quy uoc: chi khi nguoi dung yeu cau; goi Python mang theo khong co openpyxl)
    & $py -I -X utf8 (Join-Path $PSScriptRoot 'tim_truc_ky_thuat.py') $dxf --out-dir $OutDir --khong-excel
    if ($LASTEXITCODE -ne 0) { throw "tim_truc_ky_thuat.py loi (ma $LASTEXITCODE)" }
    Set-Content -LiteralPath $xong -Value 'OK' -Encoding ASCII
}
catch {
    Set-Content -LiteralPath $xong -Value ('LOI ' + $_.Exception.Message) -Encoding ASCII
    Write-Host ('LOI: ' + $_.Exception.Message)
    try { Stop-Transcript | Out-Null } catch {}
    exit 1
}
try { Stop-Transcript | Out-Null } catch {}
