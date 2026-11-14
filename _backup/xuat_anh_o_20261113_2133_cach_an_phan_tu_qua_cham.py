#! python3
# -*- coding: utf-8 -*-
"""Xuất ảnh TỪNG Ô của legend chi tiết CAD để duyệt (CHỈ ĐỂ XEM, không ghi gì vào model): ẩn tạm mọi thứ trừ group của ô
đang xuất, xuất PNG, cuối cùng hoàn tác hết (TransactionGroup.RollBack). Legend không cắt (crop) được nên phải làm vậy
mới có ảnh đủ nét từng ô.

Biến môi trường: ARV_CTC_TEN (tên legend, mặc định CHI TIẾT CỬA (CAD)), ARV_CTC_ANH_O (thư mục ảnh),
ARV_CTC_O (tên ô cách nhau |, trống = mọi ô), ARV_CTC_PX (bề rộng ảnh, mặc định 6000), ARV_CTC_OLOG (log)."""
import locale
locale.setlocale(locale.LC_ALL, "C")
import io, os, time, traceback

GOC = os.path.dirname(os.path.abspath(__file__))
TEN = os.environ.get("ARV_CTC_TEN") or u"CHI TIẾT CỬA (CAD)"
ANH = os.environ.get("ARV_CTC_ANH_O") or os.path.join(GOC, "kq", "anh_o")
CHON = [s for s in os.environ.get("ARV_CTC_O", "").split("|") if s]
PX = int(os.environ.get("ARV_CTC_PX") or 6000)
LOG = os.environ.get("ARV_CTC_OLOG") or os.path.join(GOC, "kq", "xuat_anh_o_log.txt")
if not os.path.isdir(ANH):
    os.makedirs(ANH)
f = io.open(LOG, "w", encoding="utf-8")


def w(s):
    f.write(u"{}\n".format(s)); f.flush()


try:
    import clr
    clr.AddReference("RevitAPI")
    import Autodesk.Revit.DB as DB
    from System.Collections.Generic import List as NetList

    doc = __revit__.ActiveUIDocument.Document
    FEC = DB.FilteredElementCollector
    lg = [v for v in FEC(doc).OfClass(DB.View) if v.ViewType == DB.ViewType.Legend and not v.IsTemplate and v.Name == TEN]
    if not lg:
        raise Exception(u"Không có legend tên '{}'".format(TEN))
    lg = lg[0]
    nhom = {}
    for g in FEC(doc, lg.Id).OfClass(DB.Group):
        nhom[g.GroupType.Name] = g
    w(u"--- {} | legend '{}' | {} group".format(doc.PathName, TEN, len(nhom)))
    # phần tử nằm ngoài mọi group (vd. phần tử có sẵn của legend mẫu): ẩn suốt lúc xuất
    trong_nhom = set()
    for g in nhom.values():
        trong_nhom.add(g.Id.Value)
        for i in g.GetMemberIds():
            trong_nhom.add(i.Value)
    le = [e.Id for e in FEC(doc, lg.Id).WhereElementIsNotElementType()
          if e.Id.Value not in trong_nhom and e.CanBeHidden(lg)]
    w(u"--- phần tử ngoài group (ẩn khi xuất): {}".format(len(le)))
    ten_ds = [n for n in sorted(nhom) if not CHON or any(c in n for c in CHON)]
    tg = DB.TransactionGroup(doc, u"Xuất ảnh từng ô (sẽ hoàn tác)")
    tg.Start()
    for ten in ten_ds:
        t0 = time.time()
        g = nhom[ten]
        giu = set(i.Value for i in g.GetMemberIds())
        giu.add(g.Id.Value)
        an = NetList[DB.ElementId]()
        for i in le:
            an.Add(i)
        for n2, g2 in nhom.items():
            if n2 != ten:
                an.Add(g2.Id)          # ẩn group là ẩn cả các phần tử trong group
        t = DB.Transaction(doc, u"Ẩn tạm")
        t.Start()
        if an.Count:
            lg.HideElements(an)
        t.Commit()
        # ẩn group mà phần tử bên trong vẫn hiện (tuỳ bản Revit) thì ẩn thêm từng phần tử
        khac = [g2 for n2, g2 in nhom.items() if n2 != ten]
        if khac:
            mau_id = list(khac[0].GetMemberIds())[0]
            if not doc.GetElement(mau_id).IsHidden(lg):
                them = NetList[DB.ElementId]()
                for g2 in khac:
                    for i in g2.GetMemberIds():
                        if doc.GetElement(i).CanBeHidden(lg):
                            them.Add(i)
                t = DB.Transaction(doc, u"Ẩn tạm từng phần tử")
                t.Start()
                lg.HideElements(them)
                t.Commit()
                for i in them:
                    an.Add(i)
        op = DB.ImageExportOptions()
        op.ExportRange = DB.ExportRange.SetOfViews
        vl = NetList[DB.ElementId](); vl.Add(lg.Id)
        op.SetViewsAndSheets(vl)
        ten_file = u"".join(c if c not in u'\\/:*?"<>|' else u"-" for c in ten)
        op.FilePath = os.path.join(ANH, ten_file)
        op.HLRandWFViewsFileType = DB.ImageFileType.PNG
        op.ImageResolution = DB.ImageResolution.DPI_300
        op.ZoomType = DB.ZoomFitType.FitToPage
        op.PixelSize = PX
        op.FitDirection = DB.FitDirectionType.Horizontal
        doc.ExportImage(op)
        t = DB.Transaction(doc, u"Hiện lại")
        t.Start()
        if an.Count:
            lg.UnhideElements(an)
        t.Commit()
        w(u"=== {} | {} phần tử trong group | {:.1f} s".format(ten, len(giu) - 1, time.time() - t0))
    tg.RollBack()
    w(u"--- Đã xuất {} ảnh vào {} (không lưu gì vào model)".format(len(ten_ds), ANH))
    w(u"XONG")
except Exception:
    w(u"LỖI " + traceback.format_exc())
finally:
    f.close()
