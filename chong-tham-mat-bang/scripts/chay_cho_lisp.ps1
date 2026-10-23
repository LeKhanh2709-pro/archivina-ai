<#
.SYNOPSIS
    Chay nen cho lenh LISP CHONGTHAM: no AEC tren ban sao DWG -> DXF, do phong uot -> file du lieu cho LISP.

.DESCRIPTION
    Lenh CHONGTHAM (CHONGTHAM.lsp) goi script nay va cho no chay xong, roi doc <OutDir>\du_lieu.txt
    de ve vao ban ve dang mo. Khong dong vao file DWG goc (dwg_to_dxf_aec.ps1 chep ban sao vao thu muc tam).
    Ket qua: <OutDir>\du_lieu.txt, <ten>_chongtham.json / .png (khong tao Excel), <OutDir>\xong.txt ("OK" hoac "LOI ..."),
    <OutDir>\nhat_ky.txt (toan bo thong bao, de xem khi loi o may khac).
    Python / AutoCAD tu tim tren may (moi_truong.ps1), khong gan cung duong dan.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chay_cho_lisp.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDir "D:\AI\_tmp\chongtham_lisp_x"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDir,
    # de trong: tu tim (moi_truong.ps1 / Find-Python)
    [string]$Python = '',
    # thu muc ban ve dang mo (de tim xref duong dan tuong doi khi -Dwg la ban tam -WBLOCK)
    [string]$ThuMucGoc = ''
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$xong = Join-Path $OutDir 'xong.txt'
try { Start-Transcript -LiteralPath (Join-Path $OutDir 'nhat_ky.txt') -Force | Out-Null } catch {}
try {
    . (Join-Path $PSScriptRoot 'moi_truong.ps1')
    $py = Find-Python -Python $Python -Goi @('ezdxf', 'shapely', 'matplotlib')
    Write-Host "Python: $py"
    Write-Host 'CHONGTHAM - buoc 1/2: no tuong / cua ACA tren ban sao, xuat DXF (vai phut)...'
    $kq = & (Join-Path $PSScriptRoot 'dwg_to_dxf_aec.ps1') -Dwg $Dwg -OutDir $OutDir -ThuMucGoc $ThuMucGoc
    $kq | ForEach-Object { Write-Host $_ }
    $dxf = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($Dwg) + '.dxf')
    if (-not (Test-Path -LiteralPath $dxf)) { throw "Khong tao duoc DXF: $kq" }
    Write-Host 'CHONGTHAM - buoc 2/2: do phong uot (WC, lo gia, phong rac, phong KT nuoc)...'
    $env:PYTHONUTF8 = '1'
    & $py -I -X utf8 (Join-Path $PSScriptRoot 'tim_phong_uot.py') $dxf --out-dir $OutDir --xuat-lsp (Join-Path $OutDir 'du_lieu.txt')
    if ($LASTEXITCODE -ne 0) { throw "tim_phong_uot.py loi (ma $LASTEXITCODE)" }
    Set-Content -LiteralPath $xong -Value 'OK' -Encoding ASCII
}
catch {
    # xong.txt chi ASCII: LISP doc bang read-line, thong bao loi khong dau
    Set-Content -LiteralPath $xong -Value ('LOI ' + $_.Exception.Message) -Encoding ASCII
    Write-Host ('LOI: ' + $_.Exception.Message)
    try { Stop-Transcript | Out-Null } catch {}
    exit 1
}
try { Stop-Transcript | Out-Null } catch {}
