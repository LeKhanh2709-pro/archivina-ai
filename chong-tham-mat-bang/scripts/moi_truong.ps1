<#
.SYNOPSIS
    Tim moi truong tren MAY BAT KY (khong gan cung D:\AI, C:\Program Files...): thu muc goc, thu muc tam,
    AutoCAD / Core Console, Python co goi can dung. Dung chung cho cac skill ARCHIVINA (ban sao giong nhau o
    chong-tham-mat-bang, ngan-chay-truc-hkt, truc-lo-mo-mep - sua 1 file thi chep sang 2 file kia).

.DESCRIPTION
    Dot-source:  . (Join-Path $PSScriptRoot 'moi_truong.ps1')
    Thu tu tim (bien moi truong dat duoc tren tung may de ep duong dan):
      Goc AI   : $env:ARCHIVINA_AI -> thu muc cha cua ".claude" chua skill -> thu muc cha co CLAUDE.md.
                 May D:\AI: goc = D:\AI (tam D:\AI\_tmp, sao luu D:\AI\_backup nhu CLAUDE.md).
                 Khong co goc (skill dat o %USERPROFILE%\.claude): tam / sao luu o %LOCALAPPDATA%\ARCHIVINA.
      AutoCAD  : $env:ARCHIVINA_ACAD (thu muc cai) -> registry HKLM\SOFTWARE\Autodesk\AutoCAD (AcadLocation)
                 -> <o dia>\Program Files\Autodesk\AutoCAD *, <o dia>\autocad\AutoCAD *, <o dia>\Autodesk\AutoCAD *.
      Python   : -Python -> $env:ARCHIVINA_PYTHON -> goi mang theo <goc | o cung:\AI>\_tools\CHONGTHAM_python
                 -> <goc>\_tools\venv -> %LOCALAPPDATA%\ARCHIVINA\venv
                 -> py -3 -> python trong PATH. Chi nhan ban import duoc cac goi can dung.
                 Chua co: chay 1 lan cai_dat_python.ps1 (cung thu muc).
#>

function Get-GocAI {
    if ($env:ARCHIVINA_AI -and (Test-Path -LiteralPath $env:ARCHIVINA_AI -PathType Container)) {
        return (Resolve-Path -LiteralPath $env:ARCHIVINA_AI).Path.TrimEnd('\')
    }
    $nha = if ($env:USERPROFILE) { $env:USERPROFILE.TrimEnd('\') } else { '' }
    $d = $PSScriptRoot
    while ($d) {
        $dd = $d.TrimEnd('\')
        if ((Split-Path -Leaf $d) -eq '.claude') {
            $g = Split-Path -Parent $d
            # .claude cua tai khoan (%USERPROFILE%\.claude): khong lay thu muc nguoi dung lam goc
            if ($g -and $g.TrimEnd('\') -ne $nha) { return $g.TrimEnd('\') }
            return $null
        }
        # thu muc co CLAUDE.md hoac .claude\skills (vd. D:\AI). Script giai nen tu CHONGTHAM.lsp nam o
        # <goc>\_tools\chongtham_<ban>\... nen cung tim ra <goc>. Bo qua thu muc nguoi dung.
        if ($dd -ne $nha -and ((Test-Path -LiteralPath (Join-Path $d 'CLAUDE.md')) -or
                (Test-Path -LiteralPath (Join-Path $d '.claude\skills')))) { return $dd }
        $d = Split-Path -Parent $d
    }
    return $null
}

function Get-ThuMucCon([string]$Ten) {
    $g = Get-GocAI
    $t = if ($g) { Join-Path $g $Ten } else { Join-Path $env:LOCALAPPDATA ('ARCHIVINA\' + $Ten) }
    New-Item -ItemType Directory -Force -Path $t | Out-Null
    $t
}

# Thu muc tam (khong xoa sau khi chay - quy tac 1)
function Get-ThuMucTam { Get-ThuMucCon '_tmp' }
# Thu muc sao luu ban cu truoc khi sua (quy tac 2)
function Get-ThuMucBackup { Get-ThuMucCon '_backup' }

# Thu muc lam viec moi cho Core Console. Duong dan nam trong file .scr; Core Console doc .scr theo ma ANSI
# nen duong dan co dau tieng Viet (vd. ten nguoi dung co dau) se hong -> chuyen sang C:\Users\Public\ARCHIVINA_tmp.
function New-ThuMucLam([string]$Tien) {
    $tmp = Get-ThuMucTam
    if ($tmp -match '[^\x20-\x7E]') {
        $tmp = Join-Path $env:PUBLIC 'ARCHIVINA_tmp'
        New-Item -ItemType Directory -Force -Path $tmp | Out-Null
    }
    $w = Join-Path $tmp ($Tien + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $w | Out-Null
    $w
}

function Get-ODiaCoDinh {
    [IO.DriveInfo]::GetDrives() | Where-Object { $_.DriveType -eq 'Fixed' -and $_.IsReady } |
        ForEach-Object { $_.RootDirectory.FullName.TrimEnd('\') }
}

<#
  Tim AutoCAD. -Exe accoreconsole.exe (Core Console) hoac acad.exe (AutoCAD day du).
  -UuTienACA: uu tien ban co AutoCAD Architecture (giu tuong / cua ACA khi no AEC).
  Tra ve { Exe; Dir; Product } - Product = '/product ACA' neu thu muc co ACA, khong thi ''.
#>
function Find-AutoCAD([string]$Exe = 'accoreconsole.exe', [switch]$UuTienACA) {
    $dirs = New-Object System.Collections.Generic.List[string]
    if ($env:ARCHIVINA_ACAD) { $dirs.Add($env:ARCHIVINA_ACAD) }
    foreach ($r in @('HKLM:\SOFTWARE\Autodesk\AutoCAD')) {
        foreach ($ver in @(Get-ChildItem -LiteralPath $r -ErrorAction SilentlyContinue)) {
            foreach ($sp in @(Get-ChildItem -LiteralPath $ver.PSPath -ErrorAction SilentlyContinue)) {
                $loc = (Get-ItemProperty -LiteralPath $sp.PSPath -ErrorAction SilentlyContinue).AcadLocation
                if ($loc) { $dirs.Add($loc) }
            }
        }
    }
    foreach ($o in @(Get-ODiaCoDinh)) {
        foreach ($m in @('Program Files\Autodesk\AutoCAD *', 'autocad\AutoCAD *', 'Autodesk\AutoCAD *')) {
            Get-ChildItem -Path (Join-Path $o $m) -Directory -ErrorAction SilentlyContinue | ForEach-Object { $dirs.Add($_.FullName) }
        }
    }
    $ds = foreach ($d in ($dirs | ForEach-Object { $_.TrimEnd('\') } | Sort-Object -Unique)) {
        $f = Join-Path $d $Exe
        if (Test-Path -LiteralPath $f -PathType Leaf) {
            $aca = (Test-Path -LiteralPath (Join-Path $d 'ACA')) -or [bool](Get-ChildItem (Join-Path $d 'AecBase*.dbx') -ErrorAction SilentlyContinue)
            $nam = if ($d -match '(20\d\d)') { [int]$Matches[1] } else { 0 }
            [pscustomobject]@{ Exe = $f; Dir = $d; Nam = $nam; ACA = $aca; Product = $(if ($aca) { '/product ACA' } else { '' }) }
        }
    }
    if (-not $ds) {
        throw "Khong tim thay $Exe tren may. Cai AutoCAD, hoac dat bien moi truong ARCHIVINA_ACAD = thu muc cai AutoCAD (vd. D:\autocad\AutoCAD 2021)."
    }
    if ($UuTienACA) { $ds = $ds | Sort-Object @{ e = { $_.ACA }; Descending = $true }, @{ e = { $_.Nam }; Descending = $true } }
    else { $ds = $ds | Sort-Object @{ e = { $_.Nam }; Descending = $true } }
    $ds | Select-Object -First 1
}

<#
  Tim Python import duoc cac goi -Goi. Tra ve duong dan python.exe; khong co thi bao loi kem cach cai.
#>
function Find-Python([string]$Python = '', [string[]]$Goi = @('ezdxf', 'shapely')) {
    $ErrorActionPreference = 'Continue'
    $ung = New-Object System.Collections.Generic.List[string]
    if ($Python) { $ung.Add($Python) }
    if ($env:ARCHIVINA_PYTHON) { $ung.Add($env:ARCHIVINA_PYTHON) }
    # goi Python mang theo (khong cai): thu muc CHONGTHAM_python chep vao <goc>\_tools hoac <o cung>:\AI\_tools
    $g = Get-GocAI
    if ($g) { $ung.Add((Join-Path $g '_tools\CHONGTHAM_python\python.exe')) }
    foreach ($o in @(Get-ODiaCoDinh)) { $ung.Add((Join-Path $o 'AI\_tools\CHONGTHAM_python\python.exe')) }
    if ($g) { $ung.Add((Join-Path $g '_tools\venv\Scripts\python.exe')) }
    if ($env:LOCALAPPDATA) { $ung.Add((Join-Path $env:LOCALAPPDATA 'ARCHIVINA\venv\Scripts\python.exe')) }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        try { $p = & $py.Source -3 -c 'import sys; print(sys.executable)' 2>$null; if ($p) { $ung.Add(([string]$p).Trim()) } } catch {}
    }
    # bo "python.exe" gia cua Microsoft Store (WindowsApps): go la mo Store, khong chay
    Get-Command python.exe -All -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } |
        ForEach-Object { $ung.Add($_.Source) }
    $kiem = 'import ' + ($Goi -join ', ')
    foreach ($c in ($ung | Select-Object -Unique)) {
        if (-not (Test-Path -LiteralPath $c -PathType Leaf)) { continue }
        try { & $c -I -c $kiem 2>$null | Out-Null; if ($LASTEXITCODE -eq 0) { return $c } } catch {}
    }
    throw ("Khong tim thay Python co goi " + ($Goi -join ', ') + ". Chep thu muc CHONGTHAM_python (goi Python mang theo, khong cai) vao " +
        "<o>:\AI\_tools\, hoac chay 1 lan: powershell -NoProfile -ExecutionPolicy Bypass -File `"" +
        (Join-Path $PSScriptRoot 'cai_dat_python.ps1') + "`" (hoac dat bien moi truong ARCHIVINA_PYTHON = duong dan python.exe).")
}
