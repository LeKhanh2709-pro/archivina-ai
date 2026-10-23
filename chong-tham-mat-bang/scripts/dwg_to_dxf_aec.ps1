<#
.SYNOPSIS
    Chuyen DWG sang DXF, KEM no doi tuong AutoCAD Architecture (tuong, cua, cua so ACA) thanh hinh hoc thuong,
    tren BAN SAO. Khong dong vao file goc.

.DESCRIPTION
    Dua tren dien-tich-ch\scripts\dwg_to_dxf_aec.ps1. Mat bang tang ARCHIVINA: can ho la block "CHxx (T4)" chen tai 0,0,
    tuong / cua trong block la AEC -> DXFOUT thuong lam mat tuong. Cach lam: no cac INSERT co chua AEC (toi 3 cap),
    roi no tung doi tuong AEC, roi DXFOUT 2018. Sau khi no, block thiet bi long ben trong giu ten
    "CHxx (T4)$0$<ten>" nen van biet thiet bi thuoc can nao.
    Core Console tim bang tim_accoreconsole.ps1 (kem /product ACA neu may co AutoCAD Architecture). Thu muc tam tim bang
    moi_truong.ps1 (may D:\AI: D:\AI\_tmp; may khac: <goc>\_tmp hoac %LOCALAPPDATA%\ARCHIVINA\_tmp).
    Ghi <ten>_aec.txt (dem AEC truoc / sau khi no) canh file DXF.
    Ban ve luu khi dang o UCS xoay (canh nha xoay): chuyen UCS World truoc khi no, de ket qua no AEC khong phu thuoc UCS.
    Xref ngoai (vd. CT2: moi can ho la xref o A:\...): KHONG bind, ke ca tren ban sao (nguoi dung chot 23/10/2026).
    DXFOUT khong chua noi dung xref, nen moi xref duoc chep ban sao + no AEC + DXF rieng (goi lai chinh script nay,
    chay song song, toi 2 cap xref long nhau) vao <OutDir>\xref\NN\. Ghi <ten>_xref.txt: "ten xref|duong dan|dxf"
    de tim_phong_uot.py dat noi dung xref vao dung vi tri (chi trong bo nho). -ThuMucGoc: thu muc ban ve goc de tim xref
    duong dan tuong doi (khi -Dwg la ban tam).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dwg_to_dxf_aec.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDir "D:\AI\_tmp\chongtham"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDir,
    # THU TU NO: cua / cua so / o mo truoc, tuong sau cung. No tuong truoc thi cua gan trong tuong bi xoa theo
    # (CT2 CH.02: 10 cua mat het -> net ven chay qua cua, nguoi dung bao loi 23/10/2026)
    [string]$Loai = 'AEC_DOOR,AEC_WINDOW,AEC_OPENING,AEC_*ASSEMBLY,AEC_CURTAIN*,AEC_WALL',
    [int]$TimeoutSec = 3600,
    [string]$ThuMucGoc = '',
    [int]$CapXref = 0
)
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acc = & (Join-Path $PSScriptRoot 'tim_accoreconsole.ps1')
if (-not (Test-Path -LiteralPath $Dwg)) { throw "Khong thay file: $Dwg" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$base = [IO.Path]::GetFileNameWithoutExtension($Dwg)
$dest = Join-Path $OutDir ($base + '.dxf')
# khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $dest) { throw "Da ton tai, khong ghi de: $dest (chuyen ban cu vao _backup truoc)" }

# thu muc tam (quy tac 7), khong xoa sau khi chay (quy tac 1); duong dan ASCII de dua vao .scr
$work = New-ThuMucLam 'chongtham_aec_'
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$dsLoai = ($Loai -split ',' | ForEach-Object { '"' + $_.Trim() + '"' }) -join ' '
$lisp = @"
(defun aec-types ( / ss i d lst c)
  (setq ss (ssget "X" '((0 . "AEC_*"))) lst nil i 0)
  (if ss (repeat (sslength ss) (setq d (cdr (assoc 0 (entget (ssname ss i))))) (if (setq c (assoc d lst)) (setq lst (subst (cons d (1+ (cdr c))) c lst)) (setq lst (cons (cons d 1) lst))) (setq i (1+ i))))
  lst)
(defun write-types (fn tag lst / f) (setq f (open fn "a")) (foreach c lst (write-line (strcat tag " " (car c) " " (itoa (cdr c))) f)) (close f))
(defun xpl (e) (command "_.EXPLODE" e) (while (= 1 (logand 1 (getvar "CMDACTIVE"))) (command "")))
(defun expl-all ( / ss i n e) (setq n 0)
  (foreach k '($dsLoai) (setq ss (ssget "X" (list (cons 0 k))) i 0)
    (if ss (repeat (sslength ss) (setq e (ssname ss i)) (if (entget e) (progn (xpl e) (setq n (1+ n)))) (setq i (1+ i)))))
  n)
(defun blk-aec (nm dep / e d r b) (setq b (tblsearch "BLOCK" nm)) (if (and b (/= 4 (logand 4 (cdr (assoc 70 b))))) (setq e (tblobjname "BLOCK" nm)))
  (if e (setq e (entnext e)))
  (while (and e (not r)) (setq d (entget e))
    (cond ((wcmatch (cdr (assoc 0 d)) "AEC_*") (setq r T))
          ((and (= (cdr (assoc 0 d)) "INSERT") (< dep 3)) (setq r (blk-aec (cdr (assoc 2 d)) (1+ dep)))))
    (setq e (entnext e)))
  r)
(defun expl-blk-aec ( / ss i e n) (setq ss (ssget "X" '((0 . "INSERT") (410 . "Model"))) i 0 n 0)
  (if ss (repeat (sslength ss) (setq e (ssname ss i)) (if (and (entget e) (blk-aec (cdr (assoc 2 (entget e))) 0)) (progn (xpl e) (setq n (1+ n)))) (setq i (1+ i))))
  n)
(defun log-n (fn tag n / f) (setq f (open fn "a")) (write-line (strcat tag " " (itoa n)) f) (close f))
(defun xref-list ( / ss i n b lst f) (setq f (open "$fw/xref.txt" "w" "utf8") ss (ssget "X" '((0 . "INSERT") (410 . "Model"))) i 0) (if ss (repeat (sslength ss) (setq n (cdr (assoc 2 (entget (ssname ss i)))) b (tblsearch "BLOCK" n)) (if (and b (= 4 (logand 4 (cdr (assoc 70 b)))) (not (member n lst))) (progn (setq lst (cons n lst)) (write-line (strcat n "|" (itoa (cdr (assoc 70 b))) "|" (cdr (assoc 1 b))) f))) (setq i (1+ i)))) (close f))
(xref-list)
(setvar "CMDECHO" 0)
(if (= 0 (getvar "WORLDUCS")) (command "_.UCS" "_W"))
(log-n "$fw/aec.txt" "BLOCK_CO_AEC_DA_NO" (+ (expl-blk-aec) (expl-blk-aec) (expl-blk-aec)))
(write-types "$fw/aec.txt" "TRUOC" (aec-types))
(setq nn (vl-catch-all-apply 'expl-all))
(write-types "$fw/aec.txt" "SAU" (aec-types))
"@
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nFILEDIA`r`n0`r`n_.DXFOUT`r`n$fw/out.dxf`r`nV`r`n2018`r`n16`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding ASCII
$p = Start-Process -FilePath $acc.Exe -WorkingDirectory $work -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $work 'console.txt') `
    -ArgumentList "/i `"$work\src.dwg`" /s `"$work\run.scr`" $($acc.Product) /l en-US"
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung Core Console. Thu muc tam: $work" }
$out = Join-Path $work 'out.dxf'
if (-not (Test-Path -LiteralPath $out)) { throw "Khong tao duoc DXF. Xem $work\console.txt" }
Move-Item -LiteralPath $out -Destination $dest
$rep = Join-Path $work 'aec.txt'
if (Test-Path -LiteralPath $rep) { Copy-Item -LiteralPath $rep -Destination (Join-Path $OutDir ($base + '_aec.txt')); Get-Content -LiteralPath $rep }

# Xref ngoai: khong bind. Moi xref -> ban sao + no AEC + DXF rieng (chay song song, toi da 6 tien trinh)
$xrefTxt = Join-Path $work 'xref.txt'
$bang = @()
if ((Test-Path -LiteralPath $xrefTxt) -and $CapXref -lt 2) {
    $goc = if ($ThuMucGoc) { $ThuMucGoc.TrimEnd('\') } else { (Split-Path -Parent $Dwg).TrimEnd('\') }
    # xref chi chua chu thich / khung ten / luoi truc / chi gioi: khong co ranh phong, bo qua cho nhanh
    $boQua = '(?i)khung|ghi ?ch|note|legend|chu giai|luoi|chi ?gioi|callout'
    $chay = @(); $i = 0
    foreach ($dong in Get-Content -LiteralPath $xrefTxt -Encoding UTF8) {
        # dong: ten|co 70|duong dan. Xref long dang Overlay (co 8) khong hien o ban ve chu -> bo
        $p = $dong -split '\|', 3
        if ($p.Count -lt 3 -or $p[0] -match $boQua) { continue }
        if ($CapXref -ge 1 -and ([int]$p[1] -band 8)) { continue }
        $ten = $p[0]; $duong = $p[2]
        $tim = $null
        foreach ($c in @($duong, "$goc\$duong", "$goc\$([IO.Path]::GetFileName($duong))")) {
            try { if ([IO.Path]::IsPathRooted($c) -and (Test-Path -LiteralPath $c -PathType Leaf)) { $tim = $c; break } } catch {}
        }
        if (-not $tim) { $bang += "$ten|$duong|"; Write-Output "XREF KHONG TIM THAY: $ten ($duong)"; continue }
        $i++
        $od = Join-Path $OutDir ('xref\' + $i.ToString('00'))
        $bang += "$ten|$tim|" + (Join-Path $od ([IO.Path]::GetFileNameWithoutExtension($tim) + '.dxf'))
        while (@($chay | Where-Object { -not $_.HasExited }).Count -ge 6) { Start-Sleep -Milliseconds 500 }
        $chay += Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -PassThru -ArgumentList (
            "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Dwg `"$tim`" -OutDir `"$od`" " +
            "-CapXref $($CapXref + 1) -ThuMucGoc `"$((Split-Path -Parent $tim).TrimEnd('\'))`" -TimeoutSec $TimeoutSec")
    }
    foreach ($c in $chay) { if (-not $c.WaitForExit($TimeoutSec * 1000)) { $c.Kill() } }
}
# UTF-8 khong BOM: lenh LISP CHONGTHAM doc file nay de bao xref khong tim thay
[IO.File]::WriteAllLines((Join-Path $OutDir ($base + '_xref.txt')), [string[]]$bang, (New-Object Text.UTF8Encoding $false))
if ($bang.Count) { Write-Output "XREF: $($bang.Count) file (doc rieng, khong bind)" }
Write-Output $dest
Write-Output "Thu muc tam giu lai: $work"
