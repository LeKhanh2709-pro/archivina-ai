# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoTranCanHo_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
# Revit 2026 / Dynamo 3.6 (CPython3)
#
# Tạo trần hoàn thiện (Ceiling) cho phòng ngủ, phòng khách, WC, logia của các căn hộ trên level của view mặt bằng /
# mặt bằng trần đang mở, theo biên các tấm SÀN HOÀN THIỆN đã có (ARV_TaoSanCanHoTuCAD_v1 / ARV_TaoSanHoanThien_v1):
#   1. Sàn nguồn = Floor trên level có Comments bắt đầu bằng IN[0] (mặc định "ARV-SanCanHo").
#      Comments dạng "ARV-SanCanHo CH07 KHO" → căn = từ thứ 2, loại = từ cuối (KHO / WC / LOGIA).
#      Loại không đọc được từ Comments → tra theo floor type (IN[1]).
#   2. Mỗi tấm sàn → một tấm trần cùng biên (kể cả lỗ; WC giữ biên lùi 25 mm khỏi mặt thô như sàn).
#   3. Ceiling type + cao độ ĐÁY trần so với Level theo loại (IN[2], IN[3]) – KTS chỉnh theo từng dự án.
#      Type ở IN[2] chưa có → nhân bản từ type mẫu IN[4] đúng tên đó (giữ cấu tạo lớp), chỉ khi chạy thật.
#   4. Bỏ qua tấm sàn đã có trần phía trên (điểm trong sàn nằm dưới mặt đáy một trần cùng level).
#      Comments trần = "ARV-TranCanHo <căn> <loại>".
#   5. Cảnh báo khi mặt trên trần (đáy + chiều dày type) vượt Level kế trên.
# INPUT
#   IN[0] (str)  Comments của sàn nguồn bắt đầu bằng (VD "ARV-SanCanHo"; cách ';' nếu nhiều)
#   IN[1] (str)  Loại theo floor type khi Comments không có loại: "KHO=…;WC=…;LOGIA=…" (tên floor type, cách ',')
#   IN[2] (str)  Ceiling type theo loại: "KHO=…;WC=…;LOGIA=…"
#   IN[3] (str)  Cao độ đáy trần so với Level (mm) theo loại: "KHO=2700;WC=2400;LOGIA=2700"
#   IN[4] (str)  Ceiling type mẫu để nhân bản type thiếu (VD "Plain"; trống = dừng khi thiếu type)
#   IN[5] (str)  Chỉ làm các căn (cách ';', VD "CH01;CH02"; trống = tất cả)
#   IN[6] (bool) Dry-run: True = chỉ báo cáo + xem trước (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, cảnh báo, đường dẫn log, từng tấm trần
#   OUT[1] (list[Line]) Xem trước: biên các tấm trần sẽ tạo (mm, tại cao độ đáy trần)

import os
import io
import csv
import math
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, CurveLoop, Transform, Transaction, UnitUtils,
                                   UnitTypeId, ModelPathUtils, BuiltInParameter, Floor, Ceiling, CeilingType,
                                   Level, Sketch, HostObjectUtils, Face, ViewType)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo trần căn hộ"
SCRIPT_TAG = u"ARV_TaoTranCanHo_v1"
COMMENT_TAG = u"ARV-TranCanHo"
KINDS = ("KHO", "WC", "LOGIA")
KIND_LABEL = {"KHO": u"Ngủ / khách", "WC": u"WC", "LOGIA": u"Logia"}
INNER_MM = 20.0           # Điểm đại diện: lùi vào trong từ trung điểm cạnh dài nhất


# --- Hình học 2D thuần (mm) ---------------------------------------------------------
def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def signed_area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2.0


def point_in(pt, pts):
    x, y = pt
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def interior_point(outer, holes):
    """Điểm nằm trong vòng ngoài, ngoài các lỗ: trung điểm cạnh dài lùi vào trong INNER_MM."""
    ccw = signed_area(outer) > 0
    edges = sorted(range(len(outer)), key=lambda i: -math.hypot(outer[(i + 1) % len(outer)][0] - outer[i][0],
                                                                outer[(i + 1) % len(outer)][1] - outer[i][1]))
    for i in edges:
        a, b = outer[i], outer[(i + 1) % len(outer)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l < 3 * INNER_MM:
            continue
        s = 1.0 if ccw else -1.0
        p = ((a[0] + b[0]) / 2.0 - s * (b[1] - a[1]) / l * INNER_MM,
             (a[1] + b[1]) / 2.0 + s * (b[0] - a[0]) / l * INNER_MM)
        if point_in(p, outer) and not any(point_in(p, h) for h in holes):
            return p
    return (sum(p[0] for p in outer) / len(outer), sum(p[1] for p in outer) / len(outer))


def parse_map(text):
    result = {}
    for part in (text or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            if k.strip():
                result[k.strip().upper()] = v.strip()
    return result


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def split_filters(text):
    return [s.strip() for s in (text or u"").split(u";") if s.strip()]


def parse_comment(comment, prefixes):
    """'ARV-SanCanHo CH07 KHO' → (căn, loại hoặc None). Không khớp tiền tố → None."""
    c = norm(comment)
    if not any(c.startswith(norm(p)) for p in prefixes):
        return None
    words = c.split()
    apt = words[1] if len(words) > 1 else u"—"
    kind = words[-1].upper() if len(words) > 2 and words[-1].upper() in KINDS else None
    return apt, kind


# =====================================================================================
# PHẦN REVIT
# =====================================================================================
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


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def comment_of(el):
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return (p.AsString() if p else u"") or u""


def type_thickness(ctype):
    cs = ctype.GetCompoundStructure()
    return cs.GetWidth() if cs is not None else 0.0


class Job(object):
    def __init__(self, floor, apt, kind):
        self.floor = floor
        self.apt = apt
        self.kind = kind
        self.loops = []       # [[Curve]] (feet) theo sketch sàn
        self.outer = []       # [(x, y)] mm – vòng ngoài (để xem trước / điểm đại diện)
        self.holes = []
        self.ip = (0.0, 0.0)
        self.area = 0.0
        self.status = u""
        self.id = u""


def floor_loops(floor):
    """Biên sketch của sàn → [[Curve]] và các vòng điểm (mm, đã tessellate)."""
    sk = doc.GetElement(floor.SketchId)
    if not isinstance(sk, Sketch):
        return [], []
    curves, pts = [], []
    for arr in sk.Profile:
        cs = list(arr)
        if not cs:
            continue
        curves.append(cs)
        loop = []
        for c in cs:
            loop.extend([(to_mm(p.X), to_mm(p.Y)) for p in list(c.Tessellate())[:-1]])
        pts.append(loop)
    return curves, pts


def build_loops(curves, z):
    """Đưa các cạnh sketch về cao độ z → List[CurveLoop]."""
    out = List[CurveLoop]()
    for cs in curves:
        loop = CurveLoop()
        for c in cs:
            dz = z - c.GetEndPoint(0).Z
            loop.Append(c.CreateTransformed(Transform.CreateTranslation(XYZ(0, 0, dz))) if abs(dz) > 1e-9 else c)
        out.Add(loop)
    return out


def ceiling_above(ceilings, p_mm):
    """Trần đã có (cùng level) phủ điểm p (mm) – kiểm tra bằng hình chiếu lên mặt đáy trần."""
    x, y = from_mm(p_mm[0]), from_mm(p_mm[1])
    for cg in ceilings:
        bb = cg.get_BoundingBox(None)
        if bb is None or not (bb.Min.X <= x <= bb.Max.X and bb.Min.Y <= y <= bb.Max.Y):
            continue
        for ref in HostObjectUtils.GetBottomFaces(cg):
            face = cg.GetGeometryObjectFromReference(ref)
            # Face.Project trả về None khi hình chiếu nằm ngoài mặt
            if isinstance(face, Face) and face.Project(XYZ(x, y, bb.Min.Z - 1.0)) is not None:
                return cg
    return None


def preview_lines(jobs, heights):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for j in jobs:
            z = heights.get(j.kind, 0.0)
            for loop in [j.outer] + j.holes:
                for i in range(len(loop)):
                    a, b = loop[i], loop[(i + 1) % len(loop)]
                    out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z),
                                                           DSPoint.ByCoordinates(b[0], b[1], z)))
        return out
    except Exception:
        return []


LOG_HEADER = [u"Căn", u"Loại", u"Id sàn nguồn", u"Điểm trong phòng (mm)", u"Ceiling type", u"Đáy trần (mm)",
              u"DT (m²)", u"Kết quả", u"ElementId"]


def write_log(rows, level_name, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoTranCanHo_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Level: {}\n".format(level_name))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm, m²\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def main(prefixes, floor_kind_text, type_text, height_text, template_name, only_text, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    view = doc.ActiveView
    level = view.GenLevel if view.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan) else None
    if level is None:
        return [u"DỪNG: hãy mở view mặt bằng / mặt bằng trần của tầng cần tạo trần rồi Run lại."], []
    if not prefixes:
        raise StopReport([u"DỪNG: IN[0] trống – nhập Comments của sàn nguồn (VD ARV-SanCanHo)."])

    # Đầu vào
    floor_kind = {}
    for k, v in parse_map(floor_kind_text).items():
        if k not in KINDS:
            raise StopReport([u"DỪNG: IN[1] có loại '{}' không hợp lệ (chỉ dùng {}).".format(k, u"/".join(KINDS))])
        for name in v.split(u","):
            if name.strip():
                floor_kind[norm(name)] = k
    type_names = dict((k, norm(v)) for k, v in parse_map(type_text).items() if v.strip())
    heights = {}
    for k, v in parse_map(height_text).items():
        try:
            heights[k] = float(v)
        except ValueError:
            raise StopReport([u"DỪNG: IN[3] cao độ '{}={}' không phải số.".format(k, v)])
    lack = [k for k in KINDS if k not in type_names or k not in heights]
    if lack:
        raise StopReport([u"DỪNG: chưa khai báo ceiling type (IN[2]) hoặc cao độ đáy trần (IN[3]) cho: {}.".format(
            u", ".join(lack))])
    only = set(s.upper() for s in split_filters(only_text.replace(u",", u";")))

    all_types = dict((norm(type_name(t)), t) for t in FilteredElementCollector(doc).OfClass(CeilingType).ToElements())
    template = all_types.get(norm(template_name)) if template_name else None
    if template_name and template is None:
        raise StopReport([u"DỪNG: không có ceiling type mẫu '{}' (IN[4]). Các ceiling type: {}".format(
            template_name, u", ".join(sorted(all_types.keys())))])
    ctypes, pending, missing = {}, {}, []
    for k in KINDS:
        name = type_names[k]
        if name in all_types:
            ctypes[k] = all_types[name]
        elif template is not None:
            pending[k] = name      # nhân bản khi chạy thật; dry-run tạm tính theo type mẫu
            ctypes[k] = template
        else:
            missing.append(u"{}='{}'".format(k, name))
    if missing:
        raise StopReport([u"DỪNG: không có ceiling type {} (IN[2]) và chưa có type mẫu để nhân bản (IN[4]). "
                          u"Các ceiling type: {}".format(u", ".join(missing), u", ".join(sorted(all_types.keys())))])

    def ct_label(k):
        if k in pending:
            return u"{} (sẽ nhân bản từ {})".format(pending[k], type_name(template))
        return type_name(ctypes[k])

    # Sàn nguồn
    jobs, unknown, warns = [], [], []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId != level.Id:
            continue
        parsed = parse_comment(comment_of(fl), prefixes)
        if parsed is None:
            continue
        apt, kind = parsed
        if only and apt.upper() not in only:
            continue
        if kind is None:
            kind = floor_kind.get(norm(type_name(doc.GetElement(fl.GetTypeId()))))
        if kind is None:
            unknown.append(fl)
            continue
        j = Job(fl, apt, kind)
        j.loops, pts = floor_loops(fl)
        if not pts:
            warns.append(u"Sàn Id {}: không đọc được biên sketch".format(id_value(fl.Id)))
            continue
        k_out = max(range(len(pts)), key=lambda i: abs(signed_area(pts[i])))
        j.outer = pts[k_out]
        j.holes = [p for i, p in enumerate(pts) if i != k_out]
        j.ip = interior_point(j.outer, j.holes)
        j.area = (abs(signed_area(j.outer)) - sum(abs(signed_area(h)) for h in j.holes)) / 1e6
        jobs.append(j)
    if not jobs and not unknown:
        raise StopReport([u"DỪNG: level '{}' không có sàn nào có Comments bắt đầu bằng {}{}. Chạy tool tạo sàn "
                          u"hoàn thiện trước, hoặc sửa IN[0].".format(
                              level.Name, u" / ".join(prefixes), u" thuộc căn " + u", ".join(sorted(only)) if only else u"")])

    # Bỏ qua sàn đã có trần phía trên
    old = [c for c in FilteredElementCollector(doc).OfClass(Ceiling).ToElements() if c.LevelId == level.Id]
    todo = []
    for j in jobs:
        cg = ceiling_above(old, j.ip) if old else None
        if cg is not None:
            j.status, j.id = u"Bỏ qua: đã có trần", id_value(cg.Id)
        else:
            todo.append(j)

    # Kiểm tra trần vượt level kế trên
    above = sorted([l for l in FilteredElementCollector(doc).OfClass(Level).ToElements()
                    if l.Elevation > level.Elevation + 1e-6], key=lambda l: l.Elevation)
    if above:
        room_h = to_mm(above[0].Elevation - level.Elevation)
        for k in KINDS:
            top = heights[k] + to_mm(type_thickness(ctypes[k]))
            if top > room_h:
                warns.append(u"{}: mặt trên trần {:.0f} mm vượt Level kế trên '{}' (+{:.0f})".format(
                    KIND_LABEL[k], top, above[0].Name, room_h))

    # Ghi vào mô hình
    created_types = []
    n_err = 0
    if not dry_run and todo:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for k in sorted(set(pending) & set(j.kind for j in todo)):
                name = pending.pop(k)
                ctypes[k] = template.Duplicate(name)
                created_types.append(u"{} = '{}' (nhân bản từ '{}')".format(k, name, type_name(template)))
            for j in todo:
                try:
                    cg = Ceiling.Create(doc, build_loops(j.loops, level.Elevation), ctypes[j.kind].Id, level.Id)
                except Exception as ex:
                    j.status = u"LỖI Ceiling.Create: {}".format(ex)
                    n_err += 1
                    continue
                cg.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM).Set(from_mm(heights[j.kind]))
                cm = cg.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(u"{} {} {}".format(COMMENT_TAG, j.apt, j.kind))
                j.status, j.id = u"Đã tạo", id_value(cg.Id)
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo trần, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
    elif dry_run:
        for j in todo:
            j.status = u"Sẽ tạo"

    # Báo cáo
    order = {"KHO": 0, "WC": 1, "LOGIA": 2}
    rows = []
    for j in sorted(jobs, key=lambda j: (j.apt, order.get(j.kind, 3), -j.area)):
        rows.append([j.apt, KIND_LABEL[j.kind], id_value(j.floor.Id), fmt(j.ip), ct_label(j.kind),
                     u"{:.0f}".format(heights[j.kind]), u"{:.2f}".format(j.area), j.status, j.id])
    for fl in unknown:
        rows.append([u"—", u"—", id_value(fl.Id), u"—", u"—", u"—", u"—",
                     u"Bỏ qua: không rõ loại (floor type '{}' không có trong IN[1])".format(
                         type_name(doc.GetElement(fl.GetTypeId()))), u""])

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    apts = sorted(set(j.apt for j in jobs))
    report.append(u"Level: {} – {} căn ({}) – {} tấm sàn nguồn".format(level.Name, len(apts), u", ".join(apts),
                                                                      len(jobs)))
    counts = {}
    for j in todo:
        counts[j.kind] = counts.get(j.kind, 0) + 1
    report.append(u"Tấm trần {}: {} (ngủ/khách {}, WC {}, logia {}) – bỏ qua đã có trần: {}{}".format(
        u"sẽ tạo" if dry_run else u"đã tạo", len(todo) - n_err, counts.get("KHO", 0), counts.get("WC", 0),
        counts.get("LOGIA", 0), len(jobs) - len(todo), u" – LỖI: {}".format(n_err) if n_err else u""))
    for k in KINDS:
        report.append(u"  {}: {} – đáy trần +{:.0f} mm, dày {:.0f} mm".format(
            KIND_LABEL[k], ct_label(k), heights[k], to_mm(type_thickness(ctypes[k]))))
    for line in created_types:
        report.append(u"ĐÃ NHÂN BẢN ceiling type: " + line)
    for k in sorted(pending):
        report.append(u"Ceiling type {} = '{}' chưa có → {} từ '{}'".format(
            k, pending[k], u"sẽ nhân bản khi chạy thật" if dry_run else u"không có trần dùng, không nhân bản",
            type_name(template)))
    if unknown:
        warns.append(u"{} sàn không rõ loại – xem log".format(len(unknown)))
    for a in apts:
        ks = set(j.kind for j in jobs if j.apt == a)
        for k in KINDS:
            if k not in ks:
                warns.append(u"{}: không có sàn {}".format(a, KIND_LABEL[k]))
    for w in warns:
        report.append(u"CẢNH BÁO: " + w)
    try:
        report.append(u"Log: " + write_log(rows, level.Name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra biên trần (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines(todo, heights)


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
    try:
        OUT = list(main(
            split_filters(IN[0] if IN[0] is not None else u"ARV-SanCanHo"),
            IN[1] or u"",
            IN[2] or u"",
            IN[3] or u"",
            (IN[4] or u"").strip(),
            IN[5] or u"",
            True if IN[6] is None else bool(IN[6]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoTranCanHo_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
