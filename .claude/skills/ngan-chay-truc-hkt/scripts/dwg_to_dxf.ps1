<#
.SYNOPSIS
    Chuyen DWG sang DXF (DXFOUT thuong, ban 2018) tren BAN SAO bang AutoCAD Core Console. Khong dong vao file goc.

.DESCRIPTION
    Dung cho mat bang tang co xref da bind (vd. xf-truc kt nuoc tdh, xf-PKT-TĐH). Khong no doi tuong AEC:
    dau X truc / hop ky thuat la LINE / LWPOLYLINE thuong nen DXFOUT thuong la du, va ban no AEC
    (dien-tich-ch\scripts\dwg_to_dxf_aec.ps1) bi treo voi file mat bang tang lon (thu 22/10/2026, file 42 MB).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dwg_to_dxf.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDir "D:\AI\_tmp\nganchay"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [int]$TimeoutSec = 600
)
$ErrorActionPreference = 'Stop'

# AutoCAD Core Console / thu muc tam tu tim tren may (moi_truong.ps1), khong gan cung duong dan
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acc = Find-AutoCAD -Exe 'accoreconsole.exe'
if (-not (Test-Path -LiteralPath $Dwg)) { throw "Khong thay file: $Dwg" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$base = [IO.Path]::GetFileNameWithoutExtension($Dwg)
$dest = Join-Path $OutDir ($base + '.dxf')
# khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $dest) { throw "Da ton tai, khong ghi de: $dest (chuyen ban cu vao _backup truoc)" }

# thu muc tam (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = New-ThuMucLam 'dwg2dxf_'
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$scr = "FILEDIA`r`n0`r`n_.DXFOUT`r`n$fw/out.dxf`r`nV`r`n2018`r`n16`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding ASCII
$p = Start-Process -FilePath $acc.Exe -WorkingDirectory $work -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $work 'console.txt') `
    -ArgumentList "/i `"$work\src.dwg`" /s `"$work\run.scr`" /l en-US"
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD Core Console. Thu muc tam: $work" }
$out = Join-Path $work 'out.dxf'
if (-not (Test-Path -LiteralPath $out)) { throw "Khong tao duoc DXF. Xem $work\console.txt" }
Move-Item -LiteralPath $out -Destination $dest
Write-Output $dest
Write-Output "Thu muc tam giu lai: $work"
