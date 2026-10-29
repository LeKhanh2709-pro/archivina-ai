<#
.SYNOPSIS
    Chay thu lenh LISP MDVK (file VKMD.lsp, khong hop thoai) tren BAN SAO mot ban ve bang AutoCAD day du (acad.exe /b), luu ra -OutDwg.

.DESCRIPTION
    Nap VK.lsp (skill chia-do-vach-kinh, de dung mat bang) + VKMD.lsp, roi chay cac bieu thuc thu.
    Ham thu san co:
      (vkmd:thu L ns ws nd wd vs vd ptMB gocMB H hd hs co san bau yMD)
        -> dung mat bang bang VK tai ptMB / gocMB, roi dung mat dung tu block vua tao, chan mat dung o cao do yMD
           (vach xien: goc duoi trai = (car ptMB) yMD).
    Ket qua ghi vao <OutDwg>_log.txt.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chay_thu_vkmd.ps1 -Dwg "D:\AI\_tmp\trang.dwg" -OutDwg "D:\AI\_tmp\vkmd_thu.dwg" -Lisp "(vkmd:thu 4210.0 1 1000.0 0 1665.0 '(3) nil '(0 0 0) 0.0 3850.0 nil 1185.0 T 50.0 1400.0 2000.0)"
#>
param(
    [Parameter(Mandatory = $true)][string]$Dwg,
    [Parameter(Mandatory = $true)][string]$OutDwg,
    [string]$Lisp = '',
    [string]$LispFile = '',
    [int]$TimeoutSec = 300
)
$ErrorActionPreference = 'Stop'
if ($LispFile) { $Lisp = Get-Content -LiteralPath $LispFile -Raw -Encoding UTF8 }
if (-not $Lisp) { throw "Can -Lisp hoac -LispFile" }

. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acad = Find-AutoCAD -Exe 'acad.exe'
if (-not (Test-Path -LiteralPath $Dwg)) { throw "Khong thay file: $Dwg" }
if (Test-Path -LiteralPath $OutDwg) { throw "Da ton tai, khong ghi de: $OutDwg" }
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutDwg) | Out-Null
$skill = Split-Path -Parent $PSScriptRoot
$lspMD = Join-Path $skill 'lisp\VKMD.lsp'
$lspVK = Join-Path (Split-Path -Parent $skill) 'chia-do-vach-kinh\lisp\VK.lsp'
foreach ($f in @($lspMD, $lspVK)) { if (-not (Test-Path -LiteralPath $f)) { throw "Khong thay LISP: $f" } }

$work = New-ThuMucLam 'vkmd_thu_'
Copy-Item -LiteralPath $Dwg -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')
$outF = $OutDwg.Replace('\', '/')

# SECURELOAD chan load ngoai thu muc tin cay -> chep noi dung LISP vao .scr, bo dong trong va chu thich
$hamVK = Get-Content -LiteralPath $lspVK -Encoding UTF8 | Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith(';') }
$hamMD = Get-Content -LiteralPath $lspMD -Encoding UTF8 | Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith(';') }
# VKMD.lsp boc trong 1 (progn ...): mot dong loi la ca file khong nap, GIONG APPLOAD (dong lenh .scr chay tiep
# sau dong loi nen tung bo sot loi du lieu thieu dau ' ngay 29/10/2026)
$lisp = @"
$($hamVK -join "`r`n")
(setq vkmd:nap-xong nil vkmd:dl-kinh nil vkmd:dl-cua-di nil)
(progn
$($hamMD -join "`r`n")
(setq vkmd:nap-xong T))
(defun vk:ghi (s / f) (setq f (open "$fw/log.txt" "a")) (write-line s f) (close f))
(vk:ghi (strcat "DA_NAP_LISP VKMD " (if vkmd:nap-xong "DU" "LOI_NAP") " DU_LIEU "
                (if (and vkmd:dl-kinh vkmd:dl-cua-di) "CO" "THIEU") " LENH_MDVK " (if c:MDVK "CO" "THIEU")))
(defun vkmd:thu (L ns ws nd wd vs vd ptMB gocMB H hd hs co san bau yMD / kq e r tk)
  (setq kq (vk:chia L ns ws nd wd vs vd))
  (if (listp kq)
    (progn
      (vk:thuc-hien kq L nil ptMB gocMB)
      (setq e (entlast) tk (vkmd:tinh (vkmd:doc-vach e) H hd hs co san bau))
      (setq r (vl-catch-all-apply 'vkmd:thuc-hien (list e H hd hs co san bau (list (car ptMB) yMD 0.0))))
      (vk:ghi (strcat "VACH " (vk:so L) " [" (vk:chuoi (car kq)) "] H " (vk:so H)
                      (if (listp tk) (strcat " CAO [" (vkmd:chuoi tk) "]") (strcat " LOI_TINH " tk))
                      (if (vl-catch-all-error-p r) (strcat " LOI " (vl-catch-all-error-message r)) " OK"))))
    (vk:ghi (strcat "VACH " (vk:so L) " LOI_CHIA " kq))))
$Lisp
"@
$lines = $lisp -split "`r?`n" | Where-Object { $_.Trim() -ne '' }
$scr = ($lines -join "`r`n") + "`r`nZOOM`r`nE`r`nFILEDIA`r`n0`r`n_.SAVEAS`r`n2018`r`n`"$outF`"`r`n_.QUIT`r`n_Y`r`n"
Set-Content -Path (Join-Path $work 'run.scr') -Value $scr -Encoding UTF8

$p = Start-Process -FilePath $acad.Exe -WorkingDirectory $work -WindowStyle Minimized -PassThru `
    -ArgumentList "/nologo `"$work\src.dwg`" /b `"$work\run.scr`""
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD. Thu muc tam: $work" }
$log = Join-Path $work 'log.txt'
if (Test-Path -LiteralPath $log) { Copy-Item -LiteralPath $log -Destination ($OutDwg + '_log.txt'); Get-Content -LiteralPath $log }
if (-not (Test-Path -LiteralPath $OutDwg)) { throw "Khong tao duoc ban ve. Xem $work (run.scr, log.txt)" }
Write-Output $OutDwg
Write-Output "Thu muc tam giu lai: $work"
