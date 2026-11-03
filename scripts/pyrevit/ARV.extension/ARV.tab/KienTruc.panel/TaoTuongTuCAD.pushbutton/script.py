# -*- coding: utf-8 -*-
# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-29)
"""Tạo tường kiến trúc từ mặt bằng tường xây (DWG đã Link/Import vào Revit).

Quy trình:
  1. Chọn bản CAD và các layer tường (chỉ chọn layer tường xây/tường kiến trúc,
     không chọn layer vách bê tông kết cấu hay hatch).
  2. Đọc mọi đoạn thẳng (line, polyline, kể cả trong block).
  3. Ghép cặp hai đường song song có khoảng cách nằm trong dải chiều dày cho phép
     → một đoạn tường theo đường tim. Ưu tiên cặp gần nhau nhất.
  4. Gộp các đoạn tường thẳng hàng, cùng chiều dày, bị ngắt tại chỗ giao tường (chữ T, chữ +)
     hoặc tại lỗ cửa nếu người dùng cho phép nối qua lỗ cửa.
  5. Kéo dài đầu tường tới tim tường vuông góc để nối góc chữ L và chữ T.
  6. Mỗi chiều dày tìm được → người dùng chọn wall type có sẵn (hoặc bỏ qua).
  7. Mặc định chạy thử (dry-run): chỉ báo cáo, không ghi vào mô hình.

Ghi chú:
  - Không chạy trên file central. Chạy thử trên file copy trước khi dùng cho dự án.
  - Tường cong (arc) bị bỏ qua, ghi số lượng vào báo cáo.
  - Công cụ không tự tạo wall type mới (quy ước tên type tường chưa chốt trong standards).
    Tạo type theo chuẩn trước rồi chạy lại.
"""

import os
import io
import math
import datetime

from pyrevit import revit, DB, forms, script

__title__ = "Tạo tường\ntừ CAD"
__author__ = "Archivina BIM"

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# --- Cấu hình ---------------------------------------------------------------------
JOIN_TOL_MM = 1.0          # Sai số toạ độ / thẳng hàng
THICK_TOL_MM = 2.0         # Gộp chiều dày lệch nhỏ (ví dụ 109/110/111 → 110)
DUP_TOL_MM = 10.0          # Khoảng cách tim coi là trùng tường đã có
MIN_LENGTH_MM = 50.0       # Bỏ đoạn tường ngắn hơn giá trị này
ANGLE_TOL = 1e-3           # Sai số song song (rad)
DEFAULT_THICK_RANGE = u"80-350"
LAYER_HINTS = ("TUONG", "WALL", "XAY")
SKIP_LABEL = u"[Bỏ qua – không tạo tường có chiều dày này]"

TRANSACTION_NAME = u"ARV - Tạo tường kiến trúc từ CAD"
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


def get_name(element):
    return revit.query.get_name(element)


def fmt_xy(p):
    return u"({:.0f}, {:.0f})".format(to_mm(p.X), to_mm(p.Y))


def cross2d(a, b):
    return a.X * b.Y - a.Y * b.X


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
    # Trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-A-0001
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


def read_segments(cad, layers):
    """Trả về (danh sách đoạn thẳng (a, b) đã chiếu về Z=0, số cung tròn bỏ qua)."""
    tol = from_mm(JOIN_TOL_MM)
    segs, arcs = [], 0
    for obj in iter_cad_objects(cad):
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, DB.Line):
            pts = [obj.GetEndPoint(0), obj.GetEndPoint(1)]
        elif isinstance(obj, DB.PolyLine):
            pts = list(obj.GetCoordinates())
        elif isinstance(obj, DB.Arc):
            arcs += 1
            continue
        else:
            continue
        for a, b in zip(pts[:-1], pts[1:]):
            a, b = flat(a), flat(b)
            if a.DistanceTo(b) > tol:
                segs.append((a, b))
    return segs, arcs


# --- Ghép cặp đường song song -----------------------------------------------------
class Seg(object):
    """Đoạn CAD trong hệ toạ độ của nhóm song song: off = khoảng cách pháp tuyến, [s0, s1] = hình chiếu."""

    def __init__(self, a, b, u, n):
        self.off = (a.DotProduct(n) + b.DotProduct(n)) / 2.0
        sa, sb = a.DotProduct(u), b.DotProduct(u)
        self.s0, self.s1 = min(sa, sb), max(sa, sb)
        self.free = [(self.s0, self.s1)]   # Phần chưa được dùng làm mặt tường


class WallPiece(object):
    def __init__(self, u, n, off, s0, s1, thick):
        self.u, self.n, self.off = u, n, off
        self.s0, self.s1 = s0, s1
        self.thick = thick        # feet, đo từ CAD
        self.t = None             # mm, sau khi gộp chiều dày

    def point(self, s):
        return self.u.Multiply(s).Add(self.n.Multiply(self.off))


def canonical(a, b):
    """Hướng chuẩn hoá về góc [-tol, π - tol) để hai đường ngược chiều vẫn cùng nhóm."""
    u = b.Subtract(a).Normalize()
    ang = math.atan2(u.Y, u.X)
    if ang < -ANGLE_TOL:
        ang += math.pi
        u = u.Negate()
    if ang >= math.pi - ANGLE_TOL:
        ang -= math.pi
        u = u.Negate()
    return u, ang


def parallel_groups(segs):
    data = []
    for a, b in segs:
        u, ang = canonical(a, b)
        data.append((ang, u, a, b))
    data.sort(key=lambda d: d[0])
    groups, current = [], []
    for d in data:
        if current and d[0] - current[-1][0] > ANGLE_TOL:
            groups.append(current)
            current = []
        current.append(d)
    if current:
        groups.append(current)
    return groups


def clip(free, a, b):
    return [(max(x, a), min(y, b)) for x, y in free if min(y, b) > max(x, a)]


def intersect(f1, f2):
    result = []
    for x, y in f1:
        result.extend(clip(f2, x, y))
    return result


def subtract(free, a, b):
    out = []
    for x, y in free:
        if y <= a or x >= b:
            out.append((x, y))
            continue
        if x < a:
            out.append((x, a))
        if y > b:
            out.append((b, y))
    return out


def pair_group(group, tmin, tmax):
    """Ghép cặp các đường trong một nhóm song song, ưu tiên cặp gần nhau nhất."""
    u = group[0][1]
    n = DB.XYZ(-u.Y, u.X, 0)
    tol = from_mm(JOIN_TOL_MM)
    min_len = from_mm(MIN_LENGTH_MM)
    segs = sorted([Seg(a, b, u, n) for _, _, a, b in group], key=lambda s: s.off)

    cands = []
    for i in range(len(segs)):
        si = segs[i]
        for j in range(i + 1, len(segs)):
            sj = segs[j]
            d = sj.off - si.off
            if d > tmax + tol:
                break
            if d < tmin - tol:
                continue
            a, b = max(si.s0, sj.s0), min(si.s1, sj.s1)
            if b - a >= min_len:
                cands.append((d, b - a, si, sj, a, b))

    # Gần nhất trước; cùng khoảng cách thì ưu tiên đoạn chồng dài hơn (hai mặt tường thường bằng nhau)
    cands.sort(key=lambda c: (round(to_mm(c[0]), 1), -c[1]))
    pieces = []
    for d, _, si, sj, a, b in cands:
        for x, y in intersect(clip(si.free, a, b), sj.free):
            if y - x < min_len:
                continue
            si.free = subtract(si.free, x, y)
            sj.free = subtract(sj.free, x, y)
            pieces.append(WallPiece(u, n, (si.off + sj.off) / 2.0, x, y, d))
    return pieces


def snap_thicknesses(pieces):
    """Gộp chiều dày lệch nhỏ về giá trị xuất hiện nhiều nhất trong cụm."""
    counts = {}
    for p in pieces:
        k = int(round(to_mm(p.thick)))
        counts[k] = counts.get(k, 0) + 1
    mapping, cluster = {}, []

    def close(cl):
        rep = max(cl, key=lambda k: counts[k])
        for k in cl:
            mapping[k] = rep

    for k in sorted(counts):
        if cluster and k - cluster[-1] > THICK_TOL_MM:
            close(cluster)
            cluster = []
        cluster.append(k)
    if cluster:
        close(cluster)
    for p in pieces:
        p.t = mapping[int(round(to_mm(p.thick)))]


def merge_collinear(pieces, max_gap):
    """Gộp các đoạn thẳng hàng, cùng chiều dày, cách nhau ≤ max_gap (feet)."""
    off_tol = from_mm(THICK_TOL_MM)
    # Các đoạn trong cùng nhóm song song dùng chung một vector u
    pieces = sorted(pieces, key=lambda p: (id(p.u), p.t, p.off))
    lines, current = [], []
    for p in pieces:
        if current and (p.u is not current[-1].u or p.t != current[-1].t
                        or p.off - current[-1].off > off_tol):
            lines.append(current)
            current = []
        current.append(p)
    if current:
        lines.append(current)

    merged = []
    for line in lines:
        line.sort(key=lambda p: p.s0)
        cur = line[0]
        for p in line[1:]:
            if p.s0 - cur.s1 <= max_gap:
                cur.s1 = max(cur.s1, p.s1)
            else:
                merged.append(cur)
                cur = p
        merged.append(cur)
    return merged


def extend_to_junctions(pieces):
    """Kéo dài đầu tường tới tim tường không song song gần nhất (nối góc L và chữ T)."""
    tol = from_mm(JOIN_TOL_MM)
    new_ends = []
    for w in pieces:
        ends = [w.s0, w.s1]
        for k, sign in ((0, -1.0), (1, 1.0)):
            e = w.point(ends[k])
            v = w.u.Multiply(sign)
            best = None
            for o in pieces:
                if o is w:
                    continue
                sin = abs(cross2d(w.u, o.u))
                if sin < ANGLE_TOL:
                    continue
                denom = v.DotProduct(o.n)
                if abs(denom) < ANGLE_TOL:
                    continue
                t = (o.off - e.DotProduct(o.n)) / denom
                if t <= tol or t > o.thick / 2.0 / sin + tol:
                    continue
                s = e.Add(v.Multiply(t)).DotProduct(o.u)
                reach = w.thick / 2.0 / sin + tol
                if s < o.s0 - reach or s > o.s1 + reach:
                    continue
                if best is None or t < best:
                    best = t
            if best is not None:
                ends[k] += sign * best
        new_ends.append(ends)
    for w, (a, b) in zip(pieces, new_ends):
        w.s0, w.s1 = a, b


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
    choice = forms.SelectFromList.show(sorted(options.keys()), title=u"Chọn bản CAD mặt bằng tường",
                                       button_name=u"Chọn")
    if not choice:
        script.exit()
    return options[choice], choice


def pick_level(levels, title):
    name = forms.SelectFromList.show([l.Name for l in levels], title=title, button_name=u"Chọn")
    if not name:
        script.exit()
    return [l for l in levels if l.Name == name][0]


def ask_number(title, prompt, default):
    text = forms.ask_for_string(default=default, title=title, prompt=prompt)
    try:
        return float(text)
    except (TypeError, ValueError):
        script.exit()


def ask_thickness_range():
    text = forms.ask_for_string(default=DEFAULT_THICK_RANGE, title=u"Dải chiều dày tường",
                                prompt=u"Chiều dày tường nhỏ nhất - lớn nhất (mm), ví dụ 80-350:")
    try:
        lo, hi = [float(x) for x in (text or "").replace(" ", "").split("-")]
    except ValueError:
        forms.alert(u"Sai định dạng. Nhập dạng <nhỏ nhất>-<lớn nhất>, ví dụ 80-350.", exitscript=True)
    if lo <= 0 or hi < lo:
        forms.alert(u"Dải chiều dày không hợp lệ.", exitscript=True)
    return lo, hi


def ask_wall_types(counts):
    """Với mỗi chiều dày, người dùng chọn wall type có sẵn hoặc bỏ qua. Trả về {t: WallType | None}."""
    types = [t for t in DB.FilteredElementCollector(doc).OfClass(DB.WallType).ToElements()
             if t.Kind == DB.WallKind.Basic]
    if not types:
        forms.alert(u"Mô hình không có wall type dạng Basic nào.", exitscript=True)
    mapping = {}
    for t in sorted(counts):
        labels, match, other = {}, [], []
        for wt in types:
            w = int(round(to_mm(wt.Width)))
            label = u"{}  (dày {} mm)".format(get_name(wt), w)
            labels[label] = wt
            (match if abs(w - t) <= THICK_TOL_MM else other).append(label)
        choices = sorted(match) + [SKIP_LABEL] + sorted(other)
        choice = forms.SelectFromList.show(
            choices, title=u"Tường dày {} mm ({} đoạn) – chọn wall type".format(t, counts[t]),
            button_name=u"Chọn")
        if not choice:
            script.exit()
        mapping[t] = labels.get(choice)
    return mapping


def existing_wall_lines(level):
    result = []
    for wl in DB.FilteredElementCollector(doc).OfClass(DB.Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, DB.LocationCurve) and isinstance(loc.Curve, DB.Line):
            c = loc.Curve
            result.append((flat(c.GetEndPoint(0)), flat(c.GetEndPoint(1))))
    return result


def overlaps_existing(p0, p1, existing):
    """Tường mới trùng tim và chồng ≥ 50% chiều dài lên một tường đã có."""
    dup_tol = from_mm(DUP_TOL_MM)
    for a, b in existing:
        d = b.Subtract(a)
        length = d.GetLength()
        if length < dup_tol:
            continue
        ue = d.Divide(length)
        if abs(cross2d(ue, p1.Subtract(p0).Normalize())) > ANGLE_TOL:
            continue
        ne = DB.XYZ(-ue.Y, ue.X, 0)
        if abs(p0.Subtract(a).DotProduct(ne)) > dup_tol:
            continue
        s_a, s_b = sorted([p0.Subtract(a).DotProduct(ue), p1.Subtract(a).DotProduct(ue)])
        if min(s_b, length) - max(s_a, 0.0) > 0.5 * (s_b - s_a):
            return True
    return False


# --- Log ----------------------------------------------------------------------------
LOG_HEADER = [u"STT", u"Điểm đầu (mm)", u"Điểm cuối (mm)", u"Dày CAD (mm)", u"Dài (mm)", u"Wall type",
              u"Kết quả", u"ElementId", u"Giá trị cũ", u"Giá trị mới"]


def write_log(rows, dry_run, cad_label):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoTuongTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
    with io.open(path, "w", encoding="utf-8-sig") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(cad_label))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        f.write(u",".join(LOG_HEADER) + u"\n")
        for r in rows:
            f.write(u",".join(u'"{}"'.format(u"{}".format(v).replace(u'"', u'""')) for v in r) + u"\n")
    return path


# --- Chương trình chính -----------------------------------------------------------
def main():
    if is_central_file(doc):
        forms.alert(u"File đang mở là file CENTRAL. Không được sửa trực tiếp file central.\n"
                    u"Hãy mở file local hoặc bản detached/copy rồi chạy lại.", exitscript=True)
    require_role(doc, "A", u"Kiến trúc")

    cad, cad_label = pick_cad_instance()
    all_layers = sorted(set(l for l in (layer_of(o) for o in iter_cad_objects(cad)) if l))
    if not all_layers:
        forms.alert(u"Không đọc được hình học của bản CAD.", exitscript=True)
    hinted = [l for l in all_layers if any(h in l.upper() for h in LAYER_HINTS)]
    layers = forms.SelectFromList.show(
        all_layers, title=u"Chọn layer tường kiến trúc (gợi ý: {})".format(u", ".join(hinted) or u"không có"),
        multiselect=True, button_name=u"Chọn layer")
    if not layers:
        script.exit()

    tmin_mm, tmax_mm = ask_thickness_range()
    bridge_mm = ask_number(u"Nối tường qua lỗ cửa",
                           u"Nối hai đoạn tường thẳng hàng, cùng chiều dày nếu khoảng hở ≤ (mm).\n"
                           u"Nhập 0 để không nối qua lỗ cửa (khi đó cửa phải đặt lại tường tay):", u"0")

    # Phân tích hình học
    segs, arcs = read_segments(cad, set(layers))
    pieces = []
    for group in parallel_groups(segs):
        pieces.extend(pair_group(group, from_mm(tmin_mm), from_mm(tmax_mm)))
    if not pieces:
        forms.alert(u"Không tìm thấy cặp đường song song nào có khoảng cách {:.0f}–{:.0f} mm trên layer đã chọn."
                    .format(tmin_mm, tmax_mm), exitscript=True)
    snap_thicknesses(pieces)
    # Luôn nối qua chỗ giao tường (khe ≤ chiều dày lớn nhất); nối qua lỗ cửa theo lựa chọn
    pieces = merge_collinear(pieces, from_mm(max(tmax_mm, bridge_mm) + JOIN_TOL_MM))
    extend_to_junctions(pieces)

    counts = {}
    for p in pieces:
        counts[p.t] = counts.get(p.t, 0) + 1
    type_map = ask_wall_types(counts)

    levels = sorted(DB.FilteredElementCollector(doc).OfClass(DB.Level).ToElements(), key=lambda l: l.Elevation)
    base_level = pick_level(levels, u"Chọn level chân tường")
    upper = [l for l in levels if l.Elevation > base_level.Elevation]
    if not upper:
        forms.alert(u"Không có level nào cao hơn '{}'.".format(base_level.Name), exitscript=True)
    top_level = pick_level(upper, u"Chọn level đỉnh tường")
    top_offset_mm = ask_number(u"Offset đỉnh tường",
                               u"Top Offset so với level đỉnh (mm), ví dụ -120 nếu xây tới đáy sàn dày 120:", u"0")
    top_offset = from_mm(top_offset_mm)
    height = top_level.Elevation + top_offset - base_level.Elevation
    if height <= 0:
        forms.alert(u"Chiều cao tường ≤ 0, kiểm tra lại level và offset.", exitscript=True)

    dry_run = ask_dry_run(u"Tạo tường vào mô hình")

    # --- Lập kế hoạch
    z = base_level.Elevation
    existing = existing_wall_lines(base_level)
    rows, jobs = [], []
    pieces.sort(key=lambda p: (p.t, round(p.point(p.s0).Y, 3), round(p.point(p.s0).X, 3)))
    for idx, p in enumerate(pieces, 1):
        p0, p1 = p.point(p.s0), p.point(p.s1)
        wtype = type_map.get(p.t)
        type_name = get_name(wtype) if wtype else u"—"
        row = [idx, fmt_xy(p0), fmt_xy(p1), p.t, u"{:.0f}".format(to_mm(p.s1 - p.s0)), type_name,
               u"", u"", u"—", type_name]
        if wtype is None:
            row[6] = u"Bỏ qua – không chọn wall type"
        elif overlaps_existing(p0, p1, existing):
            row[6] = u"Bỏ qua – đã có tường"
        else:
            note = u""
            w = int(round(to_mm(wtype.Width)))
            if abs(w - p.t) > THICK_TOL_MM:
                note = u" (type dày {} mm ≠ CAD {} mm)".format(w, p.t)
            row[6] = (u"Sẽ tạo" if dry_run else u"Chờ tạo") + note
            jobs.append((DB.XYZ(p0.X, p0.Y, z), DB.XYZ(p1.X, p1.Y, z), wtype, len(rows)))
        rows.append(row)

    # --- Ghi vào mô hình
    if not dry_run and jobs:
        try:
            with revit.Transaction(TRANSACTION_NAME, doc=doc):
                for p0, p1, wtype, row_idx in jobs:
                    wall = DB.Wall.Create(doc, DB.Line.CreateBound(p0, p1), wtype.Id, base_level.Id,
                                          height, 0.0, False, False)
                    wall.get_Parameter(DB.BuiltInParameter.WALL_BASE_OFFSET).Set(0.0)
                    wall.get_Parameter(DB.BuiltInParameter.WALL_HEIGHT_TYPE).Set(top_level.Id)
                    wall.get_Parameter(DB.BuiltInParameter.WALL_TOP_OFFSET).Set(top_offset)
                    rows[row_idx][6] = rows[row_idx][6].replace(u"Chờ tạo", u"Đã tạo")
                    rows[row_idx][7] = id_value(wall.Id)
        except Exception as ex:
            # revit.Transaction tự RollBack khi có lỗi
            forms.alert(u"Lỗi khi tạo tường, mọi thay đổi đã được hoàn tác.\n\n{}".format(ex), exitscript=True)

    # --- Báo cáo
    summary = u", ".join(u"{} mm → {} ({} đoạn)".format(t, get_name(type_map[t]) if type_map[t] else u"bỏ qua",
                                                        counts[t]) for t in sorted(counts))
    output.print_md(u"## {} – {}".format(TRANSACTION_NAME,
                                          u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN"))
    output.print_md(
        u"- Mô hình: **{}**\n- File CAD: **{}** – layer: {}\n- Level: **{}** → **{}** (Top Offset {:.0f} mm)\n"
        u"- Dải chiều dày: {:.0f}–{:.0f} mm – nối qua lỗ cửa ≤ {:.0f} mm\n"
        u"- Đoạn CAD đã đọc: {} – tường tìm được: {} – sẽ tạo: {}\n"
        u"- Bỏ qua: {} cung tròn (tường cong cần vẽ tay)\n- Chiều dày → type: {}".format(
            doc.Title, cad_label, u", ".join(layers), base_level.Name, top_level.Name, top_offset_mm,
            tmin_mm, tmax_mm, bridge_mm, len(segs), len(pieces), len(jobs), arcs, summary))
    output.print_table(table_data=rows, columns=LOG_HEADER)
    try:
        output.print_md(u"Log: `{}`".format(write_log(rows, dry_run, cad_label)))
    except Exception as ex:
        output.print_md(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        output.print_md(u"> Kiểm tra bảng trên. Nếu đúng, chạy lại và chọn **Tạo tường vào mô hình**.")


main()
