<#
.SYNOPSIS
    Cai moi truong Python cho cac skill ARCHIVINA tren MAY MOI (chay 1 lan, nguoi dung tu chay).

.DESCRIPTION
    Tao venv rieng, cai ezdxf, shapely, openpyxl, matplotlib (khong cai vao Python he thong):
      - co thu muc goc AI (vd. D:\AI, xem moi_truong.ps1): <goc>\_tools\venv
      - khong co: %LOCALAPPDATA%\ARCHIVINA\venv
    Can Python 3.10+ da cai san (python.org, hoac: winget install Python.Python.3.12). Script khong tu cai Python.
    venv da co thi chi cai bo sung goi con thieu, khong xoa gi.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File cai_dat_python.ps1
#>
param(
    [string]$Python = '',
    # lenh CHONGTHAM goi script nay trong cua so hien: dung lai cho nguoi dung doc truoc khi dong
    [switch]$Dung,
    # ghi ket qua "OK" / "LOI ..." ra file nay (lenh CHONGTHAM doc lai)
    [string]$KetQua = ''
)
$ErrorActionPreference = 'Stop'
try {
. (Join-Path $PSScriptRoot 'moi_truong.ps1')

$goc = Get-GocAI
$venv = if ($goc) { Join-Path $goc '_tools\venv' } else { Join-Path $env:LOCALAPPDATA 'ARCHIVINA\venv' }
$pyVenv = Join-Path $venv 'Scripts\python.exe'

if (-not (Test-Path -LiteralPath $pyVenv)) {
    $nen = $Python
    if (-not $nen) {
        $py = Get-Command py.exe -ErrorAction SilentlyContinue
        if ($py) { $nen = (& $py.Source -3 -c 'import sys; print(sys.executable)').Trim() }
    }
    if (-not $nen) {
        $c = Get-Command python.exe -All -ErrorAction SilentlyContinue | Where-Object { $_.Source -notmatch 'WindowsApps' } | Select-Object -First 1
        if ($c) { $nen = $c.Source }
    }
    if (-not $nen) { throw 'May chua co Python 3. Cai Python 3.12 (python.org hoac: winget install Python.Python.3.12) roi chay lai.' }
    Write-Host "Tao venv: $venv (tu $nen)"
    & $nen -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Tao venv loi.' }
}
Write-Host 'Cai goi: ezdxf shapely openpyxl matplotlib'
& $pyVenv -m pip install --disable-pip-version-check ezdxf shapely openpyxl matplotlib
if ($LASTEXITCODE -ne 0) { throw 'pip install loi (kiem tra mang).' }
& $pyVenv -I -c 'import ezdxf, shapely, openpyxl, matplotlib; print("OK", ezdxf.__version__, shapely.__version__)'
if ($LASTEXITCODE -ne 0) { throw 'Cai xong nhung khong import duoc goi.' }
Write-Host "Xong. Python: $pyVenv"
if ($KetQua) { Set-Content -LiteralPath $KetQua -Value 'OK' -Encoding ASCII }
}
catch {
    Write-Host ('LOI: ' + $_.Exception.Message) -ForegroundColor Red
    if ($KetQua) { Set-Content -LiteralPath $KetQua -Value ('LOI ' + $_.Exception.Message) -Encoding ASCII }
    if ($Dung) { Read-Host 'Nhan Enter de dong cua so' | Out-Null }
    exit 1
}
if ($Dung) { Read-Host 'Nhan Enter de dong cua so' | Out-Null }
