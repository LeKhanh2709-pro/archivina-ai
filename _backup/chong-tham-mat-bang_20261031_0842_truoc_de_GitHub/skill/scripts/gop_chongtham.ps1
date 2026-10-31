<#
.SYNOPSIS
    Gop lisp\chongtham_nguon.lsp + bo nhan dien (script PowerShell / Python cua skill chong-tham-mat-bang va
    dien-tich-ch) thanh MOT file CHONGTHAM.lsp: chep rieng file nay sang may nao cung chay (nguoi dung chot 23/10/2026).

.DESCRIPTION
    Moi file bo nhan dien duoc nhung dang base64 (dung tung byte, khong lo ma hoa) vao cuoi CHONGTHAM.lsp:
        (setq ct:*ban* "<10 ky tu dau SHA256 cua phan nhung>")
        (setq ct:*tep* '(("chong-tham-mat-bang/scripts/x.ps1" "<base64>" ...) ...))
    Lan chay dau lenh CHONGTHAM giai nen ra <goc>\_tools\chongtham_<ban>\ (ham ct:giai-nen). Doi script -> doi ban
    -> may tu giai nen ban moi, khong dung lai ban cu.
    Ghi ra <skill>\lisp\CHONGTHAM.lsp va <goc>\scripts\lisp\CHONGTHAM.lsp neu thu muc do co (UTF-8 khong BOM).
    Quy tac 2: ban CHONGTHAM.lsp cu duoc chep vao <goc>\_backup truoc khi ghi.
    Sua phan ve / lenh -> sua lisp\chongtham_nguon.lsp; sua nhan dien -> sua script trong scripts\ (hoac dien-tich-ch);
    roi chay lai script nay. KHONG sua tay CHONGTHAM.lsp.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File gop_chongtham.ps1
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$goc = Get-GocAI
$skill = Split-Path -Parent $PSScriptRoot
$nguon = Join-Path $skill 'lisp\chongtham_nguon.lsp'
$dtch = Join-Path (Split-Path -Parent $skill) 'dien-tich-ch\scripts'
if (-not (Test-Path -LiteralPath $dtch) -and $goc) { $dtch = Join-Path $goc '.claude\skills\dien-tich-ch\scripts' }

# file nhung: duong dan khi giai nen (giu cau truc 2 skill canh nhau de tim_phong_uot.py tim thay dien-tich-ch)
$tep = [ordered]@{
    'chong-tham-mat-bang/scripts/chay_cho_lisp.ps1'   = Join-Path $PSScriptRoot 'chay_cho_lisp.ps1'
    'chong-tham-mat-bang/scripts/dwg_to_dxf_aec.ps1'  = Join-Path $PSScriptRoot 'dwg_to_dxf_aec.ps1'
    'chong-tham-mat-bang/scripts/tim_accoreconsole.ps1' = Join-Path $PSScriptRoot 'tim_accoreconsole.ps1'
    'chong-tham-mat-bang/scripts/moi_truong.ps1'      = Join-Path $PSScriptRoot 'moi_truong.ps1'
    'chong-tham-mat-bang/scripts/cai_dat_python.ps1'  = Join-Path $PSScriptRoot 'cai_dat_python.ps1'
    'chong-tham-mat-bang/scripts/tim_phong_uot.py'    = Join-Path $PSScriptRoot 'tim_phong_uot.py'
    'dien-tich-ch/scripts/tao_polyline_phong.py'      = Join-Path $dtch 'tao_polyline_phong.py'
    'dien-tich-ch/scripts/chinh_hinh.py'              = Join-Path $dtch 'chinh_hinh.py'
}
foreach ($f in @($nguon) + @($tep.Values)) { if (-not (Test-Path -LiteralPath $f)) { throw "Khong thay file nguon: $f" } }

$utf8 = New-Object Text.UTF8Encoding($false)
$src = [IO.File]::ReadAllText($nguon, $utf8)
$moc = ';;; @@NHUNG_BO_NHAN_DIEN@@'
if (-not $src.Contains($moc)) { throw "Khong thay dong danh dau '$moc' trong $nguon" }

# phan nhung + ma bam phien ban
$sha = [Security.Cryptography.SHA256]::Create()
$ms = New-Object IO.MemoryStream
$khoi = New-Object System.Collections.Generic.List[string]
foreach ($k in $tep.Keys) {
    $b = [IO.File]::ReadAllBytes($tep[$k])
    $ten = [Text.Encoding]::ASCII.GetBytes($k)
    $ms.Write($ten, 0, $ten.Length); $ms.Write($b, 0, $b.Length)
    $s = [Convert]::ToBase64String($b)
    $khoi.Add("(`"$k`"")
    for ($i = 0; $i -lt $s.Length; $i += 200) { $khoi.Add('"' + $s.Substring($i, [Math]::Min(200, $s.Length - $i)) + '"') }
    $khoi.Add(')')
}
$ban = (($sha.ComputeHash($ms.ToArray()) | ForEach-Object { $_.ToString('x2') }) -join '').Substring(0, 10)
$nhung = @(
    ';;; ==================== BO NHAN DIEN NHUNG SAN (gop tu dong boi gop_chongtham.ps1, KHONG SUA TAY) ===================='
    ";;; Ban $ban, gop $(Get-Date -Format 'yyyy-MM-dd HH:mm'): $($tep.Keys -join ', ')"
    "(setq ct:*ban* `"$ban`")"
    "(setq ct:*tep* '("
) + $khoi + @('))', '(princ)')
# May LISPSYS = 0 doc file LISP theo bang ma ANSI, chu UTF-8 trong CHUOI bi vo font (may nguoi dung dang dat 0): doi chu co
# dau trong chuoi thanh ma \U+XXXX (chi ASCII, hien dung voi ca LISPSYS 0 va 1), giong gop_vk.py. Chu thich (;) giu nguyen.
$sb = New-Object Text.StringBuilder
$trongChuoi = $false; $chuThich = $false; $i = 0
while ($i -lt $src.Length) {
    $c = $src[$i]
    if ($chuThich) {
        [void]$sb.Append($c)
        if ($c -eq "`n") { $chuThich = $false }
    }
    elseif ($trongChuoi) {
        if ($c -eq '\') { [void]$sb.Append($src.Substring($i, 2)); $i += 2; continue }
        if ($c -eq '"') { $trongChuoi = $false }
        # trong chuoi LISP "\\" la 1 dau \ -> luc chay chuoi chua \U+XXXX
        if ([int]$c -gt 127) { [void]$sb.Append('\\U+' + ([int]$c).ToString('X4')) } else { [void]$sb.Append($c) }
    }
    else {
        if ($c -eq ';') { $chuThich = $true } elseif ($c -eq '"') { $trongChuoi = $true }
        [void]$sb.Append($c)
    }
    $i++
}
$src = $sb.ToString()
$ra = $src.Replace($moc, ($nhung -join "`r`n"))
$ra = $ra -replace "(?<!`r)`n", "`r`n"

$dichs = @(Join-Path $skill 'lisp\CHONGTHAM.lsp')
if ($goc -and (Test-Path -LiteralPath (Join-Path $goc 'scripts\lisp'))) { $dichs += (Join-Path $goc 'scripts\lisp\CHONGTHAM.lsp') }
$ts = Get-Date -Format 'yyyyMMdd_HHmm'
$bkDir = Get-ThuMucBackup
$i = 0
foreach ($dich in $dichs) {
    $i++
    if (Test-Path -LiteralPath $dich) {
        $bk = Join-Path $bkDir "CHONGTHAM_${ts}_truoc_gop_$i.lsp"
        if (-not (Test-Path -LiteralPath $bk)) { Copy-Item -LiteralPath $dich -Destination $bk }
    }
    [IO.File]::WriteAllText($dich, $ra, $utf8)
    Write-Output "Da ghi: $dich (ban $ban, $([Math]::Round($ra.Length / 1024)) KB)"
}
