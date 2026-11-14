#! python3
# -*- coding: utf-8 -*-
"""Vẽ các ô chi tiết CAD (đã trích ra ct_cua.json bằng trich_xuat.py) vào MỘT legend Revit mới.

- Nét  -> Detail Line, kiểu nét dựng sẵn của Revit: <Thin Lines> / <Medium Lines> / <Wide Lines> / <Hidden Lines> /
          <Centerline> (theo lineweight + linetype CAD). Nét trùng đã gộp còn 1 nét ở bước trích xuất.
- Hatch -> Filled Region (viền <Invisible lines>), kiểu `CTC_<mẫu>`; mẫu hatch CAD -> fill pattern Model `CTC_<mẫu>`
          dựng đúng định nghĩa đường mẫu của CAD; hatch đặc giữ màu.
          Revit không nhận biên gốc (vùng hẹp / cạnh ngắn hơn 0,78 mm, tự cắt) thì thử lần lượt các mức biên dự phòng
          `du_phong` của bước trích xuất (nắn biên -> nở 0,25 -> nở 0,5 mm -> hình bao), log ghi số vùng theo mức.
- Wipeout + nền che chữ của MULTILEADER -> Filled Region trắng (che), theo thứ tự vẽ của CAD.
- Chữ  -> Text Note kiểu `CTC_Arial <cỡ>mm` (1 kiểu chữ, 3 cỡ); MTEXT có khung, nhiều dòng / dài thì xuống dòng theo khung.
- Dim tuyến tính -> Dimension kiểu `CTC_Dim <cỡ>mm`, mỗi điểm đo bám 1 nét vuông góc với phương đo (nét CAD thật đúng vị
          trí, không có thì nét phụ 2 mm <Invisible lines>); chữ dim CAD khác số Revit đo thì ghi đè.
- Mỗi ô chi tiết -> 1 detail group `CTC_<mã ô>`.
Không xoá, không sửa phần tử / kiểu có sẵn; chỉ tạo mới. Kiểu đã có cùng tên thì dùng lại.

Biến môi trường: ARV_CTC_JSON (đường dẫn json), ARV_CTC_LOG (file log), ARV_CTC_ANH (thư mục xuất ảnh, trống = không),
ARV_CTC_CHI (danh sách tên ô cách nhau |, trống = tất cả), ARV_CTC_TEN (tên legend), ARV_CTC_LUU=1 (lưu file, chỉ cho
bản sao), ARV_CTC_RONG_CHU (hệ số rộng chữ, mặc định 0.8), ARV_CTC_PX (bề rộng ảnh xuất, mặc định 12000), ARV_CTC_KHONG_GROUP=1 (bỏ bước group, chỉ khi vẽ thử lấy ảnh).
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
# Hệ số rộng của kiểu chữ + kiểu dim chung. Sửa 2026-11-13 tối: 0,8 thay cho 1,0. Chữ trong CAD 73 % là Arial rộng 0,8, còn
# lại 0,65 - 0,75 (ISO công ty cho 0,8 - 1,0); để rộng 1 thì chữ dài hơn CAD ~25 %: đè lên đường dẫn, tràn khỏi khung ô.
RONG_CHU = float(os.environ.get("ARV_CTC_RONG_CHU") or 0.8)
CO_CHU = [(3.3, 2.5), (4.6, 3.5), (1e9, 5.0)]   # < 3,3 mm -> 2,5; < 4,6 -> 3,5; còn lại -> 5 (cỡ chuẩn ISO)
# ARV_CTC_CO_CHU = "ngưỡng:cỡ,ngưỡng:cỡ,...:cỡ" để đổi bảng cỡ chữ, vd. "2.25:2,3.3:2.5,4.6:3.5,:5" thêm cỡ 2 mm cho bản vẽ
# mà chữ ghi chú trong CAD cao 2 mm trên giấy (ctchung.dxf): dồn lên 2,5 mm thì chữ dài hơn CAD 25 %, đè lên hình.
if os.environ.get("ARV_CTC_CO_CHU"):
    CO_CHU = [(float(a) if a.strip() else 1e9, float(b)) for a, b in (x.split(":") for x in os.environ["ARV_CTC_CO_CHU"].split(","))]
GHI_TUNG = os.environ.get("ARV_CTC_GHI_TUNG") == "1"     # ghi vết từng vùng / từng pha (tìm đối tượng làm Revit văng)
CHU_BO_DUOI = float(os.environ.get("ARV_CTC_BO_DUOI") or 1.0)   # chữ CAD < 1 mm giấy (gần như không đọc được) thì bỏ, có báo
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
    # bản vẽ nhiều tờ nhiều tỉ lệ (json có "ti_le" ở từng ô): mỗi lần chạy vẽ 1 legend = các ô CÙNG tỉ lệ
    tl_o = sorted(set(int(o["ti_le"]) for o in o_ds if o.get("ti_le")))
    if len(tl_o) > 1:
        raise Exception(u"Các ô được chọn có nhiều tỉ lệ {}: mỗi legend chỉ 1 tỉ lệ, chọn ô theo từng tờ (ARV_CTC_CHI).".format(tl_o))
    if tl_o:
        TL = tl_o[0]
    w(u"Số ô: {} | tỉ lệ 1:{} | cỡ chữ {}".format(len(o_ds), TL, CO_CHU))
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
    # nhân bản legend ít phần tử nhất (model đã có legend lớn do công cụ vẽ thì không lấy nó làm gốc)
    def so_pt(v):
        try:
            return FEC(doc, v.Id).WhereElementIsNotElementType().GetElementCount()
        except Exception:
            return 10 ** 9
    mau_lg.sort(key=so_pt)
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
                it.append([1, None])    # chấm
        # Chấm (dash 0 của CAD): CAD in ra 1 điểm to bằng bề dày nét. Vẽ thành nét dài CHAM (0,2 mm trên giấy ở tỉ lệ
        # legend này) cho còn thấy - bản đầu để 0,3 mm mô hình, ở 1:50 chỉ còn 0,006 mm giấy nên mẫu cát / chấm bê tông
        # ra trắng trơn. Phần dài thêm lấy bớt ở khoảng hở kề sau để chu kỳ mẫu không đổi.
        for i_, a in enumerate(it):
            if a[1] is None:
                ke = it[(i_ + 1) % len(it)]
                if ke is not a and ke[0] == 0 and ke[1] is not None and ke[1] > 0.1:
                    dd = min(CHAM, ke[1] * 0.5)
                    ke[1] -= dd
                else:
                    dd = CHAM
                a[1] = max(dd, 0.05)
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
    CHAM = 0.2 * TL          # mm mô hình: chấm của mẫu hatch dài 0,2 mm trên giấy
    DAY_DAC = 0.12 * TL      # mm mô hình: mẫu có bước giữa các đường nhỏ hơn 0,12 mm giấy thì in ra là mảng đặc
    so_day = 0
    kieu_dung = set(v["kieu"] for o in o_ds for v in o["vung"])
    for key, m in d["mau_hatch"].items():
        if key not in kieu_dung:
            continue                 # chỉ tạo kiểu cho các ô sẽ vẽ ở lần chạy này
        ten_k = sach_ten(u"CTC_" + m["ten"])
        mau = DB.Color(*[int(c) for c in m["rgb"]])
        dac = bool(m["solid"])
        if not dac:
            # Mẫu quá dày (CAD dùng hatch ANSI31 bước 0,03 mm... để tô đen lớp chống thấm): trên giấy là mảng đặc ->
            # dùng kiểu đặc cùng màu, không dựng mẫu Model dày đặc (Revit vẽ rất chậm hoặc hiện sai).
            buoc = []
            for (ang, bx, by, ox, oy, ds) in m["lines"]:
                a = math.radians(ang)
                buoc.append(abs(-ox * math.sin(a) + oy * math.cos(a)))
            if buoc and max(buoc) < DAY_DAC:
                dac = True
                so_day += 1
                ten_k = sach_ten(u"CTC_Đặc {},{},{}".format(*[int(c) for c in m["rgb"]]))
        if dac:
            fpe = solid_fp
        else:
            # cùng tên nhưng khác định nghĩa (khác key) -> thêm mã key; mẫu có chấm thì thêm tỉ lệ (độ dài chấm theo tỉ lệ)
            co_cham = any(x == 0 for l in m["lines"] for x in l[5])
            ten_fp = sach_ten(u"CTC_{} [{}{}]".format(m["ten"], key, u" 1-{}".format(TL) if co_cham else u""))
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
    w(u"Kiểu filled region: {} | mẫu quá dày vẽ thành đặc: {} | mẫu lỗi / thay bằng đặc: {}".format(len(KIEU_HATCH), so_day, loi_mau))

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
        font, wf = FONT_CHUNG, RONG_CHU
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
            dat(e, DB.BuiltInParameter.TEXT_WIDTH_SCALE, RONG_CHU)
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

    def tao_muc(muc, typ):
        """Tạo mọi mảnh của 1 mức biên dự phòng (mỗi mảnh 1 Filled Region); hỏng 1 mảnh thì hoàn tác cả mức.
        Trả về danh sách id, None nếu không được."""
        if not muc:
            return None
        st = DB.SubTransaction(doc)
        st.Start()
        try:
            ds = [tao_vung(manh_, typ).Id for manh_ in muc]
            st.Commit()
            return ds
        except Exception:
            st.RollBack()
            return None

    TEN_MUC = d.get("muc_du_phong") or []
    DU_PHONG_O = {}      # tên ô -> {mức: số vùng} để ghi log

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
            """Reference của nét CAD thật VUÔNG GÓC với phương đo u và đi qua vị trí điểm đo p (sai ≤ 0,3 mm theo phương
            đo), gần điểm đo nhất (≤ xa mm). Trả về (id nét, Reference) hoặc None.
            Sửa 2026-11-13 tối: KHÔNG bám đầu mút nét nữa. Dim giữa 2 tham chiếu điểm bị Revit vẽ theo đường nối 2 điểm
            (xiên) chứ không theo phương đo; dim giữa 2 nét song song mới luôn đúng phương."""
            nx, ny = -u[1], u[0]
            tot = None
            for (dc, x1, y1, x2, y2) in net_thang:
                dx, dy = x2 - x1, y2 - y1
                L = math.hypot(dx, dy)
                if L > 0 and abs((dx * u[0] + dy * u[1]) / L) < 2e-4:       # nét vuông góc với phương đo
                    a = abs((x1 - p[0]) * u[0] + (y1 - p[1]) * u[1])
                    if a < 0.3:
                        s1 = (x1 - p[0]) * nx + (y1 - p[1]) * ny
                        s2 = (x2 - p[0]) * nx + (y2 - p[1]) * ny
                        bb = 0.0 if min(s1, s2) <= 0 <= max(s1, s2) else min(abs(s1), abs(s2))
                        khoa = (a > 0.02, bb)          # ưu tiên nét trùng đúng vị trí, rồi tới nét gần nhất
                        if bb <= xa and (tot is None or khoa < tot[0]):
                            tot = (khoa, dc)
            if tot is None:
                return None
            return tot[1].Id.Value, tot[1].GeometryCurve.Reference

        def net_giong(p, u, p1):
            """Nét phụ <Invisible lines> dài 2 mm (0,1 mm trên giấy), vuông góc với phương đo, đặt tại điểm đo p và
            hướng về phía đường kích thước: làm tham chiếu khi không có nét CAD thật nào đúng vị trí."""
            nx, ny = -u[1], u[0]
            s = (p1[0] - p[0]) * nx + (p1[1] - p[1]) * ny
            k = 2.0 if s >= 0 else -2.0
            dc_ = doc.Create.NewDetailCurve(lg, DB.Line.CreateBound(XYZ(p[0], p[1]), XYZ(p[0] + nx * k, p[1] + ny * k)))
            if AN is not None:
                dc_.LineStyle = AN
            TONG["dim_net_phu"] = TONG.get("dim_net_phu", 0) + 1
            return dc_

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
            typ_ = KIEU_HATCH[it["kieu"]] if loai == "vung" else KIEU_CHE
            if GHI_TUNG:
                w(u"    > {} z{} {} ({} vòng)".format(loai, it["z"], it.get("kieu"), len(it["loops"])))
            try:
                if not it["loops"]:
                    raise Exception(u"vùng quá nhỏ, không còn biên gốc")
                fr = tao_vung(it["loops"], typ_)
                ids.Add(fr.Id); TONG[loai] += 1
            except Exception as ex:
                # 1) các mức biên dự phòng từ bước trích xuất (nắn biên -> nở nhẹ -> hình bao), lấy mức đầu tiên
                #    Revit nhận ĐỦ mọi mảnh; json bản cũ chỉ có 1 mức 'sua'
                muc_ds = it.get("du_phong") or ([it["sua"]] if it.get("sua") else [])
                xong = False
                for im, muc_ in enumerate(muc_ds):
                    ds = tao_muc(muc_, typ_)
                    if ds:
                        for i_ in ds:
                            ids.Add(i_)
                        TONG[loai] += 1
                        if it.get("goc") and im == 0:
                            # dải polyline có bề rộng: hình dựng sẵn ở bước trích xuất, không phải biên hatch bị sửa
                            TONG[it["goc"]] = TONG.get(it["goc"], 0) + 1
                        else:
                            TONG["vung_bien_sua"] = TONG.get("vung_bien_sua", 0) + 1
                            DU_PHONG_O.setdefault(o["ten"], {})
                            DU_PHONG_O[o["ten"]][im] = DU_PHONG_O[o["ten"]].get(im, 0) + 1
                        xong = True
                        break
                if xong:
                    continue
                # 2) json bản cũ (không có 'du_phong'): thử từng vòng riêng
                ok = 0
                if not it.get("du_phong"):
                    for l in it["loops"]:
                        try:
                            fr = tao_vung([l], typ_)
                            ids.Add(fr.Id); ok += 1
                        except Exception:
                            pass
                if ok:
                    TONG[loai] += 1
                else:
                    LOI[loai] += 1
                    if len(loi_mau_vd) < 40:
                        loi_mau_vd.append(u"{} | {} z {} | {}".format(o["ten"], loai, it["z"], str(ex)[:120]))
        xa_lo()
        t_c = time.time()
        if GHI_TUNG:
            w(u"    > xong hình, tới chữ")
            try:
                doc.Regenerate()
                w(u"    > regenerate được")
            except Exception as ex:
                w(u"    > regenerate lỗi {}".format(ex))
        # chữ
        chu_nen = []
        for c in o["chu"]:
            try:
                op = DB.TextNoteOptions(kieu_chu(c["font"], c["h"], c["wf"]))
                op.HorizontalAlignment = HA[c["ngang"]]
                op.VerticalAlignment = VA[c["doc"]]
                op.Rotation = math.radians(c["rot"])
                # đoạn chữ MTEXT có khung (nhiều dòng / dài): xuống dòng trong đúng bề rộng khung CAD, không thì chữ
                # chạy tràn sang hình bên cạnh. Nhãn ngắn 1 dòng giữ nguyên 1 dòng.
                rong = c.get("rong") or 0
                tn = None
                if rong > 0 and (u"\n" in c["t"] or len(c["t"]) >= 40):
                    try:
                        wd = rong * 1.03 / TL * MM      # dư 3 % để dòng vừa khít trong CAD không bị rớt chữ cuối
                        wd = min(max(wd, DB.TextNote.GetMinimumAllowedWidth(doc, op.TypeId)),
                                 DB.TextNote.GetMaximumAllowedWidth(doc, op.TypeId))
                        tn = DB.TextNote.Create(doc, lg.Id, XYZ(c["x"], c["y"]), wd, c["t"], op)
                        TONG["chu_xuong_dong_theo_khung"] = TONG.get("chu_xuong_dong_theo_khung", 0) + 1
                    except Exception:
                        tn = None
                if tn is None:
                    tn = DB.TextNote.Create(doc, lg.Id, XYZ(c["x"], c["y"]), c["t"], op)
                ids.Add(tn.Id); TONG["chu"] += 1
                if c.get("nen"):
                    chu_nen.append(tn)
            except Exception as ex:
                LOI["chu"] += 1
                if len(loi_mau_vd) < 30:
                    loi_mau_vd.append(u"{} | chữ '{}' | {}".format(o["ten"], c["t"][:30], str(ex)[:100]))
        # MTEXT có nền che (background mask): vùng che trắng theo khung bao THẬT của Text Note trong Revit, nới mỗi phía
        # 0,5 mm giấy. Vùng che tạo sau hatch / nét của ô nên che được hình phía sau; chữ là chú thích nên vẫn nằm trên.
        if chu_nen:
            try:
                doc.Regenerate()
            except Exception:
                pass
            for tn_ in chu_nen:
                try:
                    bb = tn_.get_BoundingBox(lg)
                    le = 0.5 * TL * MM
                    a_ = DB.XYZ(bb.Min.X - le, bb.Min.Y - le, 0); b_ = DB.XYZ(bb.Max.X + le, bb.Min.Y - le, 0)
                    c_ = DB.XYZ(bb.Max.X + le, bb.Max.Y + le, 0); d_ = DB.XYZ(bb.Min.X - le, bb.Max.Y + le, 0)
                    cl = DB.CurveLoop()
                    for p_, q_ in ((a_, b_), (b_, c_), (c_, d_), (d_, a_)):
                        cl.Append(DB.Line.CreateBound(p_, q_))
                    ls_ = NetList[DB.CurveLoop](); ls_.Add(cl)
                    fr = DB.FilledRegion.Create(doc, KIEU_CHE, lg.Id, ls_)
                    if AN is not None:
                        try:
                            fr.SetLineStyleId(AN.Id)
                        except Exception:
                            pass
                    ids.Add(fr.Id)
                    TONG["chu_co_nen_che"] = TONG.get("chu_co_nen_che", 0) + 1
                except Exception as ex:
                    LOI["che"] += 1
                    if len(loi_mau_vd) < 45:
                        loi_mau_vd.append(u"{} | nền che chữ | {}".format(o["ten"], str(ex)[:100]))
        bam("chu", t_c); t_d = time.time()
        # dim: mỗi điểm đo bám 1 nét VUÔNG GÓC với phương đo (nét CAD thật đúng vị trí, không có thì nét phụ 2 mm
        # <Invisible lines>) -> dim luôn nằm đúng phương đo như CAD, số đo = khoảng cách giữa 2 nét song song
        dim_moi = []
        for dm in o["dim"]:
            try:
                a = math.radians(dm["ang"])
                u = DB.XYZ(math.cos(a), math.sin(a), 0)
                uu = (math.cos(a), math.sin(a))
                p1 = XYZ(*dm["p1"])
                v2 = tim_tham_chieu(dm["p2"], uu); v3 = tim_tham_chieu(dm["p3"], uu)
                if v2 is not None and v3 is not None and v2[0] == v3[0]:
                    v3 = None                   # 2 điểm đo rơi vào cùng 1 nét: không đo được trên nét đó
                phu = {}

                def tham_chieu(k_, v_):
                    if v_ is not None:
                        return v_[1]
                    if k_ not in phu:
                        phu[k_] = net_giong(dm[k_], uu, dm["p1"])
                    return phu[k_].GeometryCurve.Reference
                ra = DB.ReferenceArray()
                ra.Append(tham_chieu("p2", v2)); ra.Append(tham_chieu("p3", v3))
                ln = DB.Line.CreateBound(p1 - u * 1.0, p1 + u * 1.0)
                try:
                    dim = doc.Create.NewDimension(lg, ln, ra, doc.GetElement(kieu_dim(dm["h"])))
                    if v2 is not None or v3 is not None:
                        TONG["dim_bam_net_cad"] = TONG.get("dim_bam_net_cad", 0) + 1
                except Exception:
                    if v2 is None and v3 is None:
                        raise
                    # bám nét CAD thật không được (vd. 2 nét không song song tuyệt đối): dùng nét phụ cho cả 2 điểm
                    ra = DB.ReferenceArray()
                    ra.Append(tham_chieu("p2", None)); ra.Append(tham_chieu("p3", None))
                    dim = doc.Create.NewDimension(lg, ln, ra, doc.GetElement(kieu_dim(dm["h"])))
                for dc_ in phu.values():
                    ids.Add(dc_.Id)
                ids.Add(dim.Id); TONG["dim"] += 1
                dim_moi.append((dim, dm))
            except Exception as ex:
                LOI["dim"] += 1
                if len(loi_mau_vd) < 45:
                    loi_mau_vd.append(u"{} | dim | {}".format(o["ten"], str(ex)[:120]))
        # số / chữ hiện phải đúng như CAD: tính lại model rồi mới so, chỉ ghi đè khi Revit hiện khác CAD
        if dim_moi:
            try:
                doc.Regenerate()
            except Exception:
                pass
        for dim, dm in dim_moi:
            try:
                try:
                    vs = dim.ValueString
                except Exception:
                    vs = None
                if dm["hien"] and dm["hien"] != vs:
                    dim.ValueOverride = dm["hien"]
                    TONG["dim_ghi_de_chu"] = TONG.get("dim_ghi_de_chu", 0) + 1
                    try:
                        lech = abs(dim.Value / MM - dm["gia_tri"])
                    except Exception:
                        lech = None
                    if lech is not None and lech > 0.6:
                        TONG["dim_do_lech_cad"] = TONG.get("dim_do_lech_cad", 0) + 1
                if dm["tien_to"]:
                    dim.Prefix = dm["tien_to"]
                if dm["hau_to"]:
                    dim.Suffix = dm["hau_to"]
            except Exception:
                pass
        bam("dim", t_d); t_k = time.time()
        if GHI_TUNG:
            w(u"    > xong chữ + dim, tới commit")
        t.Commit()
        if GHI_TUNG:
            w(u"    > commit được, tới group")
        bam("commit", t_k)
        # group
        t1 = time.time()
        if os.environ.get("ARV_CTC_KHONG_GROUP") == "1":       # chỉ dùng khi vẽ thử để xuất ảnh (bỏ bước group cho nhanh)
            w(u"=== Ô {}: {} phần tử, KHÔNG group (vẽ thử để xuất ảnh) | vẽ {:.1f} s".format(o["ten"], ids.Count, t1 - t0))
            continue
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
        if callable(globals().get("_nhip")):      # ve_chung.py: ghi nhịp vào báo cáo tổng để bộ chạy nền không coi là treo
            _nhip(u"=== . ô {} xong".format(o["ten"]))
    tg.Assimilate()
    w(u"Tổng tạo: {}".format(TONG))
    w(u"Thời gian theo pha (s): {}".format(dict((k, round(v, 1)) for k, v in TG.items())))
    # vùng Revit không nhận biên gốc, đã vẽ bằng biên dự phòng: ghi theo mức để biết chỗ nào không còn đúng nguyên hình CAD
    theo_muc = {}
    for ten_o, ds in DU_PHONG_O.items():
        for im, n_ in ds.items():
            theo_muc[im] = theo_muc.get(im, 0) + n_
    for im in sorted(theo_muc):
        ten_m = TEN_MUC[im] if im < len(TEN_MUC) else u"mức {}".format(im)
        o_co = u", ".join(u"{} ({})".format(ten_o, ds[im]) for ten_o, ds in DU_PHONG_O.items() if im in ds)
        w(u"Biên dự phòng mức {} - {}: {} vùng | {}".format(im, ten_m, theo_muc[im], o_co))
    w(u"Lỗi: {}".format(LOI))
    for s in loi_mau_vd:
        w(u"  lỗi: " + s)

    # khung bao của legend theo mm mô hình: để cắt ảnh từng ô đúng chỗ khi đối chiếu với CAD
    try:
        ol = lg.Outline
        w(u"Khung view (mm mô hình): {:.1f} {:.1f} {:.1f} {:.1f}".format(ol.Min.U * TL / MM, ol.Min.V * TL / MM,
                                                                        ol.Max.U * TL / MM, ol.Max.V * TL / MM))
    except Exception as ex:
        w(u"Không đọc được khung view: {}".format(ex))
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
            op.PixelSize = int(os.environ.get("ARV_CTC_PX") or 12000)
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
