<#
.SYNOPSIS
    Chen block A-MEP (dynamic block lo mo MEP) bo khit moi truc / hop ky thuat tren BAN SAO DWG.
    Khong dong vao file goc.

.DESCRIPTION
    Do truc / hop bang ham nc:do (fire_stop_shaft.lsp, chung quy tac voi skill ngan-chay-truc-hkt),
    roi chen A-MEP va gan tham so Distance1 / Distance2 (ham amep:chay trong Lomo.lsp, lenh LOMO).
    Layer lo mo LUON la A-MEP (nguoi dung chot 22/10/2026).
    Gan tham so dynamic block can COM -> KHONG chay duoc bang Core Console; script nay chay AutoCAD
    day du (acad.exe /b) thanh mot tien trinh rieng tren ban sao dat trong D:\AI\_tmp, roi SAVEAS ra -OutDwg.
    Khong dung vao cac phien AutoCAD dang mo cua nguoi dung.
    Ket qua: <OutDwg>, <OutDwg ten>_amep.csv, <OutDwg ten>_amep.xlsx, <OutDwg>_log.txt.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chen_amep_vao_ban_sao.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDwg "D:\...\02_LoMo\MB tang 4_lo mo.dwg"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDwg,
    [int]$TimeoutSec = 3600,
    # Thu che do may khac: bo qua file thu vien A-MEP, lenh tu dung block tinh "A-MEP <rong>x<dai>"
    [switch]$KhongThuVien
)
$ErrorActionPreference = 'Stop'

$acad = Get-ChildItem 'C:\Program Files\Autodesk\AutoCAD *\acad.exe' -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1
if (-not $acad) { throw 'Khong tim thay acad.exe (AutoCAD day du).' }
if (-not (Test-Path -LiteralPath $Dwg)) { throw "Khong thay file: $Dwg" }
# D:\AI: khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg (chuyen ban cu vao D:\AI\_backup truoc)" }
$outDir = Split-Path -Parent $OutDwg
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$base = Join-Path $outDir ([IO.Path]::GetFileNameWithoutExtension($OutDwg))

# LISP: Lomo.lsp da gop san ham do cua NCL + lenh LOMO (tao bang gop_lomo.ps1). Uu tien ban trong goi skill,
# khong co thi dung ban tai D:\AI\scripts\lisp
$skill = Split-Path -Parent $PSScriptRoot
$lspAm = Join-Path $skill 'lisp\Lomo.lsp'
if (-not (Test-Path -LiteralPath $lspAm)) { $lspAm = 'D:\AI\scripts\lisp\Lomo.lsp' }
if (-not (Test-Path -LiteralPath $lspAm)) { throw "Khong thay LISP: $lspAm" }

# D:\AI: thu muc tam dat trong D:\AI\_tmp (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = Join-Path 'D:\AI\_tmp' ('amep_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $work | Out-Null
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$outF = $OutDwg.Replace('\', '/')

# Chep noi dung LISP thang vao .scr (SECURELOAD chan load ngoai thu muc tin cay), bo dong trong va dong chu thich
$ham = Get-Content -LiteralPath $lspAm -Encoding UTF8 | Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith(';') }
$lisp = @"
$($ham -join "`r`n")
(setq f (open "$fw/log.txt" "w")) (write-line "DA_NAP_LISP" f) (close f)
(setq amep-thu-vien $(if ($KhongThuVien) { '"KHONG"' } else { 'nil' }))
(setq kq (vl-catch-all-apply 'amep:chay (list "$fw/ket_qua.csv")))
(setq f (open "$fw/log.txt" "a"))
(write-line (strcat "CHE_DO " (if amep-che-do amep-che-do "(chua chon)")) f)
(write-line (if (vl-catch-all-error-p kq) (strcat "LOI " (vl-catch-all-error-message kq)) (strcat "BLOCK_DA_CHEN " (if kq (itoa kq) "0"))) f)
(write-line (strcat "BLOCK_GOM " (if amep-gom-cuoi amep-gom-cuoi "(khong gom)")) f)
(close f)
(command-s "_.UNDO" "_E")
"@
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nFILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n`"$outF`"`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding UTF8

$p = Start-Process -FilePath $acad.FullName -WorkingDirectory $work -WindowStyle Minimized -PassThru `
    -ArgumentList "/nologo `"$work\src.dwg`" /b `"$work\run.scr`""
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD. Thu muc tam: $work" }
if (-not (Test-Path -LiteralPath $OutDwg)) { throw "Khong tao duoc ban sao. Xem $work (run.scr, log.txt)" }

$csv = Join-Path $work 'ket_qua.csv'
$log = Join-Path $work 'log.txt'
if (Test-Path -LiteralPath $csv) {
    Copy-Item -LiteralPath $csv -Destination ($base + '_amep.csv')
    $py = 'D:\AI\_tools\venv\Scripts\python.exe'
    $env:PYTHONUTF8 = '1'
    & $py -I (Join-Path $PSScriptRoot 'bao_cao_excel.py') ($base + '_amep.csv') ($base + '_amep.xlsx') | Out-File -FilePath $log -Append -Encoding ascii
}
if (Test-Path -LiteralPath $log) { Copy-Item -LiteralPath $log -Destination ($OutDwg + '_log.txt'); Get-Content -LiteralPath $log }
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
