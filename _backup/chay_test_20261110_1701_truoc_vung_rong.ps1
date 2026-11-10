# Mở Revit 2027 bằng journal, chờ file báo cáo có dòng XONG (hoặc hết giờ) rồi đóng phiên.
param([string]$Journal = "D:\AI\_tmp\pyrevit_test\journal_runall.txt",
      [string]$BaoCao = "D:\AI\_tmp\pyrevit_test\ket_qua.txt", [int]$ChoToiDa = 1500, [switch]$HienCuaSo)
# Chay nen (quy tac 9 CLAUDE.md): cung cach voi revit_g19\chay_dynamo_ui.ps1; -HienCuaSo = giu cua so khi can xem loi.
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Threading; using System.Text; using System.Collections.Generic;
public static class AnCuaSo {
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool AttachThreadInput(uint a, uint b, bool f);
  [DllImport("user32.dll")] static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] static extern bool IsWindow(IntPtr h);
  [DllImport("kernel32.dll")] static extern uint GetCurrentThreadId();
  [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")] static extern IntPtr GetEx(IntPtr h, int i);
  [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW")] static extern IntPtr SetEx(IntPtr h, int i, IntPtr v);
  [DllImport("user32.dll")] static extern bool SetLayeredWindowAttributes(IntPtr h, uint k, byte a, uint f);
  [DllImport("user32.dll")] static extern bool GetLayeredWindowAttributes(IntPtr h, out uint k, out byte a, out uint f);
  static bool DaTrongSuot(IntPtr h) { uint k, f; byte a; return (GetEx(h, -20).ToInt64() & 0x80020) == 0x80020 && GetLayeredWindowAttributes(h, out k, out a, out f) && (f & 2) != 0 && a == 0; }
  static void LamTrongSuot(IntPtr h) { if (DaTrongSuot(h)) return; SetEx(h, -20, new IntPtr(GetEx(h, -20).ToInt64() | 0x80020)); SetLayeredWindowAttributes(h, 0, 0, 2); }
  static int Dem(IntPtr h) { int c; lock (_dem) { _dem.TryGetValue(h.ToInt64(), out c); } return c; }
  static Dictionary<long, int> _dem = new Dictionary<long, int>();
  static Dictionary<long, string> _ten = new Dictionary<long, string>();
  static IntPtr _khac = IntPtr.Zero;
  public static int SoLanTraFocus = 0;
  static void Ghi(IntPtr h, bool cong) { long k = h.ToInt64(); lock (_dem) {
    int c; _dem.TryGetValue(k, out c); _dem[k] = cong ? c + 1 : c;
    if (!_ten.ContainsKey(k)) { StringBuilder a = new StringBuilder(128), b = new StringBuilder(128); GetClassName(h, a, 128); GetWindowText(h, b, 128); _ten[k] = a + " | " + b; } } }
  public static string BaoCao() { StringBuilder s = new StringBuilder(); lock (_dem) { foreach (KeyValuePair<long, int> kv in _dem) {
    IntPtr h = new IntPtr(kv.Key); RECT r; string vt = "da dong";
    if (IsWindow(h) && GetWindowRect(h, out r)) vt = r.L + "," + r.T + " " + (r.R - r.L) + "x" + (r.B - r.T) + (IsWindowVisible(h) ? " hien" : " an") + (DaTrongSuot(h) ? " trong-suot" : " CHUA-TRONG-SUOT");
    s.Append("  " + kv.Value + " lan | " + vt + " | " + _ten[kv.Key] + "\n"); } } return s.ToString(); }
  public struct RECT { public int L, T, R, B; }
  delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern bool IsZoomed(IntPtr h);
  [DllImport("user32.dll")] static extern bool ShowWindowAsync(IntPtr h, int n);
  [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  public static int SoLanDay = 0, SoLanChiemFocus = 0;
  static uint _pid; static bool _focus = false;
  static EnumProc _f = Xet;
  static bool Xet(IntPtr h, IntPtr l) {
    uint p; GetWindowThreadProcessId(h, out p);
    if (p != _pid || !IsWindowVisible(h)) return true;
    LamTrongSuot(h);
    if (Dem(h) >= 5) { Ghi(h, false); return true; }
    if (IsZoomed(h)) ShowWindowAsync(h, 4);
    RECT r; Ghi(h, false); if (GetWindowRect(h, out r) && r.L > -10000) { SetWindowPos(h, IntPtr.Zero, -20000, 100, 0, 0, 0x4015); SoLanDay++; Ghi(h, true); }
    return true;
  }
  public static void BatDau(int pid) {
    _pid = (uint)pid;
    Thread t = new Thread(delegate() { while (true) {
      EnumWindows(_f, IntPtr.Zero);
      IntPtr fg = GetForegroundWindow(); uint p; uint tfg = GetWindowThreadProcessId(fg, out p);
      bool co = p == _pid; if (co && !_focus) SoLanChiemFocus++; _focus = co;
      if (!co && fg != IntPtr.Zero) _khac = fg;
      if (co && _khac != IntPtr.Zero && IsWindow(_khac)) { uint me = GetCurrentThreadId(); AttachThreadInput(me, tfg, true); if (SetForegroundWindow(_khac)) SoLanTraFocus++; AttachThreadInput(me, tfg, false); }
      Thread.Sleep(50); } });
    t.IsBackground = true; t.Start();
  }
}
"@
if (Test-Path $BaoCao) { Rename-Item $BaoCao ("ket_qua_" + (Get-Date -Format yyyyMMdd_HHmmss) + ".txt") }
$p = Start-Process "C:\Program Files\Autodesk\Revit 2027\Revit.exe" -ArgumentList "`"$Journal`"" -WorkingDirectory (Split-Path $Journal) -PassThru
if (-not $HienCuaSo) { [AnCuaSo]::BatDau($p.Id) }
trap { "LOI: $_"; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; exit 1 }
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
"Chay nen: day cua so $([AnCuaSo]::SoLanDay) lan, chiem focus $([AnCuaSo]::SoLanChiemFocus) lan, tra focus $([AnCuaSo]::SoLanTraFocus) lan"
[AnCuaSo]::BaoCao()
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
"DA DONG PHIEN"
