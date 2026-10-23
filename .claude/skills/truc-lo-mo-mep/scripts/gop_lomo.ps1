<#
.SYNOPSIS
    Gop 2 file nguon thanh MOT file Lomo.lsp de nguoi dung chi APPLOAD 1 file roi go LOMO.

.DESCRIPTION
    Lomo.lsp = phan chu thich dau cua lomo_nguon.lsp
             + phan do truc cua fire_stop_shaft.lsp (skill ngan-chay-truc-hkt; bo chu thich dau file va
               cac lenh NCL / KT-NGANCHAY o cuoi, tu dong ";;; NCL: ve luon, khong hoi")
             + phan con lai cua lomo_nguon.lsp (lenh LOMO).
    Ghi ra <skill>\lisp\Lomo.lsp va <goc>\scripts\lisp\Lomo.lsp neu thu muc do co (UTF-8 khong BOM, nhu file nguon).
    <goc> tim bang moi_truong.ps1 (may D:\AI: D:\AI). Quy tac 2: ban Lomo.lsp cu duoc chep vao <goc>\_backup truoc khi ghi.
    Sua quy tac do truc -> sua fire_stop_shaft.lsp; sua phan lo mo -> sua lomo_nguon.lsp; roi chay lai script nay.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File gop_lomo.ps1
#>
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$goc = Get-GocAI
$skill = Split-Path -Parent $PSScriptRoot
$nguon = Join-Path $skill 'lisp\lomo_nguon.lsp'
$nc = Join-Path $skill '..\ngan-chay-truc-hkt\lisp\fire_stop_shaft.lsp'
if (-not (Test-Path -LiteralPath $nc) -and $goc) { $nc = Join-Path $goc 'scripts\lisp\fire_stop_shaft.lsp' }
foreach ($f in @($nguon, $nc)) { if (-not (Test-Path -LiteralPath $f)) { throw "Khong thay file nguon: $f" } }

$utf8 = New-Object Text.UTF8Encoding($false)
$a = [IO.File]::ReadAllLines($nguon, $utf8)
$b = [IO.File]::ReadAllLines($nc, $utf8)

# Chu thich dau file lomo_nguon: cac dong ";" lien tiep tu dau file
$i = 0; while ($i -lt $a.Count -and $a[$i].TrimStart().StartsWith(';')) { $i++ }
$dau = $a[0..($i - 1)]; $lomo = $a[$i..($a.Count - 1)]

# Phan do truc: tu dong code dau tien den truoc lenh NCL
$s = 0; while ($s -lt $b.Count -and ($b[$s].Trim() -eq '' -or $b[$s].TrimStart().StartsWith(';'))) { $s++ }
$e = [Array]::FindIndex($b, [Predicate[string]]{ param($l) $l -like ';;; NCL: v*' })
if ($e -lt 0) { throw "Khong thay dong danh dau ';;; NCL: ve luon...' trong $nc - kiem tra lai file nguon" }
$do = $b[$s..($e - 1)]

$noi = @($dau) + '' +
    ';;; ==================== PHAN DO TRUC / HOP (gop tu fire_stop_shaft.lsp) ====================' +
    @($do) +
    ';;; ==================== PHAN LO MO A-MEP, LENH LOMO (gop tu lomo_nguon.lsp) ====================' +
    @($lomo)

$ts = Get-Date -Format 'yyyyMMdd_HHmm'
$dichs = @(Join-Path $skill 'lisp\Lomo.lsp')
if ($goc -and (Test-Path -LiteralPath (Join-Path $goc 'scripts\lisp'))) { $dichs += (Join-Path $goc 'scripts\lisp\Lomo.lsp') }
$bkDir = Get-ThuMucBackup
foreach ($dich in $dichs) {
    if (Test-Path -LiteralPath $dich) {
        $bk = Join-Path $bkDir "Lomo_${ts}_truoc_gop.lsp"
        if (-not (Test-Path -LiteralPath $bk)) { Copy-Item -LiteralPath $dich -Destination $bk }
    }
    [IO.File]::WriteAllText($dich, (($noi -join "`r`n") + "`r`n"), $utf8)
    Write-Output "Da ghi: $dich ($($noi.Count) dong)"
}
