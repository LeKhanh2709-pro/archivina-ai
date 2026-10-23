<#
.SYNOPSIS
    Ve mat bang chong tham vao BAN SAO DWG theo file <ten>_chongtham.json (tim_phong_uot.py). Khong dong vao file goc.

.DESCRIPTION
    Moi vung co trang_thai "se_ve" (hoac -TrangThai) duoc ve nhu ban mau CH15 (254HQV-Thap B tang 4), tat ca tren layer
    A-Material (nguoi dung chot 22/10/2026):
      1. Polyline bien kin (mat loi tuong / mat trong lan can) + polyline dao (long hop ky thuat), mau 3
      2. Hatch user-defined (_U) goc 45, khoang cach 400, double (luoi cheo), mau 3, lien ket voi polyline
      3. Net ven chan tuong: polyline ho cach bien 50, ngat tai cua di, mau 1, global width 40, net lien
    Sau do gom toan bo doi tuong vua ve vao 1 block "CHONG THAM" (trung ten -> "CHONG THAM 2"...), chen 0,0 tren A-Material.
    Layer A-Material chua co thi tao (mau 251 nhu file mau). Khong lam mo / tat layer nao.
    Chay bang AutoCAD Core Console (tim_accoreconsole.ps1, kem /product ACA de giu nguyen tuong / cua ACA) tren ban sao
    dat trong thu muc tam (moi_truong.ps1), roi SAVEAS 2018 ra -OutDwg. Ghi <OutDwg>_log.txt.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File ve_chong_tham_vao_ban_sao.ps1 -Dwg "D:\...\MB tang 4.dwg" -Json "D:\...\MB tang 4_chongtham.json" -OutDwg "D:\...\03_ChongTham\MB tang 4_chong tham.dwg"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$Json,
    [Parameter(Mandatory = $true)][string]$OutDwg,
    [string]$TrangThai = 'se_ve',
    [string]$TenBlock = 'CHONG THAM',
    [int]$TimeoutSec = 3600
)
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acc = & (Join-Path $PSScriptRoot 'tim_accoreconsole.ps1')
foreach ($f in @($Dwg, $Json)) { if (-not (Test-Path -LiteralPath $f)) { throw "Khong thay file: $f" } }
# khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg (chuyen ban cu vao _backup truoc)" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutDwg) | Out-Null

$data = Get-Content -LiteralPath $Json -Raw -Encoding UTF8 | ConvertFrom-Json
$trang = $TrangThai -split ','
$vung = @($data.vung | Where-Object { $trang -contains $_.trang_thai })
if ($vung.Count -eq 0) { throw "Khong co vung nao o trang thai '$TrangThai' trong $Json" }

$inv = [Globalization.CultureInfo]::InvariantCulture
function Diem($ds) { ($ds | ForEach-Object { '(' + ([double]$_[0]).ToString('0.###', $inv) + ' ' + ([double]$_[1]).ToString('0.###', $inv) + ')' }) -join ' ' }
# Moi polyline mot dong (setq ...): dong lenh qua dai bi Core Console cat, LISP thieu ngoac va treo
$ds = New-Object System.Collections.Generic.List[string]
$nVen = 0
foreach ($v in $vung) {
    $i = [int]$v.id
    $ds.Add("(setq ct-bo (cons (list $i '($(Diem $v.bo))) ct-bo))")
    foreach ($d in @($v.dao)) { if ($d) { $ds.Add("(setq ct-dao (cons (list $i '($(Diem $d))) ct-dao))") } }
    foreach ($l in @($v.ven)) {
        if ($l) { $ds.Add("(setq ct-ven (cons (list $i $(if ($l.dong) { 1 } else { 0 }) '($(Diem $l.dinh))) ct-ven))"); $nVen++ }
    }
}

# thu muc tam (moi_truong.ps1, quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = New-ThuMucLam 'chongtham_ve_'
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$outF = $OutDwg.Replace('\', '/')

$lisp = @"
(defun ct-layer (ten) (if (not (tblsearch "LAYER" ten)) (entmake (list '(0 . "LAYER") '(100 . "AcDbSymbolTableRecord") '(100 . "AcDbLayerTableRecord") (cons 2 ten) '(70 . 0) '(62 . 251) '(6 . "Continuous")))))
(defun ct-pl (pts kin mau rong / ) (entmake (append (list '(0 . "LWPOLYLINE") '(100 . "AcDbEntity") '(8 . "A-Material") (cons 62 mau) '(6 . "Continuous") '(100 . "AcDbPolyline") (cons 90 (length pts)) (cons 70 kin) (cons 43 rong)) (mapcar '(lambda (p) (cons 10 p)) pts))) (entlast))
(defun ct-ve ( / old moi nbo nhat nven e ss sl id)
  (setq old (mapcar 'getvar '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO" "HPISLANDDETECTION" "HPANNOTATIVE")))
  (ct-layer "A-Material")
  (setvar "OSMODE" 0) (setvar "CMDECHO" 0) (setvar "HPASSOC" 1) (setvar "HPLAYER" ".") (setvar "HPCOLOR" ".") (setvar "HPISLANDDETECTION" 1) (setvar "HPANNOTATIVE" 0)
  (if (= 0 (getvar "WORLDUCS")) (command "_.UCS" "_W"))
  (setvar "CLAYER" "A-Material") (setvar "CECOLOR" "3")
  (setq moi nil nbo 0 nhat 0 nven 0)
  (foreach b (reverse ct-bo)
    (setq id (car b) ss (ssadd) e (ct-pl (cadr b) 1 3 0.0) nbo (1+ nbo) moi (cons e moi))
    (ssadd e ss)
    (foreach d ct-dao (if (= (car d) id) (progn (setq e (ct-pl (cadr d) 1 3 0.0) moi (cons e moi)) (ssadd e ss))))
    (setq sl (entlast))
    (command "_.-HATCH" "_P" "_U" "45" "400" "_Y" "_S" ss "" "")
    (if (and (not (equal (entlast) sl)) (= (cdr (assoc 0 (entget (entlast)))) "HATCH")) (setq nhat (1+ nhat) moi (cons (entlast) moi))))
  (foreach l (reverse ct-ven) (setq e (ct-pl (caddr l) (cadr l) 1 40.0) nven (1+ nven) moi (cons e moi)))
  (mapcar 'setvar '("CLAYER" "CECOLOR" "HPASSOC" "HPLAYER" "HPCOLOR" "OSMODE" "CMDECHO" "HPISLANDDETECTION" "HPANNOTATIVE") old)
  (list nbo nhat nven moi))
(defun ct-gom (ds lay goc / ss ten i n)
  (setq ss (ssadd) ten goc i 1)
  (foreach e ds (if (entget e) (ssadd e ss)))
  (while (tblsearch "BLOCK" ten) (setq i (1+ i) ten (strcat goc " " (itoa i))))
  (if (> (sslength ss) 0)
    (progn
      (setq n (sslength ss))
      (command "_.-BLOCK" ten "0,0,0" ss "")
      (if (tblsearch "BLOCK" ten)
        (progn
          (if (not (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmake (list '(0 . "INSERT") '(100 . "AcDbEntity") (cons 8 lay) '(100 . "AcDbBlockReference") (cons 2 ten) '(10 0.0 0.0 0.0) '(41 . 1.0) '(42 . 1.0) '(43 . 1.0) '(50 . 0.0))))
          (if (setq ss (ssget "X" (list '(0 . "INSERT") '(410 . "Model") (cons 2 ten))))
            (entmod (subst (cons 8 lay) (assoc 8 (entget (ssname ss 0))) (entget (ssname ss 0)))))
          (strcat ten " (" (itoa n) " doi tuong)"))))))
(setq ct-bo nil ct-dao nil ct-ven nil)
$($ds -join "`r`n")
(setq kq (ct-ve))
(setq tb (ct-gom (cadddr kq) "A-Material" "$TenBlock"))
(setq f (open "$fw/log.txt" "w"))
(write-line "VUNG_YEU_CAU $($vung.Count)" f)
(write-line (strcat "BO_DA_TAO " (itoa (car kq))) f)
(write-line (strcat "HATCH_DA_TAO " (itoa (cadr kq))) f)
(write-line "NET_VEN_YEU_CAU $nVen" f)
(write-line (strcat "NET_VEN_DA_TAO " (itoa (caddr kq))) f)
(write-line (strcat "BLOCK " (if tb tb "(khong tao duoc)")) f)
(close f)
"@
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nFILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n`"$outF`"`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding UTF8
$p = Start-Process -FilePath $acc.Exe -WorkingDirectory $work -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $work 'console.txt') `
    -ArgumentList "/i `"$work\src.dwg`" /s `"$work\run.scr`" $($acc.Product) /l en-US"
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung Core Console. Thu muc tam: $work" }
if (-not (Test-Path -LiteralPath $OutDwg)) { throw "Khong tao duoc ban sao. Xem $work\console.txt" }
$log = Join-Path $work 'log.txt'
if (Test-Path -LiteralPath $log) { Copy-Item -LiteralPath $log -Destination ($OutDwg + '_log.txt'); Get-Content -LiteralPath $log }
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
