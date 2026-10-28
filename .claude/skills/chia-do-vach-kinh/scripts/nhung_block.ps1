<#
.SYNOPSIS
    Doc block VK_* trong assets\VK_thu_vien.dwg bang AutoCAD day du (acad.exe /b), ghi du lieu entmake ra lisp\vk_du_lieu.lsp
    de gop_vk.py nhung vao VK.lsp (VK.lsp tu tao block, khong can file thu vien ngoai - nguoi dung chot 28/10/2026).

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File nhung_block.ps1
#>
param([int]$TimeoutSec = 300)
$ErrorActionPreference = 'Stop'

# AutoCAD / thu muc tam tu tim tren may (moi_truong.ps1), khong gan cung duong dan
. (Join-Path $PSScriptRoot 'moi_truong.ps1')
$acad = Find-AutoCAD -Exe 'acad.exe'
$skill = Split-Path -Parent $PSScriptRoot
$tv = Join-Path $skill 'assets\VK_thu_vien.dwg'
$out = Join-Path $skill 'lisp\vk_du_lieu.lsp'
if (-not (Test-Path -LiteralPath $tv)) { throw "Khong thay thu vien: $tv" }

# thu muc tam (quy tac 7), khong xoa sau khi chay (quy tac 1)
$work = New-ThuMucLam 'vk_nhung_'
Copy-Item -LiteralPath $tv -Destination (Join-Path $work 'src.dwg')
$fw = $work.Replace('\', '/')

# Chep LISP thang vao .scr (SECURELOAD chan load ngoai thu muc tin cay), bo dong trong va dong chu thich
$ham = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'xuat_du_lieu_block.lsp') -Encoding UTF8 |
    Where-Object { $_.Trim() -ne '' -and -not $_.Trim().StartsWith(';') }
$lines = @($ham) + @("(dl:xuat `"$fw/vk_du_lieu.lsp`")", '_.QUIT', '_N')
Set-Content -Path (Join-Path $work 'run.scr') -Value ($lines -join "`r`n") -Encoding UTF8

$p = Start-Process -FilePath $acad.Exe -WorkingDirectory $work -WindowStyle Minimized -PassThru `
    -ArgumentList "/nologo `"$work\src.dwg`" /b `"$work\run.scr`""
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); throw "Qua $TimeoutSec giay, da dung AutoCAD. Thu muc tam: $work" }
$kq = Join-Path $work 'vk_du_lieu.lsp'
if (-not (Test-Path -LiteralPath $kq)) { throw "Khong tao duoc du lieu. Xem $work" }
# file sinh tu dong: chep de len ban cu (ban cu da sinh tu cung nguon, khong phai du lieu nguoi dung)
Copy-Item -LiteralPath $kq -Destination $out -Force
Write-Output $out
Write-Output "Thu muc tam giu lai: $work"
