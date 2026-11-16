<#
.SYNOPSIS
    Chạy 1 bước của agent hs-tkbvtc trong phiên Revit RIÊNG (mặc định 2027), chạy nền (quy tắc 9): journal không mở file nào, bấm
    nút thử ARVAgentHS (ext\ của skill), nút chạy scripts\chay_hs.py với file việc -Viec; chờ bao_cao.txt có dòng XONG
    (hoặc hết giờ / 10 phút không tiến triển) rồi đóng phiên. Không gắn cứng đường dẫn máy (quy tắc 8).
.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File chay_nen.ps1 -Viec D:\AI\_tmp\hs_agent\01_HQV\viec\01_khao_sat.json
.NOTES
    Phiên bản Revit: -PhienBan <năm> -> khoá "revit" của file việc -> 2027 (người dùng 2026-11-15: FPT P5 chạy Revit 2026).
    Tìm Revit <năm>: $env:ARCHIVINA_REVIT (chỉ khi không chỉ định năm) -> registry Autodesk\Revit\<năm>
    -> <ổ cứng>:\Program Files\Autodesk\Revit <năm>. File mở đầu theo năm vì bản cũ không mở được file của bản mới:
    ext\mo_dau_<năm>.rvt (2027: ext\mo_dau.rvt).
    Tìm pyRevit CLI: $env:ARCHIVINA_PYREVIT -> %APPDATA%\pyRevit-Master\bin\pyrevit.exe -> pyrevit trong PATH.
    -HienCuaSo: giữ cửa sổ (chỉ khi người dùng đồng ý xem lỗi).
#>
param([Parameter(Mandatory = $true)][string]$Viec, [int]$ChoToiDa = 3600, [string]$PhienBan = '', [int]$ChoKhoa = 0, [int]$KhongTienTrien = 45, [int]$JournalDung = 15, [switch]$HienCuaSo, [switch]$An)
$ErrorActionPreference = 'Stop'
$skill = Split-Path -Parent $PSScriptRoot
$ext = Join-Path $skill 'ext'
$buoc = Join-Path $ext 'buoc.txt'

function Find-Revit([string]$Nam, [bool]$ChiDinh) {
    if (-not $ChiDinh -and $env:ARCHIVINA_REVIT -and (Test-Path -LiteralPath $env:ARCHIVINA_REVIT)) { return $env:ARCHIVINA_REVIT }
    foreach ($k in "HKLM:\SOFTWARE\Autodesk\Revit\$Nam", "HKLM:\SOFTWARE\Autodesk\Revit\Autodesk Revit $Nam") {
        $ds = @()
        try {
            $ds = @(Get-ChildItem $k -Recurse -ErrorAction Stop | ForEach-Object {
                (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).InstallationLocation } |
                Where-Object { $_ -and (Test-Path (Join-Path $_ 'Revit.exe')) })
        } catch {}
        if ($ds.Count) { return (Join-Path $ds[0] 'Revit.exe') }
    }
    foreach ($o in [IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'Fixed' -and $_.IsReady }) {
        $p = Join-Path $o.RootDirectory.FullName "Program Files\Autodesk\Revit $Nam\Revit.exe"
        if (Test-Path $p) { return $p }
    }
    throw "Không tìm thấy Revit $Nam (đặt biến ARCHIVINA_REVIT = đường dẫn Revit.exe)."
}

function Find-PyRevit {
    if ($env:ARCHIVINA_PYREVIT -and (Test-Path -LiteralPath $env:ARCHIVINA_PYREVIT)) { return $env:ARCHIVINA_PYREVIT }
    $p = Join-Path $env:APPDATA 'pyRevit-Master\bin\pyrevit.exe'
    if (Test-Path $p) { return $p }
    $c = Get-Command pyrevit -ErrorAction SilentlyContinue
    if ($c) { return $c.Source }
    throw 'Không tìm thấy pyRevit CLI (pyrevit.exe).'
}

$v = Get-Content -LiteralPath $Viec -Raw -Encoding UTF8 | ConvertFrom-Json
$nam = if ($PhienBan) { $PhienBan } elseif ($v.revit) { [string]$v.revit } else { '2027' }
$revit = Find-Revit $nam ([bool]($PhienBan -or $v.revit))
"Revit $nam : $revit"
$pyrevit = Find-PyRevit
$lenh = 'CustomCtrl_%CustomCtrl_%ARVAgentHS%Agent%Chay:arvagenths_arvagenths_agent_chay'
$lenhMo = 'CustomCtrl_%CustomCtrl_%ARVAgentHS%Agent%Mo:arvagenths_arvagenths_agent_mo'
$moDau = if ($nam -eq '2027') { Join-Path $ext 'mo_dau.rvt' } else { Join-Path $ext "mo_dau_$nam.rvt" }
. (Join-Path $PSScriptRoot 'cua_so_phien.ps1')

# 1 phiên Revit nền: journal (mở file mở đầu nếu có) → bấm nút agent với file việc $ViecP → chờ XONG trong $kqP\bao_cao.txt
function Chay-Phien([string]$ViecP, [string]$KqP, [string]$MoTruoc) {
    New-Item -ItemType Directory -Force -Path $KqP | Out-Null
    $baoCao = Join-Path $KqP 'bao_cao.txt'
    if (Test-Path $baoCao) { throw "Thư mục kết quả đã có bao_cao.txt ($KqP) – dùng thư mục mới cho mỗi lần chạy (không ghi đè)." }
    $journal = Join-Path $KqP 'journal_agent.txt'
    $dong = @("'Dim Jrn", 'Set Jrn = CrsJournalScript',
        '  Jrn.Directive "DebugMode", "PermissiveJournal", 1',
        '  Jrn.Directive "DebugMode", "PerformAutomaticActionInErrorDialog", 1')
    if ($MoTruoc) {
        $dong += '  Jrn.Command "Ribbon"  , "Open an existing project , ID_REVIT_FILE_OPEN"'
        $dong += "  Jrn.Data  `"File Name`"  , `"IDOK`" , `"$MoTruoc`""
    }
    $dong += "  Jrn.RibbonEvent `"Execute external command:$lenhMo`""      # nút 1 (IronPython): mở file đích, tách central
    $dong += "  Jrn.RibbonEvent `"Execute external command:$lenh`""        # nút 2 (CPython): chạy chay_hs.py
    # journal = VBScript: chỉ ASCII thì ghi ASCII (như các lần thử trước); có ký tự khác (vd. tên người dùng có dấu) thì UTF-16
    $ma = if (($dong -join '') -match '[^\x00-\x7F]') { [Text.Encoding]::Unicode } else { [Text.Encoding]::ASCII }
    [IO.File]::WriteAllLines($journal, $dong, $ma)
    $t0 = Get-Date
    $p = $null
    try {
        [IO.File]::WriteAllText($buoc, (Resolve-Path -LiteralPath $ViecP).Path, (New-Object Text.UTF8Encoding($false)))
        & $pyrevit extensions paths add $ext | Out-Null
        "Revit: $revit | việc: $ViecP | bắt đầu $(Get-Date -Format HH:mm:ss)"
        $p = Start-Process $revit -ArgumentList "`"$journal`"" -WorkingDirectory $KqP -PassThru
        Bat-CuaSoPhien -IdTienTrinh $p.Id -HienCuaSo:$HienCuaSo -An:$An
        $nTruoc = -1; $tDoi = Get-Date; $lyDo = 'hết giờ'
        # Tiến triển = dòng "=== " mới trong bao_cao.txt. Revit còn ghi journal (đang dựng đồ hoạ / chạy lõi nặng, vd. FPT P5
        # 37 link) thì chờ thêm tới -KhongTienTrien phút (mặc định 45); journal cũng đứng 15 phút thì dừng.
        $jPhien = Join-Path $KqP 'journal.0001.txt'; $jCo = -1; $tJ = Get-Date; $cpuCu = $null
        while (((Get-Date) - $t0).TotalSeconds -lt $ChoToiDa) {
            Start-Sleep 10
            if ($p.HasExited) { $lyDo = 'Revit đã thoát'; break }
            $n = 0; $xong = $false
            if (Test-Path $baoCao) {
                $n = @(Select-String -LiteralPath $baoCao -Pattern '^=== ' -Encoding UTF8).Count
                $xong = [bool](Select-String -LiteralPath $baoCao -Pattern '^XONG' -Quiet -Encoding UTF8)
            }
            if ($n -ne $nTruoc) { $nTruoc = $n; $tDoi = Get-Date; "$n bước sau $([int]((Get-Date) - $t0).TotalSeconds)s" }
            if ($xong) { $lyDo = 'xong'; break }
            $c = if (Test-Path $jPhien) { (Get-Item $jPhien).Length } else { 0 }
            if ($c -ne $jCo) { $jCo = $c; $tJ = Get-Date }
            # 2026-11-16 (G19 Side, chi tiết cửa): Revit dựng đồ hoạ lâu không ghi journal nhưng vẫn chạy CPU → tính là
            # còn tiến triển (CPU tăng ≥ 2 giây trong 10 giây). Hết CPU + journal đứng -JournalDung phút thì mới dừng.
            try { $p.Refresh(); $cpuMoi = $p.TotalProcessorTime.TotalSeconds } catch { $cpuMoi = 0 }
            if ($null -ne $cpuCu -and ($cpuMoi - $cpuCu) -ge 2) { $tJ = Get-Date }
            $cpuCu = $cpuMoi
            $giayBao = ((Get-Date) - $tDoi).TotalSeconds; $giayJ = ((Get-Date) - $tJ).TotalSeconds
            if ($giayBao -gt 60 * $JournalDung -and $giayJ -gt 60 * $JournalDung) { $lyDo = "$JournalDung phút không tiến triển (cả journal, CPU)"; break }
            if ($giayBao -gt 60 * $KhongTienTrien) { $lyDo = "$KhongTienTrien phút không có bước mới (Revit vẫn ghi journal)"; break }
        }
        "Kết thúc: $lyDo sau $([int]((Get-Date) - $t0).TotalSeconds)s"
        $script:lyDoCuoi = $lyDo
        $script:giayCuoi = [int]((Get-Date) - $t0).TotalSeconds
        Start-Sleep 5
        Bao-CuaSoPhien
    }
    finally {
        if ($p -and -not $p.HasExited) { Stop-Process -Id $p.Id -Force }
        & $pyrevit extensions paths forget $ext | Out-Null
    }
    # Journal Revit ghi trong phiên: có mượn phần tử từ central không (bản sao phải tách → phải là 0)
    # (Revit ghi journal của phiên vào thư mục làm việc = $KqP; không đọc thư mục Journals trên ổ hệ thống – quy tắc 7)
    $jr = @(Get-ChildItem $KqP -Filter 'journal*.txt' | Where-Object { $_.LastWriteTime -ge $t0 -and $_.Name -ne 'journal_agent.txt' })
    $muon = 0
    foreach ($j in $jr) { $muon += @(Select-String -LiteralPath $j.FullName -Pattern 'borrowFromCentral|IDS_OWN_ELEMENTS' -ErrorAction SilentlyContinue).Count }
    "Journal phiên: $(@($jr).Count) file, dòng mượn phần tử từ central: $muon"
    if (Test-Path $baoCao) { Get-Content -LiteralPath $baoCao -Encoding UTF8 | Where-Object { $_ -match '^(===|KIỂM TRA|CẦN HỎI|LỖI|XONG)|^      - ' } }
    else { 'KHÔNG có bao_cao.txt – nút không chạy (xem journal phiên).' }
}

$v = Get-Content -LiteralPath $Viec -Raw -Encoding UTF8 | ConvertFrom-Json
# KHOÁ: mỗi lúc chỉ 1 lần chạy (ext\buoc.txt và đường dẫn extension dùng chung). 2026-11-15 hai lần chạy chồng nhau làm
# phiên Revit 2027 bấm nhầm việc của lần chạy 2026 (tạo mo_dau_2026.rvt bằng 2027). Mutex của Windows, không tạo file;
# tiến trình chết giữa chừng thì khoá tự nhả. -ChoKhoa <phút> = chờ lần chạy kia xong (mặc định 0 = báo ngay).
$mx = New-Object Threading.Mutex($false, 'Global\ARVAgentHS_chay_nen')
$coKhoa = $false
try { $coKhoa = $mx.WaitOne([TimeSpan]::FromMinutes($ChoKhoa)) } catch [Threading.AbandonedMutexException] { $coKhoa = $true }
if (-not $coKhoa) { throw 'ĐANG CÓ lần chạy agent hs-tkbvtc khác (chay_nen.ps1) – chờ nó xong rồi chạy lại, hoặc dùng -ChoKhoa <phút>.' }
try {
    if (-not (Test-Path $moDau)) {
        # lần đầu trên máy này (theo phiên bản Revit): tạo dự án trống làm file mở đầu (xem chay_hs.py)
        $kqDau = Join-Path ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($v.ket_qua))) ('_tao_mo_dau_' + (Get-Date -Format yyyyMMdd_HHmmss))
        New-Item -ItemType Directory -Force -Path $kqDau | Out-Null
        $vDau = Join-Path $kqDau 'viec_tao_mo_dau.json'
        $j = @{ che_do = 'tao_mo_dau'; mo = $moDau; ket_qua = $kqDau; revit = $nam } | ConvertTo-Json
        [IO.File]::WriteAllText($vDau, $j, (New-Object Text.UTF8Encoding($false)))
        'Chưa có file mở đầu → tạo ' + $moDau
        Chay-Phien $vDau $kqDau ''
        if (-not (Test-Path $moDau)) { throw "Không tạo được file mở đầu $moDau (xem $kqDau\bao_cao.txt)." }
    }
    Chay-Phien $Viec $v.ket_qua $moDau
    # Bẫy pyRevit (CLAUDE.md): lần đầu nạp extension mới / vừa đổi, phiên THOÁT SỚM trước khi bấm nút → chạy lại 1 lần vào
    # <ket_qua>_lan2 (không xoá lần 1). Chỉ khi phiên tự thoát trong 3 phút; bị tắt / hết giờ thì KHÔNG chạy lại.
    if (-not (Test-Path (Join-Path $v.ket_qua 'bao_cao.txt')) -and $script:lyDoCuoi -eq 'Revit đã thoát' -and $script:giayCuoi -lt 180) {
        'Không có bao_cao.txt (phiên thoát sớm trước khi chạy nút) → chạy lại 1 lần'
        $kq2 = ($v.ket_qua.TrimEnd('\', '/')) + '_lan2'
        $v2 = Join-Path ([IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($Viec))) ([IO.Path]::GetFileNameWithoutExtension($Viec) + '_lan2.json')
        $v.ket_qua = $kq2
        [IO.File]::WriteAllText($v2, ($v | ConvertTo-Json -Depth 5), (New-Object Text.UTF8Encoding($false)))
        Chay-Phien $v2 $kq2 $moDau
    }
}
finally {
    $mx.ReleaseMutex()
}
