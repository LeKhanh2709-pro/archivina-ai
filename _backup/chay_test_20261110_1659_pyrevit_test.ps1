# Mở Revit 2027 bằng journal, chờ file báo cáo có dòng XONG (hoặc hết giờ) rồi đóng phiên.
param([string]$Journal = "D:\AI\_tmp\pyrevit_test\journal_runall.txt",
      [string]$BaoCao = "D:\AI\_tmp\pyrevit_test\ket_qua.txt", [int]$ChoToiDa = 1500)
if (Test-Path $BaoCao) { Rename-Item $BaoCao ("ket_qua_" + (Get-Date -Format yyyyMMdd_HHmmss) + ".txt") }
$p = Start-Process "C:\Program Files\Autodesk\Revit 2027\Revit.exe" -ArgumentList "`"$Journal`"" -WorkingDirectory (Split-Path $Journal) -PassThru
"PID $($p.Id) luc $(Get-Date -Format HH:mm:ss)"
$t0 = Get-Date; $nTruoc = -1; $tDoi = Get-Date; $lyDo = "het gio"
while (((Get-Date) - $t0).TotalSeconds -lt $ChoToiDa) {
  Start-Sleep 10
  if ($p.HasExited) { $lyDo = "Revit da thoat"; break }
  $n = 0; $xong = $false
  if (Test-Path $BaoCao) {
    $n = @(Select-String -Path $BaoCao -Pattern '^=== ').Count
    $xong = [bool](Select-String -Path $BaoCao -Pattern '^XONG' -Quiet)
  }
  if ($n -ne $nTruoc) { $nTruoc = $n; $tDoi = Get-Date; "$n nut sau $([int]((Get-Date)-$t0).TotalSeconds)s" }
  if ($xong) { $lyDo = "xong"; break }
  if (((Get-Date) - $tDoi).TotalSeconds -gt 600) { $lyDo = "10 phut khong co tien trien"; break }
}
"Ket thuc: $lyDo sau $([int]((Get-Date)-$t0).TotalSeconds)s"
Start-Sleep 5
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
"DA DONG PHIEN"
