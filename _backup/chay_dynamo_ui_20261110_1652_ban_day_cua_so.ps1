# Mở Revit riêng bằng journal (đã mở Dynamo có giao diện + graph), tự bấm Run, chờ file kết quả rồi đóng phiên.
# Chạy nền (quy tắc 9 CLAUDE.md): mọi cửa sổ của phiên này bị đẩy ra ngoài vùng màn hình, không thu nhỏ vì cửa sổ Dynamo là cửa sổ con của Revit, thu nhỏ Revit thì Dynamo ẩn theo. -HienCuaSo: giữ cửa sổ trên màn hình khi cần xem lỗi.
param([string]$Journal, [string]$FileXong, [int]$ChoToiDa = 900, [switch]$HienCuaSo)
Add-Type -AssemblyName UIAutomationClient,UIAutomationTypes
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Threading;
public static class AnCuaSo {
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
    if (IsZoomed(h)) ShowWindowAsync(h, 4);
    RECT r; if (GetWindowRect(h, out r) && r.L > -10000) { SetWindowPos(h, IntPtr.Zero, -20000, 100, 0, 0, 0x4015); SoLanDay++; }
    return true;
  }
  public static void BatDau(int pid) {
    _pid = (uint)pid;
    Thread t = new Thread(delegate() { while (true) {
      EnumWindows(_f, IntPtr.Zero);
      uint p; GetWindowThreadProcessId(GetForegroundWindow(), out p);
      bool co = p == _pid; if (co && !_focus) SoLanChiemFocus++; _focus = co;
      Thread.Sleep(50); } });
    t.IsBackground = true; t.Start();
  }
}
"@
$A=[System.Windows.Automation.AutomationElement]
# Hộp thoại Dynamo "Open external file?" (graph ở thư mục chưa tin cậy) → tự bấm Yes (người dùng cho phép 2026-10-27)
function Bam-Yes($goc){ if(-not $goc){ return }
  $hd=$goc.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,'Open external file?')))
  if($hd){ $y=$goc.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.AndCondition((New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,'Yes')),(New-Object System.Windows.Automation.PropertyCondition($A::ControlTypeProperty,[System.Windows.Automation.ControlType]::Button)))))
    if($y){ $y.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); "Da bam Yes (Open external file)" } } }
function Bam-Yes-TienTrinh(){ if(-not $p){ return }
  foreach($w in $A::RootElement.FindAll([System.Windows.Automation.TreeScope]::Children,(New-Object System.Windows.Automation.PropertyCondition($A::ProcessIdProperty,$p.Id)))){ Bam-Yes $w } }
$p=Start-Process "C:\Program Files\Autodesk\Revit 2027\Revit.exe" -ArgumentList "`"$Journal`"" -WorkingDirectory (Split-Path $Journal) -PassThru
if(-not $HienCuaSo){ [AnCuaSo]::BatDau($p.Id) }
# Phiên chạy ẩn nên lỗi giữa chừng cũng phải đóng, không để Revit ẩn chạy mãi
trap { "LOI: $_"; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; exit 1 }
"PID $($p.Id)"
$c=New-Object System.Windows.Automation.PropertyCondition($A::ProcessIdProperty,$p.Id)
$b=$null; $t0=Get-Date
while(-not $b -and ((Get-Date)-$t0).TotalSeconds -lt $ChoToiDa){ Start-Sleep 5
  $rv=$A::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Children,$c)
  if($rv){ $dw=$rv.FindFirst([System.Windows.Automation.TreeScope]::Children,(New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,'Dynamo')))
    if($dw){ Bam-Yes $dw; Bam-Yes-TienTrinh; $b=$dw.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition($A::AutomationIdProperty,'RunButton'))) } } }
if(-not $b){ "KHONG THAY NUT RUN"; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; exit 1 }
$t2=Get-Date; while(((Get-Date)-$t2).TotalSeconds -lt 300){ Bam-Yes $dw; Bam-Yes-TienTrinh; if($b.Current.IsEnabled -and -not $dw.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition($A::NameProperty,'Open external file?')))){ break }; Start-Sleep 3 }
"Dynamo san sang sau $([int]((Get-Date)-$t0).TotalSeconds)s"; Start-Sleep 5
$b.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
$t1=Get-Date
while(((Get-Date)-$t1).TotalSeconds -lt $ChoToiDa){ Start-Sleep 5; Bam-Yes $dw; Bam-Yes-TienTrinh
  $t=$dw.FindFirst([System.Windows.Automation.TreeScope]::Descendants,(New-Object System.Windows.Automation.PropertyCondition($A::AutomationIdProperty,'runNotificationTextBlock')))
  if($t -and $t.Current.Name -match 'completed|Run completed|hoàn' -and (Test-Path $FileXong)){ break } }
"Trang thai: $($t.Current.Name) sau $([int]((Get-Date)-$t1).TotalSeconds)s"
Start-Sleep 10
"Chay nen: day cua so $([AnCuaSo]::SoLanDay) lan, chiem focus $([AnCuaSo]::SoLanChiemFocus) lan"
Stop-Process -Id $p.Id -Force
"DA DONG PHIEN"
