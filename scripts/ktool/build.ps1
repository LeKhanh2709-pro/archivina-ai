<#
.SYNOPSIS
    Build K-TOOL.dll (tab ribbon K-TOOL) và sinh K-TOOL.lsp, chép cả hai vào scripts\lisp.

.DESCRIPTION
    Cần .NET 10 SDK (AutoCAD 2027 chạy .NET 10) và AutoCAD 2027 để lấy DLL tham chiếu.
    File cũ trong scripts\lisp được chép vào <gốc>\_backup\<tên>_<yyyyMMdd_HHmm>.<đuôi> trước khi ghi đè.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File build.ps1 -AcadDir "C:\Program Files\Autodesk\AutoCAD 2027"
#>
param([string]$AcadDir = '')
$ErrorActionPreference = 'Stop'

$goc = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$dich = Join-Path $goc 'scripts\lisp'
$backup = Join-Path $goc '_backup'
$tg = Get-Date -Format 'yyyyMMdd_HHmm'

$dotnet = (Get-Command dotnet -ErrorAction SilentlyContinue).Source
if (-not $dotnet) { $dotnet = Join-Path $env:ProgramW6432 'dotnet\dotnet.exe' }
if (-not (Test-Path -LiteralPath $dotnet)) { throw 'Khong thay dotnet (.NET 10 SDK).' }
$py = Join-Path $goc '_tools\venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }
if (-not $py) { throw 'Khong thay Python.' }

# NuGet / file tạm của build để trong <gốc>\_tmp, không dùng ổ hệ thống
$env:NUGET_PACKAGES = Join-Path $goc '_tmp\nuget'
$env:DOTNET_CLI_TELEMETRY_OPTOUT = '1'
$env:DOTNET_NOLOGO = '1'

$arg = @('build', (Join-Path $PSScriptRoot 'KTool.csproj'), '-c', 'Release', '-nologo', '-v', 'minimal', '-nowarn:MSB3277')
if ($AcadDir) { $arg += "-p:AcadDir=$AcadDir" }
& $dotnet @arg
if ($LASTEXITCODE -ne 0) { throw "Build loi (ma $LASTEXITCODE)." }

# -Chuyen: chuyển (không chép) bản cũ vào _backup. DLL đang được AutoCAD nạp thì bị khoá ghi nhưng vẫn
# chuyển được trong cùng ổ đĩa; AutoCAD dùng bản cũ tới khi mở lại.
function Sao-Luu([string]$f, [switch]$Chuyen) {
    if (Test-Path -LiteralPath $f) {
        $ten = [IO.Path]::GetFileNameWithoutExtension($f); $duoi = [IO.Path]::GetExtension($f)
        $bk = Join-Path $backup "${ten}_$tg$duoi"
        # Đã có bản sao lưu trong cùng phút -> thêm giây, không ghi đè bản sao lưu cũ
        if (Test-Path -LiteralPath $bk) { $bk = Join-Path $backup "${ten}_$tg$(Get-Date -Format 'ss')$duoi" }
        if ($Chuyen) { Move-Item -LiteralPath $f -Destination $bk } else { Copy-Item -LiteralPath $f -Destination $bk }
    }
}

$dll = Join-Path $dich 'K-TOOL.dll'
$lsp = Join-Path $dich 'K-TOOL.lsp'
Sao-Luu $dll -Chuyen
Sao-Luu $lsp
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net10.0-windows\K-TOOL.dll') -Destination $dll -Force
& $py (Join-Path $PSScriptRoot 'gop_ktool.py') $lsp
if ($LASTEXITCODE -ne 0) { throw 'Sinh K-TOOL.lsp loi.' }
Write-Output "Xong: $dll"
Write-Output "      $lsp"
