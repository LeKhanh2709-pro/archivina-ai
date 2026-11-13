#! python3
# -*- coding: utf-8 -*-
"""Vẽ các ô chi tiết CAD (đã trích ra ct_cua.json bằng trich_xuat.py) vào MỘT legend Revit mới.

- Nét  -> Detail Line, kiểu nét dựng sẵn của Revit: <Thin Lines> / <Medium Lines> / <Wide Lines> / <Hidden Lines> /
          <Centerline> (theo lineweight + linetype CAD). Nét trùng đã gộp còn 1 nét ở bước trích xuất.
- Hatch -> Filled Region (viền <Invisible lines>), kiểu `CTC_<mẫu>`; mẫu hatch CAD -> fill pattern Model `CTC_<mẫu>`
          dựng đúng định nghĩa đường mẫu của CAD; hatch đặc giữ màu.
- Wipeout -> Filled Region trắng (che), theo thứ tự vẽ của CAD.
- Chữ  -> Text Note kiểu `CTC_<font> <cỡ>mm` (cỡ giấy = cỡ CAD / tỉ lệ legend).
- Dim tuyến tính -> Dimension kiểu `CTC_Dim <cỡ>mm`, bám 2 đầu một nét <Invisible lines>; chữ dim CAD khác số đo thì ghi đè.
- Mỗi ô chi tiết -> 1 detail group `CTC_<mã ô>`.
Không xoá, không sửa phần tử / kiểu có sẵn; chỉ tạo mới. Kiểu đã có cùng tên thì dùng lại.

Biến môi trường: ARV_CTC_JSON (đường dẫn json), ARV_CTC_LOG (file log), ARV_CTC_ANH (thư mục xuất ảnh, trống = không),
ARV_CTC_CHI (danh sách tên ô cách nhau |, trống = tất cả), ARV_CTC_TEN (tên legend).
"""
import locale
locale.setlocale(locale.LC_ALL, "C")   # tránh Revit văng khi nạp ExportDWGSettings (xem CLAUDE.md)
import io, os, json, math, time, traceback, datetime

GOC = os.path.dirname(os.path.abspath(__file__))
JSON = os.environ.get("ARV_CTC_JSON") or os.path.join(GOC, "ct_cua.json")
LOG = os.environ.get("ARV_CTC_LOG") or os.path.join(GOC, "kq", "ve_legend_log.txt")
ANH = os.environ.get("ARV_CTC_ANH", os.path.join(GOC, "kq"))
CHI = [s for s in os.environ.get("ARV_CTC_CHI", "").split("|") if s]
TEN_LEGEND = os.environ.get("ARV_CTC_TEN") or u"CHI TIẾT CỬA (CAD)"
if not os.path.isdir(os.path.dirname(LOG)):
    os.makedirs(os.path.dirname(LOG))
f = io.open(LOG, "w", encoding="utf-8")


def w(s):
    f.write(u"{}\n".format(s)); f.flush()


MM = 1.0 / 304.8
# Chữ / dim (người dùng chốt 2026-11-13: 1 kiểu chữ, 1 kiểu dim, ít cỡ chữ nhất). Cỡ giấy mm = cỡ CAD / tỉ lệ legend.
FONT_CHUNG = u"Arial"
CO_CHU = [(3.3, 2.5), (4.6, 3.5), (1e9, 5.0)]   # < 3,3 mm -> 2,5; < 4,6 -> 3,5; còn lại -> 5 (cỡ chuẩn ISO)
CHU_BO_DUOI = 1.0                                # chữ CAD < 1 mm giấy (gần như không đọc được) thì bỏ, có báo
CO_DIM = 2.5
CAM = u'\\:{}[]|;<>?`~'


def sach_ten(s):
    for c in CAM:
        s = s.replace(c, u"-")
    return s.strip()


try:
    import clr
    clr.AddReference("RevitAPI")
    import Autodesk.Revit.DB as DB
    from System.Collections.Generic import List as NetList

    doc = __revit__.ActiveUIDocument.Document
    w(u"=== Bắt đầu {} | {}".format(datetime.datetime.now(), doc.PathName))
    d = json.load(io.open(JSON, encoding="utf-8"))
    TL = int(d.get("ti_le", 20))
    o_ds = [o for o in d["o"] if not CHI or o["ten"] in CHI]
    w(u"Số ô: {} | tỉ lệ 1:{}".format(len(o_ds), TL))
    FEC = DB.FilteredElementCollector

    def ten_pt(e):
        try:
            return e.Name
        except Exception:
            p = e.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM)
            return p.AsString() if p else u""

    class _BoQuaCanhBao(DB.IFailuresPreprocessor):
        __namespace__ = "ARV.CTC.X%d" % int(time.time() * 1000)

        def PreprocessFailures(self, fa):
            for m in fa.GetFailureMessages():
                if m.GetSeverity() == DB.FailureSeverity.Warning:
                    fa.DeleteWarning(m)
            return DB.FailureProcessingResult.Continue

    def giao_dich(ten):
        t = DB.Transaction(doc, ten)
        op = t.GetFailureHandlingOptions()
        op.SetFailuresPreprocessor(_BoQuaCanhBao())
        op.SetClearAfterRollback(True)
        t.SetFailureHandlingOptions(op)
        t.Start()
        return t

    tg = DB.TransactionGroup(doc, u"Vẽ chi tiết CAD vào legend")
    tg.Start()

    # ------------------------------------------------------------ legend
    ten_view = set(v.Name for v in FEC(doc).OfClass(DB.View))
    ten = TEN_LEGEND
    k = 2
    while ten in ten_view:
        ten = u"{} ({})".format(TEN_LEGEND, k); k += 1
    mau_lg = [v for v in FEC(doc).OfClass(DB.View) if v.ViewType == DB.ViewType.Legend and not v.IsTemplate]
    if not mau_lg:
        raise Exception(u"Dự án chưa có legend nào để nhân bản (Revit API không tạo legend mới từ đầu). "
                        u"Tạo tay 1 legend bất kỳ rồi bấm lại.")
    t = giao_dich(u"Tạo legend")
    lg = doc.GetElement(mau_lg[0].Duplicate(DB.ViewDuplicateOption.Duplicate))
    lg.Name = ten
    lg.Scale = TL
    t.Commit()
    co_san = list(FEC(doc, lg.Id).WhereElementIsNotElementType().ToElementIds())
    w(u"Legend mới: {} (id {}), nhân bản từ '{}', phần tử có sẵn trong view: {}".format(ten, lg.Id.Value, mau_lg[0].Name, len(co_san)))

    # ------------------------------------------------------------ kiểu nét
    cat_lines = doc.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Lines)
    sub = {}
    for sc in cat_lines.SubCategories:
        sub[sc.Name] = sc

    def gs(ten_ds, bic_ten=None):
        if bic_ten and hasattr(DB.BuiltInCategory, bic_ten):
            v = int(getattr(DB.BuiltInCategory, bic_ten))
            for sc in cat_lines.SubCategories:
                if sc.Id.Value == v:
                    return sc.GetGraphicsStyle(DB.GraphicsStyleType.Projection)
        for n in ten_ds:
            if n in sub:
                return sub[n].GetGraphicsStyle(DB.GraphicsStyleType.Projection)
        return None
    KIEU = {
        "thin": gs([u"<Thin Lines>", u"Thin Lines"], "OST_CurvesThinLines"),
        "medium": gs([u"<Medium Lines>", u"Medium Lines"], "OST_CurvesMediumLines"),
        "wide": gs([u"<Wide Lines>", u"Wide Lines"], "OST_CurvesWideLines"),
        "hidden": gs([u"<Hidden Lines>", u"Hidden Lines", u"<Hidden>"]),
        "center": gs([u"<Centerline>", u"Centerline"], "OST_CenterLines"),
    }
    AN = gs([u"<Invisible lines>", u"Invisible lines"], "OST_InvisibleLines")
    if AN is None:
        for g_ in FEC(doc).OfClass(DB.GraphicsStyle):
            if g_.Name in (u"<Invisible lines>", u"Invisible lines") and g_.GraphicsStyleType == DB.GraphicsStyleType.Projection:
                AN = g_; break
    for kk, v in KIEU.items():
        if v is None:
            KIEU[kk] = KIEU["thin"]
    w(u"Kiểu nét: " + u", ".join(u"{}={}".format(kk, v.Name if v else None) for kk, v in KIEU.items()) +
      u" | ẩn={} (id {}, hạng mục {})".format(AN.Name if AN else None, AN.Id.Value if AN else None,
                                               AN.GraphicsStyleCategory.Name if AN else None))

    # ------------------------------------------------------------ mẫu hatch + kiểu filled region
    t = giao_dich(u"Kiểu hatch")
    solid_fp = None
    for e in FEC(doc).OfClass(DB.FillPatternElement):
        if e.GetFillPattern().IsSolidFill:
            solid_fp = e; break
    fp_ten = dict((e.Name, e) for e in FEC(doc).OfClass(DB.FillPatternElement))
    frt_all = list(FEC(doc).OfClass(DB.FilledRegionType))
    frt_ten = dict((ten_pt(e), e) for e in frt_all)
    goc_frt = frt_all[0]

    def nhom_dash(ds):
        """Dash CAD (+ nét, - hở, 0 chấm) -> (độ dịch gốc, segments Revit dương xen kẽ nét / hở, bắt đầu bằng nét)."""
        if not ds:
            return 0.0, []
        it = []
        for x in ds:
            if x > 0:
                it.append([1, x])
            elif x < 0:
                it.append([0, -x])
            else:
                it.append([1, 0.3])     # chấm
        gop = []
        for a in it:
            if gop and gop[-1][0] == a[0]:
                gop[-1][1] += a[1]
            else:
                gop.append(list(a))
        dich = 0.0
        if gop[0][0] == 0:               # bắt đầu bằng hở: đưa ra cuối
            dich = gop[0][1]
            gop = gop[1:] + [gop[0]]
            if len(gop) >= 2 and gop[-1][0] == gop[-2][0]:
                gop[-2][1] += gop[-1][1]; gop.pop()
        if gop[-1][0] == 1 and len(gop) > 1:   # kết thúc bằng nét: gộp vào nét đầu
            dich -= gop[-1][1]
            gop[0][1] += gop[-1][1]; gop.pop()
        if len(gop) == 1:
            return 0.0, []                # chỉ có nét: nét liền
        if len(gop) % 2:
            gop.append([0, 0.3])
        return dich, [max(g[1], 0.05) for g in gop]

    KIEU_HATCH = {}
    loi_mau = []
    for key, m in d["mau_hatch"].items():
        ten_k = sach_ten(u"CTC_" + m["ten"])
        mau = DB.Color(*[int(c) for c in m["rgb"]])
        if m["solid"]:
            fpe = solid_fp
        else:
            ten_fp = ten_k if ten_k not in fp_ten or key in ten_k else ten_k
            # cùng tên nhưng khác định nghĩa (khác key) -> thêm mã key
            ten_fp = sach_ten(u"CTC_{} [{}]".format(m["ten"], key))
            fpe = fp_ten.get(ten_fp)
            if fpe is None:
                grids = NetList[DB.FillGrid]()
                for (ang, bx, by, ox, oy, ds) in m["lines"]:
                    a = math.radians(ang)
                    ux, uy = math.cos(a), math.sin(a)
                    perp = -ox * uy + oy * ux
                    shift = ox * ux + oy * uy
                    if perp < 0:
                        perp, shift = -perp, -shift
                    if perp < 1e-3:
                        continue
                    dich, seg = nhom_dash(ds)
                    g = DB.FillGrid()
                    g.Angle = a
                    g.Origin = DB.UV((bx + dich * ux) * MM, (by + dich * uy) * MM)
                    g.Offset = perp * MM
                    g.Shift = shift * MM
                    if seg:
                        sl = NetList[float]()
                        for s in seg:
                            sl.Add(s * MM)
                        g.SetSegments(sl)
                    grids.Add(g)
                if grids.Count == 0:
                    loi_mau.append(key); fpe = solid_fp
                else:
                    try:
                        fp = DB.FillPattern(ten_fp, DB.FillPatternTarget.Model, DB.FillPatternHostOrientation.ToView)
                        fp.SetFillGrids(grids)
                        fpe = DB.FillPatternElement.Create(doc, fp)
                        fp_ten[ten_fp] = fpe
                    except Exception as ex:
                        loi_mau.append(u"{} ({})".format(key, ex)); fpe = solid_fp
            ten_k = ten_fp
        frt = frt_ten.get(ten_k)
        if frt is None:
            frt = goc_frt.Duplicate(ten_k)
            frt.ForegroundPatternId = fpe.Id
            frt.ForegroundPatternColor = mau
            frt.BackgroundPatternId = DB.ElementId.InvalidElementId
            try:
                frt.IsMasking = False
            except Exception:
                pass
            try:
                frt.LineWeight = 1
            except Exception:
                pass
            frt_ten[ten_k] = frt
        KIEU_HATCH[key] = frt.Id
    # vùng che (wipeout)
    ten_che = u"CTC_Che trắng"
    frt = frt_ten.get(ten_che)
    if frt is None:
        frt = goc_frt.Duplicate(ten_che)
        frt.ForegroundPatternId = solid_fp.Id
        frt.ForegroundPatternColor = DB.Color(255, 255, 255)
        frt.BackgroundPatternId = DB.ElementId.InvalidElementId
        try:
            frt.IsMasking = True
        except Exception:
            pass
    KIEU_CHE = frt.Id
    t.Commit()
    w(u"Kiểu filled region: {} | mẫu lỗi / thay bằng đặc: {}".format(len(KIEU_HATCH), loi_mau))

    # ------------------------------------------------------------ kiểu chữ + kiểu dim
    t = giao_dich(u"Kiểu chữ, dim")
    tnt_all = list(FEC(doc).OfClass(DB.TextNoteType))
    tnt_ten = dict((ten_pt(e), e) for e in tnt_all)
    KIEU_CHU = {}

    def dat(e, bip, v):
        p = e.get_Parameter(bip)
        if p is not None and not p.IsReadOnly:
            p.Set(v)

    def co_chu(h):
        """Cỡ chữ CAD (mm mô hình) -> 1 trong 3 cỡ giấy chuẩn; None = chữ quá nhỏ trong CAD (không đọc được), bỏ qua."""
        hg = h / TL
        if hg < CHU_BO_DUOI:
            return None
        for nguong, co in CO_CHU:
            if hg < nguong:
                return co
        return CO_CHU[-1][1]

    def kieu_chu(font, h, wf):
        # người dùng chốt 2026-11-13: 1 kiểu chữ (Arial, rộng 1), ít cỡ nhất -> bỏ qua font / hệ số rộng của CAD
        hg = co_chu(h)
        font, wf = FONT_CHUNG, 1.0
        ten_t = u"CTC_{} {:g}mm".format(font, hg)
        if ten_t in KIEU_CHU:
            return KIEU_CHU[ten_t]
        e = tnt_ten.get(ten_t)
        if e is None:
            e = tnt_all[0].Duplicate(ten_t)
            dat(e, DB.BuiltInParameter.TEXT_SIZE, hg * MM)
            dat(e, DB.BuiltInParameter.TEXT_FONT, font)
            dat(e, DB.BuiltInParameter.TEXT_WIDTH_SCALE, float(wf))
            dat(e, DB.BuiltInParameter.TEXT_BACKGROUND, 1)        # trong suốt
            dat(e, DB.BuiltInParameter.TEXT_BOX_VISIBILITY, 0)
            dat(e, DB.BuiltInParameter.LINE_COLOR, 0)
            dat(e, DB.BuiltInParameter.TEXT_STYLE_BOLD, 0)
            dat(e, DB.BuiltInParameter.TEXT_STYLE_ITALIC, 0)
            dat(e, DB.BuiltInParameter.TEXT_STYLE_UNDERLINE, 0)
            tnt_ten[ten_t] = e
        KIEU_CHU[ten_t] = e.Id
        return e.Id

    dt_all = [e for e in FEC(doc).OfClass(DB.DimensionType) if e.StyleType == DB.DimensionStyleType.Linear]
    dt_ten = dict((ten_pt(e), e) for e in dt_all)
    # kiểu gốc để nhân bản: ưu tiên kiểu có gạch chéo (tick) như CAD
    goc_dt = None
    for e in dt_all:
        try:
            tk = doc.GetElement(e.get_Parameter(DB.BuiltInParameter.DIM_LEADER_ARROWHEAD).AsElementId())
            if tk is not None and any(s in ten_pt(tk).lower() for s in (u"diagonal", u"arch", u"slash", u"tick")):
                goc_dt = e; break
        except Exception:
            pass
    goc_dt = goc_dt or (dt_all[0] if dt_all else None)
    KIEU_DIM = {}

    def kieu_dim(h):
        # người dùng chốt 2026-11-13: 1 kiểu dim cho mọi dim
        hg = CO_DIM
        ten_t = u"CTC_Dim {:g}mm".format(hg)
        if ten_t in KIEU_DIM:
            return KIEU_DIM[ten_t]
        e = dt_ten.get(ten_t)
        if e is None:
            e = goc_dt.Duplicate(ten_t)
            dat(e, DB.BuiltInParameter.TEXT_SIZE, hg * MM)
            dat(e, DB.BuiltInParameter.TEXT_FONT, u"Arial")
            dat(e, DB.BuiltInParameter.TEXT_WIDTH_SCALE, 1.0)
            dat(e, DB.BuiltInParameter.TEXT_BACKGROUND, 1)
            dt_ten[ten_t] = e
        KIEU_DIM[ten_t] = e.Id
        return e.Id

    CHU_BO = [0]
    for o in o_ds:
        bo = [c for c in o["chu"] if co_chu(c["h"]) is None]
        if bo:
            CHU_BO[0] += len(bo)
            w(u"  {}: bỏ {} chữ quá nhỏ (< {} mm giấy): {}".format(o["ten"], len(bo), CHU_BO_DUOI,
                                                                    u", ".join(sorted(set(c["t"][:20] for c in bo)))))
        o["chu"] = [c for c in o["chu"] if co_chu(c["h"]) is not None]
        for c in o["chu"]:
            kieu_chu(c["font"], c["h"], c["wf"])
        for dm in o["dim"]:
            kieu_dim(dm["h"])
    t.Commit()
    w(u"Kiểu chữ: {} | kiểu dim: {} (nhân bản từ '{}')".format(len(KIEU_CHU), len(KIEU_DIM), ten_pt(goc_dt) if goc_dt else None))

    # ------------------------------------------------------------ vẽ từng ô
    def XYZ(x, y):
        return DB.XYZ(x * MM, y * MM, 0)

    def ds_id(it):
        """List[ElementId] từ list Python (CPython pyRevit: List[T](list) lỗi -> Add từng cái)."""
        kq = NetList[DB.ElementId]()
        for i in it:
            kq.Add(i)
        return kq

    TG = {}

    def bam(k, t_):
        TG[k] = TG.get(k, 0.0) + time.time() - t_

    def cung_3(x0, y0, xm, ym, x1, y1):
        return DB.Arc.Create(XYZ(x0, y0), XYZ(x1, y1), XYZ(xm, ym))

    def vong(loop):
        cl = DB.CurveLoop()
        for s in loop:
            if s[0] == "L":
                cl.Append(DB.Line.CreateBound(XYZ(s[1], s[2]), XYZ(s[3], s[4])))
            else:
                cl.Append(cung_3(*s[1:7]))
        return cl

    def tao_vung(loops, typ):
        ls = NetList[DB.CurveLoop]()
        for l in loops:
            ls.Add(vong(l))
        fr = DB.FilledRegion.Create(doc, typ, lg.Id, ls)
        if AN is not None:
            try:
                fr.SetLineStyleId(AN.Id)
            except Exception:
                pass
        return fr

    TONG = {"net": 0, "cung": 0, "vung": 0, "che": 0, "chu": 0, "dim": 0}
    TONG["chu_qua_nho_bo"] = CHU_BO[0]
    LOI = {"net": 0, "cung": 0, "vung": 0, "che": 0, "chu": 0, "dim": 0}
    loi_mau_vd = []
    HA = {"L": DB.HorizontalTextAlignment.Left, "C": DB.HorizontalTextAlignment.Center, "R": DB.HorizontalTextAlignment.Right}
    VA = {"T": DB.VerticalTextAlignment.Top, "M": DB.VerticalTextAlignment.Middle, "B": DB.VerticalTextAlignment.Bottom}
    gt_ten = set(ten_pt(g) for g in FEC(doc).OfClass(DB.GroupType))
    nhom_ds = []
    for o in o_ds:
        t0 = time.time()
        t = giao_dich(u"Ô " + o["ten"])
        ids = NetList[DB.ElementId]()
        # thứ tự vẽ CAD: vùng / che / nét / cung theo z; chữ + dim sau cùng
        muc = [(v["z"], 0, "vung", v) for v in o["vung"]] + [(v["z"], 0, "che", v) for v in o["che"]] + \
              [(n[5], 1, "net", n) for n in o["net"]] + [(c[6], 1, "cung", c) for c in o["cung"]]
        muc.sort(key=lambda x: (x[0], x[1]))
        lo = []          # gom nét liên tiếp để tạo 1 lần
        dau_mut = {}     # đầu mút nét thẳng đã vẽ (lưới 0,5 mm) -> (nét, 0/1): dim bám vào nét CAD thật

        net_thang = []   # (nét, x1, y1, x2, y2) mm

        def ghi_dau_mut(dc):
            cv = dc.GeometryCurve
            if cv.GetType().Name != "Line":     # PythonNet trả về kiểu Curve: không dùng isinstance
                return
            a, b = cv.GetEndPoint(0), cv.GetEndPoint(1)
            net_thang.append((dc, a.X / MM, a.Y / MM, b.X / MM, b.Y / MM))

        def tim_tham_chieu(p, u, xa=400.0):
            """Reference của nét CAD thật cùng vị trí với điểm đo p theo phương đo u (sai ≤ 0,3 mm),
            gần đường gióng nhất (≤ xa mm): đầu mút nét, hoặc nét vuông góc với dim. Trả về (khoá, Reference)."""
            nx, ny = -u[1], u[0]
            tot = None
            for (dc, x1, y1, x2, y2) in net_thang:
                for j, (qx, qy) in enumerate(((x1, y1), (x2, y2))):
                    a = abs((qx - p[0]) * u[0] + (qy - p[1]) * u[1])
                    if a < 0.3:
                        bb = abs((qx - p[0]) * nx + (qy - p[1]) * ny)
                        if bb <= xa and (tot is None or bb < tot[0]):
                            tot = (bb, (dc.Id.Value, j), dc, j)
                dx, dy = x2 - x1, y2 - y1
                L = math.hypot(dx, dy)
                if L > 0 and abs((dx * u[0] + dy * u[1]) / L) < 1e-3:       # nét vuông góc với dim
                    a = abs((x1 - p[0]) * u[0] + (y1 - p[1]) * u[1])
                    if a < 0.3:
                        s1 = (x1 - p[0]) * nx + (y1 - p[1]) * ny
                        s2 = (x2 - p[0]) * nx + (y2 - p[1]) * ny
                        bb = 0.0 if min(s1, s2) <= 0 <= max(s1, s2) else min(abs(s1), abs(s2))
                        if bb <= xa and (tot is None or bb < tot[0]):
                            tot = (bb, (dc.Id.Value, -1), dc, -1)
            if tot is None:
                return None
            dc, j = tot[2], tot[3]
            ref = dc.GeometryCurve.Reference if j < 0 else dc.GeometryCurve.GetEndPointReference(j)
            return tot[1], ref

        def xa_lo():
            if not lo:
                return
            t_ = time.time()
            ca = DB.CurveArray()
            kieu_lo = []
            for (loai, it) in lo:
                try:
                    if loai == "net":
                        cv = DB.Line.CreateBound(XYZ(it[0], it[1]), XYZ(it[2], it[3]))
                        kk = it[4]
                    else:
                        cx, cy, r, a0, a1, kk = it[0], it[1], it[2], it[3], it[4], it[5]
                        if a1 - a0 >= 359.99:
                            cv = DB.Arc.Create(XYZ(cx, cy), r * MM, 0.0, 2 * math.pi, DB.XYZ.BasisX, DB.XYZ.BasisY)
                        else:
                            cv = DB.Arc.Create(XYZ(cx, cy), r * MM, math.radians(a0), math.radians(a1), DB.XYZ.BasisX, DB.XYZ.BasisY)
                    ca.Append(cv); kieu_lo.append(kk)
                    TONG[loai] += 1
                except Exception:
                    LOI[loai] += 1
            if ca.Size:
                try:
                    dca = doc.Create.NewDetailCurveArray(lg, ca)
                    for i in range(dca.Size):
                        dc = dca.get_Item(i)
                        g = KIEU.get(kieu_lo[i])
                        if g is not None and dc.LineStyle.Id != g.Id:
                            dc.LineStyle = g
                        ids.Add(dc.Id)
                        ghi_dau_mut(dc)
                except Exception:
                    # tạo từng nét để biết nét nào lỗi
                    for i in range(ca.Size):
                        try:
                            dc = doc.Create.NewDetailCurve(lg, ca.get_Item(i))
                            g = KIEU.get(kieu_lo[i])
                            if g is not None:
                                dc.LineStyle = g
                            ids.Add(dc.Id)
                            ghi_dau_mut(dc)
                        except Exception:
                            LOI["net"] += 1
            del lo[:]
            bam("net", t_)

        for (z, _, loai, it) in muc:
            if loai in ("net", "cung"):
                lo.append((loai, it))
                if len(lo) >= 2000:
                    xa_lo()
                continue
            xa_lo()
            try:
                fr = tao_vung(it["loops"], KIEU_HATCH[it["kieu"]] if loai == "vung" else KIEU_CHE)
                ids.Add(fr.Id); TONG[loai] += 1
            except Exception as ex:
                # 1) biên dự phòng đã nắn (tô chẵn lẻ, bỏ tự cắt) từ bước trích xuất
                if it.get("sua"):
                    ok_s = 0
                    for manh_ in it["sua"]:           # mỗi mảnh 1 Filled Region
                        try:
                            fr = tao_vung(manh_, KIEU_HATCH[it["kieu"]] if loai == "vung" else KIEU_CHE)
                            ids.Add(fr.Id); ok_s += 1
                        except Exception:
                            pass
                    if ok_s:
                        TONG[loai] += 1
                        TONG["vung_bien_sua"] = TONG.get("vung_bien_sua", 0) + 1
                        continue
                # 2) thử từng vòng riêng
                ok = 0
                for l in it["loops"]:
                    try:
                        fr = tao_vung([l], KIEU_HATCH[it["kieu"]] if loai == "vung" else KIEU_CHE)
                        ids.Add(fr.Id); ok += 1
                    except Exception:
                        pass
                if ok:
                    TONG[loai] += 1
                else:
                    LOI[loai] += 1
                    if len(loi_mau_vd) < 15:
                        loi_mau_vd.append(u"{} | {} | {}".format(o["ten"], loai, str(ex)[:120]))
        xa_lo()
        t_c = time.time()
        # chữ
        for c in o["chu"]:
            try:
                op = DB.TextNoteOptions(kieu_chu(c["font"], c["h"], c["wf"]))
                op.HorizontalAlignment = HA[c["ngang"]]
                op.VerticalAlignment = VA[c["doc"]]
                op.Rotation = math.radians(c["rot"])
                tn = DB.TextNote.Create(doc, lg.Id, XYZ(c["x"], c["y"]), c["t"], op)
                ids.Add(tn.Id); TONG["chu"] += 1
            except Exception as ex:
                LOI["chu"] += 1
                if len(loi_mau_vd) < 30:
                    loi_mau_vd.append(u"{} | chữ '{}' | {}".format(o["ten"], c["t"][:30], str(ex)[:100]))
        bam("chu", t_c); t_d = time.time()
        # dim
        for dm in o["dim"]:
            try:
                p2 = XYZ(*dm["p2"]); p3 = XYZ(*dm["p3"]); p1 = XYZ(*dm["p1"])
                # ưu tiên bám đầu mút nét CAD thật; không có thì 1 nét phụ <Invisible lines> nối 2 điểm đo
                a = math.radians(dm["ang"])
                u = DB.XYZ(math.cos(a), math.sin(a), 0)
                uu = (math.cos(a), math.sin(a))
                v2 = tim_tham_chieu(dm["p2"], uu); v3 = tim_tham_chieu(dm["p3"], uu)
                dc = None
                ra = DB.ReferenceArray()
                if v2 is None or v3 is None or v2[0] == v3[0]:
                    dc = doc.Create.NewDetailCurve(lg, DB.Line.CreateBound(p2, p3))
                    if AN is not None:
                        dc.LineStyle = AN
                    ra.Append(dc.GeometryCurve.GetEndPointReference(0))
                    ra.Append(dc.GeometryCurve.GetEndPointReference(1))
                    TONG["dim_net_phu"] = TONG.get("dim_net_phu", 0) + 1
                else:
                    ra.Append(v2[1]); ra.Append(v3[1])
                ln = DB.Line.CreateBound(p1 - u * 1.0, p1 + u * 1.0)
                try:
                    dim = doc.Create.NewDimension(lg, ln, ra, doc.GetElement(kieu_dim(dm["h"])))
                except Exception:
                    if dc is not None:
                        raise
                    # bám nét thật không được: dùng nét phụ
                    dc = doc.Create.NewDetailCurve(lg, DB.Line.CreateBound(p2, p3))
                    if AN is not None:
                        dc.LineStyle = AN
                    ra = DB.ReferenceArray()
                    ra.Append(dc.GeometryCurve.GetEndPointReference(0))
                    ra.Append(dc.GeometryCurve.GetEndPointReference(1))
                    TONG["dim_net_phu"] = TONG.get("dim_net_phu", 0) + 1
                    dim = doc.Create.NewDimension(lg, ln, ra, doc.GetElement(kieu_dim(dm["h"])))
                # số / chữ hiện phải đúng như CAD (Revit đo lại có thể lệch 1 do làm tròn hoặc điểm bám)
                try:
                    vs = dim.ValueString
                except Exception:
                    vs = None
                if dm["hien"] and dm["hien"] != vs:
                    try:
                        dim.ValueOverride = dm["hien"]
                    except Exception:
                        pass
                if dm["tien_to"]:
                    dim.Prefix = dm["tien_to"]
                if dm["hau_to"]:
                    dim.Suffix = dm["hau_to"]
                if dc is not None:
                    ids.Add(dc.Id)
                ids.Add(dim.Id); TONG["dim"] += 1
            except Exception as ex:
                LOI["dim"] += 1
                if len(loi_mau_vd) < 45:
                    loi_mau_vd.append(u"{} | dim | {}".format(o["ten"], str(ex)[:120]))
        bam("dim", t_d); t_k = time.time()
        t.Commit()
        bam("commit", t_k)
        # group
        t1 = time.time()
        t = giao_dich(u"Group " + o["ten"])
        try:
            ids = ds_id([i for i in ids if doc.GetElement(i) is not None])
            try:
                grp = doc.Create.NewGroup(ids)
            except Exception:
                # tìm phần tử Revit không cho vào group (thử trong SubTransaction rồi hoàn tác), loại ra, group phần còn lại
                def thu(ds):
                    st = DB.SubTransaction(doc); st.Start()
                    try:
                        doc.Create.NewGroup(ds_id(ds)); ok = True
                    except Exception:
                        ok = False
                    st.RollBack()
                    return ok

                def tim_xau(ds):
                    if thu(ds):
                        return []
                    if len(ds) == 1:
                        return list(ds)
                    g_ = len(ds) // 2
                    return tim_xau(ds[:g_]) + tim_xau(ds[g_:])
                theo_hm = {}
                for i in ids:
                    e = doc.GetElement(i)
                    theo_hm.setdefault(e.Category.Name if e.Category else u"?", []).append(i)
                xau = []
                for hm, ds in theo_hm.items():
                    xx = tim_xau(ds)
                    if xx:
                        w(u"    {}: {} phần tử không vào được group, vd id {}".format(hm, len(xx), [x.Value for x in xx[:5]]))
                    xau += xx
                bo = set(x.Value for x in xau)
                ids = ds_id([i for i in ids if i.Value not in bo])
                TONG["ngoai_group"] = TONG.get("ngoai_group", 0) + len(xau)
                grp = doc.Create.NewGroup(ids)
            ten_g = sach_ten(u"CTC_" + o["ten"])
            k = 2
            tg_ = ten_g
            while tg_ in gt_ten:
                tg_ = u"{} ({})".format(ten_g, k); k += 1
            grp.GroupType.Name = tg_
            gt_ten.add(tg_)
            nhom_ds.append(tg_)
            t.Commit()
            kq_g = u"group '{}' ({})".format(tg_, grp.Category.Name if grp.Category else u"?")
        except Exception as ex:
            t.RollBack()
            kq_g = u"KHÔNG tạo được group: {}".format(ex)
        w(u"=== Ô {}: {} phần tử, {} | vẽ {:.1f} s, group {:.1f} s".format(o["ten"], ids.Count, kq_g, t1 - t0, time.time() - t1))
    tg.Assimilate()
    w(u"Tổng tạo: {}".format(TONG))
    w(u"Thời gian theo pha (s): {}".format(dict((k, round(v, 1)) for k, v in TG.items())))
    w(u"Lỗi: {}".format(LOI))
    for s in loi_mau_vd:
        w(u"  lỗi: " + s)

    # ------------------------------------------------------------ xuất ảnh để duyệt
    if ANH:
        try:
            if not os.path.isdir(ANH):
                os.makedirs(ANH)
            op = DB.ImageExportOptions()
            op.ExportRange = DB.ExportRange.SetOfViews
            vl = NetList[DB.ElementId](); vl.Add(lg.Id)
            op.SetViewsAndSheets(vl)
            op.FilePath = os.path.join(ANH, u"legend")
            op.HLRandWFViewsFileType = DB.ImageFileType.PNG
            op.ImageResolution = DB.ImageResolution.DPI_300
            op.ZoomType = DB.ZoomFitType.FitToPage
            op.PixelSize = 12000
            op.FitDirection = DB.FitDirectionType.Horizontal
            doc.ExportImage(op)
            w(u"Đã xuất ảnh vào {}".format(ANH))
        except Exception as ex:
            w(u"Xuất ảnh lỗi: {}".format(ex))
    if os.environ.get("ARV_CTC_LUU") == "1":
        try:
            doc.Save()
            w(u"Đã lưu bản sao.")
        except Exception as ex:
            w(u"Không lưu: {}".format(ex))
    w(u"XONG")
except Exception:
    w(u"LỖI " + traceback.format_exc())
finally:
    f.close()
