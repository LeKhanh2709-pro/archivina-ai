<#
.SYNOPSIS
    Tim AutoCAD Core Console (accoreconsole.exe) tren may, tra ve doi tuong { Exe; Product }.

.DESCRIPTION
    Tim trong C:\Program Files\Autodesk\AutoCAD *\ va D:\autocad\AutoCAD *\ (may D:\AI: AutoCAD Architecture 2021
    cai o D:\autocad\AutoCAD 2021, khong co ban nao trong C:\Program Files). Chon ban moi nhat.
    Product = 'ACA' neu thu muc co AutoCAD Architecture (thu muc con 'ACA' hoac AecBase*.dbx) -> chay kem
    "/product ACA" de Core Console nap object enabler AEC (tuong, cua ACA), khong thi de trong.

.EXAMPLE
    $acc = & "$PSScriptRoot\tim_accoreconsole.ps1"; & $acc.Exe /i a.dwg /s b.scr $acc.Product
#>
$ErrorActionPreference = 'Stop'
$goc = @('C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe', 'D:\autocad\AutoCAD *\accoreconsole.exe')
$ds = foreach ($g in $goc) { Get-ChildItem $g -ErrorAction SilentlyContinue }
$acc = $ds | Sort-Object { $_.Directory.Name } -Descending | Select-Object -First 1
if (-not $acc) { throw ('Khong tim thay accoreconsole.exe trong: ' + ($goc -join '; ')) }
$dir = $acc.Directory.FullName
$aca = (Test-Path -LiteralPath (Join-Path $dir 'ACA')) -or [bool](Get-ChildItem (Join-Path $dir 'AecBase*.dbx') -ErrorAction SilentlyContinue)
[pscustomobject]@{ Exe = $acc.FullName; Product = $(if ($aca) { '/product ACA' } else { '' }) }
