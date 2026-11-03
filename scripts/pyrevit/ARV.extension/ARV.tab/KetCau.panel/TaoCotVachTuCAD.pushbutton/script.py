# -*- coding: utf-8 -*-
# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-29)
"""Tạo cột và vách/lõi kết cấu từ mặt bằng định vị cột vách lõi (DWG đã Link/Import vào Revit).

Quy trình:
  1. Chọn bản CAD và các layer cột / vách / lõi.
  2. Đọc mọi vòng khép kín (polyline, hoặc line rời nối nhau, kể cả trong block).
     Vòng nằm trong vòng khác được coi là lỗ rỗng (ví dụ lõi thang vẽ 2 đường viền).
  3. Phân loại:
       - Hình chữ nhật đơn có cạnh dài / cạnh ngắn < tỉ lệ (mặc định 4) → CỘT.
       - Hình chữ nhật dài hơn → VÁCH.
       - Hình L, T, U, lõi rỗng… (cạnh vuông góc nhau) → tách thành các đoạn VÁCH chữ nhật.
       - Hình tròn, hình có cạnh xiên → bỏ qua, ghi vào báo cáo.
  4. Cột: dùng family cột chữ nhật đã chọn; type tìm theo b × h, chưa có thì nhân bản.
     Vách: dùng wall type mẫu; type tìm theo chiều dày, chưa có thì nhân bản và đổi chiều dày.
  5. Mặc định chạy thử (dry-run): chỉ báo cáo, không ghi vào mô hình.

Ghi chú:
  - Không chạy trên file central. Chạy thử trên file copy trước khi dùng cho dự án.
  - Revit API không đọc được chữ (tên cột/vách) trong CAD, nên Mark để trống.
"""

import os
import io
import math
import datetime

from pyrevit import revit, DB, forms, script

__title__ = "Tạo cột vách\ntừ CAD"
__author__ = "Archivina BIM"

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# --- Cấu hình ---------------------------------------------------------------------
JOIN_TOL_MM = 1.0          # Sai số nối đầu mút line / gộp toạ độ
DUP_TOL_MM = 5.0           # Khoảng cách coi là trùng cấu kiện
ANGLE_TOL = 1e-3           # Sai số vuông góc / thẳng hàng (rad)
DEFAULT_WALL_RATIO = 4.0   # Cạnh dài / cạnh ngắn ≥ giá trị này thì là vách
LAYER_HINTS = ("COT", "VACH", "LOI", "COL", "WALL", "CORE")
# [cần xác nhận] standards chưa quy định tên type cột / vách; BIM Manager chốt rồi sửa tại đây
COLUMN_TYPE_NAME = u"{b}x{h}"
WALL_TYPE_NAME = u"{base}_{t}"

TRANSACTION_NAME = u"ARV - Tạo cột vách kết cấu từ CAD"
MM = DB.UnitTypeId.Millimeters


# --- Tiện ích ---------------------------------------------------------------------
def to_mm(feet):
    return DB.UnitUtils.ConvertFromInternalUnits(feet, MM)


def from_mm(mm):
    return DB.UnitUtils.ConvertToInternalUnits(mm, MM)


def id_value(element_id):
    value = getattr(element_id, "Value", None)
    return value if value is not None else element_id.IntegerValue


def flat(p):
    return DB.XYZ(p.X, p.Y, 0)


def same_point(a, b, tol):
    """So khoảng cách tuyệt đối. XYZ.IsAlmostEqualTo của Revit so tương đối theo độ lớn vector,
    ở toạ độ xa gốc (CAD link) ngưỡng 0.1 mm thành hàng trăm mm và gộp mất đỉnh."""
    return a.DistanceTo(b) <= tol


def get_name(element):
    return revit.query.get_name(element)


def fmt_xy(p):
    return u"({:.0f}, {:.0f})".format(to_mm(p.X), to_mm(p.Y))


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = DB.ModelPathUtils.ConvertModelPathToUserVisiblePath(
            document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def model_role(document):
    # Trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-S-0001
    parts = (document.Title or "").split("-")
    return parts[5].upper() if len(parts) >= 7 else None


def require_role(document, role, role_name):
    """Từ chối chạy nếu mã bộ môn trong tên file không đúng (CLAUDE.md mục 2, 4)."""
    actual = model_role(document)
    if actual != role:
        forms.alert(u"Công cụ này chỉ chạy trên mô hình {} ({}).\n"
                    u"Mã bộ môn đọc từ tên file '{}': {}.\n\n"
                    u"Lưu file theo tên ISO 19650 (ví dụ PRJ-ARV-T1-TY-M3-{}-0001) rồi chạy lại.".format(
                        role_name, role, document.Title, actual or u"không xác định", role),
                    exitscript=True)


def ask_dry_run(apply_label):
    """Chọn chế độ chạy. Mặc định chạy thử; chế độ ghi phải xác nhận thêm một lần."""
    dry_label = u"Chạy thử (dry-run) – chỉ báo cáo"
    mode = forms.CommandSwitchWindow.show([dry_label, apply_label], message=u"Chế độ chạy:")
    if not mode:
        script.exit()
    if mode != apply_label:
        return True
    return not forms.alert(u"Chế độ GHI sẽ thay đổi mô hình '{}'.\n"
                           u"Đã chạy thử và kiểm tra báo cáo chưa?\n\n"
                           u"Chọn No để quay về chạy thử.".format(doc.Title), yes=True, no=True)


def size_param(symbol, name):
    # Ngoại lệ quy tắc LookupParameter (CLAUDE.md mục 5): b / h là family parameter của family cột,
    # không phải shared parameter nên không có GUID hay BuiltInParameter, chỉ tra được theo tên.
    # Tên đã được kiểm tra là duy nhất trên type trước khi ghi. [cần BIM Manager duyệt ngoại lệ]
    return symbol.GetParameters(name)[0]


# --- Đọc hình học CAD -------------------------------------------------------------
def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return None


def iter_cad_objects(cad):
    """Duyệt mọi đối tượng hình học của CAD, kể cả trong block lồng nhau."""
    opt = DB.Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)

    def walk(geo):
        for obj in geo:
            if isinstance(obj, DB.GeometryInstance):
                for sub in walk(obj.GetInstanceGeometry()):
                    yield sub
            else:
                yield obj

    geo = cad.get_Geometry(opt)
    return walk(geo) if geo is not None else iter([])


def simplify_loop(points):
    """Bỏ điểm trùng, điểm đóng vòng và điểm thẳng hàng."""
    tol = from_mm(0.1)
    pts = []
    for p in points:
        p = flat(p)
        if not pts or not same_point(pts[-1], p, tol):
            pts.append(p)
    if len(pts) > 1 and same_point(pts[0], pts[-1], tol):
        pts.pop()
    changed = True
    while changed and len(pts) > 3:
        changed = False
        n = len(pts)
        for i in range(n):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n]
            v1 = b.Subtract(a).Normalize()
            v2 = c.Subtract(b).Normalize()
            if v1.CrossProduct(v2).GetLength() < ANGLE_TOL:
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

    used = set()
    loops = []
    for start in range(len(segs)):
        if start in used:
            continue
        used.add(start)
        first, current = segs[start]
        loop = [first]
        closed = False
        while True:
            if key(current) == key(first):
                closed = True
                break
            nxt = [i for i in by_key.get(key(current), []) if i not in used]
            if not nxt:
                break
            i = nxt[0]
            used.add(i)
            a, b = segs[i]
            loop.append(current)
            current = b if key(a) == key(current) else a
        if closed and len(loop) >= 3:
            loops.append(loop)
    return loops


def polygon_area(pts):
    n = len(pts)
    return abs(sum(pts[i].X * pts[(i + 1) % n].Y - pts[(i + 1) % n].X * pts[i].Y for i in range(n))) / 2.0


def centroid(pts):
    return DB.XYZ(sum(p.X for p in pts) / len(pts), sum(p.Y for p in pts) / len(pts), 0)


def point_in_poly(x, y, poly):
    """Ray casting; poly là danh sách (x, y)."""
    inside = False
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            if x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                inside = not inside
    return inside


def read_loops(cad, layers):
    """Trả về (danh sách vòng kín đã làm sạch, số hình tròn bỏ qua)."""
    polylines, lines, circles = [], [], 0
    for obj in iter_cad_objects(cad):
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, DB.PolyLine):
            polylines.append(list(obj.GetCoordinates()))
        elif isinstance(obj, DB.Line):
            lines.append(obj)
        elif isinstance(obj, DB.Arc) and not obj.IsBound:
            circles += 1

    loops = []
    tol = from_mm(DUP_TOL_MM)
    for raw in polylines + loops_from_lines(lines):
        pts = simplify_loop(raw)
        if len(pts) < 3:
            continue
        area, c = polygon_area(pts), centroid(pts)
        # Bỏ vòng vẽ chồng (cùng số đỉnh, cùng tâm, cùng diện tích)
        if any(len(o) == len(pts) and same_point(c, centroid(o), tol)
               and abs(polygon_area(o) - area) < tol * tol for o in loops):
            continue
        loops.append(pts)
    return loops, circles


def build_regions(loops):
    """Ghép vòng ngoài với các vòng lỗ nằm ngay bên trong. Trả về [(outer, [holes])]."""
    xy = [[(p.X, p.Y) for p in l] for l in loops]
    areas = [polygon_area(l) for l in loops]
    depth, parents = [], []
    for i, loop in enumerate(loops):
        # Chỉ coi là lỗ khi mọi đỉnh nằm hẳn bên trong; hai hình cắt chéo nhau không phải lỗ
        containers = [j for j in range(len(loops))
                      if j != i and areas[j] > areas[i]
                      and all(point_in_poly(x, y, xy[j]) for x, y in xy[i])]
        depth.append(len(containers))
        parents.append(containers)
    regions = []
    for i, loop in enumerate(loops):
        if depth[i] % 2 == 0:
            holes = [loops[k] for k in range(len(loops))
                     if depth[k] == depth[i] + 1 and i in parents[k]]
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
    uy = DB.XYZ(-ux.Y, ux.X, 0)
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
            min_h = None
            i = i0
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
    if abs(angle) < 1e-6:
        angle = 0.0
    return w, d, angle


# --- Chọn đầu vào -----------------------------------------------------------------
def pick_cad_instance():
    selected = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
    selected = [e for e in selected if isinstance(e, DB.ImportInstance)]
    if len(selected) == 1:
        return selected[0], get_name(doc.GetElement(selected[0].GetTypeId()))

    instances = DB.FilteredElementCollector(doc).OfClass(DB.ImportInstance).ToElements()
    if not instances:
        forms.alert(u"Không tìm thấy bản CAD nào được Link/Import trong mô hình.", exitscript=True)
    options = {}
    for inst in instances:
        label = u"{} [{}] – Id {}".format(get_name(doc.GetElement(inst.GetTypeId())),
                                          u"Link" if inst.IsLinked else u"Import", id_value(inst.Id))
        options[label] = inst
    choice = forms.SelectFromList.show(sorted(options.keys()), title=u"Chọn bản CAD mặt bằng cột vách lõi",
                                       button_name=u"Chọn")
    if not choice:
        script.exit()
    return options[choice], choice


def pick_level(levels, title):
    name = forms.SelectFromList.show([l.Name for l in levels], title=title, button_name=u"Chọn")
    if not name:
        script.exit()
    return [l for l in levels if l.Name == name][0]


def ask_column_family():
    symbols = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralColumns) \
        .WhereElementIsElementType().ToElements()
    families = {}
    for s in symbols:
        families.setdefault(s.Family.Name, s.Family)
    if not families:
        forms.alert(u"Mô hình chưa load family cột kết cấu nào.", exitscript=True)
    family_name = forms.SelectFromList.show(sorted(families), title=u"Chọn family cột (tiết diện chữ nhật)",
                                            button_name=u"Chọn")
    if not family_name:
        script.exit()
    symbols = [doc.GetElement(i) for i in families[family_name].GetFamilySymbolIds()]
    param_b = forms.ask_for_string(default="b", title=u"Parameter kích thước",
                                   prompt=u"Tên parameter type cho cạnh theo trục X của family:")
    param_h = forms.ask_for_string(default="h", title=u"Parameter kích thước",
                                   prompt=u"Tên parameter type cho cạnh theo trục Y của family:")
    if not param_b or not param_h:
        script.exit()
    for pname in (param_b, param_h):
        found = symbols[0].GetParameters(pname)
        if len(found) != 1 or found[0].StorageType != DB.StorageType.Double or found[0].IsReadOnly:
            forms.alert(u"Family '{}' phải có đúng một parameter type '{}' kiểu chiều dài, sửa được.".format(
                family_name, pname), exitscript=True)
    return family_name, symbols, param_b, param_h


def ask_wall_template():
    types = [t for t in DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
             if t.Kind == DB.WallKind.Basic]
    if not types:
        forms.alert(u"Mô hình không có wall type dạng Basic nào.", exitscript=True)
    by_name = dict((get_name(t), t) for t in types)
    name = forms.SelectFromList.show(sorted(by_name), title=u"Chọn wall type mẫu cho vách kết cấu",
                                     button_name=u"Chọn")
    if not name:
        script.exit()
    return by_name[name], by_name


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


def write_log(rows, dry_run, cad_label):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoCotVachTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
    with io.open(path, "w", encoding="utf-8-sig") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(cad_label))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm, độ\n")
        f.write(u",".join(LOG_HEADER) + u"\n")
        for r in rows:
            f.write(u",".join(u'"{}"'.format(u"{}".format(v).replace(u'"', u'""')) for v in r) + u"\n")
    return path


# --- Chương trình chính -----------------------------------------------------------
def main():
    if is_central_file(doc):
        forms.alert(u"File đang mở là file CENTRAL. Không được sửa trực tiếp file central.\n"
                    u"Hãy mở file local hoặc bản detached/copy rồi chạy lại.", exitscript=True)
    require_role(doc, "S", u"Kết cấu")

    cad, cad_label = pick_cad_instance()
    all_layers = sorted(set(l for l in (layer_of(o) for o in iter_cad_objects(cad)) if l))
    if not all_layers:
        forms.alert(u"Không đọc được hình học của bản CAD.", exitscript=True)
    hinted = [l for l in all_layers if any(h in l.upper() for h in LAYER_HINTS)]
    layers = forms.SelectFromList.show(
        all_layers, title=u"Chọn layer cột / vách / lõi (gợi ý: {})".format(u", ".join(hinted) or u"không có"),
        multiselect=True, button_name=u"Chọn layer")
    if not layers:
        script.exit()

    ratio_text = forms.ask_for_string(default=str(DEFAULT_WALL_RATIO), title=u"Phân loại cột / vách",
                                      prompt=u"Hình chữ nhật có cạnh dài / cạnh ngắn ≥ giá trị này là VÁCH:")
    try:
        wall_ratio = float(ratio_text)
    except (TypeError, ValueError):
        script.exit()

    # Phân tích hình học
    loops, circles = read_loops(cad, set(layers))
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
    if not columns and not walls:
        forms.alert(u"Không tìm thấy vòng khép kín nào trên layer đã chọn.", exitscript=True)

    col_cfg = ask_column_family() if columns else None
    wall_template, wall_types_by_name = ask_wall_template() if walls else (None, {})

    levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements(), key=lambda l: l.Elevation)
    base_level = pick_level(levels, u"Chọn level chân cột / vách")
    upper = [l for l in levels if l.Elevation > base_level.Elevation]
    if not upper:
        forms.alert(u"Không có level nào cao hơn '{}'.".format(base_level.Name), exitscript=True)
    top_level = pick_level(upper, u"Chọn level đỉnh cột / vách")

    dry_run = ask_dry_run(u"Tạo cột vách vào mô hình")

    z = base_level.Elevation
    dup_tol = from_mm(DUP_TOL_MM)
    rows, col_jobs, wall_jobs = [], [], []

    # --- Lập kế hoạch cột
    col_types, new_col_types = {}, {}
    if columns:
        family_name, symbols, param_b, param_h = col_cfg
        used_names = set(get_name(s) for s in symbols)
        for s in symbols:
            pb, ph = s.LookupParameter(param_b), s.LookupParameter(param_h)
            if pb is not None and ph is not None:
                col_types.setdefault((int(round(to_mm(pb.AsDouble()))), int(round(to_mm(ph.AsDouble())))), s)
        existing = [flat(c.Location.Point) for c in
                    DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralColumns)
                    .WhereElementIsNotElementType()
                    if c.LevelId == base_level.Id and isinstance(c.Location, DB.LocationPoint)]
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
            if any(same_point(center, p, dup_tol) for p in existing):
                row[5] = u"Bỏ qua – đã có cột"
            else:
                row[5] = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                col_jobs.append((center, k, angle, len(rows)))
            rows.append(row)

    # --- Lập kế hoạch vách
    wall_types, new_wall_types = {}, {}
    if walls:
        base_name = get_name(wall_template)
        existing = []
        for wl in DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements():
            loc = wl.Location
            if wl.LevelId == base_level.Id and isinstance(loc, DB.LocationCurve) and isinstance(loc.Curve, DB.Line):
                c = loc.Curve
                existing.append((flat(c.Evaluate(0.5, True)), c.Direction))
        for center, length, thick, direction, single in walls:
            t = int(round(to_mm(thick)))
            if t not in wall_types and t not in new_wall_types:
                if int(round(to_mm(wall_template.Width))) == t:
                    wall_types[t] = wall_template
                else:
                    name = WALL_TYPE_NAME.format(base=base_name, t=t)
                    if name in wall_types_by_name:
                        wall_types[t] = wall_types_by_name[name]
                    else:
                        new_wall_types[t] = name
            wtype = wall_types.get(t)
            type_name = get_name(wtype) if wtype else new_wall_types[t]
            angle = math.degrees(math.atan2(direction.Y, direction.X))
            row = [u"Vách" if single else u"Vách (tách từ lõi)", fmt_xy(center),
                   u"L={:.0f}, t={}".format(to_mm(length), t), u"{:.2f}".format(angle),
                   type_name + (u" (mới)" if wtype is None else u""), u"", u"", u"—", type_name]
            if wtype is not None and int(round(to_mm(wtype.Width))) != t:
                row[5] = u"Bỏ qua – type '{}' đã có nhưng dày {:.0f} mm".format(type_name, to_mm(wtype.Width))
            elif any(same_point(center, p, dup_tol) and direction.CrossProduct(dvec).GetLength() < ANGLE_TOL
                     for p, dvec in existing):
                row[5] = u"Bỏ qua – đã có vách"
            else:
                row[5] = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                half = direction.Multiply(length / 2.0)
                p0 = center.Subtract(half)
                p1 = center.Add(half)
                wall_jobs.append((DB.XYZ(p0.X, p0.Y, z), DB.XYZ(p1.X, p1.Y, z), t, len(rows)))
            rows.append(row)

    for p in skewed:
        rows.append([u"?", fmt_xy(p), u"", u"", u"", u"Bỏ qua – hình có cạnh xiên, cần vẽ tay", u"", u"—", u"—"])

    # --- Ghi vào mô hình
    if not dry_run and (col_jobs or wall_jobs):
        try:
            with revit.Transaction(TRANSACTION_NAME, doc=doc):
                if col_jobs:
                    _, symbols, param_b, param_h = col_cfg
                    for k, name in new_col_types.items():
                        sym = symbols[0].Duplicate(name)
                        size_param(sym, param_b).Set(from_mm(k[0]))
                        size_param(sym, param_h).Set(from_mm(k[1]))
                        col_types[k] = sym
                for t, name in new_wall_types.items():
                    wtype = wall_template.Duplicate(name)
                    set_wall_thickness(wtype, from_mm(t))
                    wall_types[t] = wtype

                for center, k, angle, row_idx in col_jobs:
                    sym = col_types[k]
                    if not sym.IsActive:
                        sym.Activate()
                        doc.Regenerate()
                    pt = DB.XYZ(center.X, center.Y, z)
                    inst = doc.Create.NewFamilyInstance(pt, sym, base_level, DB.Structure.StructuralType.Column)
                    inst.get_Parameter(DB.BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(0.0)
                    inst.get_Parameter(DB.BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).Set(top_level.Id)
                    inst.get_Parameter(DB.BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(0.0)
                    if angle:
                        axis = DB.Line.CreateBound(pt, pt.Add(DB.XYZ.BasisZ))
                        DB.ElementTransformUtils.RotateElement(doc, inst.Id, axis, angle)
                    rows[row_idx][5] = u"Đã tạo"
                    rows[row_idx][6] = id_value(inst.Id)

                height = top_level.Elevation - base_level.Elevation
                for p0, p1, t, row_idx in wall_jobs:
                    wall = DB.Wall.Create(doc, DB.Line.CreateBound(p0, p1), wall_types[t].Id, base_level.Id,
                                          height, 0.0, False, True)
                    wall.get_Parameter(DB.BuiltInParameter.WALL_BASE_OFFSET).Set(0.0)
                    wall.get_Parameter(DB.BuiltInParameter.WALL_HEIGHT_TYPE).Set(top_level.Id)
                    wall.get_Parameter(DB.BuiltInParameter.WALL_TOP_OFFSET).Set(0.0)
                    rows[row_idx][5] = u"Đã tạo"
                    rows[row_idx][6] = id_value(wall.Id)
        except Exception as ex:
            # revit.Transaction tự RollBack khi có lỗi
            forms.alert(u"Lỗi khi tạo cột vách, mọi thay đổi đã được hoàn tác.\n\n{}".format(ex), exitscript=True)

    # --- Báo cáo
    output.print_md(u"## {} – {}".format(TRANSACTION_NAME,
                                          u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN"))
    output.print_md(
        u"- Mô hình: **{}**\n- File CAD: **{}** – layer: {}\n- Level: **{}** → **{}**\n"
        u"- Tỉ lệ phân loại vách: ≥ {}\n- Cột: {} – Vách: {}\n"
        u"- Bỏ qua: {} hình tròn, {} hình có cạnh xiên\n- Type cột mới: {}\n- Type vách mới: {}".format(
            doc.Title, cad_label, u", ".join(layers), base_level.Name, top_level.Name, wall_ratio,
            len(columns), len(walls), circles, len(skewed),
            u", ".join(sorted(new_col_types.values())) or u"không có",
            u", ".join(sorted(new_wall_types.values())) or u"không có"))
    output.print_table(table_data=rows, columns=LOG_HEADER)
    try:
        output.print_md(u"Log: `{}`".format(write_log(rows, dry_run, cad_label)))
    except Exception as ex:
        output.print_md(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        output.print_md(u"> Kiểm tra bảng trên. Nếu đúng, chạy lại và chọn **Tạo cột vách vào mô hình**.")


main()
