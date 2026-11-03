# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoGoLogia_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo gờ bê tông mặt ngoài logia (Basic Wall), lấy tuyến từ mặt bằng DWG đã Link (KTS chốt 2026-10-21):
#   1. Logia = sàn (Floor) trên level IN[5] có tên type chứa IN[2] (VD "SHT-Gach Lat Logia-300x600"), lấy hộp bao.
#   2. Tuyến gờ = đường giữa cặp nét song song cách nhau 150 mm (± 3) trên layer IN[1], sát cạnh hộp bao logia
#      (≤ 300 mm), phủ ≥ 50 % cạnh đó, dài từ tường đến tường (đầu nét CAD) – cùng cách dò với
#      ARV_TaoLanCanLouverLogia_v1. Nét dài hơn logia → cắt ở cạnh logia rồi bắt vào đầu tường Revit trên tuyến
#      (≤ 400 mm); không có tường → giữ mép logia, báo "KIỂM TRA ĐẦU".
#   3. Gờ = Wall type IN[3] (VD "VBT-150"), tâm tường trên đường giữa cặp nét, không nối (join) đầu tường.
#      Type chưa có → nhân bản type mẫu IN[4] (VD "VBT-200", một lớp bê tông) với tên IN[3], đổi chiều dày lớp
#      = bề dày cặp nét CAD (150). Dry-run chỉ báo "SẼ NHÂN BẢN".
#   4. Cao độ theo từng logia (so với level): đỉnh gờ = mặt sàn hoàn thiện logia + IN[6] (VD -30 + 100 = +70);
#      chân gờ = IN[7] nếu có, trống = đáy sàn hoàn thiện logia (VD -30 - 50 = -80).
#   5. Gờ tạo ra có Comments "ARV-GoLogia". Chạy lại, trong phạm vi tuyến từng logia:
#      - Tường có Comments đó, đúng kế hoạch (đầu tuyến ± 20 mm, chân/đỉnh ± 2 mm, đúng type) → giữ.
#      - Có Comments đó mà sai kế hoạch → XOÁ rồi tạo lại (báo "thay").
#      - Tường khác trùng tuyến (dựng tay) → không đụng, logia đó bỏ qua, báo "đã có tường dựng tay".
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1] (str)   Layer nét mặt ngoài logia, cách nhau ';' (khớp đúng tên) – VD "A-Line;A-line1;A-line2"
#   IN[2] (str)   Chuỗi con tên floor type sàn logia – VD "Logia"
#   IN[3] (str)   Wall type gờ – VD "VBT-150"
#   IN[4] (str)   Wall type mẫu để nhân bản khi IN[3] chưa có – VD "VBT-200"
#   IN[5] (str)   Level – VD "Tầng 1"
#   IN[6] (float) Gờ cao trên mặt sàn hoàn thiện logia (mm) – VD 100
#   IN[7] (str)   Chân gờ so với level (mm); trống = đáy sàn hoàn thiện logia
#   IN[8] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng logia
#   OUT[1] (list[Line]) Xem trước: tuyến gờ ở cao độ đỉnh gờ + vạch 600 mm chỉ ra ngoài (mm)

import os
import io
import csv
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, Options, GeometryInstance, PolyLine,
                                   Line, XYZ, Transaction, UnitUtils, UnitTypeId, ModelPathUtils, BuiltInParameter,
                                   Level, Wall, WallType, WallKind, WallUtils, Floor, LocationCurve, ElementId)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo gờ bê tông logia từ CAD"
SCRIPT_TAG = u"ARV_TaoGoLogia_v1"
COMMENT = u"ARV-GoLogia"
PAIR_GAP_MM = 150.0       # Bề dày nét đôi mặt ngoài = bề dày gờ
PAIR_TOL_MM = 3.0
EDGE_MM = 300.0           # Cặp nét cách cạnh logia tối đa
COVER = 0.5               # Cặp nét phủ tối thiểu cạnh logia
SNAP_WALL_MM = 400.0      # Bắt đầu tường Revit khi nét dài hơn logia
ON_AXIS_MM = 50.0
EXIST_WALL_MM = 50.0      # Lệch ngang tim để coi là cùng tuyến
SAME_END_MM = 20.0        # Đầu đoạn khớp kế hoạch
SAME_Z_MM = 2.0           # Chân / đỉnh khớp kế hoạch


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
class Facade(object):
    """Cặp nét đôi song song trục: axis 'H' (chạy theo X, line = y) hoặc 'V' (chạy theo Y, line = x)."""
    def __init__(self, axis, line, s, e, layer, gap):
        self.axis, self.line, self.s, self.e, self.layer, self.gap = axis, line, s, e, layer, gap

    def point(self, t):
        return (t, self.line) if self.axis == 'H' else (self.line, t)


def axis_segments(segs):
    """segs [(a, b, layer)] → [(axis, line, s, e, layer)] chỉ đoạn song song trục X/Y (lệch ≤ 1 mm)."""
    out = []
    for a, b, layer in segs:
        if abs(a[1] - b[1]) <= 1.0 and abs(a[0] - b[0]) > 1.0:
            out.append(('H', (a[1] + b[1]) / 2.0, min(a[0], b[0]), max(a[0], b[0]), layer))
        elif abs(a[0] - b[0]) <= 1.0 and abs(a[1] - b[1]) > 1.0:
            out.append(('V', (a[0] + b[0]) / 2.0, min(a[1], b[1]), max(a[1], b[1]), layer))
    return out


def facade_pairs(segs):
    """Cặp nét cùng phương, cách nhau 150 ± 3, cùng hai đầu (± 3) → [Facade] trên đường giữa."""
    ax = axis_segments(segs)
    pairs, used = [], set()
    for i, p in enumerate(ax):
        if i in used:
            continue
        for j in range(i + 1, len(ax)):
            q = ax[j]
            if j in used or p[0] != q[0]:
                continue
            if (abs(abs(p[1] - q[1]) - PAIR_GAP_MM) <= PAIR_TOL_MM and abs(p[2] - q[2]) <= PAIR_TOL_MM
                    and abs(p[3] - q[3]) <= PAIR_TOL_MM):
                pairs.append(Facade(p[0], (p[1] + q[1]) / 2.0, (p[2] + q[2]) / 2.0, (p[3] + q[3]) / 2.0, p[4],
                                    abs(p[1] - q[1])))
                used.add(i)
                used.add(j)
                break
    return pairs


def match_facade(box, pairs):
    """Cặp nét mặt ngoài của logia (hộp bao x0, y0, x1, y1) → (Facade, lo, hi) hoặc None."""
    x0, y0, x1, y1 = box
    best = None
    for f in pairs:
        if f.axis == 'V':
            d, lo, hi = min(abs(f.line - x0), abs(f.line - x1)), y0, y1
        else:
            d, lo, hi = min(abs(f.line - y0), abs(f.line - y1)), x0, x1
        ov = min(f.e, hi) - max(f.s, lo)
        if d <= EDGE_MM and ov >= COVER * (hi - lo) and (best is None or d < best[0]):
            best = (d, f, lo, hi)
    return None if best is None else best[1:]


def outward(box, f):
    x0, y0, x1, y1 = box
    if f.axis == 'V':
        return (1.0 if f.line > (x0 + x1) / 2.0 else -1.0, 0.0)
    return (0.0, 1.0 if f.line > (y0 + y1) / 2.0 else -1.0)


def span_of(f, lo, hi, wall_ends):
    """Đoạn tuyến (s, e) + ghi chú. wall_ends: [(x, y)] đầu tường Revit."""
    notes = []
    s, e = f.s, f.e
    for side in (0, 1):
        val = s if side == 0 else e
        limit = lo - EDGE_MM if side == 0 else hi + EDGE_MM
        if (side == 0 and val >= limit) or (side == 1 and val <= limit):
            continue
        edge = lo if side == 0 else hi
        cand = []
        for p in wall_ends:
            off = p[1] - f.line if f.axis == 'H' else p[0] - f.line
            t = p[0] if f.axis == 'H' else p[1]
            if abs(off) <= ON_AXIS_MM and abs(t - edge) <= SNAP_WALL_MM:
                cand.append(t)
        if cand:
            val = min(cand, key=lambda t: abs(t - edge))
            notes.append(u"{} tuyến bắt đầu tường Revit".format(u"Đầu" if side == 0 else u"Cuối"))
        else:
            val = edge
            notes.append(u"KIỂM TRA ĐẦU – {} tuyến lấy mép logia (nét CAD dài hơn logia, không thấy tường)".format(
                u"đầu" if side == 0 else u"cuối"))
        if side == 0:
            s = val
        else:
            e = val
    return s, e, notes


def along(f, pt):
    """(toạ độ dọc tuyến, lệch ngang) của điểm so với tuyến f."""
    return (pt[0], pt[1] - f.line) if f.axis == 'H' else (pt[1], pt[0] - f.line)


class Plan(object):
    def __init__(self, fid, box, ffl, bottom):
        self.fid, self.box = fid, box
        self.ffl, self.floor_bottom = ffl, bottom   # mặt / đáy sàn hoàn thiện logia so với level (mm)
        self.base = self.top = None
        self.facade = None
        self.s = self.e = None
        self.out = None
        self.notes = []
        self.status = u""
        self.wall_id = u""
        self.need = False
        self.delete_ids = []

    def pt(self, t):
        return self.facade.point(t)


def plan_logia(fid, box, ffl, bottom, pairs, wall_ends, curb_h, base_mm):
    p = Plan(fid, box, ffl, bottom)
    p.top = ffl + curb_h
    p.base = bottom if base_mm is None else base_mm
    m = match_facade(box, pairs)
    if m is None:
        p.status = u"Bỏ qua – không thấy cặp nét mặt ngoài dày 150"
        return p
    f, lo, hi = m
    p.facade = f
    p.out = outward(box, f)
    p.s, p.e, p.notes = span_of(f, lo, hi, wall_ends)
    if p.e - p.s <= 0:
        p.status = u"Bỏ qua – tuyến rỗng"
    elif p.top - p.base <= 0:
        p.status = u"Bỏ qua – đỉnh gờ {:.0f} không cao hơn chân {:.0f}".format(p.top, p.base)
    else:
        p.status = u"OK"
    return p


def reconcile(p, walls, type_name):
    """walls [(a, b, Id, của tool, tên type, chân, đỉnh)] (mm, so với level) → giữ / thay / dựng tay."""
    f = p.facade
    lo, hi = min(p.s, p.e), max(p.s, p.e)
    keep = None
    for a, b, eid, mine, tname, base, top in walls:
        ta, da = along(f, a)
        tb, db = along(f, b)
        if abs(da) > EXIST_WALL_MM or abs(db) > EXIST_WALL_MM:
            continue
        s, e = min(ta, tb), max(ta, tb)
        if min(e, hi) - max(s, lo) <= 50.0:
            continue
        if not mine:
            keep = keep or eid
            p.notes.append(u"đã có tường dựng tay Id {} ({}) trên tuyến".format(eid, tname))
        elif (keep is None and abs(s - lo) <= SAME_END_MM and abs(e - hi) <= SAME_END_MM
              and abs(base - p.base) <= SAME_Z_MM and abs(top - p.top) <= SAME_Z_MM
              and norm(tname) == norm(type_name)):
            keep = eid
        else:
            p.delete_ids.append(eid)
            p.notes.append(u"thay gờ cũ Id {} ({:.0f}, {:.0f}→{:.0f})".format(eid, e - s, base, top))
    p.wall_id = keep or u""
    p.need = keep is None


# --- Revit ---------------------------------------------------------------------------
def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def get_name(element):
    try:
        return element.Name
    except Exception:
        p = element.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return norm(style.GraphicsStyleCategory.Name)
    return None


def cad_objects(cad):
    opt = Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)
    result = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            else:
                result.append(obj)

    geo = cad.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def pick_cad(cad_filter, layers):
    found = []
    for inst in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        name = get_name(doc.GetElement(inst.GetTypeId()))
        if cad_filter and cad_filter.lower() not in name.lower():
            continue
        objects = cad_objects(inst)
        all_layers = set(l for l in (layer_of(o) for o in objects) if l)
        found.append((inst, name, objects, all_layers))
    hits = [f for f in found if f[3] & layers]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise StopReport([u"DỪNG: không có bản CAD{} nào có layer '{}'.".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u"", u"; ".join(sorted(layers)))])
    raise StopReport([u"DỪNG: {} bản CAD có layer khớp – nhập tên bản CAD vào ô IN[0]: {}".format(
        len(hits), u", ".join(h[1] for h in hits))])


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name) == norm(name):
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def basic_wall_types():
    return [t for t in FilteredElementCollector(doc).OfClass(WallType).ToElements() if t.Kind == WallKind.Basic]


def find_wall_type(name, template_name):
    """→ (WallType có sẵn hoặc None, WallType mẫu hoặc None)."""
    types = basic_wall_types()
    for t in types:
        if norm(get_name(t)) == norm(name):
            return t, None
    for t in types:
        if norm(get_name(t)) == norm(template_name):
            layers = t.GetCompoundStructure().GetLayers()
            if len(layers) != 1:
                raise StopReport([u"DỪNG: type mẫu '{}' (IN[4]) có {} lớp – cần type một lớp bê tông.".format(
                    template_name, len(layers))])
            return None, t
    raise StopReport([u"DỪNG: chưa có wall type '{}' (IN[3]) và không có type mẫu '{}' (IN[4]). Các Basic Wall: {}"
                      .format(name, template_name, u", ".join(sorted(get_name(t) for t in types)))])


def duplicate_type(template, name, width_mm):
    new_type = template.Duplicate(name)
    cs = new_type.GetCompoundStructure()
    cs.SetLayerWidth(0, from_mm(width_mm))
    new_type.SetCompoundStructure(cs)
    return new_type


def logia_floors(level, type_part):
    """[(Id, hộp bao, mặt sàn, đáy sàn)] – cao độ so với level (mm)."""
    result = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId != level.Id:
            continue
        ftype = doc.GetElement(fl.GetTypeId())
        if norm(type_part).lower() not in norm(get_name(ftype)).lower():
            continue
        bb = fl.get_BoundingBox(None)
        if bb is None:
            continue
        ffl = to_mm(fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).AsDouble())
        thk = to_mm(ftype.GetCompoundStructure().GetWidth())
        result.append((fl.Id.Value, (to_mm(bb.Min.X), to_mm(bb.Min.Y), to_mm(bb.Max.X), to_mm(bb.Max.Y)),
                       ffl, ffl - thk))
    return result


def level_walls(level):
    """[(đầu, cuối, Id, của tool, tên type, chân, đỉnh)] tường thẳng trên level (mm, so với level)."""
    out = []
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId != level.Id or not isinstance(loc, LocationCurve) or not isinstance(loc.Curve, Line):
            continue
        base = to_mm(wl.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble())
        hp = wl.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
        top = base + to_mm(hp.AsDouble()) if hp is not None else base
        out.append((xy(loc.Curve.GetEndPoint(0)), xy(loc.Curve.GetEndPoint(1)), wl.Id.Value, is_mine(wl),
                    get_name(wl.WallType), base, top))
    return out


def is_mine(el):
    prm = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return prm is not None and norm(prm.AsString()) == COMMENT


def create_curb(p, wtype, level):
    a, b = p.pt(p.s), p.pt(p.e)
    line = Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), 0.0), XYZ(from_mm(b[0]), from_mm(b[1]), 0.0))
    w = Wall.Create(doc, line, wtype.Id, level.Id, from_mm(p.top - p.base), from_mm(p.base), False, False)
    w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(ElementId.InvalidElementId)   # Unconnected
    WallUtils.DisallowWallJoinAtEnd(w, 0)
    WallUtils.DisallowWallJoinAtEnd(w, 1)
    prm = w.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if prm is not None and not prm.IsReadOnly:
        prm.Set(COMMENT)
    return w


def preview_lines(plans, z0_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for p in plans:
            z = z0_mm + p.top
            a, b = p.pt(p.s), p.pt(p.e)
            m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            for u, v in ((a, b), (m, (m[0] + p.out[0] * 600.0, m[1] + p.out[1] * 600.0))):
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(u[0], u[1], z),
                                                       DSPoint.ByCoordinates(v[0], v[1], z)))
        return out
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Sàn logia Id", u"Layer mặt ngoài", u"Tuyến từ", u"Tuyến đến", u"Dài (mm)", u"Dày CAD (mm)",
              u"Mặt sàn logia", u"Chân gờ", u"Đỉnh gờ", u"Ghi chú", u"Kết quả", u"Gờ Id"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoGoLogia_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm, cao độ so với level\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def split_layers(text):
    return set(norm(s) for s in (text or u"").split(u";") if norm(s))


def main(cad_filter, facade_layers, floor_part, type_name, template_name, level_name, curb_h, base_mm, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, facade_layers)
    missing = sorted(facade_layers - all_layers)
    level = find_level(level_name)
    wtype, template = find_wall_type(type_name, template_name)
    floors = logia_floors(level, floor_part)
    if not floors:
        raise StopReport([u"DỪNG: level '{}' không có sàn nào có type chứa '{}' (IN[2]).".format(level_name, floor_part)])

    segs = []
    for obj in objects:
        l = layer_of(obj)
        if l not in facade_layers:
            continue
        if isinstance(obj, Line):
            segs.append((xy(obj.GetEndPoint(0)), xy(obj.GetEndPoint(1)), l))
        elif isinstance(obj, PolyLine):
            pts = [xy(q) for q in obj.GetCoordinates()]
            segs.extend((a, b, l) for a, b in zip(pts[:-1], pts[1:]))
    pairs = facade_pairs(segs)
    walls = level_walls(level)
    wall_ends = [w[0] for w in walls if not w[3]] + [w[1] for w in walls if not w[3]]

    plans = []
    for fid, box, ffl, bottom in floors:
        p = plan_logia(fid, box, ffl, bottom, pairs, wall_ends, curb_h, base_mm)
        if p.status == u"OK":
            reconcile(p, walls, type_name)
            if any(n.startswith(u"đã có tường dựng tay") for n in p.notes):
                p.need, p.status = False, u"Bỏ qua – đã có tường dựng tay"
            elif not (p.need or p.delete_ids):
                p.status = u"Bỏ qua – đã đúng"
        plans.append(p)
    plans.sort(key=lambda q: (-round((q.box[1] + q.box[3]) / 2.0), round((q.box[0] + q.box[2]) / 2.0)))
    jobs = [p for p in plans if p.status == u"OK"]
    gaps = sorted(set(int(round(p.facade.gap)) for p in jobs))

    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            if wtype is None:
                wtype = duplicate_type(template, type_name, PAIR_GAP_MM)
            for p in jobs:
                for eid in p.delete_ids:
                    doc.Delete(ElementId(eid))
            for p in jobs:
                p.wall_id = create_curb(p, wtype, level).Id.Value
                p.status = u"Đã tạo" if not p.delete_ids else u"Đã thay"
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
    elif dry_run:
        for p in jobs:
            p.status = u"Sẽ tạo" if not p.delete_ids else u"Sẽ thay"

    rows = []
    for i, p in enumerate(plans, 1):
        f = p.facade
        has = f is not None and p.s is not None
        rows.append([i, p.fid, f.layer if f else u"—",
                     fmt(p.pt(p.s)) if has else u"—", fmt(p.pt(p.e)) if has else u"—",
                     u"{:.0f}".format(p.e - p.s) if has else u"—", u"{:.0f}".format(f.gap) if f else u"—",
                     u"{:.0f}".format(p.ffl), u"{:.0f}".format(p.base), u"{:.0f}".format(p.top),
                     u"; ".join(p.notes), p.status, p.wall_id])

    done = [p for p in plans if p.status in (u"Sẽ tạo", u"Đã tạo", u"Sẽ thay", u"Đã thay")]
    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – level: {} – wall type '{}'{} – cao {:.0f} trên mặt sàn logia, chân {}".format(
        cad_name, level.Name, type_name,
        u"" if template is None else u" ({} từ '{}', dày {:.0f})".format(
            u"SẼ NHÂN BẢN" if dry_run else u"đã nhân bản", template_name, PAIR_GAP_MM),
        curb_h, u"= đáy sàn hoàn thiện logia" if base_mm is None else u"{:.0f}".format(base_mm)))
    if missing:
        report.append(u"LƯU Ý: bản CAD không có layer: {}".format(u"; ".join(missing)))
    if any(abs(g - PAIR_GAP_MM) > 0.5 for g in gaps):
        report.append(u"LƯU Ý: bề dày cặp nét CAD đo được {} (gờ dựng {:.0f})".format(gaps, PAIR_GAP_MM))
    report.append(u"Logia: {} – {}: {} (thay {}), đã đúng: {}, có tường dựng tay: {}".format(
        len(plans), u"Sẽ tạo" if dry_run else u"Đã tạo", len(done), len([p for p in done if p.delete_ids]),
        len([p for p in plans if p.status == u"Bỏ qua – đã đúng"]),
        len([p for p in plans if p.status == u"Bỏ qua – đã có tường dựng tay"])))
    report.append(u"Tổng chiều dài gờ: {:.2f} m".format(sum(p.e - p.s for p in done) / 1000.0))
    for p in plans:
        if p not in done and p.status != u"Bỏ qua – đã đúng":
            report.append(u"  Sàn {}: {}".format(p.fid, p.status))
    checks = [p for p in plans if any(n.startswith(u"KIỂM TRA") for n in p.notes)]
    if checks:
        report.append(u"KIỂM TRA ĐẦU tuyến {} logia: {}".format(len(checks), u", ".join(str(p.fid) for p in checks)))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Xem trước: tuyến gờ ở cao độ đỉnh gờ + vạch 600 mm chỉ ra ngoài. Đúng thì đổi Dry-run = False "
                      u"và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines(done, to_mm(level.Elevation))


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


if DYNAMO:
    import traceback

    def _s(i, default):
        v = IN[i] if len(IN) > i else None
        return (v if v is not None and u"{}".format(v).strip() else default)

    try:
        _base = _s(7, None)
        OUT = list(main(
            u"{}".format(_s(0, u"")).strip(),
            split_layers(_s(1, u"A-Line;A-line1;A-line2")),
            norm(_s(2, u"Logia")),
            norm(_s(3, u"VBT-150")),
            norm(_s(4, u"VBT-200")),
            norm(_s(5, u"Tầng 1")),
            float(_s(6, 100.0)),
            None if _base is None else float(_base),
            True if (len(IN) <= 8 or IN[8] is None) else bool(IN[8]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoGoLogia_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
