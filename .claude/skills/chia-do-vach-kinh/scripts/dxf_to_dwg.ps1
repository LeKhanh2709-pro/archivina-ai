<#
.SYNOPSIS
    Chuyen DXF (vach kinh vua dung) sang DWG 2018 bang AutoCAD Core Console. Khong ghi de file da co.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dxf_to_dwg.ps1 -Dxf "D:\...\VK_4210.dxf"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dxf,
    [string]$OutDwg = '',
    [int]$TimeoutSec = 300
)
$ErrorActionPreference = 'Stop'

# AutoCAD Core Console / thu muc tam tu tim tren may (moi_truong.ps1), khong gan cung duong dan
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acc = Find-AutoCAD -Exe 'accoreconsole.exe'
if (-not (Test-Path -LiteralPath $Dxf)) { throw "Khong thay file: $Dxf" }
if (-not $OutDwg) { $OutDwg = [IO.Path]::ChangeExtension($Dxf, '.dwg') }
# khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg" }

# thu muc tam (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = New-ThuMucLam 'vachkinh_'
Copy-Item -LiteralPath $Dxf -Destination (Join-Path $work 'src.dxf')
$fw = $work.Replace('\', '/')
# Core Console mo truc tiep file DXF, luu lai dang DWG 2018
$scr = "FILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n$fw/out.dwg`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding ASCII
$p = Start-Process -FilePath $acc.Exe -WorkingDirectory $work -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $work 'console.txt') `
    -ArgumentList "/i `"$work\src.dxf`" /s `"$work\run.scr`" /l en-US"
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD Core Console. Thu muc tam: $work" }
$out = Join-Path $work 'out.dwg'
if (-not (Test-Path -LiteralPath $out)) { throw "Khong tao duoc DWG. Xem $work\console.txt" }
Copy-Item -LiteralPath $out -Destination $OutDwg
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
