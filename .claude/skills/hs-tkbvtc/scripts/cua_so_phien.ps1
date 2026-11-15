# Điều khiển cửa sổ của phiên Revit / phần mềm Claude tự mở (quy tắc 9 CLAUDE.md, sửa 2026-11-15).
# Dot-source rồi gọi:  Bat-CuaSoPhien -IdTienTrinh <pid> [-HienCuaSo] [-An]   …   Bao-CuaSoPhien
#  - Mặc định (máy có màn hình phụ): mọi cửa sổ của PID lấn sang màn hình chính bị dời sang màn hình phụ
#    (ưu tiên \\.\DISPLAY2), không làm trong suốt / không cắt vùng hiển thị. Dời không ăn sau 20 lần thì cửa sổ đó
#    mới bị ẩn (trong suốt + vùng rỗng) như cách cũ.
#  - Không có màn hình phụ, hoặc -An: ẩn như cách cũ (trong suốt + vùng rỗng + đẩy ra ngoài màn hình).
#  - Cả 2 chế độ: phiên chiếm focus thì trả focus về ứng dụng người dùng đang dùng; đếm số lần lộ trên màn hình chính.
#  - -HienCuaSo: không đụng gì (giữ cửa sổ khi cần xem lỗi).
Add-Type -AssemblyName System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Threading; using System.Text; using System.Collections.Generic;
public static class CuaSoPhien {
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
  public struct RECT { public int L, T, R, B; }
  public struct POINT { public int X, Y; }
  delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern bool IsZoomed(IntPtr h);
  [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] static extern bool ShowWindowAsync(IntPtr h, int n);
  [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int cx, int cy, uint f);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern int SetWindowRgn(IntPtr h, IntPtr r, bool d);
  [DllImport("user32.dll")] static extern int GetWindowRgn(IntPtr h, IntPtr r);
  [DllImport("gdi32.dll")] static extern IntPtr CreateRectRgn(int a, int b, int c, int d);
  [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr o);
  [DllImport("user32.dll")] static extern IntPtr WindowFromPoint(POINT p);

  public static int SoLanDay = 0, SoLanChiemFocus = 0, SoLanTraFocus = 0, SoLanQuet = 0, SoLanLo = 0, SoCuaSoPhaiAn = 0;
  static uint _pid; static bool _focus = false; static IntPtr _khac = IntPtr.Zero;
  static bool _manHinhPhu;                    // true = dời sang màn hình phụ, false = ẩn như cũ
  static int _cX, _cY, _cW, _cH;              // màn hình chính (bounds)
  static int _pX, _pY, _pW, _pH;              // vùng làm việc màn hình phụ
  static Dictionary<long, int> _dem = new Dictionary<long, int>();
  static Dictionary<long, string> _ten = new Dictionary<long, string>();
  static HashSet<long> _daAn = new HashSet<long>();

  static bool DaTrongSuot(IntPtr h) { uint k, f; byte a; return (GetEx(h, -20).ToInt64() & 0x80020) == 0x80020 && GetLayeredWindowAttributes(h, out k, out a, out f) && (f & 2) != 0 && a == 0; }
  static void LamTrongSuot(IntPtr h) { if (DaTrongSuot(h)) return; SetEx(h, -20, new IntPtr(GetEx(h, -20).ToInt64() | 0x80020)); SetLayeredWindowAttributes(h, 0, 0, 2); }
  static bool VungRong(IntPtr h) { IntPtr r = CreateRectRgn(0, 0, 0, 0); int t = GetWindowRgn(h, r); DeleteObject(r); return t == 1; }
  static void LamVungRong(IntPtr h) { if (!VungRong(h)) SetWindowRgn(h, CreateRectRgn(0, 0, 0, 0), false); }
  static int Dem(IntPtr h) { int c; lock (_dem) { _dem.TryGetValue(h.ToInt64(), out c); } return c; }
  static void Ghi(IntPtr h, bool cong) { long k = h.ToInt64(); lock (_dem) {
    int c; _dem.TryGetValue(k, out c); _dem[k] = cong ? c + 1 : c;
    if (!_ten.ContainsKey(k)) { StringBuilder a = new StringBuilder(128), b = new StringBuilder(128); GetClassName(h, a, 128); GetWindowText(h, b, 128); _ten[k] = a + " | " + b; } } }
  static bool LanManHinhChinh(RECT r) { return r.R - r.L > 0 && r.B - r.T > 0 && r.L < _cX + _cW && r.R > _cX && r.T < _cY + _cH && r.B > _cY; }

  static EnumProc _f = Xet;
  static bool Xet(IntPtr h, IntPtr l) {
    uint p; GetWindowThreadProcessId(h, out p);
    if (p != _pid || !IsWindowVisible(h)) return true;
    if (!_manHinhPhu) {                       // cách cũ: ẩn hẳn
      LamTrongSuot(h); LamVungRong(h);
      if (Dem(h) >= 5) { Ghi(h, false); return true; }
      if (IsZoomed(h)) ShowWindowAsync(h, 4);
      RECT q; Ghi(h, false); if (GetWindowRect(h, out q) && q.L > -10000) { SetWindowPos(h, IntPtr.Zero, -20000, 100, 0, 0, 0x4015); SoLanDay++; Ghi(h, true); }
      return true;
    }
    if (IsIconic(h)) return true;
    RECT r; if (!GetWindowRect(h, out r)) return true;
    Ghi(h, false);
    if (!LanManHinhChinh(r)) return true;     // đã ở màn hình phụ / ngoài màn hình chính: để yên
    if (Dem(h) >= 20) {                       // Revit cứ kéo về màn hình chính → ẩn riêng cửa sổ này
      if (!_daAn.Contains(h.ToInt64())) { _daAn.Add(h.ToInt64()); SoCuaSoPhaiAn++; }
      LamTrongSuot(h); LamVungRong(h); return true;
    }
    if (IsZoomed(h)) { ShowWindowAsync(h, 4); Ghi(h, true); return true; }   // bỏ phóng to (không lấy focus), vòng sau dời
    int w = r.R - r.L, c = r.B - r.T; uint f = 0x4015;                        // ASYNC | NOACTIVATE | NOZORDER | NOSIZE
    if (w > _pW || c > _pH) { w = Math.Min(w, _pW); c = Math.Min(c, _pH); f = 0x4014; }
    SetWindowPos(h, IntPtr.Zero, _pX + (_pW - w) / 2, _pY + (_pH - c) / 2, w, c, f);
    SoLanDay++; Ghi(h, true);
    return true;
  }
  static void DoManHinhChinh() { bool lo = false;
    for (int i = 0; i < 5; i++) for (int j = 0; j < 5; j++) { POINT p; p.X = _cX + _cW * (2 * i + 1) / 10; p.Y = _cY + _cH * (2 * j + 1) / 10; uint q; IntPtr a = WindowFromPoint(p); if (a != IntPtr.Zero) { GetWindowThreadProcessId(a, out q); if (q == _pid) lo = true; } }
    SoLanQuet++; if (lo) SoLanLo++; }

  public static void BatDau(int pid, bool manHinhPhu, int cX, int cY, int cW, int cH, int pX, int pY, int pW, int pH) {
    _pid = (uint)pid; _manHinhPhu = manHinhPhu;
    _cX = cX; _cY = cY; _cW = cW; _cH = cH; _pX = pX; _pY = pY; _pW = pW; _pH = pH;
    Thread t = new Thread(delegate() { while (true) {
      try {
        EnumWindows(_f, IntPtr.Zero);
        IntPtr fg = GetForegroundWindow(); uint p; uint tfg = GetWindowThreadProcessId(fg, out p);
        bool co = p == _pid; if (co && !_focus) SoLanChiemFocus++; _focus = co;
        if (!co && fg != IntPtr.Zero) _khac = fg;
        if (co && _khac != IntPtr.Zero && IsWindow(_khac)) { uint me = GetCurrentThreadId(); AttachThreadInput(me, tfg, true); if (SetForegroundWindow(_khac)) SoLanTraFocus++; AttachThreadInput(me, tfg, false); }
        DoManHinhChinh();
      } catch { }
      Thread.Sleep(50); } });
    t.IsBackground = true; t.Start();
  }
  public static string BaoCao() { StringBuilder s = new StringBuilder(); lock (_dem) { foreach (KeyValuePair<long, int> kv in _dem) {
    IntPtr h = new IntPtr(kv.Key); RECT r; string vt = "da dong";
    if (IsWindow(h) && GetWindowRect(h, out r)) vt = r.L + "," + r.T + " " + (r.R - r.L) + "x" + (r.B - r.T) + (IsWindowVisible(h) ? " hien" : " an")
      + (LanManHinhChinh(r) ? " LAN-MAN-HINH-CHINH" : "") + (DaTrongSuot(h) ? " trong-suot" : "") + (VungRong(h) ? " vung-rong" : "");
    s.Append("  " + kv.Value + " lan | " + vt + " | " + _ten[kv.Key] + "\n"); } } return s.ToString(); }
}
"@

$script:CheDoCuaSo = "giu nguyen (HienCuaSo)"
function Bat-CuaSoPhien([int]$IdTienTrinh, [switch]$HienCuaSo, [switch]$An) {
    $Pid_ = $IdTienTrinh
    if ($HienCuaSo) { return }
    $chinh = [System.Windows.Forms.Screen]::PrimaryScreen
    $phu = @([System.Windows.Forms.Screen]::AllScreens | Where-Object { -not $_.Primary })
    $mh = $phu | Where-Object { $_.DeviceName -match 'DISPLAY2$' } | Select-Object -First 1
    if (-not $mh) { $mh = $phu | Select-Object -First 1 }
    $c = $chinh.Bounds
    if ($mh -and -not $An) {
        $w = $mh.WorkingArea
        [CuaSoPhien]::BatDau($Pid_, $true, $c.X, $c.Y, $c.Width, $c.Height, $w.X, $w.Y, $w.Width, $w.Height)
        $script:CheDoCuaSo = "man hinh phu $($mh.DeviceName) ($($w.X),$($w.Y) $($w.Width)x$($w.Height))"
    } else {
        [CuaSoPhien]::BatDau($Pid_, $false, $c.X, $c.Y, $c.Width, $c.Height, 0, 0, 0, 0)
        $script:CheDoCuaSo = "an cua so" + $(if (-not $mh) { " (khong co man hinh phu)" } else { "" })
    }
    "Che do cua so: $script:CheDoCuaSo"
}
function Bao-CuaSoPhien {
    "Chay nen [$script:CheDoCuaSo]: doi / day cua so $([CuaSoPhien]::SoLanDay) lan, phai an $([CuaSoPhien]::SoCuaSoPhaiAn) cua so, chiem focus $([CuaSoPhien]::SoLanChiemFocus) lan, tra focus $([CuaSoPhien]::SoLanTraFocus) lan, lo tren man hinh chinh $([CuaSoPhien]::SoLanLo)/$([CuaSoPhien]::SoLanQuet) lan quet"
    [CuaSoPhien]::BaoCao()
}
