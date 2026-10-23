<#
.SYNOPSIS
    Ve hatch ngan chay lan vao truc / hop ky thuat tren BAN SAO DWG, theo file <ten>_vung.json
    do tim_truc_ky_thuat.py tao ra. Khong dong vao file goc.

.DESCRIPTION
    Moi vung co trang_thai "se_hatch" duoc ve dung nhu ban mau ARCHIVINA:
      1. Polyline bien kin, layer A-Material, mau 6
      2. Hatch NET, ti le 1000, goc 315, True Color RGB 220,30,30 (gan mau 22), layer A-Material,
         lien ket (associative) voi polyline
    Nguoi dung chot 22/10/2026: bo va hatch ngan chay lan LUON tren layer A-Material, moi ban ve
    (ban mau cu de hatch o "A-HATCH- Color" - khong dung nua). Layer chua co thi tao moi (mau 251).
    Sau khi hatch: gom duong bo + hatch vao block "NGAN CHAY LAN" (chen 0,0, layer A-Material);
    tat layer noi that / thiet bi ve sinh, doi moi layer khac sang mau 150,150,150
    (ham nc:lam-mo trong lisp\fire_stop_shaft.lsp cua skill). Bo buoc nay: them -KhongLamMo.
    Chay bang AutoCAD Core Console (tu tim, moi_truong.ps1) tren ban sao dat trong thu muc tam, roi SAVEAS ra -OutDwg.
    Ghi bao cao <OutDwg>_log.txt: so polyline va hatch da tao.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File ve_hatch_vao_ban_sao.ps1 -Dwg "D:\...\MB tang 4.dwg" -Json "D:\...\MB tang 4_vung.json" -OutDwg "D:\...\05_NganChay\MB tang 4_ngan chay.dwg"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$Json,
    [Parameter(Mandatory = $true)][string]$OutDwg,
    [string]$TrangThai = 'se_hatch',
    [switch]$KhongLamMo,
    [int]$TimeoutSec = 3600
)
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acc = Find-AutoCAD -Exe 'accoreconsole.exe'
foreach ($f in @($Dwg, $Json)) { if (-not (Test-Path -LiteralPath $f)) { throw "Khong thay file: $f" } }
# khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg (chuyen ban cu vao _backup truoc)" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutDwg) | Out-Null

$data = Get-Content -LiteralPath $Json -Raw -Encoding UTF8 | ConvertFrom-Json
$vung = @($data.vung | Where-Object { $_.trang_thai -eq $TrangThai })
if ($vung.Count -eq 0) { throw "Khong co vung nao o trang thai '$TrangThai' trong $Json" }

$inv = [Globalization.CultureInfo]::InvariantCulture
# Moi vung mot dong (setq ...): dong lenh qua dai bi Core Console cat, LISP thieu ngoac va treo
$ds = foreach ($v in $vung) {
    $pts = ($v.dinh | ForEach-Object { '(' + $_[0].ToString('0.###', $inv) + ' ' + $_[1].ToString('0.###', $inv) + ')' }) -join ' '
    "(setq nc-ds (cons '($pts) nc-ds))"
}

# thu muc tam (moi_truong.ps1, quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = New-ThuMucLam 'nganchay_'
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$outF = $OutDwg.Replace('\', '/')

# Ham ve / gom block / lam mo dung chung LISP cua lenh NCL (mot nguon quy tac, ke ca tu chinh ti le NET cho dung
# luoi 125 mm khi may lay mau tu acadiso.pat). Chep noi dung LISP vao .scr (SECURELOAD chan load ngoai thu muc tin cay).
# LISP nam trong goi skill (lisp\), khong co thi dung ban tai <goc>\scripts\lisp
$lsp = Join-Path $PSScriptRoot '..\lisp\fire_stop_shaft.lsp'
if (-not (Test-Path -LiteralPath $lsp) -and (Get-GocAI)) { $lsp = Join-Path (Get-GocAI) 'scripts\lisp\fire_stop_shaft.lsp' }
if (-not (Test-Path -LiteralPath $lsp)) { throw "Khong thay LISP: $lsp" }
$ham = Get-Content -LiteralPath $lsp -Encoding UTF8 | Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith(';') }

$lisp = ($ham -join "`r`n") + "`r`n" + @"
(defun nc-ve (ds / old r n h nc-tl)
  (setq old (mapcar 'getvar nc:*bien*))
  (nc:tao-layer "A-Material")
  (setvar "OSMODE" 0) (setvar "CMDECHO" 0)
  (nc:dat-hatch)
  (nc:ucs-world)
  (setvar "CLAYER" "A-Material") (setvar "CECOLOR" "RGB:220,30,30")
  (setq n 0 h 0 nc-moi nil)
  (foreach pts ds
    (setq r (nc:ve-vung pts "A-Material") n (1+ n) nc-moi (append r nc-moi))
    (if (cadr r) (setq h (1+ h))))
  (setq nc-tl-cuoi nc-tl)
  (mapcar 'nc:dat nc:*bien* old)
  (list n h))
(setq nc-ds nil)
$($ds -join "`r`n")
(setq kq (nc-ve (reverse nc-ds)))
(setq f (open "$fw/log.txt" "w"))
(write-line (strcat "VUNG_YEU_CAU $($vung.Count)") f)
(write-line (strcat "POLYLINE_DA_TAO " (itoa (car kq))) f)
(write-line (strcat "HATCH_DA_TAO " (itoa (cadr kq))) f)
(write-line (strcat "NET_TI_LE " (if nc-tl-cuoi (rtos nc-tl-cuoi 2 4) "-")) f)
(close f)
(setq tb (nc:gom-block nc-moi "A-Material"))
(setq f (open "$fw/log.txt" "a"))
(write-line (strcat "BLOCK " (if tb tb "(khong tao duoc)")) f)
(close f)
"@
# Sau khi ve: gom duong bo + hatch vao 1 block "NGAN CHAY LAN" (nc:gom-block), roi tat layer noi that /
# thiet bi ve sinh, doi mau bang layer sang xam (nc:lam-mo).
if (-not $KhongLamMo) {
    $lisp += "`r`n(setvar `"CLAYER`" `"A-Material`")`r`n(setq nlm (nc:lam-mo `"A-Material`"))`r`n(setq f (open `"$fw/log.txt`" `"a`"))`r`n(write-line (strcat `"LAYER_DA_TAT `" (itoa nlm)) f)`r`n(close f)"
}
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nFILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n`"$outF`"`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding UTF8
$p = Start-Process -FilePath $acc.Exe -WorkingDirectory $work -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $work 'console.txt') `
    -ArgumentList "/i `"$work\src.dwg`" /s `"$work\run.scr`" /l en-US"
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD Core Console. Thu muc tam: $work" }
if (-not (Test-Path -LiteralPath $OutDwg)) { throw "Khong tao duoc ban sao. Xem $work\console.txt" }
$log = Join-Path $work 'log.txt'
if (Test-Path -LiteralPath $log) { Copy-Item -LiteralPath $log -Destination ($OutDwg + '_log.txt'); Get-Content -LiteralPath $log }
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
