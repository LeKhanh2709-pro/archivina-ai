# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoCotVachTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo cột và vách/lõi kết cấu từ mặt bằng định vị cột vách lõi (DWG đã Link/Import vào Revit).
#   - Hình chữ nhật đơn có cạnh dài / cạnh ngắn < tỉ lệ  → CỘT (đúng b × h, góc xoay)
#   - Hình chữ nhật dài hơn                            → VÁCH
#   - Lõi hình L, T, U, lõi rỗng (cạnh vuông góc)        → tách thành các đoạn VÁCH chữ nhật
#   - Hình tròn, hình có cạnh xiên                      → bỏ qua, ghi vào báo cáo
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống nếu mô hình chỉ có 1 bản CAD)
#   IN[1] (str)   Chuỗi lọc layer, nhiều chuỗi cách nhau bằng ';' – layer chứa một trong các chuỗi sẽ được dùng
#                 (ví dụ "$0$S-Cot vach" lấy cả "...$0$S-Cot vach" và "...$0$S-Cot vach dung")
#   IN[2] (float) Tỉ lệ cạnh dài / cạnh ngắn để coi là vách (mặc định 4)
#   IN[3] (str)   Tên family cột kết cấu tiết diện chữ nhật (để trống = lấy theo tên file ở IN[10])
#   IN[4] (str)   Tên parameter type cạnh theo trục X của family (ví dụ "b")
#   IN[5] (str)   Tên parameter type cạnh theo trục Y của family (ví dụ "h")
#   IN[6] (str)   Tên wall type mẫu (Basic) cho vách kết cấu
#   IN[7] (str)   Tên level chân cột / vách
#   IN[8] (str)   Tên level đỉnh cột / vách
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo, không ghi vào mô hình (mặc định True)
#   IN[10] (str)  Đường dẫn file .rfa của family cột (tuỳ chọn). Nếu mô hình chưa có family ở IN[3] thì load
#                 từ file này; khi dry-run, family được load tạm để kiểm tra rồi hoàn tác.
# OUTPUT
#   OUT (list[str]) Báo cáo: tóm tắt, layer đã dùng, đường dẫn log, rồi từng cấu kiện:
#                   Loại | Tâm | Kích thước | Góc | Type | Kết quả | ElementId

import clr
import os
import io
import csv
import math
import datetime

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, Options, GeometryInstance, PolyLine,
                               Line, Arc, XYZ, Transaction, UnitUtils, UnitTypeId, ModelPathUtils,
                               BuiltInParameter, BuiltInCategory, Level, Wall, WallType, WallKind,
                               LocationPoint, LocationCurve, StorageType, ElementTransformUtils)
from Autodesk.Revit.DB.Structure import StructuralType
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo cột vách kết cấu từ CAD"
JOIN_TOL_MM = 1.0          # Sai số nối đầu mút line / gộp toạ độ
DUP_TOL_MM = 5.0           # Khoảng cách coi là trùng cấu kiện
ANGLE_TOL = 1e-3           # Sai số vuông góc / thẳng hàng (rad)
# [cần xác nhận] standards chưa quy định tên type cột / vách; BIM Manager chốt rồi sửa tại đây
COLUMN_TYPE_NAME = u"{b}x{h}"
WALL_TYPE_NAME = u"{base}_{t}"

cad_filter = (IN[0] or u"").strip()
layer_filters = [s.strip() for s in (IN[1] or u"").split(u";") if s.strip()]
wall_ratio = float(IN[2]) if IN[2] else 4.0
family_path = (IN[10] or u"").strip() if len(IN) > 10 else u""
family_name = (IN[3] or u"").strip() or os.path.splitext(os.path.basename(family_path))[0]
param_b = (IN[4] or u"b").strip()
param_h = (IN[5] or u"h").strip()
wall_type_name = (IN[6] or u"").strip()
base_level_name = (IN[7] or u"").strip()
top_level_name = (IN[8] or u"").strip()
dry_run = True if IN[9] is None else bool(IN[9])


# --- Tiện ích ---------------------------------------------------------------------
def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def flat(p):
    return XYZ(p.X, p.Y, 0)


def fmt_xy(p):
    return u"({:.0f}, {:.0f})".format(to_mm(p.X), to_mm(p.Y))


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


def model_role(document):
    # Trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-S-0001
    parts = (document.Title or "").split("-")
    return parts[5].upper() if len(parts) >= 7 else None


# --- Đọc hình học CAD -------------------------------------------------------------
def pick_cad():
    instances = list(FilteredElementCollector(doc).OfClass(ImportInstance).ToElements())
    if cad_filter:
        instances = [i for i in instances
                     if cad_filter.lower() in get_name(doc.GetElement(i.GetTypeId())).lower()]
    if len(instances) != 1:
        names = [get_name(doc.GetElement(i.GetTypeId())) for i in
                 FilteredElementCollector(doc).OfClass(ImportInstance).ToElements()]
        raise Exception(u"Tìm thấy {} bản CAD khớp '{}'. Nhập tên bản CAD vào ô IN[0]. Các bản CAD: {}".format(
            len(instances), cad_filter, u", ".join(names) or u"không có"))
    return instances[0]


def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return None


def cad_objects(cad):
    """Mọi đối tượng hình học của CAD, kể cả trong block lồng nhau."""
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


def simplify_loop(points):
    """Bỏ điểm trùng, điểm đóng vòng và điểm thẳng hàng."""
    tol = from_mm(0.1)
    pts = []
    for p in points:
        p = flat(p)
        if not pts or not pts[-1].IsAlmostEqualTo(p, tol):
            pts.append(p)
    if len(pts) > 1 and pts[0].IsAlmostEqualTo(pts[-1], tol):
        pts.pop()
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            if b.Subtract(a).Normalize().CrossProduct(c.Subtract(b).Normalize()).GetLength() < ANGLE_TOL:
                del pts[i]
                changed = True
                break
    return pts


def loops_from_lines(lines):
    """Nối các line rời thành các vòng khép kín."""
    step = from_mm(JOIN_TOL_MM)

    def key(p):
        return (int(round(p.X / step)), int(round(p.Y / step)))

    segs = [(flat(l.GetEndPoint(0)), flat(l.GetEndPoint(1))) for l in lines]
    by_key = {}
    for idx, (a, b) in enumerate(segs):
        by_key.setdefault(key(a), []).append(idx)
        by_key.setdefault(key(b), []).append(idx)
    used, loops = set(), []
    for start in range(len(segs)):
        if start in used:
            continue
        used.add(start)
        first, current = segs[start]
        loop, closed = [first], False
        while True:
            if key(current) == key(first):
                closed = True
                break
            nxt = [i for i in by_key.get(key(current), []) if i not in used]
            if not nxt:
                break
            used.add(nxt[0])
            a, b = segs[nxt[0]]
            loop.append(current)
            current = b if key(a) == key(current) else a
        if closed and len(loop) >= 3:
            loops.append(loop)
    return loops


def polygon_area(pts):
    n = len(pts)
    return abs(sum(pts[i].X * pts[(i + 1) % n].Y - pts[(i + 1) % n].X * pts[i].Y for i in range(n))) / 2.0


def centroid(pts):
    return XYZ(sum(p.X for p in pts) / len(pts), sum(p.Y for p in pts) / len(pts), 0)


def point_in_poly(x, y, poly):
    """Ray casting; poly là danh sách (x, y)."""
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def read_loops(objects, layers):
    polylines, lines, circles = [], [], 0
    for obj in objects:
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, PolyLine):
            polylines.append(list(obj.GetCoordinates()))
        elif isinstance(obj, Line):
            lines.append(obj)
        elif isinstance(obj, Arc) and not obj.IsBound:
            circles += 1
    loops = []
    tol = from_mm(DUP_TOL_MM)
    for raw in polylines + loops_from_lines(lines):
        pts = simplify_loop(raw)
        if len(pts) < 3:
            continue
        area, c = polygon_area(pts), centroid(pts)
        # Bỏ vòng vẽ chồng (cùng số đỉnh, cùng tâm, cùng diện tích) – kể cả ở hai layer khác nhau
        if any(len(o) == len(pts) and c.IsAlmostEqualTo(centroid(o), tol)
               and abs(polygon_area(o) - area) < tol * tol for o in loops):
            continue
        loops.append(pts)
    return loops, circles


def build_regions(loops):
    """Ghép vòng ngoài với các vòng lỗ nằm hẳn bên trong. Trả về [(outer, [holes])]."""
    xy = [[(p.X, p.Y) for p in l] for l in loops]
    areas = [polygon_area(l) for l in loops]
    parents = []
    for i in range(len(loops)):
        parents.append([j for j in range(len(loops))
                        if j != i and areas[j] > areas[i] and all(point_in_poly(x, y, xy[j]) for x, y in xy[i])])
    regions = []
    for i, loop in enumerate(loops):
        if len(parents[i]) % 2 == 0:
            holes = [loops[k] for k in range(len(loops))
                     if len(parents[k]) == len(parents[i]) + 1 and i in parents[k]]
            regions.append((loop, holes))
    return regions


def unique_sorted(values, tol):
    result = []
    for v in sorted(values):
        if not result or v - result[-1] > tol:
            result.append(v)
    return result


def decompose(outer, holes):
    """Tách vùng có cạnh vuông góc thành các hình chữ nhật lớn nhất có thể.

    Trả về [(tâm, cạnh dài, cạnh ngắn, vector phương cạnh dài)] hoặc None nếu có cạnh xiên.
    """
    ux = outer[1].Subtract(outer[0]).Normalize()
    uy = XYZ(-ux.Y, ux.X, 0)
    polys = [[(p.DotProduct(ux), p.DotProduct(uy)) for p in loop] for loop in [outer] + holes]
    tol = from_mm(JOIN_TOL_MM)
    for poly in polys:
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            if abs(x1 - x0) > tol and abs(y1 - y0) > tol:
                return None
    xs = unique_sorted([x for poly in polys for x, _ in poly], tol)
    ys = unique_sorted([y for poly in polys for _, y in poly], tol)
    free = set()
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2.0, (ys[j] + ys[j + 1]) / 2.0
            if point_in_poly(cx, cy, polys[0]) and not any(point_in_poly(cx, cy, h) for h in polys[1:]):
                free.add((i, j))
    pieces = []
    while free:
        # Chọn hình chữ nhật diện tích lớn nhất trong các ô còn lại (ô gốc ở góc dưới trái)
        best = None
        for (i0, j0) in free:
            min_h, i = None, i0
            while (i, j0) in free:
                h = 0
                while (i, j0 + h) in free:
                    h += 1
                min_h = h if min_h is None else min(min_h, h)
                area = (xs[i + 1] - xs[i0]) * (ys[j0 + min_h] - ys[j0])
                if best is None or area > best[0] + 1e-9:
                    best = (area, i0, i, j0, j0 + min_h - 1)
                i += 1
        _, i0, i1, j0, j1 = best
        for i in range(i0, i1 + 1):
            for j in range(j0, j1 + 1):
                free.discard((i, j))
        x0, x1, y0, y1 = xs[i0], xs[i1 + 1], ys[j0], ys[j1 + 1]
        center = ux.Multiply((x0 + x1) / 2.0).Add(uy.Multiply((y0 + y1) / 2.0))
        lx, ly = x1 - x0, y1 - y0
        pieces.append((center, lx, ly, ux) if lx >= ly else (center, ly, lx, uy))
    return pieces


def column_frame(direction, along, across):
    """Đưa góc xoay về [-45°, 45°); mỗi lần xoay 90° thì đổi chỗ b và h."""
    angle = math.atan2(direction.Y, direction.X)
    w, d = along, across
    while angle >= math.pi / 4:
        angle -= math.pi / 2
        w, d = d, w
    while angle < -math.pi / 4:
        angle += math.pi / 2
        w, d = d, w
    return w, d, (0.0 if abs(angle) < 1e-6 else angle)


# --- Type, level ----------------------------------------------------------------
def find_level(name):
    for l in FilteredElementCollector(doc).OfClass(Level).ToElements():
        if l.Name == name:
            return l
    names = sorted(l.Name for l in FilteredElementCollector(doc).OfClass(Level).ToElements())
    raise Exception(u"Không có level '{}'. Các level: {}".format(name, u", ".join(names)))


def column_symbols(notes):
    """Lấy các type của family cột; nếu mô hình chưa có thì load từ file .rfa (phải gọi trong Transaction)."""
    def collect():
        return list(FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsElementType().ToElements())

    symbols = collect()
    result = [s for s in symbols if s.Family.Name == family_name]
    if not result and family_path:
        if not os.path.isfile(family_path):
            raise Exception(u"Không tìm thấy file family: {}".format(family_path))
        doc.LoadFamily(family_path)
        symbols = collect()
        result = [s for s in symbols if s.Family.Name == family_name]
        if not result:
            raise Exception(u"Đã load '{}' nhưng không thấy family cột KẾT CẤU tên '{}'. Kiểm tra category của "
                            u"family (phải là Structural Columns) và ô IN[3].".format(family_path, family_name))
        notes.append(u"Family '{}' được load từ {}{}.".format(
            family_name, family_path, u" (tạm, sẽ hoàn tác vì dry-run)" if dry_run else u""))
    if not result:
        names = sorted(set(s.Family.Name for s in symbols))
        if not family_name:
            raise Exception(u"Ô IN[3] (tên family cột) đang trống. Điền một trong các family cột: {}".format(
                u", ".join(names) or u"không có"))
        raise Exception(u"Không có family cột '{}'. Các family cột: {}".format(
            family_name, u", ".join(names) or u"không có"))
    for pname in (param_b, param_h):
        p = result[0].LookupParameter(pname)
        if p is None or p.StorageType != StorageType.Double:
            raise Exception(u"Family '{}' không có parameter type '{}' kiểu chiều dài.".format(family_name, pname))
    return result


def wall_types():
    types = [t for t in FilteredElementCollector(doc).OfClass(WallType).ToElements() if t.Kind == WallKind.Basic]
    by_name = dict((get_name(t), t) for t in types)
    if wall_type_name not in by_name:
        raise Exception(u"Không có wall type '{}'. Các wall type Basic: {}".format(
            wall_type_name, u", ".join(sorted(by_name))))
    return by_name[wall_type_name], by_name


def set_wall_thickness(wall_type, total_ft):
    """Đổi chiều dày lớp kết cấu để tổng chiều dày tường bằng giá trị yêu cầu."""
    cs = wall_type.GetCompoundStructure()
    idx = cs.StructuralMaterialIndex
    if idx < 0:
        idx = cs.GetFirstCoreLayerIndex()
    others = sum(cs.GetLayerWidth(i) for i in range(cs.LayerCount) if i != idx)
    core = total_ft - others
    if core < from_mm(1.0):
        raise Exception(u"Type '{}' có lớp hoàn thiện dày hơn chiều dày vách {:.0f} mm".format(
            get_name(wall_type), to_mm(total_ft)))
    cs.SetLayerWidth(idx, core)
    wall_type.SetCompoundStructure(cs)


# --- Log ----------------------------------------------------------------------------
LOG_HEADER = [u"Loại", u"Tâm (mm)", u"Kích thước (mm)", u"Góc (°)", u"Type", u"Kết quả",
              u"ElementId", u"Giá trị cũ", u"Giá trị mới"]


def write_log(rows, source):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoCotVachTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm, độ\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


# --- Chương trình chính -----------------------------------------------------------
def main():
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."]
    warnings = []
    if model_role(doc) == "A":
        warnings.append(u"CẢNH BÁO: đây có vẻ là mô hình Kiến trúc (A). Cột và vách kết cấu thuộc mô hình Kết cấu (S).")

    cad = pick_cad()
    cad_name = get_name(doc.GetElement(cad.GetTypeId()))
    objects = cad_objects(cad)
    all_layers = sorted(set(l for l in (layer_of(o) for o in objects) if l))
    layers = set(l for l in all_layers if any(f.lower() in l.lower() for f in layer_filters))
    if not layers:
        return [u"DỪNG: không có layer nào chứa '{}'. Các layer trong CAD:".format(u"; ".join(layer_filters))] \
            + all_layers

    base_level = find_level(base_level_name)
    top_level = find_level(top_level_name)
    if top_level.Elevation <= base_level.Elevation:
        raise Exception(u"Level đỉnh '{}' phải cao hơn level chân '{}'.".format(top_level_name, base_level_name))

    # Phân tích hình học
    loops, circles = read_loops(objects, layers)
    columns, walls, skewed = [], [], []
    for outer, holes in build_regions(loops):
        pieces = decompose(outer, holes)
        if pieces is None:
            skewed.append(centroid(outer))
            continue
        single = len(pieces) == 1
        for center, along, across, direction in pieces:
            if single and along / across < wall_ratio:
                columns.append((center,) + column_frame(direction, along, across))
            else:
                walls.append((center, along, across, direction, single))

    z = base_level.Elevation
    dup_tol = from_mm(DUP_TOL_MM)
    rows, col_jobs, wall_jobs, notes = [], [], [], []

    # Mở Transaction từ bước lập kế hoạch vì có thể phải load family.
    # Dry-run: cuối cùng RollBack toàn bộ, mô hình không thay đổi.
    global active_tx
    TransactionManager.Instance.ForceCloseTransaction()
    active_tx = Transaction(doc, TRANSACTION_NAME)
    active_tx.Start()

    # --- Lập kế hoạch cột
    col_types, new_col_types, symbols = {}, {}, []
    if columns:
        symbols = column_symbols(notes)
        used_names = set(get_name(s) for s in symbols)
        for s in symbols:
            pb, ph = s.LookupParameter(param_b), s.LookupParameter(param_h)
            if pb is not None and ph is not None:
                col_types.setdefault((int(round(to_mm(pb.AsDouble()))), int(round(to_mm(ph.AsDouble())))), s)
        existing = [flat(c.Location.Point) for c in
                    FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType().ToElements()
                    if c.LevelId == base_level.Id and isinstance(c.Location, LocationPoint)]
        for center, w, d, angle in columns:
            k = (int(round(to_mm(w))), int(round(to_mm(d))))
            if k in col_types:
                type_name = get_name(col_types[k])
            elif k in new_col_types:
                type_name = new_col_types[k]
            else:
                type_name = COLUMN_TYPE_NAME.format(b=k[0], h=k[1])
                suffix = 1
                while type_name in used_names:
                    type_name = COLUMN_TYPE_NAME.format(b=k[0], h=k[1]) + u"_{}".format(suffix)
                    suffix += 1
                used_names.add(type_name)
                new_col_types[k] = type_name
            row = [u"Cột", fmt_xy(center), u"{} x {}".format(*k), u"{:.2f}".format(math.degrees(angle)),
                   type_name + (u" (mới)" if k in new_col_types else u""), u"", u"", u"—", type_name]
            if any(center.IsAlmostEqualTo(p, dup_tol) for p in existing):
                row[5] = u"Bỏ qua – đã có cột"
            else:
                row[5] = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                col_jobs.append((center, k, angle, len(rows)))
            rows.append(row)

    # --- Lập kế hoạch vách
    wall_by_t, new_wall_types, wall_template = {}, {}, None
    if walls:
        wall_template, types_by_name = wall_types()
        base_name = get_name(wall_template)
        existing = []
        for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
            loc = wl.Location
            if wl.LevelId == base_level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
                existing.append((flat(loc.Curve.Evaluate(0.5, True)), loc.Curve.Direction))
        for center, length, thick, direction, single in walls:
            t = int(round(to_mm(thick)))
            if t not in wall_by_t and t not in new_wall_types:
                if int(round(to_mm(wall_template.Width))) == t:
                    wall_by_t[t] = wall_template
                else:
                    name = WALL_TYPE_NAME.format(base=base_name, t=t)
                    if name in types_by_name:
                        wall_by_t[t] = types_by_name[name]
                    else:
                        new_wall_types[t] = name
            wtype = wall_by_t.get(t)
            type_name = get_name(wtype) if wtype else new_wall_types[t]
            row = [u"Vách" if single else u"Vách (tách từ lõi)", fmt_xy(center),
                   u"L={:.0f}, t={}".format(to_mm(length), t),
                   u"{:.2f}".format(math.degrees(math.atan2(direction.Y, direction.X))),
                   type_name + (u" (mới)" if wtype is None else u""), u"", u"", u"—", type_name]
            if wtype is not None and int(round(to_mm(wtype.Width))) != t:
                row[5] = u"Bỏ qua – type '{}' đã có nhưng dày {:.0f} mm".format(type_name, to_mm(wtype.Width))
            elif any(center.IsAlmostEqualTo(p, dup_tol) and direction.CrossProduct(dv).GetLength() < ANGLE_TOL
                     for p, dv in existing):
                row[5] = u"Bỏ qua – đã có vách"
            else:
                row[5] = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                half = direction.Multiply(length / 2.0)
                p0, p1 = center.Subtract(half), center.Add(half)
                wall_jobs.append((XYZ(p0.X, p0.Y, z), XYZ(p1.X, p1.Y, z), t, len(rows)))
            rows.append(row)

    for p in skewed:
        rows.append([u"?", fmt_xy(p), u"", u"", u"", u"Bỏ qua – hình có cạnh xiên, cần vẽ tay", u"", u"—", u"—"])

    # --- Ghi vào mô hình
    if not dry_run and (col_jobs or wall_jobs):
        try:
            for k, name in new_col_types.items():
                sym = symbols[0].Duplicate(name)
                sym.LookupParameter(param_b).Set(from_mm(k[0]))
                sym.LookupParameter(param_h).Set(from_mm(k[1]))
                col_types[k] = sym
            for th, name in new_wall_types.items():
                wtype = wall_template.Duplicate(name)
                set_wall_thickness(wtype, from_mm(th))
                wall_by_t[th] = wtype

            for center, k, angle, idx in col_jobs:
                sym = col_types[k]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                pt = XYZ(center.X, center.Y, z)
                inst = doc.Create.NewFamilyInstance(pt, sym, base_level, StructuralType.Column)
                inst.get_Parameter(BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(0.0)
                inst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).Set(top_level.Id)
                inst.get_Parameter(BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(0.0)
                if angle:
                    ElementTransformUtils.RotateElement(doc, inst.Id, Line.CreateBound(pt, pt.Add(XYZ.BasisZ)), angle)
                rows[idx][5] = u"Đã tạo"
                rows[idx][6] = inst.Id.Value

            height = top_level.Elevation - base_level.Elevation
            for p0, p1, th, idx in wall_jobs:
                wall = Wall.Create(doc, Line.CreateBound(p0, p1), wall_by_t[th].Id, base_level.Id,
                                   height, 0.0, False, True)
                wall.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).Set(0.0)
                wall.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(top_level.Id)
                wall.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(0.0)
                rows[idx][5] = u"Đã tạo"
                rows[idx][6] = wall.Id.Value
        except Exception as ex:
            active_tx.RollBack()
            return warnings + [u"LỖI khi tạo cột vách, mọi thay đổi đã được hoàn tác: {}".format(ex)]

    # Dry-run hoàn tác cả family load tạm; chế độ thực hiện thì ghi (Undo được trong Revit)
    if dry_run:
        active_tx.RollBack()
    else:
        active_tx.Commit()

    summary = (u"{} – {}: {} cột, {} vách; bỏ qua {} hình tròn, {} hình cạnh xiên. Tỉ lệ vách ≥ {}. "
               u"Level {} → {}. Type cột mới: {}. Type vách mới: {}.").format(
        TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN",
        len(columns), len(walls), circles, len(skewed), wall_ratio, base_level.Name, top_level.Name,
        u", ".join(sorted(new_col_types.values())) or u"không có",
        u", ".join(sorted(new_wall_types.values())) or u"không có")
    try:
        log_line = u"Log: " + write_log(rows, cad_name)
    except Exception as ex:
        log_line = u"Không ghi được file log: {}".format(ex)
    return warnings + [summary] + notes + [u"Layer đã dùng: " + u"; ".join(sorted(layers)), log_line] \
        + [u" | ".join(u"{}".format(v) for v in r[:7]) for r in rows]


active_tx = None
try:
    OUT = main()
except Exception as ex:
    if active_tx is not None and active_tx.HasStarted() and not active_tx.HasEnded():
        active_tx.RollBack()
    OUT = [u"LỖI: {}".format(ex)]
