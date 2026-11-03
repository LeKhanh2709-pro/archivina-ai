# -*- coding: utf-8 -*-
# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-29)
"""Tạo cột kết cấu từ mặt bằng định vị cột trong file CAD (DWG link hoặc import).

Đọc các hình chữ nhật khép kín (polyline hoặc 4 line nối nhau, kể cả nằm trong block)
trên layer cột của file CAD, rồi đặt cột tại tâm, đúng kích thước b x h và góc xoay.
Kiểu cột (type) được tìm theo kích thước; nếu chưa có thì nhân bản từ type đầu tiên của family.

Mặc định chạy thử (dry-run): chỉ báo cáo, không ghi vào mô hình.
"""
import os
import math
import io
import datetime

from pyrevit import revit, DB, forms, script

__title__ = "Tạo cột\ntừ CAD"

doc = revit.doc
output = script.get_output()

MM = DB.UnitTypeId.Millimeters
TOL_JOIN_MM = 1.0       # sai số nối đầu mút line thành vòng kín
TOL_DUP_MM = 5.0        # khoảng cách coi là trùng cột
ANGLE_TOL = 1e-3        # sai số kiểm tra vuông góc / thẳng hàng (rad)
# [cần xác nhận] standards chưa quy định tên type cột; BIM Manager chốt rồi sửa tại đây
COLUMN_TYPE_NAME = u"{b}x{h}"

DRY_RUN = "Chạy thử (dry-run) – chỉ báo cáo"
APPLY = "Tạo cột trong mô hình"


def to_mm(value_ft):
    return DB.UnitUtils.ConvertFromInternalUnits(value_ft, MM)


def from_mm(value_mm):
    return DB.UnitUtils.ConvertToInternalUnits(value_mm, MM)


def flat(p):
    return DB.XYZ(p.X, p.Y, 0)


def same_point(a, b, tol):
    """So khoảng cách tuyệt đối. XYZ.IsAlmostEqualTo của Revit so tương đối theo độ lớn vector,
    ở toạ độ xa gốc (CAD link) ngưỡng 0.1 mm thành hàng trăm mm và gộp mất đỉnh."""
    return a.DistanceTo(b) <= tol


def get_name(element):
    return revit.query.get_name(element)


# ---------------------------------------------------------------- Kiểm tra an toàn

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
    mode = forms.CommandSwitchWindow.show([DRY_RUN, apply_label],
                                          message="Chế độ chạy (mặc định nên chạy thử trước):")
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


# ---------------------------------------------------------------- Đọc hình học CAD

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
    if geo is None:
        return iter([])
    return walk(geo)


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


def rect_from_loop(points):
    """Trả về (tâm, rộng theo trục X cục bộ, sâu, góc xoay) nếu vòng là hình chữ nhật."""
    pts = simplify_loop(points)
    if len(pts) != 4:
        return None
    edges = [pts[(i + 1) % 4].Subtract(pts[i]) for i in range(4)]
    for i in range(4):
        e1 = edges[i].Normalize()
        e2 = edges[(i + 1) % 4].Normalize()
        if abs(e1.DotProduct(e2)) > ANGLE_TOL:
            return None
    if abs(edges[0].GetLength() - edges[2].GetLength()) > from_mm(1.0):
        return None

    cx = sum(p.X for p in pts) / 4.0
    cy = sum(p.Y for p in pts) / 4.0
    width = edges[0].GetLength()
    depth = edges[1].GetLength()
    angle = math.atan2(edges[0].Y, edges[0].X)

    # Đưa góc về [-45°, 45°); mỗi lần xoay 90° thì đổi chỗ b và h
    while angle >= math.pi / 4:
        angle -= math.pi / 2
        width, depth = depth, width
    while angle < -math.pi / 4:
        angle += math.pi / 2
        width, depth = depth, width
    if abs(angle) < 1e-6:
        angle = 0.0
    return DB.XYZ(cx, cy, 0), width, depth, angle


def loops_from_lines(lines):
    """Nối các line rời thành các vòng khép kín."""
    step = from_mm(TOL_JOIN_MM)

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


def collect_columns(cad, layers):
    """Đọc các hình chữ nhật trên layer đã chọn. Trả về (danh sách cột, số hình bỏ qua)."""
    polylines, lines = [], []
    skipped = {"circle": 0, "not_rect": 0}
    for obj in iter_cad_objects(cad):
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, DB.PolyLine):
            polylines.append(list(obj.GetCoordinates()))
        elif isinstance(obj, DB.Line):
            lines.append(obj)
        elif isinstance(obj, DB.Arc) and not obj.IsBound:
            skipped["circle"] += 1

    rects = []
    for loop in polylines + loops_from_lines(lines):
        rect = rect_from_loop(loop)
        if rect is None:
            skipped["not_rect"] += 1
        else:
            rects.append(rect)

    # Bỏ hình trùng tâm và trùng kích thước (vẽ chồng, hoặc viền trong/ngoài)
    tol = from_mm(TOL_DUP_MM)
    unique = []
    for r in rects:
        if not any(same_point(r[0], u[0], tol)
                   and abs(r[1] - u[1]) < tol and abs(r[2] - u[2]) < tol for u in unique):
            unique.append(r)
    return unique, skipped


# ---------------------------------------------------------------- Chọn đầu vào

if is_central_file(doc):
    forms.alert(u"File đang mở là file CENTRAL. Không được sửa trực tiếp file central.\n"
                u"Hãy mở file local hoặc bản detached/copy rồi chạy lại.", exitscript=True)
require_role(doc, "S", u"Kết cấu")

cads =DB.FilteredElementCollector(doc).OfClass(DB.ImportInstance).ToElements()
if not cads:
    forms.alert("Không tìm thấy file CAD (link hoặc import) nào trong mô hình.", exitscript=True)

cad_options = {}
for c in cads:
    label = "{} [Id {}]".format(get_name(doc.GetElement(c.GetTypeId())), c.Id.Value)
    cad_options[label] = c
cad_label = forms.SelectFromList.show(sorted(cad_options), title="Chọn file CAD mặt bằng định vị cột",
                                      button_name="Chọn")
if not cad_label:
    script.exit()
cad = cad_options[cad_label]

all_layers = sorted(set(l for l in (layer_of(o) for o in iter_cad_objects(cad)) if l))
if not all_layers:
    forms.alert("File CAD đã chọn không có đối tượng hình học nào đọc được.", exitscript=True)
layers = forms.SelectFromList.show(all_layers, title="Chọn layer cột trong CAD",
                                   multiselect=True, button_name="Chọn")
if not layers:
    script.exit()

symbols = DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralColumns) \
    .WhereElementIsElementType().ToElements()
families = {}
for s in symbols:
    families.setdefault(s.Family.Name, s.Family)
if not families:
    forms.alert("Mô hình chưa load family cột kết cấu nào.", exitscript=True)
family_name = forms.SelectFromList.show(sorted(families), title="Chọn family cột (tiết diện chữ nhật)",
                                        button_name="Chọn")
if not family_name:
    script.exit()
family = families[family_name]
family_symbols = [doc.GetElement(i) for i in family.GetFamilySymbolIds()]

param_b = forms.ask_for_string(default="b", prompt="Tên parameter type cho cạnh theo trục X của family:",
                               title="Parameter kích thước")
param_h = forms.ask_for_string(default="h", prompt="Tên parameter type cho cạnh theo trục Y của family:",
                               title="Parameter kích thước")
if not param_b or not param_h:
    script.exit()
for pname in (param_b, param_h):
    found = family_symbols[0].GetParameters(pname)
    if len(found) != 1 or found[0].StorageType != DB.StorageType.Double or found[0].IsReadOnly:
        forms.alert("Family '{}' phải có đúng một parameter type '{}' kiểu chiều dài, sửa được.".format(
            family_name, pname), exitscript=True)

levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements(), key=lambda l: l.Elevation)
level_by_name = dict((l.Name, l) for l in levels)
base_name = forms.SelectFromList.show([l.Name for l in levels], title="Chọn level chân cột", button_name="Chọn")
if not base_name:
    script.exit()
base_level = level_by_name[base_name]
upper = [l.Name for l in levels if l.Elevation > base_level.Elevation]
if not upper:
    forms.alert("Không có level nào cao hơn '{}' để làm đỉnh cột.".format(base_name), exitscript=True)
top_name = forms.SelectFromList.show(upper, title="Chọn level đỉnh cột", button_name="Chọn")
if not top_name:
    script.exit()
top_level = level_by_name[top_name]

dry_run = ask_dry_run(APPLY)

# ---------------------------------------------------------------- Phân tích

columns, skipped = collect_columns(cad, set(layers))
if not columns:
    forms.alert("Không tìm thấy hình chữ nhật khép kín nào trên layer đã chọn.", exitscript=True)


def size_key(width, depth):
    return int(round(to_mm(width))), int(round(to_mm(depth)))


types_by_size = {}
type_names = set()
for s in family_symbols:
    type_names.add(get_name(s))
    pb, ph = s.LookupParameter(param_b), s.LookupParameter(param_h)
    if pb is not None and ph is not None:
        types_by_size.setdefault(size_key(pb.AsDouble(), ph.AsDouble()), s)

new_type_names = {}
for _, w, d, _ in columns:
    k = size_key(w, d)
    if k in types_by_size or k in new_type_names:
        continue
    name = COLUMN_TYPE_NAME.format(b=k[0], h=k[1])
    suffix = 1
    while name in type_names:
        name = COLUMN_TYPE_NAME.format(b=k[0], h=k[1]) + u"_{}".format(suffix)
        suffix += 1
    type_names.add(name)
    new_type_names[k] = name

existing_points = []
for col in DB.FilteredElementCollector(doc).OfCategory(DB.BuiltInCategory.OST_StructuralColumns) \
        .WhereElementIsNotElementType():
    if col.LevelId == base_level.Id and isinstance(col.Location, DB.LocationPoint):
        existing_points.append(flat(col.Location.Point))

dup_tol = from_mm(TOL_DUP_MM)
log_rows = []
to_create = []
for center, w, d, angle in columns:
    k = size_key(w, d)
    type_name = get_name(types_by_size[k]) if k in types_by_size else new_type_names[k] + " (mới)"
    row = [to_mm(center.X), to_mm(center.Y), k[0], k[1], math.degrees(angle), type_name]
    if any(same_point(center, p, dup_tol) for p in existing_points):
        log_rows.append(row + ["Bỏ qua – đã có cột", ""])
    else:
        to_create.append((center, k, angle, row))

# ---------------------------------------------------------------- Ghi vào mô hình

if not dry_run and to_create:
    try:
        with revit.Transaction("ARV - Tạo cột kết cấu từ CAD"):
            template = family_symbols[0]
            for k, name in new_type_names.items():
                new_sym = template.Duplicate(name)
                size_param(new_sym, param_b).Set(from_mm(k[0]))
                size_param(new_sym, param_h).Set(from_mm(k[1]))
                types_by_size[k] = new_sym

            for center, k, angle, row in to_create:
                sym = types_by_size[k]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                inst = doc.Create.NewFamilyInstance(center, sym, base_level, DB.Structure.StructuralType.Column)
                inst.get_Parameter(DB.BuiltInParameter.FAMILY_BASE_LEVEL_OFFSET_PARAM).Set(0.0)
                inst.get_Parameter(DB.BuiltInParameter.FAMILY_TOP_LEVEL_PARAM).Set(top_level.Id)
                inst.get_Parameter(DB.BuiltInParameter.FAMILY_TOP_LEVEL_OFFSET_PARAM).Set(0.0)
                if angle:
                    axis = DB.Line.CreateBound(center, center.Add(DB.XYZ.BasisZ))
                    DB.ElementTransformUtils.RotateElement(doc, inst.Id, axis, angle)
                log_rows.append(row + ["Đã tạo", str(inst.Id.Value)])
    except Exception as err:
        forms.alert("Lỗi khi tạo cột, đã hoàn tác toàn bộ thay đổi.\n\nChi tiết: {}".format(err), exitscript=True)
else:
    for _, _, _, row in to_create:
        log_rows.append(row + ["Sẽ tạo (dry-run)" if dry_run else "", ""])

# ---------------------------------------------------------------- Báo cáo

now = datetime.datetime.now()
output.print_md("## Tạo cột kết cấu từ CAD – {}".format("CHẠY THỬ (không ghi mô hình)" if dry_run else "ĐÃ GHI MÔ HÌNH"))
output.print_md("- Mô hình: **{}**\n- File CAD: **{}** – layer: {}\n- Family: **{}** ({} / {})\n"
                "- Level: **{}** → **{}**\n- Hình bỏ qua: {} hình tròn, {} hình không phải chữ nhật\n"
                "- Type mới: {}".format(doc.Title, cad_label, ", ".join(layers), family_name, param_b, param_h,
                                        base_name, top_name, skipped["circle"], skipped["not_rect"],
                                        ", ".join(sorted(new_type_names.values())) or "không có"))

headers = ["X (mm)", "Y (mm)", "b (mm)", "h (mm)", "Góc (°)", "Type", "Trạng thái", "ElementId"]
table = [["{:.0f}".format(r[0]), "{:.0f}".format(r[1]), r[2], r[3], "{:.2f}".format(r[4])] + r[5:]
         for r in log_rows]
output.print_table(table_data=table, columns=headers)

log_dir = os.path.join(os.path.expanduser("~"), "Documents", "ARV_logs")
if not os.path.isdir(log_dir):
    os.makedirs(log_dir)
log_path = os.path.join(log_dir, "TaoCotTuCAD_{}.csv".format(now.strftime("%Y%m%d_%H%M%S")))
with io.open(log_path, "w", encoding="utf-8-sig") as f:
    f.write(u"Mô hình,{}\nFile CAD,{}\nNgày,{}\nChế độ,{}\nĐơn vị,mm / độ\n\n".format(
        doc.Title, cad_label, now.strftime("%Y-%m-%d %H:%M"), "dry-run" if dry_run else "ghi mô hình"))
    f.write(u",".join(headers) + u"\n")
    for r in table:
        f.write(u",".join(u'"{}"'.format(v) for v in r) + u"\n")
output.print_md("Log đã lưu: `{}`".format(log_path))
