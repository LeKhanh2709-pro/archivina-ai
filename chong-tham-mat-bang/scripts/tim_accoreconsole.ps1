<#
.SYNOPSIS
    Tim AutoCAD Core Console (accoreconsole.exe) tren may, tra ve doi tuong { Exe; Product }.

.DESCRIPTION
    Dung Find-AutoCAD trong moi_truong.ps1 (chay duoc tren may bat ky): bien ARCHIVINA_ACAD, registry Autodesk,
    roi <o dia>\Program Files\Autodesk\AutoCAD *, <o dia>\autocad\AutoCAD * (vd. may cai ACA 2021 o D:\autocad).
    Uu tien ban co AutoCAD Architecture, roi ban moi nhat.
    Product = '/product ACA' neu thu muc co AutoCAD Architecture (thu muc con 'ACA' hoac AecBase*.dbx) -> chay kem
    "/product ACA" de Core Console nap object enabler AEC (tuong, cua ACA), khong thi de trong.

.EXAMPLE
    $acc = & "$PSScriptRoot\tim_accoreconsole.ps1"; & $acc.Exe /i a.dwg /s b.scr $acc.Product
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
Find-AutoCAD -Exe 'accoreconsole.exe' -UuTienACA
