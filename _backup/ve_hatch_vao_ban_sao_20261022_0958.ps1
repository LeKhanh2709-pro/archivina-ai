<#
.SYNOPSIS
    Ve hatch ngan chay lan vao truc / hop ky thuat tren BAN SAO DWG, theo file <ten>_vung.json
    do tim_truc_ky_thuat.py tao ra. Khong dong vao file goc.

.DESCRIPTION
    Moi vung co trang_thai "se_hatch" duoc ve dung nhu ban mau ARCHIVINA:
      1. Polyline bien kin, layer A-Material, mau 6
      2. Hatch NET, ti le 1000, goc 315, True Color RGB 220,30,30 (gan mau 22), layer "A-HATCH- Color",
         lien ket (associative) voi polyline
    Layer chua co thi tao moi (A-Material mau 251, A-HATCH- Color mau 7, nhu ban mau).
    Chay bang AutoCAD Core Console (accoreconsole) tren ban sao dat trong D:\AI\_tmp, roi SAVEAS ra -OutDwg.
    Ghi bao cao <OutDwg>_log.txt: so polyline va hatch da tao.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File ve_hatch_vao_ban_sao.ps1 -Dwg "D:\...\MB tang 4.dwg" -Json "D:\...\MB tang 4_vung.json" -OutDwg "D:\...\05_NganChay\MB tang 4_ngan chay.dwg"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$Json,
    [Parameter(Mandatory = $true)][string]$OutDwg,
    [string]$TrangThai = 'se_hatch',
    [int]$TimeoutSec = 900
)
$ErrorActionPreference = 'Stop'

$acc = Get-ChildItem 'C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe' -ErrorAction SilentlyContinue |
    Sort-Object FullName -Descending | Select-Object -First 1
if (-not $acc) { throw 'Khong tim thay accoreconsole.exe (AutoCAD Core Console).' }
foreach ($f in @($Dwg, $Json)) { if (-not (Test-Path -LiteralPath $f)) { throw "Khong thay file: $f" } }
# D:\AI: khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg (chuyen ban cu vao D:\AI\_backup truoc)" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutDwg) | Out-Null

$data = Get-Content -LiteralPath $Json -Raw -Encoding UTF8 | ConvertFrom-Json
$vung = @($data.vung | Where-Object { $_.trang_thai -eq $TrangThai })
if ($vung.Count -eq 0) { throw "Khong co vung nao o trang thai '$TrangThai' trong $Json" }

$inv = [Globalization.CultureInfo]::InvariantCulture
$ds = foreach ($v in $vung) {
    $pts = ($v.dinh | ForEach-Object { '(' + $_[0].ToString('0.###', $inv) + ' ' + $_[1].ToString('0.###', $inv) + ')' }) -join ' '
    "($pts)"
}

# D:\AI: thu muc tam dat trong D:\AI\_tmp (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = Join-Path 'D:\AI\_tmp' ('nganchay_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $work | Out-Null
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$outF = $OutDwg.Replace('\', '/')

$lisp = @"
(defun nc-layer (ten mau) (if (not (tblsearch "LAYER" ten)) (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord") (cons 2 ten) '(70 . 0) (cons 62 mau) '(6 . "Continuous")))))
(defun nc-pline (pts / ) (entmake (append (list '(0 . "LWPOLYLINE") '(100 . "AcDbEntity") '(8 . "A-Material") '(62 . 6) '(100 . "AcDbPolyline") (cons 90 (length pts)) '(70 . 1)) (mapcar '(lambda (p) (cons 10 p)) pts))) (entlast))
(defun nc-ve (ds / old e n h sl)
  (setq old (mapcar 'getvar '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO")))
  (nc-layer "A-Material" 251) (nc-layer "A-HATCH- Color" 7)
  (setvar "OSMODE" 0) (setvar "CMDECHO" 0) (setvar "HPASSOC" 1) (setvar "HPLAYER" ".") (setvar "HPCOLOR" ".")
  (setvar "CLAYER" "A-HATCH- Color") (setvar "CECOLOR" "RGB:220,30,30")
  (setq n 0 h 0)
  (foreach pts ds
    (setq e (nc-pline pts) n (1+ n) sl (entlast))
    (command "_.-HATCH" "_P" "NET" "1000" "315" "_S" e "" "")
    (if (and (not (equal (entlast) sl)) (= (cdr (assoc 0 (entget (entlast)))) "HATCH")) (setq h (1+ h))))
  (mapcar 'setvar '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO") old)
  (list n h))
(setq kq (nc-ve '($($ds -join ' '))))
(setq f (open "$fw/log.txt" "w"))
(write-line (strcat "VUNG_YEU_CAU $($vung.Count)") f)
(write-line (strcat "POLYLINE_DA_TAO " (itoa (car kq))) f)
(write-line (strcat "HATCH_DA_TAO " (itoa (cadr kq))) f)
(close f)
"@
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nFILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n`"$outF`"`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding UTF8
$p = Start-Process -FilePath $acc.FullName -WorkingDirectory $work -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $work 'console.txt') `
    -ArgumentList "/i `"$work\src.dwg`" /s `"$work\run.scr`" /l en-US"
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD Core Console. Thu muc tam: $work" }
if (-not (Test-Path -LiteralPath $OutDwg)) { throw "Khong tao duoc ban sao. Xem $work\console.txt" }
$log = Join-Path $work 'log.txt'
if (Test-Path -LiteralPath $log) { Copy-Item -LiteralPath $log -Destination ($OutDwg + '_log.txt'); Get-Content -LiteralPath $log }
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
