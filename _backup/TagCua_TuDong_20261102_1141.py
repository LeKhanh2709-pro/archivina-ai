# Tự động tag cửa đi + cửa sổ trên mặt bằng đang mở của Revit (người dùng chốt 2026-11-02):
#   - Cửa đi: family tag "AV_Door Tag" (hiện S3.<Type Mark>); cửa sổ: "AV_Window Tag"; lam / louver: "AV_Louver Tag"
#     (cửa sổ có tên family / type chứa từ khoá lam). Mã cửa lấy từ Type Mark (nhãn trong family).
#   - Tag nằm ngang, không leader, KHÔNG đè lên cửa (kể cả cánh mở), cửa sổ, tường, cột, tag / chữ khác:
#     cửa đi ưu tiên phía không mở cánh, cửa sổ ưu tiên phía ngoài (theo FacingOrientation); thử lưới vị trí quanh cửa
#     xếp theo khoảng cách (phía kia bị cộng phạt); không chỗ nào trống thì đặt chỗ ít đè nhất và liệt kê để xem lại.
#   - Nội thất không né mà ẩn: tạo view template riêng "<template gốc> (ẩn nội thất)" (tạo từ view vì API không nhân
#     bản được view template), ẩn các hạng mục nội thất, gán cho view. KHÔNG sửa template gốc.
#   - Cửa có EI (tham số chống cháy có giá trị) thì EI phải hiện trên tag: tag đã đặt mà chữ tag không chứa giá trị EI
#     → báo family tag chưa có nhãn EI.
#   - Cửa / cửa sổ đã có tag trong view thì bỏ qua: bấm lại không tạo trùng, không xoá gì.
# Dry-run chỉ báo cáo (đặt thử trong SubTransaction rồi huỷ), không sửa mô hình.
# INPUT
#   IN[0] (str)   Tên view mặt bằng (để trống = view đang mở)
#   IN[1] (str)   Family tag cửa đi
#   IN[2] (str)   Family tag cửa sổ
#   IN[3] (str)   Family tag lam / louver
#   IN[4] (str)   Từ khoá nhận lam / louver trong tên family / type cửa sổ, cách nhau bằng ;
#   IN[5] (bool)  Dry-run (True = chỉ báo cáo)
#   IN[6] (bool)  Tạo + gán view template ẩn nội thất
#   IN[7] (str)   Hạng mục nội thất cần ẩn (tên BuiltInCategory), cách nhau bằng ;
#   IN[8] (str)   Tên tham số chống cháy (EI) của cửa, cách nhau bằng ;
#   IN[9] (float) Khoảng hở giữa tag và vật cản (mm trên giấy in)
#   IN[10] (str)  Thư mục ghi log + ảnh (để trống = Documents\ARV_Logs\tag_cua)
# OUTPUT
#   OUT (list[str])  Báo cáo
import math
import os
import traceback
import unicodedata
from datetime import datetime
import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitServices")
from Autodesk.Revit.DB import *
import Autodesk.Revit.DB as _RevitDB
# pythonnet 3.0: tên đã được import đích danh trước đó trong phiên bị loại khỏi "import *" → bổ sung đủ tên
globals().update({_n: getattr(_RevitDB, _n) for _n in dir(_RevitDB) if not _n.startswith("_") and _n not in globals()})
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

MAC_DINH = ["", "AV_Door Tag", "AV_Window Tag", "AV_Louver Tag", "Lam;Louver", True, True,
            "OST_Furniture;OST_FurnitureSystems;OST_Casework;OST_SpecialityEquipment;OST_PlumbingFixtures",
            "Fire Rating;EI;Giới hạn chịu lửa", 1.0, ""]
HAU_TO_TEMPLATE = u" (ẩn nội thất)"
PHAT_PHIA_MM_GIAY = 8.0     # phạt khi đặt tag ở phía không ưu tiên (mm trên giấy, cộng vào khoảng cách)
TAM_XA_MM_GIAY = 15.0       # tag đặt xa nhất cách mép tường / cánh cửa (mm trên giấy)


def doc_in(i):
    try:
        v = IN[i]
    except Exception:
        v = None
    return MAC_DINH[i] if v is None or (isinstance(v, str) and v == "" and MAC_DINH[i] != "") else v


def khong_dau(s):
    s = unicodedata.normalize("NFD", u"%s" % (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"D")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def tach(s):
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def mm(v):
    return UnitUtils.ConvertFromInternalUnits(v, UnitTypeId.Millimeters)


def ft(v):
    return UnitUtils.ConvertToInternalUnits(v, UnitTypeId.Millimeters)


def ten(e):
    try:
        return Element.Name.GetValue(e)
    except Exception:
        try:
            return e.Name
        except Exception:
            return "?"


# ---------------- Hình học 2D trong hệ toạ độ view (u = phải, v = lên) ----------------
def da_giac_giao(a, b):
    """Hai đa giác lồi (list (x, y)) có phần trong giao nhau không (định lý trục tách)."""
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            nx, ny = y1 - y2, x2 - x1
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) <= min(pb) + 1e-9 or max(pb) <= min(pa) + 1e-9:
                return False
    return True


def dien_tich_giao_hop(a, b):
    """Diện tích giao xấp xỉ theo khung bao (để chọn chỗ ít đè nhất)."""
    ax = [p[0] for p in a]
    ay = [p[1] for p in a]
    bx = [p[0] for p in b]
    by = [p[1] for p in b]
    w = min(max(ax), max(bx)) - max(min(ax), min(bx))
    h = min(max(ay), max(by)) - max(min(ay), min(by))
    return w * h if w > 0 and h > 0 else 0.0


def _chinh():
    doc = DocumentManager.Instance.CurrentDBDocument
    bao_cao = []
    xem_lai = []
    chi_tiet = []

    def p(s):
        bao_cao.append(u"%s" % s)

    # ---------- View ----------
    ten_view = doc_in(0)
    view = None
    if ten_view:
        # Trùng tên (vd. "Tầng 1" có cả mặt bằng kiến trúc, trần, kết cấu) → ưu tiên Floor Plan
        ung = [v for v in FilteredElementCollector(doc).OfClass(ViewPlan) if not v.IsTemplate and v.Name == ten_view]
        ung.sort(key=lambda v: 0 if v.ViewType == ViewType.FloorPlan else 1)
        av = doc.ActiveView        # nút một chạm truyền tên view đang mở → lấy đúng view đó
        if av is not None and any(v.Id.Value == av.Id.Value for v in ung):
            ung = [av]
        view = ung[0] if ung else None
        if view is None:
            return [u"Không có view mặt bằng tên '%s'." % ten_view]
    else:
        view = doc.ActiveView
    if view is None or view.ViewType not in (ViewType.FloorPlan, ViewType.EngineeringPlan, ViewType.AreaPlan):
        return [u"View '%s' không phải mặt bằng. Mở mặt bằng cần tag rồi chạy lại." % (ten(view) if view else "-")]
    dry = bool(doc_in(5))
    tl = float(view.Scale)
    U = view.RightDirection
    V = view.UpDirection
    khe = ft(float(doc_in(9)) * tl)

    def uv(pt):
        return (pt.X * U.X + pt.Y * U.Y + pt.Z * U.Z, pt.X * V.X + pt.Y * V.Y + pt.Z * V.Z)

    def xyz(a, b, z):
        return XYZ(a * U.X + b * V.X, a * U.Y + b * V.Y, z)

    def khung_hop(bb):
        """BoundingBoxXYZ → hình chữ nhật trong hệ uv (khung bao các góc)."""
        if bb is None:
            return None
        tf = bb.Transform
        pts = [uv(tf.OfPoint(XYZ(x, y, bb.Min.Z))) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
        xs = [q[0] for q in pts]
        ys = [q[1] for q in pts]
        return [(min(xs), min(ys)), (max(xs), min(ys)), (max(xs), max(ys)), (min(xs), max(ys))]

    def diem_hinh_hoc(e):
        """Các điểm hình học của đối tượng hiện trong view (gồm nét 2D của family: cánh mở, ký hiệu)."""
        opt = Options()
        opt.View = view
        opt.IncludeNonVisibleObjects = False
        pts = []

        def duyet(geo):
            for g in geo:
                tn = g.GetType().Name
                if tn == "GeometryInstance":
                    duyet(g.GetInstanceGeometry())
                elif tn == "Solid":
                    if g.Volume <= 0 and g.Edges.Size == 0:
                        continue
                    for ed in g.Edges:
                        pts.extend(ed.Tessellate())
                elif tn in ("Line", "Arc", "Ellipse", "NurbSpline", "HermiteSpline", "CylindricalHelix"):
                    pts.extend(g.Tessellate())
                elif tn == "PolyLine":
                    pts.extend(g.GetCoordinates())
        try:
            geo = e.get_Geometry(opt)
            if geo is not None:
                duyet(geo)
        except Exception:
            pass
        return pts

    def hcn_cuc_bo(pts, goc, h, f):
        """Hình chữ nhật bao các điểm theo hệ (h, f) đặt tại goc; trả về (đa giác uv, h0, h1, f0, f1)."""
        if not pts:
            return None
        hs = [(q.X - goc.X) * h.X + (q.Y - goc.Y) * h.Y for q in pts]
        fs = [(q.X - goc.X) * f.X + (q.Y - goc.Y) * f.Y for q in pts]
        h0, h1, f0, f1 = min(hs), max(hs), min(fs), max(fs)
        poly = [uv(goc + h * a + f * b) for a, b in ((h0, f0), (h1, f0), (h1, f1), (h0, f1))]
        return poly, h0, h1, f0, f1

    # ---------- Kiểu tag ----------
    def tim_kieu_tag(ten_fam, bic):
        for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(bic):
            if s.FamilyName == ten_fam:
                return s
        return None

    kieu_cua = tim_kieu_tag(doc_in(1), BuiltInCategory.OST_DoorTags)
    kieu_cs = tim_kieu_tag(doc_in(2), BuiltInCategory.OST_WindowTags)
    kieu_lam = tim_kieu_tag(doc_in(3), BuiltInCategory.OST_WindowTags) or kieu_cs
    tk_lam = [khong_dau(x) for x in tach(doc_in(4))]
    for ten_fam, k in ((doc_in(1), kieu_cua), (doc_in(2), kieu_cs)):
        if k is None:
            p(u"CHƯA CÓ family tag '%s' trong dự án → bỏ qua hạng mục này (Load family rồi chạy lại)." % ten_fam)

    # ---------- Đối tượng cần tag ----------
    def thay(bic):
        return list(FilteredElementCollector(doc, view.Id).OfCategory(bic).WhereElementIsNotElementType())

    cuas = thay(BuiltInCategory.OST_Doors)
    css = thay(BuiltInCategory.OST_Windows)
    da_tag = set()
    vat_can = []          # (đa giác uv, mô tả)
    for tg in FilteredElementCollector(doc, view.Id).OfClass(IndependentTag):
        try:
            for i in tg.GetTaggedLocalElementIds():
                da_tag.add(i.Value)
        except Exception:
            pass
    # Chữ / tag có sẵn trong view
    for cls in (IndependentTag, TextNote, SpatialElementTag):
        try:
            for e in FilteredElementCollector(doc, view.Id).OfClass(cls):
                k = khung_hop(e.get_BoundingBox(view))
                if k:
                    vat_can.append((k, u"chữ / tag %d" % e.Id.Value))
        except Exception:
            pass
    # Tường: hình chữ nhật dấu chân thật (theo hình học, đúng cả khi location line lệch tâm)
    so_tuong = 0
    diem_tuong = {}
    for w in FilteredElementCollector(doc, view.Id).OfClass(Wall):
        lc = w.Location
        cv = lc.Curve if lc is not None and hasattr(lc, "Curve") else None
        poly = None
        if cv is not None and cv.GetType().Name == "Line":
            d = cv.Direction
            h = XYZ(d.X, d.Y, 0).Normalize()
            f = XYZ(-h.Y, h.X, 0)
            pts_w = diem_hinh_hoc(w)
            diem_tuong[w.Id.Value] = pts_w
            r = hcn_cuc_bo(pts_w, cv.GetEndPoint(0), h, f)
            poly = r[0] if r else None
        if poly is None:
            poly = khung_hop(w.get_BoundingBox(view))
        if poly:
            vat_can.append((poly, u"tường %d" % w.Id.Value))
            so_tuong += 1
    for bic in (BuiltInCategory.OST_Columns, BuiltInCategory.OST_StructuralColumns):
        for e in thay(bic):
            k = khung_hop(e.get_BoundingBox(view))
            if k:
                vat_can.append((k, u"cột %d" % e.Id.Value))
    # Cửa đi / cửa sổ: dấu chân theo hệ của cửa (gồm cánh mở)
    dau_chan = {}
    for e in cuas + css:
        try:
            goc = e.Location.Point
            h = e.HandOrientation
            f = e.FacingOrientation
        except Exception:
            k = khung_hop(e.get_BoundingBox(view))
            if k:
                vat_can.append((k, u"cửa %d" % e.Id.Value))
            continue
        r = hcn_cuc_bo(diem_hinh_hoc(e), goc, h, f)
        if r is None:
            continue
        dau_chan[e.Id.Value] = (goc, h, f) + r
        vat_can.append((r[0], u"cửa %d" % e.Id.Value))

    _bb_cache = []

    def vat_can_bb():
        while len(_bb_cache) < len(vat_can):
            pl, mt = vat_can[len(_bb_cache)]
            xs = [q[0] for q in pl]
            ys = [q[1] for q in pl]
            _bb_cache.append((pl, mt, (min(xs), min(ys), max(xs), max(ys))))
        return _bb_cache

    # Vùng crop của view
    crop = None
    if view.CropBoxActive:
        crop = khung_hop(view.CropBox)

    # ---------- Ghi ----------
    TransactionManager.Instance.EnsureInTransaction(doc)
    st = SubTransaction(doc)
    st.Start()
    tao = {"cua": 0, "cs": 0, "lam": 0}
    bo_qua = 0
    tag_moi = []
    ei_thieu = []
    tpl_msg = u""
    try:
        # --- View template ẩn nội thất ---
        if doc_in(6):
            tpl_msg = gan_template(doc, view, [x for x in tach(doc_in(7))])
        for s in (kieu_cua, kieu_cs, kieu_lam):
            if s is not None and not s.IsActive:
                s.Activate()

        ds = [(e, "cua") for e in cuas] + [(e, "cs") for e in css]
        for e, loai in ds:
            if e.Id.Value in da_tag:
                bo_qua += 1
                continue
            kieu = kieu_cua
            if loai == "cs":
                t = doc.GetElement(e.GetTypeId())
                ten_ft = khong_dau((t.FamilyName if t else "") + " " + ten(t))
                if any(k in ten_ft for k in tk_lam):
                    loai, kieu = "lam", kieu_lam
                else:
                    kieu = kieu_cs
            if kieu is None:
                continue
            dc = dau_chan.get(e.Id.Value)
            if dc is None:
                xem_lai.append(u"%d (Mark %s): không đọc được hình học / vị trí → chưa tag" % (e.Id.Value, mark(e)))
                continue
            goc, h, f, poly_e, h0, h1, f0, f1 = dc
            tg = IndependentTag.Create(doc, kieu.Id, view.Id, Reference(e), False, TagOrientation.Horizontal, goc)
            doc.Regenerate()
            k = khung_hop(tg.get_BoundingBox(view))
            hu, hv = uv(goc)
            cu = (k[0][0] + k[2][0]) / 2.0 - hu       # lệch tâm khung so với đầu tag
            cv_ = (k[0][1] + k[2][1]) / 2.0 - hv
            a = (k[2][0] - k[0][0]) / 2.0              # nửa rộng, nửa cao khung tag (hệ uv)
            b = (k[2][1] - k[0][1]) / 2.0
            h2 = uv(h)
            f2 = uv(f)
            e_f = a * abs(f2[0]) + b * abs(f2[1])      # nửa bề dày tag chiếu lên phương vuông tường
            e_h = a * abs(h2[0]) + b * abs(h2[1])      # nửa bề dài tag chiếu lên phương dọc tường
            # Mặt tường host hai phía, đo theo hình học thật (điểm đặt cửa có thể không nằm giữa tường)
            mat_tuong = {1: 0.0, -1: 0.0}
            try:
                pts_w = diem_tuong.get(e.Host.Id.Value)
                if pts_w:
                    fs = [(q.X - goc.X) * f.X + (q.Y - goc.Y) * f.Y for q in pts_w]
                    mat_tuong = {1: max(max(fs), 0.0), -1: max(-min(fs), 0.0)}
                else:
                    mat_tuong = {1: e.Host.Width / 2.0, -1: e.Host.Width / 2.0}
            except Exception:
                pass
            # Phía ưu tiên: cửa đi = phía không mở cánh (phía dấu chân ngắn hơn); cửa sổ = phía ngoài (+Facing).
            # Ứng viên = lưới vị trí quanh cửa ở cả hai phía, xếp theo khoảng cách tới cửa (+ phạt phía không ưu tiên),
            # thử lần lượt, lấy chỗ trống đầu tiên. Vùng cánh mở bị loại vì dấu chân cửa là vật cản.
            if loai == "cua":
                uu_tien = -1 if f1 >= -f0 else 1
            else:
                uu_tien = 1
            phat = ft(PHAT_PHIA_MM_GIAY * tl)
            buoc_h = max(e_h * 0.5, ft(50))
            buoc_f = max(e_f * 0.5, ft(50))
            tam_h = (h0 + h1) / 2.0
            gioi_han_h = (h1 - h0) / 2.0 + e_h * 3.0
            ung_vien = []
            for s_ in (1, -1):
                d0 = mat_tuong[s_] + khe + e_f
                d_max = max(f1 if s_ > 0 else -f0, mat_tuong[s_]) + khe + e_f + ft(TAM_XA_MM_GIAY * tl)
                i = 0
                while d0 + i * buoc_f <= d_max:
                    d = d0 + i * buoc_f
                    j = -int(gioi_han_h / buoc_h)
                    while j * buoc_h <= gioi_han_h:
                        dh = j * buoc_h
                        diem = (d - d0) + abs(dh) * 0.5 + (0.0 if s_ == uu_tien else phat)
                        ung_vien.append((diem, goc + h * (tam_h + dh) + f * (s_ * d),
                                         u"phía %s cách tường %d dịch %d" % (u"ưu tiên" if s_ == uu_tien else u"kia",
                                                                            round(mm(d - d0)), round(mm(dh)))))
                        j += 1
                    i += 1
            ung_vien.sort(key=lambda x: x[0])
            # Vật cản ở gần (lọc trước theo khung bao cho nhanh)
            r_gan = gioi_han_h + ft(TAM_XA_MM_GIAY * tl) + max(f1, -f0) + 2 * (e_f + e_h)
            gu, gv = uv(goc)
            gan = [(pl, mt, bb) for pl, mt, bb in vat_can_bb()
                   if bb[0] <= gu + r_gan and bb[2] >= gu - r_gan and bb[1] <= gv + r_gan and bb[3] >= gv - r_gan]
            tot = None
            loai_bo = []          # lý do bỏ các ứng viên trước chỗ được chọn (ghi log để soát)
            for _, c, nhan in ung_vien:
                cu0, cv0 = uv(c)
                hop = [(cu0 - a - khe, cv0 - b - khe), (cu0 + a + khe, cv0 - b - khe),
                       (cu0 + a + khe, cv0 + b + khe), (cu0 - a - khe, cv0 + b + khe)]
                if crop and not (hop[0][0] >= crop[0][0] and hop[0][1] >= crop[0][1] and
                                 hop[2][0] <= crop[2][0] and hop[2][1] <= crop[2][1]):
                    loai_bo.append(u"%s: ngoài crop" % nhan)
                    continue
                de = [(pl, mt) for pl, mt, bb in gan
                      if bb[0] < hop[2][0] and bb[2] > hop[0][0] and bb[1] < hop[2][1] and bb[3] > hop[0][1]
                      and da_giac_giao(hop, pl)]
                if de:
                    loai_bo.append(u"%s: đè %s" % (nhan, ", ".join(sorted(set(m for _, m in de))[:3])))
                dt = sum(dien_tich_giao_hop(hop, pl) for pl, mt in de)
                if tot is None or dt < tot[1] - 1e-9:
                    tot = (c, dt, hop, de, nhan)
                if not de:
                    break
            if tot is None:
                c, de, hop, nhan = goc, [("", u"ngoài vùng crop")], None, u"-"
            else:
                c, _, hop, de, nhan = tot
            chi_tiet.append(u"%d Mark %s %s: %s (%d ứng viên)" % (e.Id.Value, mark(e), loai, nhan, len(ung_vien)))
            chi_tiet.extend(u"      bỏ " + x for x in [x for x in loai_bo if not x.endswith(u"ngoài crop")][:12])
            cu0, cv0 = uv(c)
            tg.TagHeadPosition = xyz(cu0 - cu, cv0 - cv_, goc.Z)
            if hop:
                vat_can.append(([(hop[0][0] + khe, hop[0][1] + khe), (hop[1][0] - khe, hop[1][1] + khe),
                                 (hop[2][0] - khe, hop[2][1] - khe), (hop[3][0] + khe, hop[3][1] - khe)],
                                u"tag mới %d" % e.Id.Value))
            tao[loai] += 1
            tag_moi.append(tg)
            if de:
                xem_lai.append(u"%d (Mark %s, %s): tag còn đè %s" % (e.Id.Value, mark(e), loai,
                                                                     ", ".join(sorted(set(m for _, m in de))[:4])))
            # EI
            if loai == "cua":
                ei = gia_tri_ei(doc, e, tach(doc_in(8)))
                if ei:
                    doc.Regenerate()
                    txt = u""
                    try:
                        txt = tg.TagText or u""
                    except Exception:
                        pass
                    if khong_dau(ei).replace(" ", "") not in khong_dau(txt).replace(" ", ""):
                        ei_thieu.append(u"%d (Mark %s, %s): chữ tag '%s'" % (e.Id.Value, mark(e), ei, txt.strip()))
        if dry:
            st.RollBack()
        else:
            st.Commit()
    except Exception:
        if st.HasStarted() and not st.HasEnded():
            st.RollBack()
        raise
    finally:
        TransactionManager.Instance.TransactionTaskDone()

    p(u"View: %s (1:%d)%s" % (view.Name, view.Scale, u" – DRY-RUN, chưa ghi gì" if dry else u""))
    p(u"Đã tag: %d cửa đi, %d cửa sổ, %d lam / louver; bỏ qua %d đối tượng đã có tag" %
      (tao["cua"], tao["cs"], tao["lam"], bo_qua))
    p(u"Vật cản đã xét: %d (tường %d)" % (len(vat_can), so_tuong))
    if tpl_msg:
        p(tpl_msg)
    if xem_lai:
        p(u"CẦN XEM LẠI (%d):" % len(xem_lai))
        for s in xem_lai:
            p(u"   " + s)
    else:
        p(u"Không tag nào đè lên cửa / tường / chữ.")
    if ei_thieu:
        p(u"CỬA CÓ EI NHƯNG TAG KHÔNG HIỆN EI (%d) – family tag cửa chưa có nhãn tham số chống cháy:" % len(ei_thieu))
        for s in ei_thieu:
            p(u"   " + s)
    if dry:
        p(u"DRY-RUN: chưa tạo gì. Đặt IN[5] = False để tag.")

    # Log + ảnh
    thu_muc = doc_in(10) or os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs", "tag_cua")
    try:
        os.makedirs(thu_muc, exist_ok=True)
        f_log = os.path.join(thu_muc, "tag_cua_%s_%d.txt" % (datetime.now().strftime("%Y%m%d_%H%M%S_%f"), view.Id.Value))
        with open(f_log, "w", encoding="utf-8") as fh:
            fh.write("\n".join(bao_cao + [u"", u"CHI TIẾT VỊ TRÍ:"] + chi_tiet))
        p(u"Log: " + f_log)
    except Exception as ex:
        p(u"Không ghi được log: %s" % ex)
    return bao_cao


def mark(e):
    try:
        return e.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString() or "-"
    except Exception:
        return "-"


def gia_tri_ei(doc, e, ten_ts):
    """Giá trị chống cháy của cửa (instance trước, rồi type); rỗng nếu không có."""
    t = doc.GetElement(e.GetTypeId())
    for el in (e, t):
        if el is None:
            continue
        for n in ten_ts:
            try:
                pr = el.LookupParameter(n)
                if pr is None:
                    continue
                v = pr.AsString() if pr.StorageType == StorageType.String else pr.AsValueString()
                if v and v.strip() and v.strip() not in ("0", "-"):
                    return v.strip()
            except Exception:
                pass
    return u""


def gan_template(doc, view, ten_bic):
    """Gán view template '<gốc> (ẩn nội thất)' cho view: nhân bản template đang gán (không sửa bản gốc) hoặc tạo từ
    view nếu chưa có; ẩn các hạng mục nội thất. Template đã có thì dùng lại."""
    cats = []
    for n in ten_bic:
        try:
            cats.append(ElementId(getattr(BuiltInCategory, n)))
        except Exception:
            pass
    tpl_id = view.ViewTemplateId
    goc = doc.GetElement(tpl_id) if tpl_id != ElementId.InvalidElementId else None
    if goc is not None and goc.Name.endswith(HAU_TO_TEMPLATE):
        moi = goc
        thong_bao = u"View template '%s' đã gán sẵn" % goc.Name
    else:
        ten_moi = (goc.Name if goc is not None else view.Name) + HAU_TO_TEMPLATE
        moi = None
        for v in FilteredElementCollector(doc).OfClass(View):
            if v.IsTemplate and v.Name == ten_moi:
                moi = v
        if moi is not None:
            thong_bao = u"Gán view template có sẵn '%s'" % ten_moi
        else:
            # View template không Duplicate được qua API → tạo từ view (view đang hiển thị đúng theo template gốc)
            moi = view.CreateViewTemplate()
            moi.Name = ten_moi
            thong_bao = u"Tạo view template '%s' (từ %s)" % (ten_moi, u"template '%s'" % goc.Name if goc else u"view")
    # Template phải điều khiển V/G hạng mục model thì việc ẩn mới có tác dụng
    try:
        pid = ElementId(BuiltInParameter.VIS_GRAPHICS_MODEL)
        nc = list(moi.GetNonControlledTemplateParameterIds())
        if any(i.Value == pid.Value for i in nc):
            from System.Collections.Generic import List
            ds = List[ElementId]()
            for i in nc:
                if i.Value != pid.Value:
                    ds.Add(i)
            moi.SetNonControlledTemplateParameterIds(ds)
    except Exception:
        pass
    an = []
    for c in cats:
        try:
            if moi.CanCategoryBeHidden(c) and not moi.GetCategoryHidden(c):
                moi.SetCategoryHidden(c, True)
            an.append(Category.GetCategory(doc, c).Name)
        except Exception:
            pass
    for bic in (BuiltInCategory.OST_DoorTags, BuiltInCategory.OST_WindowTags):
        try:
            if moi.GetCategoryHidden(ElementId(bic)):
                moi.SetCategoryHidden(ElementId(bic), False)
        except Exception:
            pass
    if view.ViewTemplateId.Value != moi.Id.Value:
        view.ViewTemplateId = moi.Id
    return thong_bao + u", ẩn: " + u", ".join(an)


try:
    OUT = _chinh()
except Exception:
    OUT = [u"LỖI:", traceback.format_exc()]
