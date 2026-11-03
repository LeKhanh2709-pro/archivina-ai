# -*- coding: utf-8 -*-
# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-29)
"""Tạo lưới trục (Grid) từ bản vẽ AutoCAD đã Link/Import vào Revit.

Quy trình:
  1. Chọn bản CAD (ImportInstance) và layer chứa đường trục.
  2. Gộp các đoạn thẳng thẳng hàng thành một trục, bỏ đoạn ngắn và vòng tròn ký hiệu trục.
  3. Đặt tên theo file CSV tên trục xuất từ DWG (Ten, X1, Y1, X2, Y2 – mm, toạ độ CAD),
     hoặc tự động: trục đứng / trục ngang theo số hoặc chữ (người dùng chọn).
     Revit API không đọc được chữ trong CAD nên tên trên bản vẽ phải lấy qua file CSV.
  4. Mặc định chạy thử (dry-run): chỉ báo cáo, không ghi vào mô hình.

Ghi chú:
  - Level và Grid do bộ môn Kết cấu (S) làm chủ; mô hình Kiến trúc dùng Copy/Monitor.
  - Không chạy trên file central. Chạy thử trên file copy trước khi dùng cho dự án.
"""

import os
import csv
import io
import math
import datetime

from pyrevit import revit, DB, forms, script

__title__ = "Tạo trục\ntừ CAD"
__author__ = "Archivina BIM"

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# --- Cấu hình (mm) ------------------------------------------------------------
MIN_LENGTH_MM = 1000.0      # Bỏ các đoạn ngắn hơn giá trị này (nét ký hiệu, nét gạch)
MIN_ARC_RADIUS_MM = 5000.0  # Bỏ cung tròn bán kính nhỏ (vòng tròn ký hiệu trục)
COLLINEAR_TOL_MM = 1.0      # Sai số khoảng cách để coi hai đoạn là cùng một trục
ANGLE_TOL_RAD = 1e-4        # Sai số góc để coi hai đoạn là song song
CSV_MATCH_TOL_MM = 5.0      # Sai số khi khớp trục với toạ độ trong file CSV tên trục
LAYER_HINTS = ("AXIS", "TRUC", "GRID", "TRỤC")
LETTERS = [c for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if c not in ("I", "O")]

TRANSACTION_NAME = "ARV - Tạo lưới trục từ CAD"


# --- Tiện ích đơn vị -----------------------------------------------------------
def to_mm(feet):
    return DB.UnitUtils.ConvertFromInternalUnits(feet, DB.UnitTypeId.Millimeters)


def from_mm(mm):
    return DB.UnitUtils.ConvertToInternalUnits(mm, DB.UnitTypeId.Millimeters)


def id_value(element_id):
    # Revit 2024+ dùng ElementId.Value; IntegerValue đã bị loại bỏ ở bản mới
    value = getattr(element_id, "Value", None)
    return value if value is not None else element_id.IntegerValue


def fmt_xy(pt):
    return "({:.0f}, {:.0f})".format(to_mm(pt.X), to_mm(pt.Y))


# --- Kiểm tra an toàn -------------------------------------------------------
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
    # Lấy trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-A-0001
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


def require_no_grids(document):
    """Chỉ tạo trục khi khởi tạo mô hình KC chưa có lưới trục (CLAUDE.md mục 4, 7)."""
    count = DB.FilteredElementCollector(document).OfClass(DB.Grid).GetElementCount()
    if count > 0:
        forms.alert(u"Mô hình đã có {} trục. Công cụ chỉ dùng khi khởi tạo mô hình Kết cấu chưa có "
                    u"lưới trục; không thêm hay sửa vào lưới trục đã có.".format(count), exitscript=True)
    if not forms.alert(u"Tạo lưới trục chỉ dùng khi khởi tạo mô hình Kết cấu và phải được BIM Manager duyệt.\n\n"
                       u"BIM Manager đã duyệt việc tạo lưới trục cho mô hình này?", yes=True, no=True):
        script.exit()


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


# --- Đọc hình học CAD -------------------------------------------------------
def layer_name(geom_obj):
    style = doc.GetElement(geom_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return None


def iter_cad_curves(geom_elem):
    """Duyệt toàn bộ curve (kể cả trong block lồng nhau), trả về (layer, curve)."""
    for g in geom_elem:
        if isinstance(g, DB.GeometryInstance):
            for item in iter_cad_curves(g.GetInstanceGeometry()):
                yield item
        elif isinstance(g, DB.PolyLine):
            name = layer_name(g)
            pts = list(g.GetCoordinates())
            for p0, p1 in zip(pts[:-1], pts[1:]):
                if p0.DistanceTo(p1) > 1e-6:
                    yield name, DB.Line.CreateBound(p0, p1)
        elif isinstance(g, (DB.Line, DB.Arc)):
            yield layer_name(g), g


def flatten(pt):
    return DB.XYZ(pt.X, pt.Y, 0)


# --- Gộp đoạn thẳng hàng ------------------------------------------------------
class AxisLine(object):
    def __init__(self, direction, offset, t_min, t_max):
        self.direction = direction  # vector đơn vị, đã chuẩn hoá chiều
        self.offset = offset        # khoảng cách có dấu tới gốc theo pháp tuyến
        self.t_min = t_min
        self.t_max = t_max
        self.source_count = 1

    @property
    def normal(self):
        return DB.XYZ(-self.direction.Y, self.direction.X, 0)

    def point_at(self, t):
        return self.normal.Multiply(self.offset).Add(self.direction.Multiply(t))

    @property
    def start(self):
        return self.point_at(self.t_min)

    @property
    def end(self):
        return self.point_at(self.t_max)

    @property
    def mid(self):
        return self.point_at((self.t_min + self.t_max) / 2.0)

    @property
    def is_vertical(self):
        return abs(self.direction.Y) > abs(self.direction.X)

    @property
    def angle_deg(self):
        return math.degrees(math.atan2(self.direction.Y, self.direction.X))

    def to_curve(self):
        return DB.Line.CreateBound(self.start, self.end)


def canonical_direction(p0, p1):
    d = p1.Subtract(p0).Normalize()
    # Chuẩn hoá chiều để hai đoạn ngược chiều vẫn được coi là cùng phương
    if d.X < -1e-9 or (abs(d.X) <= 1e-9 and d.Y < 0):
        d = d.Negate()
    return d


def merge_lines(lines, dist_tol):
    axes = []
    for line in lines:
        p0 = flatten(line.GetEndPoint(0))
        p1 = flatten(line.GetEndPoint(1))
        d = canonical_direction(p0, p1)
        n = DB.XYZ(-d.Y, d.X, 0)
        offset = p0.DotProduct(n)
        t0, t1 = sorted((p0.DotProduct(d), p1.DotProduct(d)))

        target = None
        for ax in axes:
            if abs(ax.direction.CrossProduct(d).Z) < ANGLE_TOL_RAD \
                    and abs(ax.offset - offset) < dist_tol:
                target = ax
                break
        if target is None:
            axes.append(AxisLine(d, offset, t0, t1))
        else:
            target.t_min = min(target.t_min, t0)
            target.t_max = max(target.t_max, t1)
            target.source_count += 1
    return axes


def dedupe_arcs(arcs, dist_tol):
    result = []
    for arc in arcs:
        c = flatten(arc.Center)
        ends = sorted([flatten(arc.GetEndPoint(0)), flatten(arc.GetEndPoint(1))],
                      key=lambda p: (round(p.X, 6), round(p.Y, 6)))
        duplicate = False
        for other in result:
            oc = flatten(other.Center)
            oends = sorted([flatten(other.GetEndPoint(0)), flatten(other.GetEndPoint(1))],
                           key=lambda p: (round(p.X, 6), round(p.Y, 6)))
            if c.DistanceTo(oc) < dist_tol and abs(arc.Radius - other.Radius) < dist_tol \
                    and ends[0].DistanceTo(oends[0]) < dist_tol \
                    and ends[1].DistanceTo(oends[1]) < dist_tol:
                duplicate = True
                break
        if not duplicate:
            result.append(arc)
    return result


def flat_arc(arc):
    return DB.Arc.Create(flatten(arc.GetEndPoint(0)),
                         flatten(arc.GetEndPoint(1)),
                         flatten(arc.Evaluate(0.5, True)))


# --- Đặt tên ----------------------------------------------------------------------
def letter_name(index):
    base = len(LETTERS)
    if index < base:
        return LETTERS[index]
    return LETTERS[index // base - 1] + LETTERS[index % base]


def number_name(index):
    return str(index + 1)


def load_name_csv(path, cad_transform):
    """Đọc file tên trục (Ten, X1, Y1, X2, Y2 – mm, toạ độ CAD), đổi sang toạ độ mô hình.

    Dòng bắt đầu bằng '#' là ghi chú. Trả về danh sách dict: name, direction, offset, note.
    """
    with io.open(path, "r", encoding="utf-8-sig") as f:
        content = [l for l in f.read().splitlines() if l.strip() and not l.lstrip().startswith(u"#")]
    entries = []
    for i, row in enumerate(csv.reader(content)):
        if i == 0 or len(row) < 5:
            continue  # dòng tiêu đề
        try:
            pts = [from_mm(float(v)) for v in row[1:5]]
        except ValueError:
            continue
        p0 = flatten(cad_transform.OfPoint(DB.XYZ(pts[0], pts[1], 0)))
        p1 = flatten(cad_transform.OfPoint(DB.XYZ(pts[2], pts[3], 0)))
        if p0.DistanceTo(p1) < 1e-6:
            continue
        d = canonical_direction(p0, p1)
        entries.append({
            "name": row[0].strip(),
            "direction": d,
            "offset": p0.DotProduct(DB.XYZ(-d.Y, d.X, 0)),
            "note": row[5].strip() if len(row) > 5 else u"",
            "used": False,
        })
    return entries


def find_csv_name(axis, entries, dist_tol):
    for e in entries:
        if abs(e["direction"].CrossProduct(axis.direction).Z) < ANGLE_TOL_RAD \
                and abs(e["offset"] - axis.offset) < dist_tol:
            e["used"] = True
            return e
    return None


# --- Lưới trục có sẵn --------------------------------------------------------
def existing_grids():
    grids = DB.FilteredElementCollector(doc).OfClass(DB.Grid).ToElements()
    lines = []
    names = set()
    for g in grids:
        names.add(g.Name)
        curve = g.Curve
        if isinstance(curve, DB.Line):
            p0, p1 = flatten(curve.GetEndPoint(0)), flatten(curve.GetEndPoint(1))
            d = canonical_direction(p0, p1)
            n = DB.XYZ(-d.Y, d.X, 0)
            lines.append((g, d, p0.DotProduct(n)))
    return lines, names


def find_matching_grid(axis, grid_lines, dist_tol):
    for g, d, offset in grid_lines:
        if abs(d.CrossProduct(axis.direction).Z) < ANGLE_TOL_RAD \
                and abs(offset - axis.offset) < dist_tol:
            return g
    return None


# --- Log ------------------------------------------------------------------------------
def write_log(rows, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoTrucTuCAD_{}_{}.csv".format(
        "DRYRUN" if dry_run else "THUCHIEN", stamp))
    header = [u"Tên trục", u"Loại", u"Điểm đầu (mm)", u"Điểm cuối (mm)",
              u"Số đoạn gộp", u"Kết quả", u"ElementId", u"Giá trị cũ", u"Giá trị mới"]
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
    with io.open(path, "w", encoding="utf-8-sig") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        f.write(u",".join(header) + u"\n")
        for r in rows:
            f.write(u",".join(u'"{}"'.format(u"{}".format(v).replace(u'"', u'""')) for v in r) + u"\n")
    return path


# --- Chương trình chính ----------------------------------------------------------
def pick_cad_instance():
    selected = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
    selected = [e for e in selected if isinstance(e, DB.ImportInstance)]
    if len(selected) == 1:
        return selected[0]

    instances = DB.FilteredElementCollector(doc).OfClass(DB.ImportInstance).ToElements()
    if not instances:
        forms.alert(u"Không tìm thấy bản CAD nào được Link/Import trong mô hình.", exitscript=True)

    options = {}
    for inst in instances:
        cad_type = doc.GetElement(inst.GetTypeId())
        param = cad_type.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_NAME) if cad_type else None
        type_name = param.AsString() if param else u"CAD"
        label = u"{} [{}] – Id {}".format(
            type_name, u"Link" if inst.IsLinked else u"Import", id_value(inst.Id))
        options[label] = inst
    choice = forms.SelectFromList.show(sorted(options.keys()),
                                       title=u"Chọn bản CAD chứa lưới trục",
                                       multiselect=False)
    if not choice:
        script.exit()
    return options[choice]


def main():
    if is_central_file(doc):
        forms.alert(u"File đang mở là file CENTRAL. Không được sửa trực tiếp file central.\n"
                    u"Hãy mở file local hoặc bản detached/copy rồi chạy lại.", exitscript=True)

    # Grid do Kết cấu (S) làm chủ, Kiến trúc dùng Copy/Monitor
    require_role(doc, "S", u"Kết cấu")
    require_no_grids(doc)

    cad = pick_cad_instance()
    geom = cad.get_Geometry(DB.Options())
    if geom is None:
        forms.alert(u"Không đọc được hình học của bản CAD.", exitscript=True)

    curves_by_layer = {}
    for name, curve in iter_cad_curves(geom):
        curves_by_layer.setdefault(name or u"(không có layer)", []).append(curve)
    if not curves_by_layer:
        forms.alert(u"Bản CAD không có đường thẳng hoặc cung tròn nào.", exitscript=True)

    layer_labels = sorted(curves_by_layer.keys())
    hinted = [l for l in layer_labels if any(h in l.upper() for h in LAYER_HINTS)]
    layers = forms.SelectFromList.show(
        layer_labels, title=u"Chọn layer trục (gợi ý: {})".format(u", ".join(hinted) or u"không có"),
        multiselect=True, button_name=u"Chọn layer")
    if not layers:
        script.exit()

    naming = forms.CommandSwitchWindow.show(
        [u"Theo file CSV tên trục (xuất từ DWG)",
         u"Trục đứng = số (1, 2, 3…), trục ngang = chữ (A, B, C…)",
         u"Trục đứng = chữ (A, B, C…), trục ngang = số (1, 2, 3…)"],
        message=u"Cách đặt tên trục (tự động: trái → phải, dưới → trên):")
    if not naming:
        script.exit()
    vertical_numbers = naming.startswith(u"Trục đứng = số")
    csv_entries = None
    if naming.startswith(u"Theo file CSV"):
        csv_path = forms.pick_file(file_ext="csv", title=u"Chọn file CSV tên trục")
        if not csv_path:
            script.exit()
        try:
            csv_entries = load_name_csv(csv_path, cad.GetTotalTransform())
        except Exception as ex:
            forms.alert(u"Không đọc được file CSV tên trục.\n\n{}".format(ex), exitscript=True)
        if not csv_entries:
            forms.alert(u"File CSV không có dòng tên trục hợp lệ (Ten, X1, Y1, X2, Y2).", exitscript=True)

    dry_run = ask_dry_run(u"Tạo lưới trục vào mô hình")

    # Lọc curve
    min_len = from_mm(MIN_LENGTH_MM)
    min_radius = from_mm(MIN_ARC_RADIUS_MM)
    tol = from_mm(COLLINEAR_TOL_MM)
    lines, arcs, skipped = [], [], 0
    for layer in layers:
        for c in curves_by_layer[layer]:
            if isinstance(c, DB.Line):
                if c.Length >= min_len:
                    lines.append(c)
                else:
                    skipped += 1
            elif isinstance(c, DB.Arc):
                if c.IsBound and c.Radius >= min_radius:
                    arcs.append(c)
                else:
                    skipped += 1

    axes = merge_lines(lines, tol)
    arcs = dedupe_arcs(arcs, tol)

    # Đặt tên: trục đứng sắp trái → phải, trục ngang sắp dưới → trên
    vertical = sorted([a for a in axes if a.is_vertical], key=lambda a: a.mid.X)
    horizontal = sorted([a for a in axes if not a.is_vertical], key=lambda a: a.mid.Y)
    plan = []
    if csv_entries is not None:
        csv_tol = from_mm(CSV_MATCH_TOL_MM)
        for kind, group in ((u"Trục đứng", vertical), (u"Trục ngang", horizontal)):
            for ax in group:
                entry = find_csv_name(ax, csv_entries, csv_tol)
                label = kind + (u" – " + entry["note"] if entry and entry["note"] else u"")
                plan.append((entry["name"] if entry else None, label, ax))
    else:
        for i, ax in enumerate(vertical):
            plan.append((number_name(i) if vertical_numbers else letter_name(i), u"Trục đứng", ax))
        for i, ax in enumerate(horizontal):
            plan.append((letter_name(i) if vertical_numbers else number_name(i), u"Trục ngang", ax))
    for i, arc in enumerate(sorted(arcs, key=lambda a: a.Radius)):
        plan.append((u"R{}".format(i + 1), u"Trục cong (cần kiểm tra tên)", arc))

    grid_lines, grid_names = existing_grids()

    rows = []
    to_create = []
    planned_names = set()
    for name, kind, item in plan:
        if isinstance(item, AxisLine):
            start, end, count = item.start, item.end, item.source_count
            match = find_matching_grid(item, grid_lines, tol)
        else:
            start, end, count, match = item.GetEndPoint(0), item.GetEndPoint(1), 1, None
        if name is None:
            name = u"?"
            result = u"Bỏ qua – không có tên trong file CSV"
            eid = u""
        elif name in planned_names:
            result = u"Bỏ qua – tên '{}' bị trùng với trục khác trong lần chạy này".format(name)
            eid = u""
        elif match is not None:
            result = u"Bỏ qua – trùng trục có sẵn '{}'".format(match.Name)
            eid = id_value(match.Id)
        elif name in grid_names:
            result = u"Bỏ qua – tên '{}' đã tồn tại ở vị trí khác".format(name)
            eid = u""
        else:
            result = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            eid = u""
            to_create.append((name, item, len(rows)))
            planned_names.add(name)
        rows.append([name, kind, fmt_xy(start), fmt_xy(end), count, result, eid, u"—", name])

    # Tên trong CSV không tìm thấy đường trục tương ứng trên layer đã chọn
    for e in (csv_entries or []):
        if not e["used"]:
            rows.append([e["name"], u"Trong CSV", u"", u"", 0,
                         u"Không có đường trục tương ứng trên layer đã chọn", u"", u"—", u"—"])

    if not dry_run and to_create:
        try:
            with revit.Transaction(TRANSACTION_NAME, doc=doc):
                for name, item, row_idx in to_create:
                    curve = item.to_curve() if isinstance(item, AxisLine) else flat_arc(item)
                    grid = DB.Grid.Create(doc, curve)
                    grid.Name = name
                    rows[row_idx][5] = u"Đã tạo"
                    rows[row_idx][6] = id_value(grid.Id)
        except Exception as ex:
            # revit.Transaction tự RollBack khi có lỗi
            forms.alert(u"Lỗi khi tạo lưới trục, mọi thay đổi đã được hoàn tác.\n\n{}".format(ex),
                        exitscript=True)

    # Báo cáo
    output.print_md(u"## {} – {}".format(TRANSACTION_NAME,
                                          u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN"))
    output.print_md(u"- Mô hình: **{}**\n- Layer: {}\n- Đoạn thẳng hợp lệ: {} → gộp thành {} trục"
                    u"\n- Cung tròn: {}\n- Bỏ qua (ngắn / vòng ký hiệu): {}".format(
                        doc.Title, u", ".join(layers), len(lines), len(axes), len(arcs), skipped))
    output.print_table(table_data=rows,
                       columns=[u"Tên", u"Loại", u"Điểm đầu (mm)", u"Điểm cuối (mm)", u"Số đoạn gộp",
                                u"Kết quả", u"ElementId", u"Giá trị cũ", u"Giá trị mới"])
    try:
        log_path = write_log(rows, dry_run)
        output.print_md(u"Log: `{}`".format(log_path))
    except Exception as ex:
        output.print_md(u"Không ghi được file log: {}".format(ex))

    if dry_run:
        output.print_md(u"> Kiểm tra bảng trên. Nếu đúng, chạy lại và chọn **Tạo lưới trục vào mô hình**.")


main()
