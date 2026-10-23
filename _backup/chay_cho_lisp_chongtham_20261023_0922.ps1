<#
.SYNOPSIS
    Chay nen cho lenh LISP CHONGTHAM: no AEC tren ban sao DWG -> DXF, do phong uot -> file du lieu cho LISP.

.DESCRIPTION
    Lenh CHONGTHAM (scripts\lisp\CHONGTHAM.lsp) goi script nay va cho no chay xong, roi doc <OutDir>\du_lieu.txt
    de ve vao ban ve dang mo. Khong dong vao file DWG goc (dwg_to_dxf_aec.ps1 chep ban sao vao D:\AI\_tmp).
    Ket qua: <OutDir>\du_lieu.txt, <ten>_chongtham.json / .xlsx / .png, <OutDir>\xong.txt ("OK" hoac "LOI ...").

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chay_cho_lisp.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDir "D:\AI\_tmp\chongtham_lisp_x"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Python = 'D:\AI\_tools\venv\Scripts\python.exe'
)
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$xong = Join-Path $OutDir 'xong.txt'
try {
    Write-Host 'CHONGTHAM - buoc 1/2: no tuong / cua ACA tren ban sao, xuat DXF (vai phut)...'
    $kq = & (Join-Path $PSScriptRoot 'dwg_to_dxf_aec.ps1') -Dwg $Dwg -OutDir $OutDir
    $dxf = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($Dwg) + '.dxf')
    if (-not (Test-Path -LiteralPath $dxf)) { throw "Khong tao duoc DXF: $kq" }
    Write-Host 'CHONGTHAM - buoc 2/2: do phong uot (WC, lo gia, phong rac, phong KT nuoc)...'
    $env:PYTHONUTF8 = '1'
    & $Python -I -X utf8 (Join-Path $PSScriptRoot 'tim_phong_uot.py') $dxf --out-dir $OutDir --xuat-lsp (Join-Path $OutDir 'du_lieu.txt')
    if ($LASTEXITCODE -ne 0) { throw "tim_phong_uot.py loi (ma $LASTEXITCODE)" }
    Set-Content -LiteralPath $xong -Value 'OK' -Encoding ASCII
}
catch {
    Set-Content -LiteralPath $xong -Value ('LOI ' + $_.Exception.Message) -Encoding ASCII
    Write-Host ('LOI: ' + $_.Exception.Message)
    exit 1
}
