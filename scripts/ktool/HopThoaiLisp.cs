// HopThoaiLisp.cs — cầu nối LISP -> hộp thoại WPF: (ktool_bang_vk <dữ liệu>), (ktool_bang_mdvk <dữ liệu>).
// Dữ liệu vào / ra là danh sách các cặp chuỗi khoá - giá trị. Lỗi -> trả nil, LISP dùng hộp thoại DCL cũ.
// VK.lsp / VKMD.lsp vẫn chạy một mình khi không có K-TOOL.dll (DCL).

using System;
using System.Collections.Generic;
using System.Linq;
using Autodesk.AutoCAD.ApplicationServices;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.AutoCAD.Runtime;
using AcApp = Autodesk.AutoCAD.ApplicationServices.Application;

[assembly: CommandClass(typeof(KTool.HopThoaiLisp))]

namespace KTool
{
    public class HopThoaiLisp
    {
        // Mọi chuỗi trong tham số (bỏ qua dấu mở / đóng danh sách, cặp chấm)
        static List<string> Chuoi(ResultBuffer rb) =>
            rb == null ? new List<string>() :
            rb.Cast<TypedValue>().Where(t => t.TypeCode == (short)LispDataType.Text).Select(t => (string)t.Value).ToList();

        static Dictionary<string, string> Cap(List<string> ds, List<string> nhieu = null)
        {
            var d = new Dictionary<string, string>();
            for (int i = 0; i + 1 < ds.Count; i += 2)
                if (nhieu != null && ds[i] == "vach") nhieu.Add(ds[i + 1]);
                else d[ds[i]] = ds[i + 1];
            return d;
        }

        static ResultBuffer Tra(Dictionary<string, string> kq)
        {
            var rb = new ResultBuffer(new TypedValue((short)LispDataType.ListBegin));
            foreach (var kv in kq)
            {
                rb.Add(new TypedValue((short)LispDataType.Text, kv.Key));
                rb.Add(new TypedValue((short)LispDataType.Text, kv.Value ?? ""));
            }
            rb.Add(new TypedValue((short)LispDataType.ListEnd));
            return rb;
        }

        // Chế độ đã nhớ ("dark" / "light"); chưa có thì theo giao diện AutoCAD (COLORTHEME: 0 tối, 1 sáng)
        static bool LaToi(Dictionary<string, string> vao)
        {
            if (vao.TryGetValue("theme", out string t) && (t == "dark" || t == "light")) return t == "dark";
            try { return Convert.ToInt32(AcApp.GetSystemVariable("COLORTHEME")) == 0; }
            catch { return true; }
        }

        static bool CoBlock(Database db, string ten)
        {
            using var tr = db.TransactionManager.StartOpenCloseTransaction();
            var bt = (BlockTable)tr.GetObject(db.BlockTableId, OpenMode.ForRead);
            return bt.Has(ten);
        }

        static bool TenHopLe(string ten)
        {
            try { SymbolUtilityServices.ValidateSymbolName(ten, false); return true; }
            catch { return false; }
        }

        static bool? Mo(System.Windows.Window w) => AcApp.ShowModalWindow(AcApp.MainWindow.Handle, w, false);

        [LispFunction("ktool_bang_vk")]
        public ResultBuffer BangVkLisp(ResultBuffer args)
        {
            try
            {
                var vao = Cap(Chuoi(args));
                Database db = AcApp.DocumentManager.MdiActiveDocument.Database;
                var b = new BangVk(vao, LaToi(vao), t => CoBlock(db, t), TenHopLe);
                Mo(b.CuaSo);
                return Tra(b.KetQua());
            }
            catch (System.Exception ex)
            {
                KToolApp.Ghi("lỗi hộp thoại VK: " + ex);
                return null;
            }
        }

        [LispFunction("ktool_bang_mdvk")]
        public ResultBuffer BangMdvkLisp(ResultBuffer args)
        {
            try
            {
                var chuoiVach = new List<string>();
                var vao = Cap(Chuoi(args), chuoiVach);
                var b = new BangMdvk(vao, chuoiVach.Select(VachMd.Doc).ToList(), LaToi(vao));
                Mo(b.CuaSo);
                return Tra(b.KetQua());
            }
            catch (System.Exception ex)
            {
                KToolApp.Ghi("lỗi hộp thoại MDVK: " + ex);
                return null;
            }
        }
    }
}
