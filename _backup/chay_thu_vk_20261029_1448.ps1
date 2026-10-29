<#
.SYNOPSIS
    Chay thu lenh LISP VK (khong hop thoai) tren BAN SAO mot ban ve bang AutoCAD day du (acad.exe /b), luu ra -OutDwg.

.DESCRIPTION
    Hop thoai DCL khong chay duoc khi tu dong, nen script goi thang ham vk:chia + vk:thuc-hien voi diem / goc cho san.
    -Lisp: cac bieu thuc thu, vd. "(vk:thuc-hien (vk:chia 5300.0 1 1000.0 0 1665.0 nil nil) 5300.0 nil '(0 0 0) 0.0)".
    Ket qua chuoi o cua tung lan goi ghi vao <OutDwg>_log.txt.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chay_thu_vk.ps1 -Dwg "D:\AI\_tmp\trang.dwg" -OutDwg "D:\AI\_tmp\vk_thu.dwg" -Lisp "(...)"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDwg,
    [string]$Lisp = '',
    # file chua bieu thuc thu (tranh loi dau ngoac kep khi truyen qua dong lenh)
    [string]$LispFile = '',
    [int]$TimeoutSec = 300
)
$ErrorActionPreference = 'Stop'
if ($LispFile) { $Lisp = Get-Content -LiteralPath $LispFile -Raw -Encoding UTF8 }
if (-not $Lisp) { throw "Can -Lisp hoac -LispFile" }

# AutoCAD / thu muc tam tu tim tren may (moi_truong.ps1), khong gan cung duong dan
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acad = Find-AutoCAD -Exe 'acad.exe'
if (-not (Test-Path -LiteralPath $Dwg)) { throw "Khong thay file: $Dwg" }
# khong ghi de file da co (quy tac 2)
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutDwg) | Out-Null
$lsp = Join-Path (Split-Path -Parent $PSScriptRoot) 'lisp\VK.lsp'
if (-not (Test-Path -LiteralPath $lsp)) { throw "Khong thay LISP: $lsp" }

# thu muc tam (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = New-ThuMucLam 'vk_thu_'
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$outF = $OutDwg.Replace('\', '/')

# Chep noi dung LISP thang vao .scr (SECURELOAD chan load ngoai thu muc tin cay), bo dong trong va dong chu thich
$ham = Get-Content -LiteralPath $lsp -Encoding UTF8 | Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith(';') }
$lisp = @"
$($ham -join "`r`n")
(defun vk:ghi (s / f) (setq f (open "$fw/log.txt" "a")) (write-line s f) (close f))
(vk:ghi "DA_NAP_LISP")
(defun vk:thu (L ns ws nd wd vs vd lat pt goc / kq r)
  (setq kq (vk:chia L ns ws nd wd vs vd))
  (if (listp kq)
    (progn
      (setq r (vl-catch-all-apply 'vk:thuc-hien (list kq L lat pt goc)))
      (vk:ghi (strcat "VACH " (vk:so L) " DO " (itoa (length (cadr kq))) " [" (vk:chuoi (car kq)) "]"
                      (if (vl-catch-all-error-p r) (strcat " LOI " (vl-catch-all-error-message r)) " OK"))))
    (vk:ghi (strcat "VACH " (vk:so L) " LOI_CHIA " kq))))
$Lisp
(vk:ghi (strcat "BLOCK_VK " (if (vk:du-block) "CO" "THIEU")))
"@
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nFILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n`"$outF`"`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding UTF8

$p = Start-Process -FilePath $acad.Exe -WorkingDirectory $work -WindowStyle Minimized -PassThru `
    -ArgumentList "/nologo `"$work\src.dwg`" /b `"$work\run.scr`""
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD. Thu muc tam: $work" }
$log = Join-Path $work 'log.txt'
if (Test-Path -LiteralPath $log) { Copy-Item -LiteralPath $log -Destination ($OutDwg + '_log.txt'); Get-Content -LiteralPath $log }
if (-not (Test-Path -LiteralPath $OutDwg)) { throw "Khong tao duoc ban ve. Xem $work (run.scr, log.txt)" }
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
