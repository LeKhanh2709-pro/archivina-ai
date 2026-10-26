# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoThietBiWCTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Đặt thiết bị vệ sinh (bệt xí + lavabo) trong WC theo vị trí trên bản CAD đã Link:
#   1. Lavabo: polyline chữ nhật kín trên layer IN[1] (khung ngoài block lavabo, VD block động 半挂式台盆),
#      cạnh dài 800–1100, cạnh ngắn 400–650 mm. Lưng lavabo = cạnh dài phía có vòi (trọng tâm các nét thiết bị
#      trong khung lệch về phía vòi). Kích thước lấy theo khung CAD (trạng thái hiển thị của block động).
#   2. Bệt xí: cung đầu bệt (≈ nửa vòng tròn, R 150–230) trên layer IN[2] + nét két nước vuông góc trục bệt
#      (dài ≈ 2R, nằm sau cung 1,8R–3,5R). Lưng bệt = nét két xa nhất; tổng sâu 600–800 mm. Cung không có két → bỏ.
#   3. Đặt family: tâm thiết bị theo trục CAD, lưng áp mặt hoàn thiện tường gần nhất (tia dò ≤ IN[7] mm sau lưng
#      CAD; CAD vẽ sát mặt tường thô, mô hình có trát + ốp) – không gặp tường thì giữ đúng vị trí CAD.
#      Lavabo lấn mặt hoàn thiện tường bên (CAD vẽ kín tới mặt thô) → dời ngang ra ≤ LAT_MAX_MM, giữ kích thước CAD;
#      lấn nhiều hơn / kẹp hai bên → giữ CAD, báo KIỂM TRA.
#      Lưng / tâm đo trên khối đặc của family sau khi đặt (không phụ thuộc điểm chèn của family).
#   4. Lavabo: type của family IN[4] có Width × Depth đúng khung CAD thì dùng; chưa có → nhân bản type mẫu IN[5]
#      thành "{rộng}x{sâu}". Bệt: một type IN[3] cho mọi WC (kích thước CAD chỉ ghi vào log).
#   5. Cao độ = mặt sàn hoàn thiện WC (sàn có Comments chứa "WC" dưới thiết bị): bệt (family Work Plane) host lên
#      mặt trên sàn WC, lavabo (family theo level) Offset from Host = cao độ sàn WC. Không có sàn WC → đặt theo
#      level, lavabo Offset = IN[6], bệt Work Plane nằm ở level (báo cáo). Comments "ARV-ThietBiWC <loại> <căn>".
#      Đã có thiết bị cùng family tại chỗ (khối đặc phủ ≥ 30 % khung CAD): đúng hướng → bỏ qua; sai hướng → xoá
#      cái cũ, đặt lại (báo trước trong dry-run). Mỗi thiết bị một SubTransaction – lỗi thì hoàn tác riêng cái đó.
# INPUT
#   IN[0] (str)   Tên bản CAD (chuỗi con). Trống = bản CAD link duy nhất có layer IN[1]
#   IN[1] (str)   Layer lavabo, mặc định "A-Interior WC"
#   IN[2] (str)   Layer bệt xí, mặc định "0" (khớp đúng tên)
#   IN[3] (str)   Bệt: "Family : Type", mặc định "AV-Toilet : AV-Toilet"
#   IN[4] (str)   Lavabo: family, mặc định "AV-Bàn Lavabo chữ nhật bán âm"
#   IN[5] (str)   Lavabo: type mẫu để nhân bản, mặc định "900x470"
#   IN[6] (float) Cao độ chân thiết bị so với level khi không có sàn WC (mm), mặc định -15
#   IN[7] (float) Tầm dò mặt tường hoàn thiện sau lưng CAD (mm), mặc định 100; 0 = giữ đúng vị trí CAD
#   IN[8] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng thiết bị
#   OUT[1] (list[Line]) Xem trước: khung thiết bị theo CAD (mm, tại cao độ level)

import os
import io
import csv
import math
import re
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, Line, Arc, PolyLine, Transaction, SubTransaction,
                                   UnitUtils,
                                   UnitTypeId, ModelPathUtils, BuiltInParameter, BuiltInCategory, Floor,
                                   ImportInstance, Options, ViewDetailLevel, Solid, GeometryInstance, ElementId,
                                   SolidCurveIntersectionOptions, SolidCurveIntersectionMode, Outline, Level,
                                   BoundingBoxIntersectsFilter, ElementMulticategoryFilter, FamilyInstance,
                                   FamilySymbol, FamilyPlacementType, ElementTransformUtils, Curve,
                                   HostObjectUtils)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Tạo thiết bị vệ sinh WC từ CAD"
SCRIPT_TAG = u"ARV_TaoThietBiWCTuCAD_v1"
COMMENT_TAG = u"ARV-ThietBiWC"
LAV_LONG = (800.0, 1100.0)    # Khung lavabo CAD: cạnh dài (mm)
LAV_SHORT = (400.0, 650.0)    # cạnh ngắn
WC_R = (150.0, 230.0)         # Bán kính cung đầu bệt
WC_SWEEP = (160.0, 190.0)     # Góc quét cung đầu bệt (độ)
WC_DEPTH = (600.0, 800.0)     # Tổng sâu bệt (lưng → đầu cung)
TANK_TOL_MM = 60.0            # Nét két nước: lệch trục bệt tối đa
ROUND_MM = 10.0               # Làm tròn kích thước lavabo → tên type
RAY_IN_MM = 150.0             # Tia dò mặt tường bắt đầu trước lưng CAD (trong phòng)
RAY_Z_MM = 300.0              # Cao độ tia dò mặt tường sau lưng, so với level
LAT_Z_MM = 700.0              # Cao độ tia dò tường bên lavabo (ngang mặt đá)
LAT_MAX_MM = 50.0             # Lavabo lấn tường bên tối đa được dời ngang ra
EXIST_IN_MM = 100.0           # Điểm thử "đã có thiết bị": trước lưng CAD
SEARCH_MM = 600.0             # Nới hộp tìm tường quanh thiết bị


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def dir_label(v):
    if abs(v[0]) >= abs(v[1]):
        return u"+X" if v[0] > 0 else u"-X"
    return u"+Y" if v[1] > 0 else u"-Y"


def detect_lavabos(rects, pts):
    """rects: [(x0, y0, x1, y1)] khung chữ nhật kín; pts: mọi điểm nét layer lavabo.
    Trả về [dict(kind, back, n, lat, long, short, center)] – n: hướng từ lưng vào phòng, lat: trục dọc lưng."""
    out = []
    for b in sorted(rects, key=lambda r: -(r[2] - r[0]) * (r[3] - r[1])):
        w, h = b[2] - b[0], b[3] - b[1]
        L, S = max(w, h), min(w, h)
        if not (LAV_LONG[0] <= L <= LAV_LONG[1] and LAV_SHORT[0] <= S <= LAV_SHORT[1]):
            continue
        cx, cy = (b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0
        if any(abs(o["center"][0] - cx) < L / 2.0 and abs(o["center"][1] - cy) < L / 2.0 for o in out):
            continue   # khung lồng trong khung đã nhận (mặt đá + chân tủ của cùng block)
        inside = [p for p in pts if b[0] - 1 <= p[0] <= b[2] + 1 and b[1] - 1 <= p[1] <= b[3] + 1]
        mx = sum(p[0] for p in inside) / len(inside) if inside else cx
        my = sum(p[1] for p in inside) / len(inside) if inside else cy
        if w >= h:
            n = (0.0, -1.0 if my > cy else 1.0)
            lat = (1.0, 0.0)
        else:
            n = (-1.0 if mx > cx else 1.0, 0.0)
            lat = (0.0, 1.0)
        back = (cx - n[0] * S / 2.0, cy - n[1] * S / 2.0)
        out.append(dict(kind=u"LAVABO", back=back, n=n, lat=lat, long=L, short=S, center=(cx, cy),
                        skew=abs(my - cy) if w >= h else abs(mx - cx)))
    return out


def detect_toilets(arcs, segs):
    """arcs: [(cx, cy, r, sweep_deg, mid_x, mid_y)]; segs: [(x0, y0, x1, y1)] nét layer bệt.
    Trả về [dict(kind, back, n, lat, long, short, center)] – n: hướng từ lưng ra đầu bệt."""
    out, dropped = [], []
    for cx, cy, r, sw, mx, my in arcs:
        if not (WC_R[0] <= r <= WC_R[1] and WC_SWEEP[0] <= sw <= WC_SWEEP[1]):
            continue
        dx, dy = mx - cx, my - cy
        L = math.hypot(dx, dy)
        if L < 1e-6:
            continue
        dx, dy = dx / L, dy / L
        best = None
        for x0, y0, x1, y1 in segs:
            ux, uy = x1 - x0, y1 - y0
            ln = math.hypot(ux, uy)
            if ln < 1.6 * r or ln > 2.5 * r or abs(ux * dx + uy * dy) / ln > 0.02:
                continue
            px, py = (x0 + x1) / 2.0 - cx, (y0 + y1) / 2.0 - cy
            s = -(px * dx + py * dy)
            t = abs(-px * dy + py * dx)
            if t <= TANK_TOL_MM and 1.8 * r <= s <= 3.5 * r and (best is None or s > best):
                best = s
        depth = (best + r) if best is not None else None
        if depth is None or not (WC_DEPTH[0] <= depth <= WC_DEPTH[1]):
            dropped.append((cx, cy, r, depth))
            continue
        back = (cx - dx * best, cy - dy * best)
        key = (round(back[0] / 20.0), round(back[1] / 20.0), round(dx), round(dy))
        if any(o["key"] == key for o in out):
            continue
        out.append(dict(kind=u"BET", back=back, n=(dx, dy), lat=(-dy, dx), long=depth, short=2.0 * r,
                        center=(cx, cy), key=key))
    return out, dropped


def footprint(f):
    """Khung 2D thiết bị theo CAD: 4 điểm (mm)."""
    bx, by = f["back"]
    nx, ny = f["n"]
    lx, ly = f["lat"]
    if f["kind"] == u"LAVABO":
        depth, half = f["short"], f["long"] / 2.0
    else:
        depth, half = f["long"], f["short"] / 2.0
    return [(bx - lx * half, by - ly * half), (bx + lx * half, by + ly * half),
            (bx + lx * half + nx * depth, by + ly * half + ny * depth),
            (bx - lx * half + nx * depth, by - ly * half + ny * depth)]


def lav_type_name(f):
    w = int(round(f["long"] / ROUND_MM) * ROUND_MM)
    d = int(round(f["short"] / ROUND_MM) * ROUND_MM)
    return w, d, u"{}x{}".format(w, d)


# --- Revit: tiện ích -------------------------------------------------------------------
class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def get_name(element):
    try:
        return element.Name
    except Exception:
        p = element.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def type_name(t):
    p = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p else get_name(t)


def id_value(eid):
    v = getattr(eid, "Value", None)
    return v if v is not None else eid.IntegerValue


def comments(el):
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return (p.AsString() or u"") if p else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def layer_of(obj):
    gs = doc.GetElement(obj.GraphicsStyleId)
    cat = gs.GraphicsStyleCategory if gs is not None else None
    return norm(cat.Name) if cat is not None else u""


def read_cad(inst, lav_layer, wc_layer):
    """Hình học bản CAD link theo toạ độ mô hình (mm)."""
    rects, lav_pts, segs, arcs = [], [], [], []

    def xy(p):
        return (to_mm(p.X), to_mm(p.Y))

    def walk(geo):
        for o in geo:
            if isinstance(o, GeometryInstance):
                walk(o.GetInstanceGeometry())
                continue
            lay = layer_of(o)
            is_lav, is_wc = lay == lav_layer, lay == wc_layer
            if not (is_lav or is_wc):
                continue
            if isinstance(o, PolyLine):
                c = [xy(p) for p in o.GetCoordinates()]
                if is_lav:
                    lav_pts.extend(c)
                    if 4 <= len(c) <= 5 and math.hypot(c[0][0] - c[-1][0], c[0][1] - c[-1][1]) < 1.0:
                        rects.append((min(p[0] for p in c), min(p[1] for p in c),
                                      max(p[0] for p in c), max(p[1] for p in c)))
                if is_wc:
                    segs.extend((c[i][0], c[i][1], c[i + 1][0], c[i + 1][1]) for i in range(len(c) - 1))
            elif isinstance(o, Line):
                a, b = xy(o.GetEndPoint(0)), xy(o.GetEndPoint(1))
                if is_lav:
                    lav_pts.extend([a, b])
                if is_wc:
                    segs.append((a[0], a[1], b[0], b[1]))
            elif isinstance(o, Arc):
                if is_wc and o.IsBound:
                    m = xy(o.Evaluate(0.5, True))
                    sw = math.degrees(o.GetEndParameter(1) - o.GetEndParameter(0))
                    arcs.append((to_mm(o.Center.X), to_mm(o.Center.Y), to_mm(o.Radius), sw, m[0], m[1]))
                if is_lav and o.IsBound:
                    lav_pts.extend(xy(p) for p in o.Tessellate())
            elif isinstance(o, Curve) and is_lav and o.IsBound:
                lav_pts.extend(xy(p) for p in o.Tessellate())

    geo = inst.get_Geometry(Options())
    if geo is not None:
        walk(geo)
    return rects, lav_pts, segs, arcs


def pick_cad(cad_filter, lav_layer):
    links = [i for i in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements() if i.IsLinked]
    names = [get_name(doc.GetElement(i.GetTypeId())) for i in links]
    if cad_filter:
        hit = [i for i, n in zip(links, names) if cad_filter.lower() in n.lower()]
    else:
        hit = []
        for i in links:
            cat = i.Category
            subs = [norm(c.Name) for c in cat.SubCategories] if cat is not None else []
            if lav_layer in subs:
                hit.append(i)
    if len(hit) != 1:
        raise StopReport([u"DỪNG: tìm thấy {} bản CAD link khớp '{}'. Nhập tên bản CAD vào ô IN[0]. "
                          u"Các bản CAD link: {}".format(len(hit), cad_filter or lav_layer,
                                                         u", ".join(names) or u"không có")])
    return hit[0]


def pick_level(inst):
    owner = doc.GetElement(inst.OwnerViewId) if inst.OwnerViewId != ElementId.InvalidElementId else None
    view = owner if owner is not None else doc.ActiveView
    lvl = getattr(view, "GenLevel", None)
    if lvl is None:
        raise StopReport([u"DỪNG: không xác định được level. Bản CAD phải Link vào một mặt bằng "
                          u"(view-specific), hoặc mở view mặt bằng của tầng rồi Run."])
    return lvl, view


def find_symbol(fam_name, typ_name):
    for s in FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_PlumbingFixtures):
        if norm(s.FamilyName) == norm(fam_name) and (typ_name is None or norm(type_name(s)) == norm(typ_name)):
            return s
    return None


def family_types(fam_name):
    return [s for s in FilteredElementCollector(doc).OfClass(FamilySymbol)
            .OfCategory(BuiltInCategory.OST_PlumbingFixtures) if norm(s.FamilyName) == norm(fam_name)]


def list_types_text():
    return u", ".join(sorted(u"{} : {}".format(s.FamilyName, type_name(s)) for s in FilteredElementCollector(doc)
                             .OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_PlumbingFixtures)))


def len_param(sym, name):
    p = sym.LookupParameter(name)
    return to_mm(p.AsDouble()) if p is not None and p.HasValue else None


def element_solids(element):
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    result = []

    def walk(geo):
        for g in geo:
            if isinstance(g, Solid) and g.Volume > 0:
                result.append(g)
            elif isinstance(g, GeometryInstance):
                walk(g.GetInstanceGeometry())

    geo = element.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def wall_solids_near(f, z0):
    xs = [p[0] for p in footprint(f)]
    ys = [p[1] for p in footprint(f)]
    mn = XYZ(from_mm(min(xs) - SEARCH_MM), from_mm(min(ys) - SEARCH_MM), z0)
    mx = XYZ(from_mm(max(xs) + SEARCH_MM), from_mm(max(ys) + SEARCH_MM), z0 + from_mm(2000.0))
    cats = [BuiltInCategory.OST_Walls, BuiltInCategory.OST_StructuralColumns, BuiltInCategory.OST_Columns]
    els = FilteredElementCollector(doc).WherePasses(ElementMulticategoryFilter(List[BuiltInCategory](cats))) \
        .WherePasses(BoundingBoxIntersectsFilter(Outline(mn, mx))).WhereElementIsNotElementType().ToElements()
    return [(s, e) for e in els for s in element_solids(e)]


SCI_OPT = None


def first_hit(solids, a, b):
    global SCI_OPT
    if SCI_OPT is None:
        SCI_OPT = SolidCurveIntersectionOptions()
        SCI_OPT.ResultType = SolidCurveIntersectionMode.CurveSegmentsInside
    line = Line.CreateBound(a, b)
    best = None
    for s, el in solids:
        try:
            res = s.IntersectWithCurve(line, SCI_OPT)
        except Exception:
            continue
        for i in range(res.SegmentCount):
            c = res.GetCurveSegment(i)
            t = min(c.GetEndPoint(0).DistanceTo(a), c.GetEndPoint(1).DistanceTo(a))
            if best is None or t < best:
                best = t
    return best


def wall_face_shift(f, z0, reach_mm, solids):
    """Khoảng dời lưng thiết bị (mm, dương = vào phòng) để áp mặt tường hoàn thiện gần nhất; None = không gặp."""
    if reach_mm <= 0:
        return None
    bx, by = f["back"]
    nx, ny = f["n"]
    lx, ly = f["lat"]
    half = (f["long"] if f["kind"] == u"LAVABO" else f["short"]) / 2.0
    z = z0 + from_mm(RAY_Z_MM)
    hits = []
    for k in (-0.5, 0.0, 0.5):
        px, py = bx + lx * half * k, by + ly * half * k
        a = XYZ(from_mm(px + nx * RAY_IN_MM), from_mm(py + ny * RAY_IN_MM), z)
        b = XYZ(from_mm(px - nx * reach_mm), from_mm(py - ny * reach_mm), z)
        t = first_hit(solids, a, b)
        if t is not None and to_mm(t) > 0.5:
            hits.append(RAY_IN_MM - to_mm(t))
    return max(hits) if hits else None


def side_shift(f, z0, solids):
    """Lavabo: (dời ngang mm theo f['lat'], ghi chú). Lấn mặt tường bên ≤ LAT_MAX_MM → dời ra, giữ kích thước."""
    cx, cy = f["center"]
    s = f.get("shift") or 0.0
    cx, cy = cx + f["n"][0] * s, cy + f["n"][1] * s
    lx, ly = f["lat"]
    half = f["long"] / 2.0
    z = z0 + from_mm(LAT_Z_MM)
    over = []
    for sg in (-1.0, 1.0):
        a = XYZ(from_mm(cx), from_mm(cy), z)
        b = XYZ(from_mm(cx + sg * lx * (half + 200.0)), from_mm(cy + sg * ly * (half + 200.0)), z)
        t = first_hit(solids, a, b)
        over.append(None if t is None else half - to_mm(t))   # dương = lấn vào tường
    lo, hi = over
    bad = [o for o in over if o is not None and o > 0.5]
    if not bad:
        return 0.0, u""
    if len(bad) == 2:
        return 0.0, u"KIỂM TRA: lavabo lấn tường cả hai bên ({:.0f} / {:.0f} mm)".format(lo, hi)
    o = bad[0]
    other = hi if lo is not None and lo > 0.5 else lo
    if o > LAT_MAX_MM or (other is not None and -other < o):
        return 0.0, u"KIỂM TRA: lavabo lấn tường bên {:.0f} mm – giữ vị trí CAD".format(o)
    return (o if lo is not None and lo > 0.5 else -o), u""


def solid_extent(inst, axis, lat):
    """(lưng, giữa dọc lưng) của khối đặc family theo trục axis (hướng vào tường) / lat, toạ độ mm từ gốc."""
    pmax, lmin, lmax = None, None, None
    for s in element_solids(inst):
        for e in s.Edges:
            for p in e.Tessellate():
                a = to_mm(p.X) * axis[0] + to_mm(p.Y) * axis[1]
                l = to_mm(p.X) * lat[0] + to_mm(p.Y) * lat[1]
                pmax = a if pmax is None else max(pmax, a)
                lmin = l if lmin is None else min(lmin, l)
                lmax = l if lmax is None else max(lmax, l)
    if pmax is None:
        return None
    return pmax, (lmin + lmax) / 2.0


def place(f, sym, level, offset_mm, facing_to_wall, floor):
    """Đặt family, quay, dời cho lưng khối đặc trùng f['target'] và giữa thân trùng trục CAD (+ f['lat_shift']).
    Family Work Plane: host lên mặt trên sàn WC (floor) nếu có; family theo level: Offset from Host = offset_mm."""
    nx, ny = f["n"]
    fx, fy = (-nx, -ny) if facing_to_wall else (nx, ny)
    bx, by = f["target"]
    p = XYZ(from_mm(bx + nx * 300.0), from_mm(by + ny * 300.0), level.Elevation + from_mm(offset_mm))
    if not sym.IsActive:
        sym.Activate()
    hosted = False
    if sym.Family.FamilyPlacementType == FamilyPlacementType.WorkPlaneBased:
        top = list(HostObjectUtils.GetTopFaces(floor)) if floor is not None else []
        if top:
            inst = doc.Create.NewFamilyInstance(top[0], p, XYZ(fy, -fx, 0), sym)
            hosted = True
            sl = inst.get_Parameter(BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM)
            if sl is not None and not sl.IsReadOnly:
                sl.Set(level.Id)
        else:
            inst = doc.Create.NewFamilyInstance(p, sym, XYZ(fy, -fx, 0), level, StructuralType.NonStructural)
    else:
        inst = doc.Create.NewFamilyInstance(p, sym, level, StructuralType.NonStructural)
        doc.Regenerate()
        ang = math.atan2(fy, fx) - math.atan2(inst.FacingOrientation.Y, inst.FacingOrientation.X)
        if abs(ang) > 1e-9:
            # CPython3 trong Dynamo không cộng được XYZ bằng "+" → dùng XYZ.Add
            ElementTransformUtils.RotateElement(doc, inst.Id, Line.CreateBound(p, p.Add(XYZ.BasisZ)), ang)
        off = inst.get_Parameter(BuiltInParameter.INSTANCE_FREE_HOST_OFFSET_PARAM)
        if off is not None and not off.IsReadOnly:
            off.Set(from_mm(offset_mm))
        hosted = True
    doc.Regenerate()
    fo = inst.FacingOrientation
    ok_dir = fo.X * fx + fo.Y * fy > 0.99
    ext = solid_extent(inst, (-nx, -ny), f["lat"])
    if ext is not None:
        back_now, lat_now = ext
        want_back = -(bx * nx + by * ny)
        want_lat = f["center"][0] * f["lat"][0] + f["center"][1] * f["lat"][1] + f.get("lat_shift", 0.0)
        da, dl = want_back - back_now, want_lat - lat_now
        mv = XYZ(from_mm(-nx * da + f["lat"][0] * dl), from_mm(-ny * da + f["lat"][1] * dl), 0)
        if mv.GetLength() > from_mm(0.1):
            ElementTransformUtils.MoveElement(doc, inst.Id, mv)
    cm = inst.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if cm is not None and not cm.IsReadOnly:
        cm.Set(u"{} {} {}".format(COMMENT_TAG, f["kind"], f.get("apt") or u"").strip())
    return inst, ok_dir, ext is not None, hosted


def wc_floors(level):
    """[(tên căn, x0, y0, x1, y1, floor, cao độ mặt sàn so với level mm)] các sàn WC (Comments chứa 'WC')."""
    out = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        c = comments(fl)
        if fl.LevelId != level.Id or u"WC" not in c.upper():
            continue
        bb = fl.get_BoundingBox(None)
        m = re.search(r"CH\d+", c)
        hp = fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM)
        top = to_mm(hp.AsDouble()) if hp is not None else to_mm(bb.Max.Z - level.Elevation)
        out.append((m.group(0) if m else c, to_mm(bb.Min.X), to_mm(bb.Min.Y), to_mm(bb.Max.X), to_mm(bb.Max.Y),
                    fl, top))
    return out


def floor_of(f, floors):
    x = f["back"][0] + f["n"][0] * 200.0
    y = f["back"][1] + f["n"][1] * 200.0
    for row in floors:
        if row[1] - 60 <= x <= row[3] + 60 and row[2] - 60 <= y <= row[4] + 60:
            return row
    return None


def existing_at(f, fam_name, level, facing_to_wall):
    """Thiết bị cùng family đã có tại chỗ: (element, đúng hướng?) – khối đặc phủ ≥ 30 % khung CAD; None nếu không có.
    Sai hướng = Facing lệch hướng cần đặt (VD lavabo của bản lỗi 2026-10-21 không xoay được, nằm quay +Y)."""
    pts = footprint(f)
    fx0, fy0 = min(p[0] for p in pts), min(p[1] for p in pts)
    fx1, fy1 = max(p[0] for p in pts), max(p[1] for p in pts)
    area = max((fx1 - fx0) * (fy1 - fy0), 1.0)
    nx, ny = f["n"]
    want = (-nx, -ny) if facing_to_wall else (nx, ny)
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        if not isinstance(e, FamilyInstance) or norm(e.Symbol.FamilyName) != norm(fam_name):
            continue
        bb = e.get_BoundingBox(None)
        if bb is None or abs(bb.Min.Z - level.Elevation) > from_mm(1500.0):
            continue
        sol = solid_extent_box(e)
        if sol is None:
            continue
        ox = min(sol[2], fx1) - max(sol[0], fx0)
        oy = min(sol[3], fy1) - max(sol[1], fy0)
        if ox > 0 and oy > 0 and ox * oy >= 0.3 * area:
            fo = e.FacingOrientation
            return e, fo.X * want[0] + fo.Y * want[1] > 0.99
    return None


def solid_extent_box(e):
    xs, ys = [], []
    for s in element_solids(e):
        for ed in s.Edges:
            for p in ed.Tessellate():
                xs.append(to_mm(p.X))
                ys.append(to_mm(p.Y))
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def preview_lines(items, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for f in items:
            pts = footprint(f)
            for i in range(4):
                a, b = pts[i], pts[(i + 1) % 4]
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                                       DSPoint.ByCoordinates(b[0], b[1], z_mm)))
        return out
    except Exception:
        return []


HEADER = [u"Căn", u"Loại", u"Lưng CAD (mm)", u"Hướng vào phòng", u"Kích thước CAD (mm)", u"Family : Type",
          u"Dời áp tường (mm)", u"Cao độ chân (mm)", u"Kết quả", u"ElementId"]


def write_log(rows, dry_run, settings):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoThietBiWCTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Thiết lập: {}\n".format(settings))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    return path


def main(cad_filter, lav_layer, wc_layer, wc_fam_type, lav_fam, lav_template, offset_mm, reach_mm, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    inst = pick_cad(cad_filter, lav_layer)
    cad_name = get_name(doc.GetElement(inst.GetTypeId()))
    level, view = pick_level(inst)

    # Family
    if u":" in wc_fam_type:
        wf, wt = [s.strip() for s in wc_fam_type.split(u":", 1)]
    else:
        wf, wt = wc_fam_type.strip(), None
    wc_sym = find_symbol(wf, wt)
    if wc_sym is None:
        raise StopReport([u"DỪNG: không có family bệt '{}' (IN[3]). Các type thiết bị vệ sinh: {}".format(
            wc_fam_type, list_types_text())])
    lav_syms = family_types(lav_fam)
    tmpl = [s for s in lav_syms if norm(type_name(s)) == norm(lav_template)]
    if not lav_syms or not tmpl:
        raise StopReport([u"DỪNG: không có lavabo '{} : {}' (IN[4], IN[5]). Các type thiết bị vệ sinh: {}".format(
            lav_fam, lav_template, list_types_text())])
    tmpl = tmpl[0]
    for pn in (u"Width", u"Depth"):
        if tmpl.LookupParameter(pn) is None:
            raise StopReport([u"DỪNG: type mẫu lavabo '{}' không có tham số '{}'.".format(lav_template, pn)])

    # Đọc CAD + nhận thiết bị
    rects, lav_pts, segs, arcs = read_cad(inst, lav_layer, wc_layer)
    lavs = detect_lavabos(rects, lav_pts)
    wcs, dropped = detect_toilets(arcs, segs)
    floors = wc_floors(level)
    items = sorted(lavs + wcs, key=lambda f: (round(f["back"][1] / 1000.0), f["back"][0]))
    for f in items:
        f["floor"] = floor_of(f, floors)
        f["apt"] = f["floor"][0] if f["floor"] else u""

    # Type lavabo theo khung CAD
    type_of = {}
    pending = {}
    for f in lavs:
        w, d, name = lav_type_name(f)
        hit = [s for s in lav_syms if abs((len_param(s, u"Width") or -1) - w) < 1.0
               and abs((len_param(s, u"Depth") or -1) - d) < 1.0]
        if hit:
            type_of[name] = hit[0]
        elif name not in pending:
            clash = [s for s in lav_syms if norm(type_name(s)) == name]
            pending[name] = (w, d, bool(clash))
        f["tname"] = name

    z0 = level.Elevation
    rows, created, errors = [], 0, []
    for f in items:
        solids = wall_solids_near(f, z0)
        shift = wall_face_shift(f, z0, reach_mm, solids)
        f["shift"] = shift
        s = shift or 0.0
        f["target"] = (f["back"][0] + f["n"][0] * s, f["back"][1] + f["n"][1] * s)
        f["lat_shift"], f["note"] = side_shift(f, z0, solids) if f["kind"] == u"LAVABO" and reach_mm > 0 \
            else (0.0, u"")
        f["z"] = f["floor"][6] if f["floor"] else offset_mm
        fam = wf if f["kind"] == u"BET" else lav_fam
        old = existing_at(f, fam, level, f["kind"] == u"BET")
        f["replace"] = None
        f["id"] = u""
        if old is not None and old[1]:
            f["status"] = u"Đã có (Id {})".format(id_value(old[0].Id))
        elif old is not None:
            f["replace"] = old[0]
            f["status"] = u"Sai hướng (Id {}) → {}".format(
                id_value(old[0].Id), u"sẽ xoá + đặt lại" if dry_run else u"xoá + đặt lại")
        else:
            f["status"] = u"Sẽ tạo" if dry_run else u""

    todo = [f for f in items if not f["status"].startswith(u"Đã có")]
    if not dry_run and todo:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        step = [u"nhân bản type lavabo"]
        try:
            for name in sorted(pending):
                w, d, clash = pending[name]
                nm = name if not clash else u"{} (ARV)".format(name)
                ns = tmpl.Duplicate(nm)
                ns.LookupParameter(u"Width").Set(from_mm(w))
                ns.LookupParameter(u"Depth").Set(from_mm(d))
                type_of[name] = ns
            for f in todo:
                step[0] = u"đặt {} {}".format(f["kind"], fmt(f["back"]))
                sym = wc_sym if f["kind"] == u"BET" else type_of[f["tname"]]
                # Mỗi thiết bị một SubTransaction: lỗi giữa chừng → hoàn tác riêng thiết bị đó, không để lại
                # phần tử đặt dở (bản trước để lại 26 lavabo chưa xoay khi RotateElement lỗi)
                st = SubTransaction(doc)
                st.Start()
                try:
                    pre = u""
                    if f["replace"] is not None:
                        pre = u"Thay Id {} (sai hướng) – ".format(id_value(f["replace"].Id))
                        doc.Delete(f["replace"].Id)
                    el, ok_dir, measured, at_z = place(f, sym, level, f["z"], f["kind"] == u"BET",
                                                       f["floor"][5] if f["floor"] else None)
                    st.Commit()
                    f["id"] = id_value(el.Id)
                    f["status"] = pre + u"Đã tạo" + (u"" if ok_dir else u" – KIỂM TRA HƯỚNG") + \
                        (u"" if measured else u" – family không có khối đặc, giữ điểm chèn") + \
                        (u"" if at_z else u" – Work Plane ở level (không có sàn WC)")
                    created += 1
                except Exception as ex:
                    st.RollBack()
                    f["status"] = u"LỖI: {}".format(ex)
                    errors.append(f)
            tx.Commit()
        except Exception as ex:
            import traceback
            tx.RollBack()
            return [u"LỖI khi ghi vào mô hình (bước: {}), mọi thay đổi đã được hoàn tác: {}".format(step[0], ex),
                    traceback.format_exc()], []

    for f in items:
        if f["kind"] == u"BET":
            ft = u"{} : {}".format(wc_sym.FamilyName, type_name(wc_sym))
            size = u"sâu {:.0f} × rộng {:.0f}".format(f["long"], f["short"])
        else:
            ft = u"{} : {}{}".format(lav_fam, f["tname"], u" (nhân bản)" if f["tname"] in pending else u"")
            size = u"{:.0f} × {:.0f}".format(f["long"], f["short"])
        sh = u"không gặp tường – giữ CAD" if f["shift"] is None else u"{:.0f}".format(f["shift"])
        if abs(f["lat_shift"]) > 0.5:
            sh += u"; ngang {:.0f}".format(f["lat_shift"])
        st = f["status"] + (u" – " + f["note"] if f["note"] else u"")
        rows.append([f["apt"] or u"—", f["kind"], fmt(f["back"]), dir_label(f["n"]), size, ft, sh,
                     u"{:.0f}".format(f["z"]), st, f["id"]])

    n_bet = len(wcs)
    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    if dry_run:
        report.append(u">>> ĐANG CHẠY THỬ: chưa ghi gì vào mô hình. Đổi ô IN[8] Dry-run = False rồi Run để đặt.")
    report.append(u"CAD: {} – level: {} (view '{}') – cao độ chân = mặt sàn WC (không có sàn: {:.0f} mm)".format(
        cad_name, level.Name, view.Name, offset_mm))
    report.append(u"Nhận từ CAD: {} bệt xí (layer '{}'), {} lavabo (layer '{}')".format(
        n_bet, wc_layer, len(lavs), lav_layer))
    n_old = sum(1 for f in items if f["status"].startswith(u"Đã có"))
    n_rep = sum(1 for f in items if f["replace"] is not None)
    report.append(u"Thiết bị {}: {} – đã có, bỏ qua: {}{}{}".format(
        u"sẽ đặt" if dry_run else u"đã đặt", len(todo) if dry_run else created, n_old,
        u" – trong đó {} thay thiết bị sai hướng cùng chỗ ({} xoá cái cũ)".format(
            n_rep, u"sẽ" if dry_run else u"đã") if n_rep else u"",
        u" – lỗi: {}".format(len(errors)) if errors else u""))
    shifts = [f["shift"] for f in items if f["shift"] is not None]
    if shifts:
        report.append(u"Áp mặt tường hoàn thiện: {} thiết bị dời {:.0f}…{:.0f} mm so với CAD; {} không gặp tường "
                      u"trong {:.0f} mm (giữ CAD)".format(len(shifts), min(shifts), max(shifts),
                                                         len(items) - len(shifts), reach_mm))
    lat = [f for f in items if abs(f["lat_shift"]) > 0.5]
    if lat:
        report.append(u"Lavabo lấn mặt hoàn thiện tường bên: {} cái dời ngang {:.0f}…{:.0f} mm (giữ kích thước CAD)"
                      .format(len(lat), min(abs(f["lat_shift"]) for f in lat), max(abs(f["lat_shift"]) for f in lat)))
    for f in items:
        if f["note"]:
            report.append(u"{} {} {}: {}".format(f["apt"] or u"—", f["kind"], fmt(f["back"]), f["note"]))
    for name in sorted(pending):
        w, d, clash = pending[name]
        report.append(u"Type lavabo '{}' (Width {} × Depth {}) chưa có → {} từ '{}'{}".format(
            name, w, d, u"sẽ nhân bản" if dry_run else u"ĐÃ NHÂN BẢN", lav_template,
            u" – tên đã có khác kích thước → đặt tên '{} (ARV)'".format(name) if clash else u""))
    if dropped:
        report.append(u"Bỏ qua {} cung R{}–{} không có nét két nước bệt (không phải bệt): {}".format(
            len(dropped), int(WC_R[0]), int(WC_R[1]),
            u"; ".join(fmt(d[:2]) for d in dropped[:8]) + (u"…" if len(dropped) > 8 else u"")))
    no_apt = [f for f in items if not f["apt"]]
    if no_apt:
        report.append(u"CẢNH BÁO: {} thiết bị không nằm trong sàn WC nào (Comments chứa 'WC') – vẫn đặt theo CAD, "
                      u"cao độ IN[6], bệt nằm trên level: {}".format(len(no_apt), u"; ".join(u"{} {}".format(f["kind"], fmt(f["back"]))
                                                            for f in no_apt)))
    for f in errors:
        report.append(u"LỖI {} {}: {}".format(f["kind"], fmt(f["back"]), f["status"]))
    settings = u"CAD={}; lavabo={}; bệt layer={}; bệt={}; lavabo={} (mẫu {}); offset={}; dò tường={}".format(
        cad_name, lav_layer, wc_layer, wc_fam_type, lav_fam, lav_template, offset_mm, reach_mm)
    try:
        report.append(u"Log: " + write_log(rows, dry_run, settings))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra khung thiết bị (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines(items, to_mm(z0))


def force_rerun_next_time():
    """Đánh dấu node 'đã sửa' để lần Run sau luôn chạy lại (chỉ ở chế độ Manual)."""
    try:
        clr.AddReference("DynamoRevitDS")
        from Dynamo.Applications import DynamoRevit
        ws = DynamoRevit.RevitDynamoModel.CurrentWorkspace
        rt = ws.RunSettings.RunType
        try:
            clr.AddReference("DynamoCore")
            from Dynamo.Models import RunType
            manual = rt == RunType.Manual
        except Exception:
            manual = False
        if not (manual or str(rt) in ("0", "Manual", "RunType.Manual")):
            return u"Chế độ chạy không phải Manual – lần sau phải đổi một ô đầu vào thì node mới chạy lại."
        for n in ws.Nodes:
            if SCRIPT_TAG in (getattr(n, "Script", None) or u""):
                n.MarkNodeAsModified(True)
                return None
        return u"Không tìm thấy node để đánh dấu chạy lại."
    except Exception as ex:
        return u"Không đánh dấu được node chạy lại ({}) – lần sau đổi một ô đầu vào rồi Run.".format(ex)


def num(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


if DYNAMO:
    import traceback
    try:
        OUT = list(main(
            (IN[0] or u"").strip(),
            norm(IN[1] or u"A-Interior WC"),
            norm(IN[2] if IN[2] not in (None, u"") else u"0"),
            norm(IN[3] or u"AV-Toilet : AV-Toilet"),
            norm(IN[4] or u"AV-Bàn Lavabo chữ nhật bán âm"),
            norm(IN[5] or u"900x470"),
            num(IN[6], -15.0),
            num(IN[7], 100.0),
            True if IN[8] is None else bool(IN[8]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoThietBiWCTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
