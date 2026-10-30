// K-TOOL.dll — thêm tab ribbon "K-TOOL" vào AutoCAD. Các file LISP Archivina được NHÚNG SẴN trong DLL
// (xem KTool.csproj). Nạp DLL là nạp luôn mọi lệnh LISP vào bản vẽ đang mở, và vào mỗi bản vẽ khác ở lần đầu
// bản vẽ đó được kích hoạt (LISP riêng từng bản vẽ) -> nút và lệnh gõ tay (VK, MDVK...) dùng được ngay.
// Bấm nút -> chạy lệnh; bản vẽ nào chưa có lệnh (nạp lỗi) thì nạp lại file đó trước.
// Máy khác chỉ cần chép K-TOOL.dll. Không sửa file CUIx của máy: tab tạo lại mỗi lần nạp DLL.
// Lệnh: KTOOLTAB (thêm lại tab nếu bị mất, vd. sau khi đổi workspace).
// Sửa file LISP trong scripts\lisp thì phải chạy lại scripts\ktool\build.ps1 để nút dùng bản mới.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.Runtime;
using Autodesk.Windows;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

[assembly: ExtensionApplication(typeof(KTool.KToolApp))]
[assembly: CommandClass(typeof(KTool.KToolApp))]

namespace KTool
{
    // Nút: tên lệnh c: trong file LISP, file LISP nhúng, nhãn, chú thích, ký hiệu biểu tượng (BieuTuong.cs)
    record Nut(string Lenh, string FileLisp, string Nhan, string ChuThich, string Ky);

    public class KToolApp : IExtensionApplication
    {
        const string TabId = "ARCHIVINA_KTOOL_TAB";

        // Panel: tiêu đề + các nút
        static readonly (string Tieu, Nut[] Nuts)[] Panels =
        {
            ("Vách kính", new[]
            {
                new Nut("VK", "VK.lsp", "Vách kính", "VK: chia đố và dựng vách kính mặt bằng", "VK"),
                new Nut("MDVK", "VKMD.lsp", "Mặt đứng VK", "MDVK: dựng mặt đứng vách kính từ block VACH KINH", "MĐ"),
            }),
            ("Trục kỹ thuật", new[]
            {
                new Nut("LOMO", "Lomo.lsp", "Lỗ mở MEP", "LOMO: chèn block A-MEP cho trục / hộp kỹ thuật", "LM"),
                new Nut("NCL", "fire_stop_shaft.lsp", "Ngăn cháy lan", "NCL: vẽ bo + hatch ngăn cháy lan, không hỏi trước", "NC"),
            }),
            ("Chống thấm", new[]
            {
                new Nut("CHONGTHAM", "CHONGTHAM.lsp", "Chống thấm", "CHONGTHAM: vẽ mặt bằng chống thấm (WC, lô gia, phòng rác...)", "CT"),
            }),
        };

        internal static string ThuMucDll => Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);

        // Các bản vẽ đã được gửi lệnh nạp LISP (mỗi bản vẽ một lần)
        static readonly HashSet<Document> DaNapLisp = new HashSet<Document>();

        public void Initialize()
        {
            Ghi($"đã nạp {Assembly.GetExecutingAssembly().Location}");
            try
            {
                if (ComponentManager.Ribbon != null) TaoTab();
                else
                {
                    Ghi("ribbon chưa sẵn sàng, chờ ribbon dựng xong rồi thêm tab");
                    ComponentManager.ItemInitialized += KhiRibbonSanSang;
                }
                AcApp.SystemVariableChanged += KhiDoiBien;

                DocumentCollection dm = AcApp.DocumentManager;
                dm.DocumentActivated += (s, e) => NapLisp(e.Document);
                dm.DocumentToBeDestroyed += (s, e) => DaNapLisp.Remove(e.Document);
                NapLisp(dm.MdiActiveDocument);
            }
            catch (System.Exception ex) { Ghi("lỗi khi khởi tạo: " + ex); }
        }

        // Nạp mọi file LISP nhúng vào bản vẽ (nếu bản vẽ chưa có lệnh của file đó)
        static void NapLisp(Document doc)
        {
            if (doc == null || !DaNapLisp.Add(doc)) return;
            try
            {
                var sb = new StringBuilder("(progn");
                var lenh = new List<string>();
                var daCo = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
                foreach (var (_, nuts) in Panels)
                    foreach (Nut n in nuts)
                    {
                        lenh.Add(n.Lenh);
                        if (!daCo.Add(n.FileLisp)) continue;
                        string f = ChayLisp.LayFileLisp(n.FileLisp);
                        sb.Append($" (if (not c:{n.Lenh}) (load \"{ChayLisp.ChuoiLisp(f)}\" nil))");
                    }
                string ds = string.Join(", ", lenh);
                sb.Append($" (princ \"{ChayLisp.ChuoiLisp($"\nK-TOOL: đã nạp sẵn các lệnh {ds}.")}\") (princ))\n");
                Ghi($"nạp sẵn LISP vào {doc.Name}", false);
                doc.SendStringToExecute(sb.ToString(), true, false, false);
            }
            catch (System.Exception ex) { Ghi("lỗi khi nạp sẵn LISP: " + ex); }
        }

        public void Terminate() { }

        // Thông báo ra dòng lệnh và ghi K-TOOL.log cạnh DLL (để người dùng gửi lại khi có lỗi)
        internal static void Ghi(string s, bool raDongLenh = true)
        {
            if (raDongLenh)
                try { AcApp.DocumentManager.MdiActiveDocument?.Editor.WriteMessage("\nK-TOOL: " + s); } catch { }
            try
            {
                File.AppendAllText(Path.Combine(ThuMucDll, "K-TOOL.log"),
                    $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {s}{Environment.NewLine}");
            }
            catch { }
        }

        // Ribbon chưa dựng xong lúc nạp DLL (nạp khi khởi động) -> chờ rồi mới thêm tab
        static void KhiRibbonSanSang(object sender, RibbonItemEventArgs e)
        {
            if (ComponentManager.Ribbon == null) return;
            ComponentManager.ItemInitialized -= KhiRibbonSanSang;
            TaoTab();
        }

        // Đổi workspace thì ribbon dựng lại và mất tab tự thêm -> thêm lại
        static void KhiDoiBien(object sender, SystemVariableChangedEventArgs e)
        {
            if (string.Equals(e.Name, "WSCURRENT", StringComparison.OrdinalIgnoreCase)) TaoTab();
        }

        [CommandMethod("KTOOLTAB")]
        public void LenhTab()
        {
            TaoTab();
            RibbonTab tab = ComponentManager.Ribbon?.FindTab(TabId);
            if (tab != null) tab.IsActive = true;
            else Ghi("không thấy tab sau khi tạo (ribbon đang tắt? gõ RIBBON để bật)");
        }

        static void TaoTab()
        {
            try { TaoTabLoi(); }
            catch (System.Exception ex) { Ghi("lỗi khi tạo tab: " + ex); }
        }

        static void TaoTabLoi()
        {
            RibbonControl rb = ComponentManager.Ribbon;
            if (rb == null) { Ghi("chưa có ribbon (gõ RIBBON để bật rồi gõ KTOOLTAB)"); return; }
            if (rb.FindTab(TabId) != null) return;

            var tab = new RibbonTab { Title = "K-TOOL", Id = TabId };
            foreach (var (tieu, nuts) in Panels)
            {
                var src = new RibbonPanelSource { Title = tieu };
                foreach (Nut n in nuts)
                {
                    src.Items.Add(new RibbonButton
                    {
                        Text = n.Nhan,
                        ShowText = true,
                        ShowImage = true,
                        Size = RibbonItemSize.Large,
                        Orientation = Orientation.Vertical,
                        LargeImage = BieuTuong.Ve(n.Ky, 32),
                        Image = BieuTuong.Ve(n.Ky, 16),
                        ToolTip = n.ChuThich,
                        CommandParameter = n,
                        CommandHandler = new ChayLisp(),
                    });
                }
                tab.Panels.Add(new RibbonPanel { Source = src });
            }
            rb.Tabs.Add(tab);
            Ghi("đã thêm tab K-TOOL trên ribbon");
        }
    }

    // Bấm nút: huỷ lệnh đang chạy rồi gọi (c:<lệnh>); bản vẽ chưa có lệnh (nạp sẵn bị lỗi / bị chặn) thì nạp lại file
    class ChayLisp : ICommand
    {
        public event EventHandler CanExecuteChanged { add { } remove { } }

        public bool CanExecute(object parameter) => true;

        public void Execute(object parameter)
        {
            try
            {
                Nut n = (parameter as RibbonButton)?.CommandParameter as Nut;
                if (n == null) { KToolApp.Ghi($"nút không có dữ liệu lệnh ({parameter?.GetType().FullName ?? "null"})"); return; }
                Document doc = AcApp.DocumentManager.MdiActiveDocument;
                if (doc == null) { KToolApp.Ghi("chưa có bản vẽ nào đang mở"); return; }

                string f = LayFileLisp(n.FileLisp);
                string lisp =
                    "(progn" +
                    $" (if (not c:{n.Lenh}) (load \"{ChuoiLisp(f)}\" nil))" +
                    $" (if c:{n.Lenh} (c:{n.Lenh}) (princ \"{ChuoiLisp($"\nK-TOOL: không nạp được {f} (SECURELOAD chặn? thêm thư mục vào Trusted Locations)")}\"))" +
                    " (princ))\n";
                KToolApp.Ghi($"bấm {n.Lenh}: {f}", false);
                doc.SendStringToExecute("\x03\x03" + lisp, true, false, false);
            }
            catch (System.Exception ex) { KToolApp.Ghi("lỗi khi bấm nút: " + ex); }
        }

        // File LISP để nạp: dùng file cạnh DLL nếu giống hệt bản nhúng, không thì ghi bản nhúng ra thư mục
        // K-TOOL_lisp cạnh DLL (không ghi được thì %LOCALAPPDATA%\ARCHIVINA\K-TOOL_lisp). Không ghi đè file cạnh DLL.
        internal static string LayFileLisp(string ten)
        {
            byte[] nhung;
            using (Stream s = Assembly.GetExecutingAssembly().GetManifestResourceStream(ten)
                              ?? throw new FileNotFoundException("DLL không có LISP nhúng: " + ten))
            using (var ms = new MemoryStream())
            {
                s.CopyTo(ms);
                nhung = ms.ToArray();
            }

            string canh = Path.Combine(KToolApp.ThuMucDll, ten);
            if (GiongHet(canh, nhung)) return canh;

            foreach (string thuMuc in new[]
            {
                Path.Combine(KToolApp.ThuMucDll, "K-TOOL_lisp"),
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "ARCHIVINA", "K-TOOL_lisp"),
            })
            {
                try
                {
                    Directory.CreateDirectory(thuMuc);
                    string f = Path.Combine(thuMuc, ten);
                    if (!GiongHet(f, nhung)) File.WriteAllBytes(f, nhung);
                    return f;
                }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
            throw new IOException("không ghi được file LISP nhúng: " + ten);
        }

        static bool GiongHet(string f, byte[] nhung) =>
            File.Exists(f) && File.ReadAllBytes(f).AsSpan().SequenceEqual(nhung);

        // Chuỗi đưa vào LISP: \ -> /, " -> \", chữ có dấu -> \U+XXXX (đúng cả khi LISPSYS = 0)
        internal static string ChuoiLisp(string s)
        {
            var sb = new StringBuilder();
            foreach (char c in s)
            {
                if (c == '\\') sb.Append('/');
                else if (c == '"') sb.Append("\\\"");
                else if (c == '\n') sb.Append("\\n");
                else if (c < 128) sb.Append(c);
                else sb.Append($"\\U+{(int)c:X4}");
            }
            return sb.ToString();
        }
    }
}
