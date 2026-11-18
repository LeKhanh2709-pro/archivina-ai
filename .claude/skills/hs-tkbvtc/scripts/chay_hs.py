#! python3
# -*- coding: utf-8 -*-
# Bước chạy TRONG Revit cho agent hs-tkbvtc (2026-11-15). Nút thử ARVAgentHS (ext\ của skill) đọc buoc.txt rồi chạy file
# này với biến VIEC = đường dẫn file việc (JSON). Không gắn cứng đường dẫn máy: thư mục gốc tìm theo vị trí file này.
#
# File việc (JSON):
#   "mo":          .rvt cần mở. Workshared thì mở TÁCH khỏi central (DetachAndPreserveWorksets) → không bao giờ mượn phần
#                  tử từ central thật trên ổ mạng; không workshared thì mở thường.
#   "che_do":      "khao_sat" (chỉ đọc, ghi khao_sat.json) | "chay" (chạy các nút theo phương án) | "dat_mark_vk" (đặt
#                  Mark vách kính) | "kiem_tra" (2026-11-16: chỉ kiểm tra + xuất ảnh các bản vẽ có số hiệu bắt đầu bằng
#                  "sheet_tien_to" – chuỗi hoặc danh sách, vd. ["A_TC.14.", "A_TC.22."]; không chạy nút, không lưu. Dùng
#                  sau chuỗi phiên chi tiết cửa: ảnh / kiểm tra của từng phiên chỉ có tờ phiên đó chạm tới và có thể cũ)
#                  | "script" (2026-11-18: chạy file Python "script" trên file đã mở, xem chỗ điều phối che_do)
#   "phuong_an":   JSON phương án (định dạng nút Hồ sơ đã duyệt + mục ChiTietCua), che_do = chay
#   "chi":         ["<view>|<nút>", ...] chỉ chạy các mục này (trống = mọi mục của phương án)
#   "luu":         .rvt lưu ra sau khi chạy (file MỚI, có rồi thì không ghi đè); trống = không lưu
#   "ket_qua":     thư mục ghi báo cáo + ảnh
#   "log":         thư mục log lõi + đệm nhận diện CAD (giữ giữa các lần chạy để khỏi chạy lại AutoCAD)
#   "anh":         true = xuất PNG từng bản vẽ (mặc định true)
#   "tra_loi_xoa": "khong" (mặc định: mọi câu hỏi xoá / gộp / vẽ lại của lõi trả lời KHÔNG, ghi vào mục cần hỏi) | "co"
#   "khao_sat_view": ["<tên mặt bằng>", ...] khảo sát thêm cửa / vách kính theo tầng (cho Chi tiết cửa)
# Ra: <ket_qua>\ket_qua.json + bao_cao.txt (+ <số hiệu>.png). Dòng "=== " = tiến độ, "XONG" = hết (chay_nen.ps1 chờ).
import locale
locale.setlocale(locale.LC_ALL, "C")          # chữa Revit văng corruptData (CLAUDE.md: Revit văng do locale CPython)
import os
import sys
import io
import json
import datetime
import traceback
import unicodedata

_DAY = os.path.dirname(os.path.abspath(__file__))


def tim_goc():
    """Thư mục gốc AI: cha của .claude chứa skill; không có thì thư mục cha có scripts\\pyrevit\\ARVTools.extension."""
    d = _DAY
    while True:
        cha = os.path.dirname(d)
        if os.path.basename(d).lower() == ".claude":
            return cha
        if os.path.isdir(os.path.join(d, "scripts", "pyrevit", "ARVTools.extension")):
            return d
        if cha == d:
            return None
        d = cha


GOC = os.environ.get("ARCHIVINA_AI") or tim_goc()
EXT_ARV = os.path.join(GOC, "scripts", "pyrevit", "ARVTools.extension")
EXT_HSD = os.path.join(GOC, "scripts", "pyrevit", "ARVHoSoDuyet.extension")
PANEL = os.path.join(EXT_ARV, "Archivina.tab", "HoSo.panel")

V = json.load(io.open(VIEC, encoding="utf-8-sig"))         # noqa: F821 – VIEC do nút truyền vào
for _k in ("mo", "luu", "ket_qua", "log", "phuong_an"):
    if V.get(_k):
        V[_k] = os.path.normpath(V[_k])                     # nhận cả dấu / và \
KQ = V["ket_qua"]
if not os.path.isdir(KQ):
    os.makedirs(KQ)
LOG = V.get("log") or os.path.join(KQ, "log")
f = io.open(os.path.join(KQ, "bao_cao.txt"), "w", encoding="utf-8")
KET = {"bat_dau": datetime.datetime.now().isoformat(), "viec": V, "muc": [], "kiem_tra": [], "can_hoi": [], "loi": [],
       "hop_thoai": []}


def w(s):
    f.write(u"{}\n".format(s))
    f.flush()


def ghi_json():
    with io.open(os.path.join(KQ, "ket_qua.json"), "w", encoding="utf-8") as g:
        g.write(json.dumps(KET, ensure_ascii=False, indent=1, default=str))


def kd(s):
    s = unicodedata.normalize("NFD", u"{}".format(s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def ft2mm(x):
    return x * 304.8


try:
    import clr
    clr.AddReference("RevitAPI")
    clr.AddReference("RevitAPIUI")
    clr.AddReference("System.Windows.Forms")
    import Autodesk.Revit.DB as DB
    import Autodesk.Revit.UI as UI
    from System.Collections.Generic import List as NetList

    uiapp = __revit__        # noqa: F821
    app = uiapp.Application
    w(u"=== Bắt đầu {} | gốc {} | chế độ {}".format(datetime.datetime.now(), GOC, V.get("che_do")))

    # ------------------------------------------------------------ hộp thoại Revit trong lúc chạy
    TU_HOI = (u"xoá", u"xóa", u"gộp", u"vẽ lại", u"delete", u"merge")

    def bat_hop_thoai(sender, e):
        try:
            tin = (getattr(e, "Message", u"") or u"").replace(u"\n", u" / ")
            did = u"%s" % e.DialogId
            if u"Unresolved" in did or u"unresolved" in kd(tin):
                kq = 1002                                    # mở tiếp, bỏ qua link thiếu (báo trong kết quả)
            elif any(t in kd(tin) for t in (kd(x) for x in TU_HOI)):
                kq = 6 if V.get("tra_loi_xoa") == "co" else 7
                KET["can_hoi"].append(u"Lõi hỏi: %s → đã trả lời %s" % (tin[:300], u"Có" if kq == 6 else u"KHÔNG"))
            else:
                kq = 1
            KET["hop_thoai"].append(u"%s | %s | %s → %s" % (type(e).__name__, did, tin[:300], kq))
            w(u"   [HỘP THOẠI REVIT] {} | {} → {}".format(did, tin[:300], kq))
            try:
                e.OverrideResult(kq)
            except Exception:
                e.OverrideResult(2)
        except Exception as ex:
            w(u"   [HỘP THOẠI REVIT] lỗi bắt: {}".format(ex))
    uiapp.DialogBoxShowing += bat_hop_thoai

    # ------------------------------------------------------------ file mở đầu (journal mở trước, xem chay_nen.ps1)
    # Mở file bằng API khi chưa có file nào mở qua giao diện thì lần clr.AddReference sau đó lỗi nạp
    # DesktopConnectorInterop v26 → journal luôn mở trước 1 dự án trống nhỏ (ext\mo_dau.rvt). Chưa có thì che_do
    # "tao_mo_dau" tạo nó (không cần template).
    # đúng phiên bản Revit file việc yêu cầu (2026-11-15: lần chạy chồng nhau làm Revit 2027 chạy việc của lần chạy 2026)
    if V.get("revit") and u"%s" % app.VersionNumber != u"%s" % V["revit"]:
        raise Exception(u"Phiên Revit %s nhưng file việc yêu cầu Revit %s – dừng (có lần chạy khác chồng lên?)." % (
            app.VersionNumber, V["revit"]))
    if V.get("che_do") == "tao_mo_dau":
        nd = app.NewProjectDocument(DB.UnitSystem.Metric)
        o_ = DB.SaveAsOptions()
        o_.OverwriteExistingFile = False
        nd.SaveAs(V["mo"], o_)
        nd.Close(False)
        w(u"=== Đã tạo file mở đầu {}".format(V["mo"]))
        raise SystemExit(0)
    # ------------------------------------------------------------ file đích do nút Mo (IronPython) đã mở
    # KHÔNG mở file bằng API ở đây (CPython đã chạy rồi mới mở thì lỗi nạp DesktopConnectorInterop, xem Mo.pushbutton).
    mo = V["mo"]
    try:
        w(u"Nút Mo: " + io.open(os.path.join(KQ, "mo.txt"), encoding="utf-8").read().strip().replace(u"\n", u" | "))
    except Exception:
        w(u"Nút Mo: không có mo.txt")
    uidoc = uiapp.ActiveUIDocument
    doc = uidoc.Document if uidoc is not None else None
    # file workshared mở TÁCH central thì PathName rỗng, Title = "<tên gốc>_detached" (agent phát hiện 2026-11-15 trên FPT P5)
    goc_ten = os.path.splitext(os.path.basename(mo))[0]
    dung = doc is not None and (
        os.path.normcase(os.path.normpath(doc.PathName or u"")) == os.path.normcase(mo) or
        # tách central: PathName = "<tên>_detached.rvt" (chỉ tên, không thư mục – agent đo 2026-11-15) hoặc rỗng
        (bool(getattr(doc, "IsDetached", False)) and
         os.path.splitext(os.path.basename(doc.PathName or doc.Title or u""))[0] in (goc_ten, goc_ten + u"_detached")))
    if not dung:
        raise Exception(u"File đang mở (%s) không phải file cần mở %s – nút Mo không mở được (xem mo.txt)." % (
            doc.PathName if doc is not None else u"-", mo))
    w(u"=== Đã mở: {} | workshared {} | tách {}".format(doc.Title, doc.IsWorkshared, getattr(doc, "IsDetached", u"?")))
    if doc.IsWorkshared and not getattr(doc, "IsDetached", False):
        raise Exception(u"File workshared nhưng KHÔNG ở trạng thái tách – dừng để không mượn phần tử từ central.")
    KET["file"] = {"mo": mo, "title": doc.Title, "workshared": doc.IsWorkshared,
                   "tach": bool(getattr(doc, "IsDetached", False))}

    # link
    links = []
    for li in DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkInstance):
        ld = li.GetLinkDocument()
        links.append({"ten": li.Name, "nap": ld is not None, "file": ld.PathName if ld is not None else None})
    KET["link"] = links
    for l_ in links:
        if not l_["nap"]:
            KET["can_hoi"].append(u"Link KHÔNG nạp được: %s" % l_["ten"])
    w(u"Link: {} ({} không nạp)".format(len(links), sum(1 for l_ in links if not l_["nap"])))

    sys.path.insert(0, os.path.join(EXT_ARV, "lib"))
    sys.path.insert(0, os.path.join(EXT_HSD, "lib"))
    try:
        import arv_hoi_sheet
    except Exception as ex_:
        # chẩn đoán lỗi nạp DesktopConnectorInterop sau khi mở file bằng API
        from System import AppDomain
        w(u"CHẨN ĐOÁN import lỗi: %s" % (u"%s" % ex_)[:300])
        for a_ in AppDomain.CurrentDomain.GetAssemblies():
            try:
                n_ = a_.GetName()
                if u"DesktopConnector" in n_.Name:
                    w(u"   nạp: %s %s | %s" % (n_.Name, n_.Version, a_.Location if not a_.IsDynamic else u"động"))
                for r_ in a_.GetReferencedAssemblies():
                    if u"DesktopConnectorInterop" in r_.Name:
                        w(u"   %s %s tham chiếu %s %s | %s" % (n_.Name, n_.Version, r_.Name, r_.Version,
                                                           a_.Location if not a_.IsDynamic else u"động"))
            except Exception:
                pass
        raise

    def ten(e):
        return arv_hoi_sheet._ten(e)

    def tpl_cua(v):
        return doc.GetElement(v.ViewTemplateId) if v.ViewTemplateId != DB.ElementId.InvalidElementId else None

    def so_sheet(v):
        try:
            p = v.get_Parameter(DB.BuiltInParameter.VIEWER_SHEET_NUMBER)
            s = p.AsString() if p is not None else None
            return s if s and s not in (u"---", u"-") else None
        except Exception:
            return None

    # ------------------------------------------------------------ vùng vẽ khung tên (như DatSheet_chung.sh_vung_ve)
    _NET = {}

    def net_khung(sym):
        k = sym.Id.Value
        if k in _NET:
            return _NET[k]
        dung, ngang = [], []
        fd = None
        try:
            fd = doc.EditFamily(sym.Family)
            for c in DB.FilteredElementCollector(fd).OfClass(DB.CurveElement):
                try:
                    g = c.GeometryCurve
                    if g is None or not g.IsBound or g.GetType().Name != "Line":
                        continue
                    a, b = g.GetEndPoint(0), g.GetEndPoint(1)
                    if abs(a.X - b.X) < 1e-6:
                        dung.append((a.X, abs(a.Y - b.Y)))
                    elif abs(a.Y - b.Y) < 1e-6:
                        ngang.append((a.Y, abs(a.X - b.X)))
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            if fd is not None:
                try:
                    fd.Close(False)
                except Exception:
                    pass
        _NET[k] = (dung, ngang)
        return _NET[k]

    def vung_ve(sheet, tb):
        net = net_khung(tb.Symbol)
        tf = tb.GetTotalTransform()
        dung = [(tf.OfPoint(DB.XYZ(x, 0, 0)).X, l) for x, l in net[0]]
        ngang = [(tf.OfPoint(DB.XYZ(0, y, 0)).Y, l) for y, l in net[1]]
        bb = tb.get_BoundingBox(sheet)
        X0, Y0, X1, Y1 = bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y
        W, H = X1 - X0, Y1 - Y0
        d40 = 40.0 / 304.8
        dai_d = [x for x, l in dung if l > 0.6 * H]
        dai_n = [y for y, l in ngang if l > 0.6 * W]
        x0 = max([x for x in dai_d if x < X0 + d40] or [X0 + 25.0 / 304.8])
        x1 = max([x for x in dai_d if X0 + d40 < x < X1 - d40] or [X1 - W / 6.0])
        y0 = max([y for y in dai_n if y < Y0 + d40] or [Y0 + 15.0 / 304.8])
        y1 = min([y for y in dai_n if y > Y1 - d40] or [Y1 - 15.0 / 304.8])
        return (x0, y0, x1, y1), (X0, Y0, X1, Y1)

    def giao(a, b, tol):
        dx = min(a[2], b[2]) - max(a[0], b[0])
        dy = min(a[3], b[3]) - max(a[1], b[1])
        return (dx, dy) if dx > tol and dy > tol else None

    def tag_de(v):
        """Cặp tag đè nhau trong view (khung tag ước lượng: tag không leader = bounding box; tag có leader = khung cỡ
        trung vị của tag cùng kiểu, tâm tại đầu tag). Trả về (số tag, [(id, id, mm x mm giấy)])."""
        tl = float(v.Scale or 100)
        tags = list(DB.FilteredElementCollector(doc, v.Id).OfClass(DB.IndependentTag))
        co = {}
        for t in tags:
            if not t.HasLeader:
                bb = t.get_BoundingBox(v)
                if bb is not None:
                    co.setdefault(t.GetTypeId().Value, []).append((bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y))
        hop = []
        for t in tags:
            try:
                if t.HasLeader:
                    ds = sorted(co.get(t.GetTypeId().Value) or [])
                    if not ds:
                        continue
                    wv, hv = ds[len(ds) // 2]
                    p = t.TagHeadPosition
                    hop.append((t.Id.Value, (p.X - wv / 2, p.Y - hv / 2, p.X + wv / 2, p.Y + hv / 2)))
                else:
                    bb = t.get_BoundingBox(v)
                    if bb is not None:
                        hop.append((t.Id.Value, (bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y)))
            except Exception:
                pass
        tol = 0.3 / 304.8 * tl         # 0,3 mm giấy
        cap = []
        for i in range(len(hop)):
            for j in range(i + 1, len(hop)):
                g = giao(hop[i][1], hop[j][1], tol)
                if g:
                    cap.append((hop[i][0], hop[j][0], u"%.1f x %.1f" % (ft2mm(g[0]) / tl, ft2mm(g[1]) / tl)))
        return len(tags), cap

    def kiem_sheet(s, so_mong, ten_mong):
        r = {"so": s.SheetNumber, "ten": s.Name, "loi": [], "luu_y": []}
        if so_mong and s.SheetNumber != so_mong:
            r["loi"].append(u"Số hiệu %s khác số yêu cầu %s" % (s.SheetNumber, so_mong))
        if ten_mong and kd(s.Name).strip() != kd(ten_mong).strip():
            r["luu_y"].append(u"Tên bản vẽ '%s' khác tên yêu cầu '%s'" % (s.Name, ten_mong))
        tbs = list(DB.FilteredElementCollector(doc, s.Id).OfCategory(DB.BuiltInCategory.OST_TitleBlocks)
                   .WhereElementIsNotElementType())
        if not tbs:
            r["loi"].append(u"Bản vẽ không có khung tên")
            return r
        tb = tbs[0]
        r["khung_ten"] = u"%s : %s" % (tb.Symbol.FamilyName, ten(tb.Symbol))
        vv, ngoai_cung = vung_ve(s, tb)
        r["vung_ve_mm"] = u"%d x %d" % (ft2mm(vv[2] - vv[0]), ft2mm(vv[3] - vv[1]))
        hop = []
        for vp in DB.FilteredElementCollector(doc, s.Id).OfClass(DB.Viewport):
            o = vp.GetBoxOutline()
            v = doc.GetElement(vp.ViewId)
            hop.append((u"view '%s'" % v.Name, (o.MinimumPoint.X, o.MinimumPoint.Y, o.MaximumPoint.X, o.MaximumPoint.Y), v))
        for si in DB.FilteredElementCollector(doc, s.Id).OfClass(DB.ScheduleSheetInstance):
            if si.IsTitleblockRevisionSchedule:
                continue
            bb = si.get_BoundingBox(s)
            if bb is not None:
                hop.append((u"bảng '%s'" % ten(doc.GetElement(si.ScheduleId)), (bb.Min.X, bb.Min.Y, bb.Max.X, bb.Max.Y), None))
        tol = 1.0 / 304.8
        for nhan, b, _ in hop:
            tran = [ft2mm(vv[0] - b[0]), ft2mm(vv[1] - b[1]), ft2mm(b[2] - vv[2]), ft2mm(b[3] - vv[3])]
            if max(tran) > 1.0:
                r["loi"].append(u"%s (%d x %d mm) tràn ra ngoài vùng vẽ %s mm: trái %d / dưới %d / phải %d / trên %d mm" % (
                    nhan, ft2mm(b[2] - b[0]), ft2mm(b[3] - b[1]), r["vung_ve_mm"], *[max(0, int(round(x))) for x in tran]))
        for i in range(len(hop)):
            for j in range(i + 1, len(hop)):
                g = giao(hop[i][1], hop[j][1], tol)
                if g:
                    r["loi"].append(u"%s đè %s (%d x %d mm)" % (hop[i][0], hop[j][0], ft2mm(g[0]), ft2mm(g[1])))
        r["viewport"] = [u"%s %d x %d mm" % (n, ft2mm(b[2] - b[0]), ft2mm(b[3] - b[1])) for n, b, _ in hop]
        for nhan, b, v in hop:
            if v is None or v.ViewType not in (DB.ViewType.FloorPlan, DB.ViewType.CeilingPlan):
                continue
            n, cap = tag_de(v)
            r.setdefault("tag", []).append(u"%s: %d tag, %d cặp đè nhau" % (nhan, n, len(cap)))
            if cap:
                r["loi"].append(u"%s: %d cặp tag đè nhau (id: %s%s)" % (
                    nhan, len(cap), u"; ".join(u"%d/%d %s mm" % c for c in cap[:15]), u"; …" if len(cap) > 15 else u""))
        r["dat"] = not r["loi"]
        return r

    def xuat_anh(s, px=4000):
        o = DB.ImageExportOptions()
        o.ExportRange = DB.ExportRange.SetOfViews
        ds = NetList[DB.ElementId]()
        ds.Add(s.Id)
        o.SetViewsAndSheets(ds)
        o.FilePath = os.path.join(KQ, s.SheetNumber.replace(u".", u"-").replace(u"/", u"-"))
        o.ZoomType = DB.ZoomFitType.FitToPage
        o.PixelSize = px
        o.HLRandWFViewsFileType = DB.ImageFileType.PNG
        o.ShadowViewsFileType = DB.ImageFileType.PNG
        doc.ExportImage(o)

    # ------------------------------------------------------------ khảo sát (chỉ đọc)
    def khao_sat():
        ks = {"file": KET["file"], "link": links}
        ks["cad_link"] = []
        for ii in DB.FilteredElementCollector(doc).OfClass(DB.ImportInstance):
            try:
                ov = doc.GetElement(ii.OwnerViewId) if ii.ViewSpecific else None
                ks["cad_link"].append({"ten": ten(doc.GetElement(ii.GetTypeId())), "link": ii.IsLinked,
                                       "view": ov.Name if ov is not None else None})
            except Exception:
                pass
        ks["level"] = [{"ten": l.Name, "cao_do_mm": round(ft2mm(l.Elevation))} for l in
                       sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level), key=lambda l: l.Elevation)]
        mb = []
        for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan):
            if v.IsTemplate or v.ViewType != DB.ViewType.FloorPlan or v.GenLevel is None:
                continue
            t = tpl_cua(v)
            try:
                bro = v.get_Parameter(DB.BuiltInParameter.VIEW_TYPE).AsString()
            except Exception:
                bro = None
            # KHÔNG gom phần tử theo view ở đây: FilteredElementCollector(doc, v.Id) bắt Revit dựng đồ hoạ từng view
            # (FPT P5 37 link: treo > 15 phút, 23 GB RAM – agent đo 2026-11-15). Link thấy trong view = IsHidden.
            mb.append({"ten": v.Name, "tang": v.GenLevel.Name, "loai_view": bro, "template": ten(t) if t else None,
                       "ti_le": v.Scale, "sheet": so_sheet(v), "crop": v.CropBoxActive,
                       "link_thay": len(link_thay_trong(v))})
        ks["mat_bang"] = sorted(mb, key=lambda x: (x["tang"], x["ten"]))
        ks["template_mat_bang"] = [{"ten": ten(t), "ti_le": t.Scale, "khoa_ti_le": bool(arv_hoi_sheet._tpl_khoa_tl(t))}
                                   for t in arv_hoi_sheet._templates(doc)]
        ks["khung_ten"] = sorted(u"%s : %s" % (s.FamilyName, ten(s)) for s in DB.FilteredElementCollector(doc)
                                 .OfClass(DB.FamilySymbol).OfCategory(DB.BuiltInCategory.OST_TitleBlocks))
        pid_gd, pid_hm = arv_hoi_sheet._gd_hm(doc)
        sh = []
        gd_co, hm_co = {}, {}
        for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet):
            gd = hm = None
            try:
                if pid_gd is not None:
                    gd = arv_hoi_sheet._gt(arv_hoi_sheet._ts(s, pid_gd))
                if pid_hm is not None:
                    hm = arv_hoi_sheet._gt(arv_hoi_sheet._ts(s, pid_hm))
            except Exception:
                pass
            if gd:
                gd_co[gd] = gd_co.get(gd, 0) + 1
            if hm:
                hm_co[hm] = hm_co.get(hm, 0) + 1
            sh.append({"so": s.SheetNumber, "ten": s.Name, "so_view": s.GetAllPlacedViews().Count, "giai_doan": gd,
                       "hang_muc": hm})
        ks["sheet"] = sorted(sh, key=lambda x: x["so"])
        ks["giai_doan"] = gd_co
        ks["hang_muc"] = hm_co
        # cửa / vách kính theo tầng (Chi tiết cửa chọn theo Type Mark / Mark)
        ks["cua_theo_tang"] = {}
        for ten_v in V.get("khao_sat_view") or []:
            v = next((x for x in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
                      if not x.IsTemplate and x.Name == ten_v and x.GenLevel is not None), None)
            if v is None:
                ks["cua_theo_tang"][ten_v] = u"không có mặt bằng này"
                continue
            dem = {}
            for e, li in phan_tu_tang(v):
                k = khoa_cua(e)
                if k:
                    dem[k] = dem.get(k, 0) + 1
            ks["cua_theo_tang"][ten_v] = dict(sorted(dem.items()))
        with io.open(os.path.join(KQ, "khao_sat.json"), "w", encoding="utf-8") as g:
            g.write(json.dumps(ks, ensure_ascii=False, indent=1, default=str))
        w(u"=== Khảo sát: {} mặt bằng, {} template, {} khung tên, {} sheet".format(
            len(ks["mat_bang"]), len(ks["template_mat_bang"]), len(ks["khung_ten"]), len(ks["sheet"])))

    BIC_CUA = (int(DB.BuiltInCategory.OST_Doors), int(DB.BuiltInCategory.OST_Windows))
    _LINK_TAT_CA = []

    def link_thay_trong(v):
        """Link instance không bị ẩn trong view v (theo phần tử + hạng mục RVT Links) – không dùng collector theo view."""
        if not _LINK_TAT_CA:
            _LINK_TAT_CA.extend(DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkInstance))
        try:
            if v.GetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_RvtLinks)):
                return []
        except Exception:
            pass
        ra = []
        for li in _LINK_TAT_CA:
            try:
                if not li.IsHidden(v):
                    ra.append(li)
            except Exception:
                ra.append(li)
        return ra

    def la_vach(e):
        try:
            return e is not None and e.GetType().Name == "Wall" and e.CurtainGrid is not None
        except Exception:
            return False

    def khoa_cua(e):
        """'Cửa <Type Mark>' / 'Vách kính <Mark>' / None."""
        try:
            if la_vach(e):
                p = e.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                return u"Vách kính %s" % ((p.AsString() if p else None) or u"(chưa có Mark)")
            if e.Category is None or e.Category.Id.Value not in BIC_CUA:
                return None
            try:
                h = e.Host
                if la_vach(h):
                    return None          # cửa nằm trong vách kính: chi tiết theo vách
            except Exception:
                pass
            t = e.Document.GetElement(e.GetTypeId())
            p = t.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_MARK) if t is not None else None
            return u"Cửa %s" % ((p.AsString() if p else None) or u"(chưa có Type Mark)")
        except Exception:
            return None

    def phan_tu_tang(v):
        """[(phần tử, link instance | None)] cửa đi / cửa sổ / vách kính ở tầng của mặt bằng v (model chính + link thấy
        trong view, nhận tầng theo cao độ)."""
        z = v.GenLevel.Elevation
        ra = []
        for bic in (DB.BuiltInCategory.OST_Doors, DB.BuiltInCategory.OST_Windows, DB.BuiltInCategory.OST_Walls):
            for e in DB.FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType():
                if e.LevelId.Value == v.GenLevel.Id.Value:      # so .Value (PythonNet3: == giữa 2 ElementId không tin được)
                    ra.append((e, None))
        for li in link_thay_trong(v):
            ld = li.GetLinkDocument()
            if ld is None:
                continue
            oz = li.GetTotalTransform().Origin.Z
            ids = set(l.Id.Value for l in DB.FilteredElementCollector(ld).OfClass(DB.Level) if abs(l.Elevation + oz - z) < 0.02)
            for bic in (DB.BuiltInCategory.OST_Doors, DB.BuiltInCategory.OST_Windows, DB.BuiltInCategory.OST_Walls):
                for e in DB.FilteredElementCollector(ld).OfCategory(bic).WhereElementIsNotElementType():
                    if e.LevelId.Value in ids:
                        ra.append((e, li))
        return ra

    def luu_ra(luu):
        """SaveAs ra file MỚI (có rồi thì không ghi đè); workshared → central mới."""
        if os.path.isfile(luu):
            KET["loi"].append(u"KHÔNG LƯU: đã có file %s (không ghi đè)" % luu)
            return
        if not os.path.isdir(os.path.dirname(luu)):
            os.makedirs(os.path.dirname(luu))
        o_ = DB.SaveAsOptions()
        o_.OverwriteExistingFile = False
        if doc.IsWorkshared:
            ws_ = DB.WorksharingSaveAsOptions()
            ws_.SaveAsCentral = True
            o_.SetWorksharingOptions(ws_)
        doc.SaveAs(luu, o_)
        KET["da_luu"] = luu
        w(u"=== Đã lưu {}".format(luu))

    def dat_mark_vk():
        """che_do "dat_mark_vk" (2026-11-16, G19 Side; người dùng: "tên của VK nếu chưa có thì theo thứ tự các tầng, ví dụ
        tầng 1 là VKT1-01, VKT1-02"). Chạy trên BẢN SAO file chứa vách kính (thường là file link của model chính).
        Vách kính (curtain wall) trên tầng V["vk_tang"] (số tầng, mặc định 1–4; level tên "TẦNG <n>", bỏ hầm) chưa có Mark
        → đặt Mark V["vk_dang"] (mặc định "VKT{t}-{n:02d}") theo thứ tự đọc trên mặt bằng (trên → dưới theo dải 3 m, trái →
        phải). Vách GIỐNG HỆT nhau (cùng kiểu, dài, cao, panel / cửa cùng loại + cùng vị trí; lật đầu tính là giống) dùng
        CHUNG 1 Mark – người dùng: "các cửa trùng nhau trong dự án thì triển khai 1 lần"; giống vách đã có Mark thì lấy Mark
        đó. Không đổi Mark đã có. Ghi <ket_qua>\\vk_mark.json, lưu ra V["luu"].
        V["vk_bo_loai"]: chữ trong tên kiểu (không dấu) thì KHÔNG coi là vách kính, không đặt Mark (G19: curtain wall kiểu
        "Tuong lam_*" là tường lam)."""
        import re
        tang_can = set(int(x) for x in (V.get("vk_tang") or [1, 2, 3, 4]))
        dang = V.get("vk_dang") or u"VKT{t}-{n:02d}"
        bo_loai = [kd(x) for x in (V.get("vk_bo_loai") or [])]

        def so_tang(lv):
            if lv is None or u"ham" in kd(lv.Name):
                return None
            m_ = re.search(r"\btang\s+(\d+)\b", kd(lv.Name))
            return int(m_.group(1)) if m_ else None

        def ten_loai(e):
            t = doc.GetElement(e.GetTypeId())
            if t is None:
                return u"-"
            return u"%s : %s" % (getattr(t, "FamilyName", u"") or u"", ten(t))

        def chu_ky(wl):
            cv = wl.Location.Curve
            dai = cv.Length
            bb = wl.get_BoundingBox(None)
            z0 = bb.Min.Z
            p0, p1 = cv.GetEndParameter(0), cv.GetEndParameter(1)
            ds = []
            for pid in wl.CurtainGrid.GetPanelIds():
                pe = doc.GetElement(pid)
                bp = pe.get_BoundingBox(None) if pe is not None else None
                if bp is None:
                    continue
                c = bp.Min.Add(bp.Max).Multiply(0.5)
                ir = cv.Project(c)
                s = (ir.Parameter - p0) / (p1 - p0) * dai if ir is not None else 0.0
                ds.append((ten_loai(pe), s, c.Z - z0, bp.Max.Z - bp.Min.Z))
            tron = lambda x: int(round(ft2mm(x) / 10.0))
            xuoi = tuple(sorted((a, tron(s), tron(z), tron(h)) for a, s, z, h in ds))
            nguoc = tuple(sorted((a, tron(dai - s), tron(z), tron(h)) for a, s, z, h in ds))
            return (ten_loai(wl), tron(dai), tron(bb.Max.Z - bb.Min.Z), min(xuoi, nguoc))

        ds_vach = []
        for wl in DB.FilteredElementCollector(doc).OfClass(DB.Wall):
            if not la_vach(wl):
                continue
            lv = doc.GetElement(wl.LevelId)
            p = wl.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
            cv = wl.Location.Curve
            g = cv.GetEndPoint(0).Add(cv.GetEndPoint(1)).Multiply(0.5)
            try:
                ck = chu_ky(wl)
            except Exception as ex_:
                ck = None
                w(u"   vách %d: không tính được chữ ký (%s) → coi là riêng" % (wl.Id.Value, ex_))
            ds_vach.append({"wl": wl, "id": wl.Id.Value, "tang_ten": lv.Name if lv is not None else u"-",
                            "tang": so_tang(lv), "mark_cu": (p.AsString() if p else None) or u"", "ck": ck,
                            "x": ft2mm(g.X), "y": ft2mm(g.Y), "dai": ck[1] * 10 if ck else None,
                            "cao": ck[2] * 10 if ck else None, "loai": ck[0] if ck else ten_loai(wl)})
        da_co = set(v["mark_cu"] for v in ds_vach if v["mark_cu"])
        biet = {}
        for v in ds_vach:
            if v["mark_cu"] and v["ck"] is not None:
                biet.setdefault(v["ck"], v["mark_cu"])
        dem = {}
        t_ = DB.Transaction(doc, u"Agent HS TKBVTC – đặt Mark vách kính")
        t_.Start()
        for tg in sorted(tang_can):
            ds = [v for v in ds_vach if v["tang"] == tg and not v["mark_cu"] and
                  not any(b in kd(v["loai"]) for b in bo_loai)]
            ds.sort(key=lambda v: (-int(v["y"] // 3000), v["x"]))
            for v in ds:
                if v["ck"] is not None and v["ck"] in biet:
                    mk, cach = biet[v["ck"]], u"giống vách đã đặt"
                else:
                    while True:
                        dem[tg] = dem.get(tg, 0) + 1
                        mk = dang.format(t=tg, n=dem[tg])
                        if mk not in da_co:
                            break
                    da_co.add(mk)
                    cach = u"mới"
                    if v["ck"] is not None:
                        biet[v["ck"]] = mk
                try:
                    v["wl"].get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).Set(mk)
                    v["mark_moi"], v["cach"] = mk, cach
                except Exception as ex_:
                    v["loi"] = u"%s" % ex_
                w(u"   {} | tầng {} | {} | dài {} cao {} → {} ({})".format(
                    v["id"], v["tang_ten"], v["loai"], v["dai"], v["cao"], v.get("mark_moi", u"LỖI"), cach))
        t_.Commit()
        ra = []
        for v in ds_vach:
            r_ = dict((k, v[k]) for k in v if k not in ("wl", "ck"))
            ra.append(r_)
        with io.open(os.path.join(KQ, "vk_mark.json"), "w", encoding="utf-8") as g_:
            g_.write(json.dumps(ra, ensure_ascii=False, indent=1))
        n_moi = sum(1 for v in ds_vach if v.get("mark_moi"))
        n_ten = len(set(v["mark_moi"] for v in ds_vach if v.get("mark_moi")))
        w(u"=== Vách kính: {} vách, đặt Mark {} vách ({} tên); giữ {} vách đã có Mark".format(
            len(ds_vach), n_moi, n_ten, sum(1 for v in ds_vach if v["mark_cu"])))
        KET["vk_mark"] = {"so_vach": len(ds_vach), "dat": n_moi, "so_ten": n_ten}
        if V.get("luu"):
            luu_ra(V["luu"])

    if V.get("che_do") == "khao_sat":
        khao_sat()
    elif V.get("che_do") == "script":
        # 2026-11-18: chạy 1 file Python tuỳ ý (V["script"]) trên file đã mở – dùng để soi dữ liệu model (kiểu dim,
        # section tag, Fire Rating...) khi sửa lõi nút. Biến có sẵn: doc, uiapp, DB, w, KET, KQ, V, luu_ra. Không tự lưu.
        _sp = os.path.normpath(V["script"])
        w(u"=== chạy script {}".format(_sp))
        exec(compile(io.open(_sp, encoding="utf-8").read(), _sp, "exec"),
             {"doc": doc, "uiapp": uiapp, "DB": DB, "w": w, "KET": KET, "KQ": KQ, "V": V, "luu_ra": luu_ra,
              "__name__": "__script__"})
        w(u"=== script xong")
    elif V.get("che_do") == "dat_mark_vk":
        dat_mark_vk()
    elif V.get("che_do") == "kiem_tra":
        # 2026-11-16 (G19 Side): chỉ kiểm tra + xuất ảnh MỌI bản vẽ có số hiệu bắt đầu bằng V["sheet_tien_to"], không
        # chạy nút nào, không lưu. Lý do: trong chuỗi phiên chi tiết cửa, mỗi phiên chỉ kiểm / xuất ảnh tờ phiên đó chạm
        # tới, và ảnh tờ được xuất ngay sau mục đầu nên thiếu cửa mục sau thêm vào.
        tt = V.get("sheet_tien_to") or []
        if not isinstance(tt, list):
            tt = [tt]
        tt = [u"%s" % t for t in tt]
        ds_s = sorted(DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet), key=lambda x: x.SheetNumber)
        n_kt = 0
        for s in ds_s:
            if tt and not any(s.SheetNumber.startswith(t) for t in tt):
                continue
            n_kt += 1
            w(u"=== kiểm tra bản vẽ {}".format(s.SheetNumber))
            r = kiem_sheet(s, u"", u"")
            r["muc"] = u"kiểm tra"
            KET["kiem_tra"].append(r)
            if V.get("anh", True):
                try:
                    xuat_anh(s)
                except Exception as ex:
                    r["luu_y"].append(u"Không xuất được ảnh: %s" % ex)
        w(u"=== Đã kiểm tra {} bản vẽ (tiền tố {})".format(n_kt, u", ".join(tt) or u"mọi tờ"))
    else:
        # -------------------------------------------------------- chạy theo phương án
        os.environ["ARV_HO_SO_DUYET_LOG"] = LOG
        os.environ["ARV_HO_SO_DUYET_KHONG_NHOM"] = "1"
        os.environ["ARV_HOI_ANH"] = os.path.join(KQ, "_hop_thoai.png")       # hộp thoại của lib vẽ ra PNG, không hiện
        tra = "1" if V.get("tra_loi_xoa") == "co" else "0"
        for k_ in ("ARV_XOA_TAG_VK", "ARV_VE_LAI_BANG", "ARV_GOP_HATCH"):
            os.environ[k_] = tra
        import arv_ho_so_duyet as hsd
        import arv_bang_cua
        import arv_bang_lan_can

        class HopThoaiGia(object):
            @staticmethod
            def Show(*a):
                tin = u"%s" % (a[0] if a else u"")
                KET["hop_thoai"].append(u"MessageBox: %s → Không" % tin[:300])
                w(u"   [HỘP THOẠI] {} → Không".format(tin[:300]))
                if any(t in kd(tin) for t in (kd(x) for x in TU_HOI)):
                    KET["can_hoi"].append(u"Lõi hỏi: %s → đã trả lời KHÔNG" % tin[:300])
                return arv_bang_cua.DialogResult.No
        for m_ in (arv_hoi_sheet, arv_bang_cua, arv_bang_lan_can):
            if hasattr(m_, "MessageBox"):
                m_.MessageBox = HopThoaiGia

        PA = json.load(io.open(V["phuong_an"], encoding="utf-8-sig"))
        # thông tin dự án người dùng cấp → Project Information (tên tham số đúng như trong Revit; thiếu thì báo, không tạo)
        ttda = PA.get("thong_tin_du_an") or {}
        if ttda:
            pi = doc.ProjectInformation
            t_ = DB.Transaction(doc, u"Agent HS TKBVTC – thông tin dự án")
            t_.Start()
            da_dien = []
            for k, gt in ttda.items():
                prm = pi.LookupParameter(k)
                if prm is None or prm.IsReadOnly or prm.StorageType != DB.StorageType.String:
                    KET["can_hoi"].append(u"Thông tin dự án: không điền được tham số '%s' (không có / chỉ đọc / không phải chữ)" % k)
                    continue
                prm.Set(u"%s" % gt)
                da_dien.append(k)
            t_.Commit()
            w(u"=== Thông tin dự án: đã điền {}".format(u", ".join(da_dien) or u"-"))
            KET["thong_tin_du_an"] = da_dien
        THU_TU = ("ChongTham", "NganChay", "LanCanLouver", "TagCua", "ChiTietCua")
        muc_ds = []
        chung = PA.get("chung", {})
        for mb in PA.get("mat_bang", []):
            for nut in THU_TU:
                rieng = (mb.get("viec") or {}).get(nut)
                if rieng is None:
                    continue
                d = {}
                d.update(chung)
                d.update((PA.get("nut") or {}).get(nut, {}))
                d.update(rieng)
                muc_ds.append({"view": mb["view"], "nut": nut, "so": (d.get("so") or u"").strip(),
                               "ten": (d.get("ten") or u"").strip(), "tpl": (d.get("template") or u"").strip(),
                               "tl": int(d.get("ti_le") or 0), "gd": d.get("giai_doan") or u"",
                               "hm": d.get("hang_muc") or u"", "kho": d.get("kho") or u"A1",
                               "kt": d.get("khung_ten") or u"", "mark": d.get("mark") or [],
                               # 2026-11-18: chi tiết vách kính bản vẽ riêng (tên + tầng) – số hiệu / tên riêng
                               "so_vk": (d.get("so_vk") or u"").strip(), "ten_vk": (d.get("ten_vk") or u"").strip(),
                               # 2026-11-15 (FPT P5): chọn sẵn view đích khi tầng có ≥ 2 view cùng loại; ô nhập thêm
                               # của lõi, vd. {"21": true} = Không dùng CAD link (Chống thấm / Ngăn cháy)
                               "view_dich": (d.get("view_dich") or u"").strip(),
                               # 2026-11-16 (FPT P5, người dùng "Tạo view mới, thử"): view đích có sẵn của tầng (view
                               # mẫu đã có tag / hatch) được ĐỔI TÊN trên bản sao cho nút không nhận ra → nút tạo view mới
                               "tao_view_moi": bool(d.get("tao_view_moi")),
                               "them_in": dict((int(k), v) for k, v in (d.get("them_in") or {}).items())})
                if d.get("khong_dung_cad") and nut in ("ChongTham", "NganChay"):
                    muc_ds[-1]["them_in"][21] = True
        chi = set(V.get("chi") or [])
        if chi:
            muc_ds = [m for m in muc_ds if u"%s|%s" % (m["view"], m["nut"]) in chi]
        w(u"=== {} mục: {}".format(len(muc_ds), u"; ".join(u"%s|%s" % (m["view"], m["nut"]) for m in muc_ds)))

        _DA_KIEM = set()

        def kiem_muc(kq):
            """Kiểm tra + xuất ảnh các bản vẽ của 1 mục vừa chạy (mỗi bản vẽ 1 lần)."""
            sheets = dict((s.SheetNumber, s) for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))
            for so in kq.get("sheet") or []:
                if so in _DA_KIEM or so not in sheets:
                    continue
                _DA_KIEM.add(so)
                w(u"=== kiểm tra bản vẽ {}".format(so))
                ten_mong = kq["ten_yeu_cau"]
                if kq["nut"] == "ChiTietCua" and kd(sheets[so].Name).startswith(kd(kq.get("ten_vk") or u"CHI TIẾT VÁCH KÍNH")):
                    ten_mong = u""          # bản vẽ vách kính riêng: tên = tên vách kính + tầng
                r = kiem_sheet(sheets[so], kq["so_yeu_cau"] if kq["nut"] != "ChiTietCua" else u"", ten_mong)
                r["muc"] = u"%s – %s" % (kq["view"], kq["nut"])
                KET["kiem_tra"].append(r)
                if V.get("anh", True):
                    try:
                        xuat_anh(sheets[so])
                    except Exception as ex:
                        r["luu_y"].append(u"Không xuất được ảnh: %s" % ex)
            if not kq.get("sheet") and not kq["loi"]:
                KET["kiem_tra"].append({"muc": u"%s – %s" % (kq["view"], kq["nut"]), "so": None, "dat": False,
                                        "loi": [u"Mục không nằm trên bản vẽ nào"], "luu_y": []})

        def _tra_loi_them(ham_goc):
            """Câu trả lời của nút Hồ sơ đã duyệt + ô nhập thêm của mục (them_in)."""
            def ham(*a):
                ra = ham_goc(*a)
                m_ = hsd._DANG.get("muc") or {}
                if ra is not None and m_.get("them_in"):
                    ra.update(m_["them_in"])
                    hsd._DANG["tra_loi"] = ra
                return ra
            return ham

        # trả lời sẵn hộp thoại của 4 nút mặt bằng (như nút Hồ sơ đã duyệt) + Chi tiết cửa
        goc_ham = dict((hsd.NUT[n]["ham"], getattr(arv_hoi_sheet, hsd.NUT[n]["ham"])) for n in hsd.NUT)
        goc_ham["hoi_chi_tiet_cua"] = arv_hoi_sheet.hoi_chi_tiet_cua
        for n in hsd.NUT:
            setattr(arv_hoi_sheet, hsd.NUT[n]["ham"], _tra_loi_them(hsd._tra_loi(n)))

        def hoi_ctc(doc_, view_, uidoc_=None):
            m = hsd._DANG.get("muc") or {}
            ra = {1: m.get("kt") or u"", 2: (m.get("ten") or u"CHI TIẾT CỬA").upper(), 3: m.get("so") or u"",
                  16: m.get("gd") or u"", 17: m.get("hm") or u"",
                  # vách kính: bản vẽ riêng mỗi tầng (khung tên / giai đoạn / hạng mục như cửa)
                  18: m.get("kt") or u"", 19: (m.get("ten_vk") or u"CHI TIẾT VÁCH KÍNH").upper(), 20: m.get("so_vk") or u"",
                  21: m.get("gd") or u"", 22: m.get("hm") or u""}
            ra.update(m.get("them_in") or {})       # ô nhập thêm của mục, vd. {"0": "id;id"} = danh sách đối tượng
            hsd._DANG["tra_loi"] = ra
            return ra
        arv_hoi_sheet.hoi_chi_tiet_cua = hoi_ctc
        tra_loi_tag = hsd._thay_loi_tag(PA.get("tag_cua") or "goc", w)
        nhom = hsd._Nhom(doc, w)

        def chon_cua(v, marks):
            """Chọn trên mặt bằng v mỗi Type Mark (cửa) / Mark (vách kính) 1 đối tượng. Trả về (số chọn, [thiếu])."""
            refs = NetList[DB.Reference]()
            con = [u"%s" % x for x in marks]
            for e, li in phan_tu_tang(v):
                k = khoa_cua(e)
                if not k:
                    continue
                mk = k.split(u" ", 1)[1] if not k.startswith(u"Vách") else k[len(u"Vách kính "):]
                if mk in con:
                    r_ = DB.Reference(e)
                    refs.Add(r_.CreateLinkReference(li) if li is not None else r_)
                    con.remove(mk)
            uiapp.ActiveUIDocument.Selection.SetReferences(refs)
            return refs.Count, con

        _DOI_TEN = ((u"ĐỊNH VỊ", u"ĐV"), (u"Định vị", u"ĐV"), (u"định vị", u"ĐV"), (u"CHỐNG THẤM", u"CTH"),
                    (u"Chống thấm", u"CTH"), (u"chống thấm", u"CTH"), (u"CHÁY LAN", u"CLAN"), (u"CHAY LAN", u"CLAN"),
                    (u"Cháy lan", u"CLAN"), (u"cháy lan", u"CLAN"))

        def an_view_mau(mb_, m_, kq_):
            """Khoá tao_view_moi: đổi tên view đích có sẵn cùng tầng (CHỈ trên bản sao) để nút không nhận ra mà tạo view
            mới. View vẫn nằm nguyên trên bản vẽ cũ, không xoá gì. Template của view mang chữ khoá thì không giấu được
            bằng đổi tên → không chạy, ghi can_hoi."""
            tk = hsd.NUT[m_["nut"]]["tu_khoa"]
            ds = hsd.view_dich(doc, mb_, m_["nut"])
            if not ds:
                return
            vuong = [v for v in ds if tk not in kd(v.Name)]
            if vuong:
                KET["can_hoi"].append(u"%s – %s: view có template mang chữ khoá '%s', đổi tên không giấu được: %s" % (
                    m_["view"], m_["nut"], tk, u"; ".join(v.Name for v in vuong)))
                raise Exception(u"tao_view_moi: không giấu được view mẫu (template mang chữ khoá) – không chạy.")
            t_ = DB.Transaction(doc, u"Agent HS TKBVTC – đổi tên view mẫu")
            t_.Start()
            try:
                for v in ds:
                    cu = v.Name
                    moi = cu
                    for a, b in _DOI_TEN:
                        moi = moi.replace(a, b)
                    moi = u"MẪU - " + moi
                    if tk in kd(moi):
                        moi = u"MẪU - view %d" % v.Id.Value
                    try:
                        v.Name = moi
                    except Exception:
                        moi = u"%s (%d)" % (moi, v.Id.Value)
                        v.Name = moi
                    dong = u"Đổi tên view mẫu (bản sao, để nút tạo view mới): '%s' → '%s'%s" % (
                        cu, moi, u" – vẫn nằm trên bản vẽ %s" % so_sheet(v) if so_sheet(v) else u"")
                    kq_["dong"].append(dong)
                    w(u"   " + dong)
                t_.Commit()
            except BaseException:
                if t_.HasStarted() and not t_.HasEnded():
                    t_.RollBack()
                raise

        try:
            for m in muc_ds:
                kq = {"view": m["view"], "nut": m["nut"], "so_yeu_cau": m["so"], "ten_yeu_cau": m["ten"],
                      "ten_vk": m.get("ten_vk") or u"", "dong": [],
                      "can_xem": [], "loi": False}
                KET["muc"].append(kq)
                w(u"=== {} – {} ({}) {}".format(m["view"], m["nut"], m["so"], datetime.datetime.now().strftime("%H:%M:%S")))
                try:
                    mb = hsd.mat_bang_nguon(doc, m["view"])
                    if mb is None:
                        raise Exception(u"File không có mặt bằng tầng tên '%s'" % m["view"])
                    mo_view = mb
                    if m["tao_view_moi"] and m["nut"] in hsd.NUT and m["nut"] != "TagCua":
                        an_view_mau(mb, m, kq)
                    if m["nut"] in hsd.NUT and m["nut"] != "TagCua":
                        dich = hsd.view_dich(doc, mb, m["nut"])
                        if m["view_dich"]:
                            # mở thẳng view đích → nút dùng view đang mở, không hỏi chọn view
                            chon = [x for x in dich if x.Name == m["view_dich"]]
                            if not chon:
                                raise Exception(u"Không có view đích '%s' cùng tầng (view đích có: %s)" % (
                                    m["view_dich"], u"; ".join(x.Name for x in dich) or u"-"))
                            mo_view = chon[0]
                        elif len(dich) > 1:
                            # nút sẽ mở hộp chọn view (WinForms) và chờ mãi trong phiên nền → không chạy, hỏi người dùng
                            KET["can_hoi"].append(u"%s – %s: tầng có %d view đích, cần chọn 1 (khoá view_dich): %s" % (
                                m["view"], m["nut"], len(dich), u" | ".join(
                                    u"%s%s" % (x.Name, u" (bản vẽ %s)" % so_sheet(x) if so_sheet(x) else u"") for x in dich)))
                            raise Exception(u"Tầng có %d view đích cùng loại – chưa chọn view_dich, không chạy." % len(dich))
                    hsd._doi_view(uiapp.ActiveUIDocument, doc, mo_view, nhom, u"Agent HS TKBVTC")
                    hsd._DANG.clear()
                    hsd._DANG["muc"] = m
                    sh_truoc = set(s.Id.Value for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet))
                    if m["nut"] == "ChiTietCua":
                        n_chon, thieu = chon_cua(mb, m["mark"])
                        w(u"   chọn {} đối tượng; không thấy: {}".format(n_chon, u", ".join(thieu) or u"-"))
                        if thieu:
                            kq["can_xem"].append(u"Không thấy trên tầng: %s" % u", ".join(thieu))
                        if m["them_in"].get(0):
                            # danh sách id có sẵn (IN[0]) → lõi làm đúng các id đó, không dùng vùng chọn
                            w(u"   IN[0] = {}".format(m["them_in"][0]))
                        elif not n_chon:
                            raise Exception(u"Không chọn được cửa / vách kính nào (Mark: %s) – không chạy để nút không "
                                            u"chờ chọn trên màn hình." % u", ".join(m["mark"]))
                    kq["dong"] = hsd._chay_nut(uiapp, PANEL, m["nut"], w)
                    kq["tra_loi"] = hsd._DANG.get("tra_loi")
                    kq["can_xem"] += [ln.strip() for ln in kq["dong"] if u"CẦN XEM LẠI" in ln or u"KHÔNG " in ln[:12]]
                    # bản vẽ của mục
                    if m["nut"] == "ChiTietCua":
                        moi = [s for s in DB.FilteredElementCollector(doc).OfClass(DB.ViewSheet)
                               if s.Id.Value not in sh_truoc or s.SheetNumber == m["so"]]
                        kq["sheet"] = sorted(s.SheetNumber for s in moi)
                    else:
                        dich = hsd.view_dich(doc, mb, m["nut"])
                        if m["view_dich"]:
                            dich = [x for x in dich if x.Name == m["view_dich"]] or dich
                        kq["view_dich"] = dich[0].Name if dich else None
                        kq["sheet"] = [so_sheet(dich[0])] if dich and so_sheet(dich[0]) else []
                except BaseException:
                    kq["dong"].append(u"LỖI: " + traceback.format_exc())
                    w(u"   LỖI: " + traceback.format_exc())
                kq["loi"] = any(ln.strip().startswith((u"LỖI", u"Traceback")) for ln in kq["dong"])
                if kq["loi"]:
                    KET["loi"].append(u"%s – %s" % (m["view"], m["nut"]))
                # kiểm tra + ảnh NGAY sau mục (2026-11-15 FPT P5: mục sau treo thì kết quả mục trước vẫn còn)
                try:
                    kiem_muc(kq)
                except Exception as ex_:
                    w(u"   lỗi kiểm tra mục: %s" % ex_)
                ghi_json()
        finally:
            hsd._DANG.clear()
            for k, v in goc_ham.items():
                setattr(arv_hoi_sheet, k, v)
            tra_loi_tag()

        # (kiểm tra + ảnh từng bản vẽ: kiem_muc, gọi ngay sau mỗi mục ở vòng lặp trên)
        ghi_json()

        # -------------------------------------------------------- lưu ra file mới
        luu = V.get("luu")
        if luu:
            if os.path.isfile(luu):
                KET["loi"].append(u"KHÔNG LƯU: đã có file %s (không ghi đè)" % luu)
            else:
                if not os.path.isdir(os.path.dirname(luu)):
                    os.makedirs(os.path.dirname(luu))
                o_ = DB.SaveAsOptions()
                o_.OverwriteExistingFile = False
                if doc.IsWorkshared:
                    ws_ = DB.WorksharingSaveAsOptions()
                    ws_.SaveAsCentral = True
                    o_.SetWorksharingOptions(ws_)
                doc.SaveAs(luu, o_)
                KET["da_luu"] = luu
                w(u"=== Đã lưu {}".format(luu))

    # ------------------------------------------------------------ tóm tắt
    w(u"-" * 100)
    for kq in KET["muc"]:
        w(u"{} | {} | bản vẽ {} | {}".format(kq["view"], kq["nut"], u", ".join(kq.get("sheet") or []) or u"-",
                                           u"LỖI" if kq["loi"] else u"chạy xong"))
        for ln in kq["dong"]:
            s = ln.strip()
            if s.startswith(hsd.DONG_CHINH if V.get("che_do") != "khao_sat" else ()):
                w(u"      " + s[:400])
    for r in KET["kiem_tra"]:
        w(u"KIỂM TRA {} ({}): {}".format(r.get("so"), r.get("muc"), u"ĐẠT" if r.get("dat") else u"KHÔNG ĐẠT"))
        for x in r.get("loi", []) + r.get("luu_y", []):
            w(u"      - " + x)
    for x in KET["can_hoi"]:
        w(u"CẦN HỎI: " + x)
except SystemExit:
    pass
except BaseException:
    KET["loi"].append(traceback.format_exc())
    w(u"LỖI: " + traceback.format_exc())
finally:
    KET["ket_thuc"] = datetime.datetime.now().isoformat()
    try:
        ghi_json()
    except Exception:
        pass
    w(u"XONG {}".format(datetime.datetime.now()))
    f.close()
