# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_CatTuongTheoDamSan_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Cập nhật chiều cao tường kiến trúc theo dầm / sàn phía trên, bỏ phần tường đè lên dầm, sàn:
#   1. Lấy các tường trên level chân (IN[0]) có tên type chứa chuỗi lọc (IN[1]).
#   2. Với mỗi tường: tìm sàn (Floors) và dầm (Structural Framing) có khối giao với khối tường.
#      Đáy phần giao = đáy dầm / sàn ngay trên tường.
#   3. Hạ đỉnh tường về đáy CAO NHẤT trong các dầm / sàn đó (thường là đáy sàn → tường kín tới sàn, không hở).
#      Giữ ràng buộc Top Constraint, chỉ đổi Top Offset (tường "Unconnected" thì đổi Unconnected Height).
#   4. Dầm / sàn thấp hơn đỉnh mới (dầm cắt ngang, sàn dày) → Join Geometry, dầm / sàn CẮT tường
#      (Switch Join Order nếu tường đang cắt) → phần tường đè lên bị bỏ, khối lượng tường đúng.
#      Dầm / sàn chỉ phủ một phần đỉnh tường (VD dầm vuông góc nằm trên đầu tường) → giữ đỉnh, chỉ cắt phần đè.
#   5. Dự phòng: Join không cắt được (còn giao sau khi Join) → bỏ Join đó, TÁCH tường tại mặt dầm/sàn: đoạn dưới
#      dầm lấy đỉnh = đáy dầm, đoạn còn lại giữ đỉnh (tường gốc giữ đoạn đầu, đoạn sau là tường mới cùng type/thông số).
#   6. Kiểm tra lại: đếm cặp tường – dầm/sàn còn đè sau khi cắt (gồm cả tường mới tách).
# Chạy lại an toàn: tường đã cắt không còn giao → không đổi gì thêm.
# INPUT
#   IN[0] (str)  Tên level chân tường (VD "Tầng 1")
#   IN[1] (str)  Lọc wall type theo chuỗi con, nhiều chuỗi cách nhau bằng ';' (VD "WB " – không lấy vách BTCT VBT-)
#   IN[2] (bool) Dry-run: True = chỉ báo cáo, không ghi vào mô hình (mặc định True)
# OUTPUT
#   OUT (list[str]) Báo cáo: tóm tắt, phân bố cao độ đỉnh mới, log, từng tường thay đổi

import os
import io
import csv
import datetime
import unicodedata

import clr
clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import (FilteredElementCollector, Options, ViewDetailLevel, GeometryInstance, Solid, Level,
                               Wall, BuiltInParameter, BuiltInCategory, ElementCategoryFilter, LogicalOrFilter,
                               BoundingBoxIntersectsFilter, Outline, BooleanOperationsUtils, BooleanOperationsType,
                               JoinGeometryUtils, Transaction, UnitUtils, UnitTypeId, ModelPathUtils, ElementId,
                               XYZ, Line, WallUtils)
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Cắt tường theo dầm sàn"
SCRIPT_TAG = u"ARV_CatTuongTheoDamSan_v1"
MIN_CLASH_FT3 = 1e-4       # Khối giao nhỏ hơn (~2,8 cm³) coi như chạm, không đè
TOL_MM = 1.0               # Sai số cao độ
MIN_HEIGHT_MM = 100.0      # Đỉnh mới thấp hơn chân + giá trị này → bỏ qua, báo kiểm tra
COVER_TOL_MM = 5.0         # Sai số khi xét dầm/sàn phủ kín chiều dài tường / ranh giới đoạn tách


def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


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


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name) == norm(name):
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def main_solid(element):
    """Khối lớn nhất của đối tượng (kể cả trong family instance)."""
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    best = None
    geo = element.get_Geometry(opt)
    if geo is None:
        return None
    for g in geo:
        items = g.GetInstanceGeometry() if isinstance(g, GeometryInstance) else [g]
        for s in items:
            if isinstance(s, Solid) and s.Volume > 1e-9 and (best is None or s.Volume > best.Volume):
                best = s
    return best


STRUCT_FILTER = None


def wall_axis(wall):
    """(điểm đầu, vector đơn vị, chiều dài) của đường định vị tường (ft)."""
    c = wall.Location.Curve
    p0, p1 = c.GetEndPoint(0), c.GetEndPoint(1)
    # CPython3 (pythonnet) không hỗ trợ toán tử +/- giữa XYZ → dùng Add/Subtract
    return p0, p1.Subtract(p0).Normalize(), c.Length


def along_range(solid, p0, u):
    """Khoảng [s0, s1] (ft) hình chiếu khối lên trục tường."""
    bb = solid.GetBoundingBox()
    ss = []
    for x in (bb.Min.X, bb.Max.X):
        for y in (bb.Min.Y, bb.Max.Y):
            for z in (bb.Min.Z, bb.Max.Z):
                pt = bb.Transform.OfPoint(XYZ(x, y, z))
                ss.append(pt.Subtract(p0).DotProduct(u))
    return min(ss), max(ss)


def clashes(wall):
    """[(dầm/sàn, cao độ đáy phần giao (ft), thể tích giao (ft³), s0, s1 dọc trục tường (ft))] với khối tường."""
    result = []
    ws = main_solid(wall)
    bb = wall.get_BoundingBox(None)
    if ws is None or bb is None:
        return result
    p0, u, _ = wall_axis(wall)
    cands = (FilteredElementCollector(doc).WherePasses(STRUCT_FILTER).WhereElementIsNotElementType()
             .WherePasses(BoundingBoxIntersectsFilter(Outline(bb.Min, bb.Max))).ToElements())
    for c in cands:
        cs = main_solid(c)
        if cs is None:
            continue
        try:
            x = BooleanOperationsUtils.ExecuteBooleanOperation(ws, cs, BooleanOperationsType.Intersect)
        except Exception:
            continue
        if x is None or x.Volume < MIN_CLASH_FT3:
            continue
        xb = x.GetBoundingBox()
        s0, s1 = along_range(x, p0, u)
        result.append((c, xb.Transform.OfPoint(xb.Min).Z, x.Volume, s0, s1))
    return result


def covers_full_length(cl, length):
    """Các phần giao (dầm/sàn) phủ kín chiều dài tường (sai số COVER_TOL_MM)?"""
    tol = from_mm(COVER_TOL_MM)
    reach = 0.0
    for s0, s1 in sorted((max(0.0, c[3]), min(length, c[4])) for c in cl):
        if s0 > reach + tol:
            return False
        reach = max(reach, s1)
    return reach >= length - tol


def set_top(w, top, base_level):
    top_id = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).AsElementId()
    if top_id != ElementId.InvalidElementId:
        w.get_Parameter(BuiltInParameter.WALL_TOP_OFFSET).Set(top - doc.GetElement(top_id).Elevation)
    else:
        base_z = base_level.Elevation + w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
        w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(top - base_z)


def split_under(w, cl, base_level):
    """Join không cắt được → tách tường tại mặt dầm/sàn còn đè: mỗi đoạn lấy đỉnh = đáy thấp nhất phía trên đoạn đó.
    Đoạn đầu giữ tường gốc (đổi đường định vị), các đoạn sau tạo tường mới cùng type / thông số. Trả về tường mới."""
    p0, u, length = wall_axis(w)
    cur_top = w.get_BoundingBox(None).Max.Z
    tol = from_mm(COVER_TOL_MM)
    cuts = sorted(set([0.0, length] + [min(length, max(0.0, s)) for c in cl for s in (c[3], c[4])]))
    bounds = [cuts[0]]
    for s in cuts[1:]:
        if s - bounds[-1] > tol:
            bounds.append(s)
    bounds[-1] = length
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        m = (a + b) / 2.0
        top = min([c[1] for c in cl if c[3] - tol <= m <= c[4] + tol] + [cur_top])
        if segs and abs(segs[-1][2] - top) < from_mm(TOL_MM):
            segs[-1][1] = b
        else:
            segs.append([a, b, top])
    if len(segs) == 1:
        set_top(w, segs[0][2], base_level)
        return []
    z = w.Location.Curve.GetEndPoint(0).Z
    key_ref = w.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).AsInteger()
    base_off = w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
    top_id = w.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).AsElementId()

    def seg_line(a, b):
        pa, pb = p0.Add(u.Multiply(a)), p0.Add(u.Multiply(b))
        return Line.CreateBound(XYZ(pa.X, pa.Y, z), XYZ(pb.X, pb.Y, z))

    # Cắt tường gốc về đoạn đầu TRƯỚC khi tạo tường mới. Tạm cấm nối ở hai đầu, nếu không Revit có thể kéo đầu tường
    # về chỗ nối cũ và giữ nguyên chiều dài (gặp ở mô hình 254: tường 1022413 không bị cắt, chồng lên tường mới).
    a, b, top = segs[0]
    for end in (0, 1):
        WallUtils.DisallowWallJoinAtEnd(w, end)
    w.Location.Curve = seg_line(a, b)
    doc.Regenerate()
    if abs(w.Location.Curve.Length - (b - a)) > from_mm(TOL_MM):
        raise Exception(u"không cắt được tường gốc Id {} (dài {:.0f} mm, cần {:.0f} mm)".format(
            w.Id.Value, to_mm(w.Location.Curve.Length), to_mm(b - a)))
    set_top(w, top, base_level)
    new_walls = []
    for a, b, top in segs[1:]:
        line = seg_line(a, b)
        nw = Wall.Create(doc, line, w.WallType.Id, w.LevelId, top - base_level.Elevation - base_off, base_off,
                         w.Flipped, False)
        if top_id != ElementId.InvalidElementId:
            nw.get_Parameter(BuiltInParameter.WALL_HEIGHT_TYPE).Set(top_id)
        nw.get_Parameter(BuiltInParameter.WALL_KEY_REF_PARAM).Set(key_ref)
        nw.Location.Curve = line
        set_top(nw, top, base_level)
        new_walls.append(nw)
    for end in (0, 1):
        WallUtils.AllowWallJoinAtEnd(w, end)
    return new_walls


def category_label(e):
    return u"Dầm" if e.Category.BuiltInCategory == BuiltInCategory.OST_StructuralFraming else u"Sàn"


LOG_HEADER = [u"ElementId tường", u"Wall type", u"Đỉnh cũ (mm)", u"Đỉnh mới (mm)", u"Dầm/sàn đỡ đỉnh",
              u"Join (dầm/sàn cắt tường)", u"Kết quả", u"Giá trị cũ", u"Giá trị mới"]


def write_log(rows, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "CatTuongTheoDamSan_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm (cao độ tuyệt đối theo project)\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def main(base_name, type_filters, dry_run):
    global STRUCT_FILTER
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."]
    STRUCT_FILTER = LogicalOrFilter(ElementCategoryFilter(BuiltInCategory.OST_Floors),
                                    ElementCategoryFilter(BuiltInCategory.OST_StructuralFraming))
    base_level = find_level(base_name)
    walls = [w for w in FilteredElementCollector(doc).OfClass(Wall).ToElements()
             if w.LevelId == base_level.Id and any(norm(f).lower() in norm(get_name(w)).lower() for f in type_filters)]
    if not walls:
        raise StopReport([u"DỪNG: không có tường nào trên level '{}' có tên type chứa '{}'.".format(
            base_name, u"; ".join(type_filters))])

    # --- Lập kế hoạch
    plans, rows, hist, n_join = [], [], {}, 0
    for w in walls:
        cl = clashes(w)
        if not cl:
            continue
        bb = w.get_BoundingBox(None)
        old_top = bb.Max.Z
        # Dầm/sàn phủ kín chiều dài tường → hạ đỉnh về đáy cao nhất; chỉ phủ một phần (VD dầm cắt ngang đầu tường)
        # → giữ đỉnh hiện tại, chỉ cắt phần đè
        new_top = max(c[1] for c in cl) if covers_full_length(cl, wall_axis(w)[2]) else old_top
        base_z = base_level.Elevation + w.get_Parameter(BuiltInParameter.WALL_BASE_OFFSET).AsDouble()
        support = [c[0] for c in cl if abs(c[1] - new_top) < from_mm(TOL_MM)]
        cutters = [c[0] for c in cl if c[1] < new_top - from_mm(TOL_MM)]
        row = [w.Id.Value, get_name(w), u"{:.0f}".format(to_mm(old_top)), u"{:.0f}".format(to_mm(new_top)),
               u", ".join(u"{} {}".format(category_label(c), get_name(c)) for c in support),
               u", ".join(u"{} {} (Id {})".format(category_label(c), get_name(c), c.Id.Value) for c in cutters),
               u"", u"{:.0f}".format(to_mm(old_top)), u"{:.0f}".format(to_mm(new_top))]
        if new_top - base_z < from_mm(MIN_HEIGHT_MM):
            row[6] = u"Bỏ qua – đỉnh mới quá thấp, kiểm tra tay"
        else:
            row[6] = u"Sẽ cập nhật" if dry_run else u"Chờ cập nhật"
            plans.append((w, new_top, cutters, len(rows)))
            k = int(round(to_mm(new_top - base_level.Elevation)))
            hist[k] = hist.get(k, 0) + 1
            n_join += len(cutters)
        rows.append(row)
    n_clash_walls = len(rows)

    remain, fails, n_split, new_walls = None, [], 0, []
    if not dry_run and plans:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for w, new_top, _, ri in plans:
                set_top(w, new_top, base_level)
            doc.Regenerate()
            for w, _, cutters, ri in plans:
                for c in cutters:
                    try:
                        if not JoinGeometryUtils.AreElementsJoined(doc, c, w):
                            JoinGeometryUtils.JoinGeometry(doc, c, w)
                        if JoinGeometryUtils.IsCuttingElementInJoin(doc, w, c):
                            JoinGeometryUtils.SwitchJoinOrder(doc, c, w)
                    except Exception as ex:
                        fails.append(u"{}/{}: {}".format(w.Id.Value, c.Id.Value, ex))
                rows[ri][6] = u"Đã cập nhật"
            doc.Regenerate()
            # Dự phòng: Join không cắt được (VD đầu tường nằm dưới dầm vuông góc) → tách tường tại mặt dầm/sàn,
            # đoạn dưới dầm lấy đỉnh = đáy dầm
            for w, _, _, ri in plans:
                cl = clashes(w)
                if not cl:
                    continue
                for c in cl:
                    try:
                        if JoinGeometryUtils.AreElementsJoined(doc, c[0], w):
                            JoinGeometryUtils.UnjoinGeometry(doc, c[0], w)
                    except Exception:
                        pass
                try:
                    added = split_under(w, cl, base_level)
                except Exception as ex:
                    for end in (0, 1):
                        WallUtils.AllowWallJoinAtEnd(w, end)
                    rows[ri][6] = u"LỖI tách tường: {} – xử lý tay".format(ex)
                    continue
                new_walls.extend(added)
                n_split += 1
                rows[ri][6] = u"Đã cập nhật – tách tường tại {} (Join không cắt được){}".format(
                    u", ".join(u"{} Id {}".format(category_label(c[0]), c[0].Id.Value) for c in cl),
                    u"; tường mới Id " + u", ".join(str(nw.Id.Value) for nw in added) if added else u"")
            doc.Regenerate()
            remain = [(w, cl) for w in [p[0] for p in plans] + new_walls for cl in [clashes(w)] if cl]
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI, mọi thay đổi đã được hoàn tác: {}".format(ex)]
        for w, cl in remain:
            for c, _, v, _, _ in cl:
                rows.append([w.Id.Value, get_name(w), u"", u"", u"", u"{} {} (Id {})".format(
                    category_label(c), get_name(c), c.Id.Value),
                    u"CÒN ĐÈ {:.4f} m³ – kiểm tra tay".format(v * 0.0283168), u"—", u"—"])

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run
                                 else u"ĐÃ THỰC HIỆN")]
    n_lower = sum(1 for r in rows if r[2] and r[3] and r[2] != r[3])
    report.append(u"Level chân {} – lọc type '{}': {} tường, {} tường đè lên dầm/sàn → hạ đỉnh {} tường; "
                  u"{} cặp dầm/sàn cắt tường (Join, dầm/sàn cắt tường).".format(
                      base_level.Name, u"; ".join(type_filters), len(walls), n_clash_walls, n_lower, n_join))
    report.append(u"Đỉnh tường mới so với level chân (mm × số tường): " + u", ".join(
        u"{} × {}".format(k, hist[k]) for k in sorted(hist)))
    if remain is not None:
        report.append(u"Kiểm tra sau khi cắt: {} cặp còn đè{}".format(
            sum(len(cl) for _, cl in remain), u"" if not remain else u" – xem dòng 'CÒN ĐÈ' trong log"))
        if fails:
            report.append(u"Join lỗi {} cặp: {}".format(len(fails), u"; ".join(fails[:5])))
        if n_split:
            report.append(u"Tách {} tường tại mặt dầm/sàn vì Join không cắt được – đoạn dưới dầm lấy đỉnh = đáy dầm "
                          u"(xem cột Kết quả trong log).".format(n_split))
    try:
        report.append(u"Log: " + write_log(rows, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER[:7]))
    report += [u" | ".join(u"{}".format(v) for v in r[:7]) for r in rows]
    return report


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


import traceback
try:
    OUT = main((IN[0] or u"Tầng 1"),
               [s for s in (IN[1] or u"WB ").split(u";") if s.strip()],
               True if IN[2] is None else bool(IN[2]))
except StopReport as ex:
    OUT = ex.lines
except Exception as ex:
    OUT = [u"LỖI: {}".format(ex), traceback.format_exc()]
note = force_rerun_next_time()
if note:
    OUT.append(u"LƯU Ý: " + note)
