<#
.SYNOPSIS
    Chuyen DWG sang DXF, KEM no doi tuong AutoCAD Architecture (tuong, cua, cua so ACA) thanh hinh hoc thuong,
    tren BAN SAO. Khong dong vao file goc.

.DESCRIPTION
    Dua tren dien-tich-ch\scripts\dwg_to_dxf_aec.ps1. Mat bang tang ARCHIVINA: can ho la block "CHxx (T4)" chen tai 0,0,
    tuong / cua trong block la AEC -> DXFOUT thuong lam mat tuong. Cach lam: no cac INSERT co chua AEC (toi 3 cap),
    roi no tung doi tuong AEC, roi DXFOUT 2018. Sau khi no, block thiet bi long ben trong giu ten
    "CHxx (T4)$0$<ten>" nen van biet thiet bi thuoc can nao.
    Core Console tim bang tim_accoreconsole.ps1 (kem /product ACA neu may co AutoCAD Architecture).
    Ghi <ten>_aec.txt (dem AEC truoc / sau khi no) canh file DXF.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File dwg_to_dxf_aec.ps1 -Dwg "D:\...\MB tang 4.dwg" -OutDir "D:\AI\_tmp\chongtham"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDir,
    [string]$Loai = 'AEC_WALL,AEC_DOOR,AEC_WINDOW,AEC_OPENING,AEC_CURTAIN*,AEC_*ASSEMBLY',
    [int]$TimeoutSec = 3600
)
$ErrorActionPreference = 'Stop'

$acc = & (Join-Path $PSScriptRoot 'tim_accoreconsole.ps1')
if (-not (Test-Path -LiteralPath $Dwg)) { throw "Khong thay file: $Dwg" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$base = [IO.Path]::GetFileNameWithoutExtension($Dwg)
$dest = Join-Path $OutDir ($base + '.dxf')
# D:\AI: khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $dest) { throw "Da ton tai, khong ghi de: $dest (chuyen ban cu vao D:\AI\_backup truoc)" }

# D:\AI: thu muc tam dat trong D:\AI\_tmp (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = Join-Path 'D:\AI\_tmp' ('chongtham_aec_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $work | Out-Null
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$lisp = @"
(defun aec-types ( / ss i d lst c)
  (setq ss (ssget "X" '((0 . "AEC_*"))) lst nil i 0)
  (if ss (repeat (sslength ss) (setq d (cdr (assoc 0 (entget (ssname ss i))))) (if (setq c (assoc d lst)) (setq lst (subst (cons d (1+ (cdr c))) c lst)) (setq lst (cons (cons d 1) lst))) (setq i (1+ i))))
  lst)
(defun write-types (fn tag lst / f) (setq f (open fn "a")) (foreach c lst (write-line (strcat tag " " (car c) " " (itoa (cdr c))) f)) (close f))
(defun xpl (e) (command "_.EXPLODE" e) (while (= 1 (logand 1 (getvar "CMDACTIVE"))) (command "")))
(defun expl-all ( / ss i n e)
  (setq ss (ssget "X" '((0 . "$Loai"))) i 0 n 0)
  (if ss (repeat (sslength ss) (setq e (ssname ss i)) (if (entget e) (progn (xpl e) (setq n (1+ n)))) (setq i (1+ i))))
  n)
(defun blk-aec (nm dep / e d r) (setq e (tblobjname "BLOCK" nm))
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
(setvar "CMDECHO" 0)
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
Write-Output $dest
Write-Output "Thu muc tam giu lai: $work"
