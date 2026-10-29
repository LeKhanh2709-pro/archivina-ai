// K-TOOL.dll — thêm tab ribbon "K-TOOL" vào AutoCAD, mỗi nút gọi một lệnh LISP Archivina qua hàm kt:chay
// trong K-TOOL.lsp (đặt cùng thư mục với DLL). Không sửa file CUIx của máy: tab tạo lại mỗi lần nạp DLL.
// Lệnh: KTOOLTAB (thêm lại tab nếu bị mất, vd. sau khi đổi workspace).

using System;
using System.Globalization;
using System.IO;
using System.Reflection;
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
    public class KToolApp : IExtensionApplication
    {
        const string TabId = "ARCHIVINA_KTOOL_TAB";

        // Nút: tên trong kt:bang của K-TOOL.lsp, nhãn, chú thích, chữ trên biểu tượng, màu biểu tượng
        record Nut(string Ten, string Nhan, string ChuThich, string Ky, Color Mau);

        // Panel: tiêu đề + các nút
        static readonly (string Tieu, Nut[] Nuts)[] Panels =
        {
            ("Vách kính", new[]
            {
                new Nut("VK", "Vách kính", "VK: chia đố và dựng vách kính mặt bằng", "VK", Color.FromRgb(0x1F, 0x6F, 0xB2)),
                new Nut("MDVK", "Mặt đứng VK", "MDVK: dựng mặt đứng vách kính từ block VACH KINH", "MĐ", Color.FromRgb(0x2E, 0x8B, 0xC0)),
            }),
            ("Trục kỹ thuật", new[]
            {
                new Nut("LOMO", "Lỗ mở MEP", "LOMO: chèn block A-MEP cho trục / hộp kỹ thuật", "LM", Color.FromRgb(0x6A, 0x4C, 0x93)),
                new Nut("NCL", "Ngăn cháy lan", "NCL: vẽ bo + hatch ngăn cháy lan, không hỏi trước", "NC", Color.FromRgb(0xC6, 0x28, 0x28)),
                new Nut("KT-NGANCHAY", "Ngăn cháy (hỏi)", "KT-NGANCHAY: ngăn cháy lan, xem danh sách vùng trước khi vẽ", "NC?", Color.FromRgb(0xE0, 0x6C, 0x1F)),
            }),
            ("Chống thấm", new[]
            {
                new Nut("CHONGTHAM", "Chống thấm", "CHONGTHAM: vẽ mặt bằng chống thấm (WC, lô gia, phòng rác...)", "CT", Color.FromRgb(0x2E, 0x7D, 0x32)),
            }),
        };

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
            }
            catch (System.Exception ex) { Ghi("lỗi khi khởi tạo: " + ex); }
        }

        public void Terminate() { }

        // Thông báo ra dòng lệnh và ghi K-TOOL.log cạnh DLL (để người dùng gửi lại khi có lỗi)
        static void Ghi(string s)
        {
            try { AcApp.DocumentManager.MdiActiveDocument?.Editor.WriteMessage("\nK-TOOL: " + s); } catch { }
            try
            {
                string log = Path.Combine(Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location), "K-TOOL.log");
                File.AppendAllText(log, $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {s}{Environment.NewLine}");
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
            if (rb == null) { Ghi("chưa có ribbon (gõ RIBBON để bật rồi gõ KTOOL)"); return; }
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
                        LargeImage = BieuTuong(n.Ky, n.Mau, 32),
                        Image = BieuTuong(n.Ky, n.Mau, 16),
                        ToolTip = n.ChuThich,
                        CommandParameter = n.Ten,
                        CommandHandler = new ChayLisp(),
                    });
                }
                tab.Panels.Add(new RibbonPanel { Source = src });
            }
            rb.Tabs.Add(tab);
            Ghi("đã thêm tab K-TOOL trên ribbon");
        }

        // Biểu tượng vẽ bằng code: ô vuông bo góc màu + chữ trắng (không cần file ảnh mang theo)
        static BitmapSource BieuTuong(string ky, Color mau, int px)
        {
            var dv = new DrawingVisual();
            using (DrawingContext dc = dv.RenderOpen())
            {
                dc.DrawRoundedRectangle(new SolidColorBrush(mau), null, new Rect(0, 0, px, px), px * 0.18, px * 0.18);
                var ft = new FormattedText(ky, CultureInfo.InvariantCulture, FlowDirection.LeftToRight,
                    new Typeface(new FontFamily("Arial"), FontStyles.Normal, FontWeights.Bold, FontStretches.Normal),
                    px * (ky.Length > 2 ? 0.34 : 0.42), Brushes.White, 1.0);
                dc.DrawText(ft, new Point((px - ft.Width) / 2, (px - ft.Height) / 2));
            }
            var bmp = new RenderTargetBitmap(px, px, 96, 96, PixelFormats.Pbgra32);
            bmp.Render(dv);
            bmp.Freeze();
            return bmp;
        }
    }

    // Bấm nút: huỷ lệnh đang chạy, nạp K-TOOL.lsp (nếu bản vẽ này chưa nạp) rồi gọi (kt:chay "<tên>")
    class ChayLisp : ICommand
    {
        public event EventHandler CanExecuteChanged { add { } remove { } }

        public bool CanExecute(object parameter) => true;

        public void Execute(object parameter)
        {
            string ten = (parameter as RibbonButton)?.CommandParameter as string;
            Document doc = AcApp.DocumentManager.MdiActiveDocument;
            if (ten == null || doc == null) return;

            // Thư mục chứa DLL = thư mục chứa các file LISP; báo cho kt:tim qua ARCHIVINA_LISP
            string thuMuc = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location).Replace('\\', '/');
            string lisp =
                "(progn" +
                $" (setenv \"ARCHIVINA_LISP\" \"{thuMuc}\")" +
                $" (if (not kt:chay) (load \"{thuMuc}/K-TOOL.lsp\" nil))" +
                $" (if kt:chay (kt:chay \"{ten}\")" +
                // "không tìm thấy" viết bằng mã \U+XXXX để hiện đúng cả khi LISPSYS = 0
                " (princ \"\\nK-TOOL: kh\\U+00F4ng t\\U+00ECm th\\U+1EA5y K-TOOL.lsp c\\U+1EA1nh K-TOOL.dll\")))\n";
            doc.SendStringToExecute("\x03\x03" + lisp, true, false, false);
        }
    }
}
