# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-29)
# Mã nguồn của Python node trong 12. ARV_TraGoLogia_v1.dyn.
# Revit 2027 / Dynamo (CPython3)
#
# Trát gờ logia 3 mặt (mặt trong phía logia, mặt trên, mặt ngoài) cho gờ do tool gờ logia tạo (Comments "ARV-GoLogia"):
#   1. Phạm vi: phần tử đang chọn / Id ở IN[3]; không chọn gì → mọi gờ (Wall, Comments bắt đầu bằng IN[2]) trên level
#      của view mặt bằng đang mở; view khác (3D, mặt cắt…) → mọi gờ trong mô hình. Chỉ gờ thẳng.
#   2. Mặt bên: tường trát (wall type MATBEN, VD "WA_M15" 15 mm) áp sát mặt bên gờ, dài bằng gờ, đỉnh = đỉnh gờ + dày
#      trát (bọc mép lớp trát trên). Chân trát mặt trong = chân gờ + IN[1] (mặc định 50 = dày sàn logia, không chồng
#      sàn đã có); chân trát mặt ngoài = chân gờ + IN[5].
#   3. Phía logia: mặt bên có sàn logia của tool 06 (Comments "ARV-SanCanHo … LOGIA") cách mặt gờ ≤ 100 mm.
#      Không xác định được → bỏ qua gờ đó, báo.
#   4. Mặt trên: Floor dày = dày trát (type MATTREN), phủ đỉnh gờ + hai lớp trát bên, mặt = đỉnh gờ + dày trát.
#      Type chưa có → khi chạy thật nhân bản một floor type có sẵn, gán 1 lớp (Structure) dày = dày trát, vật liệu = vật
#      liệu lớp của wall type MATBEN (cùng vật liệu trát).
#   5. Phần tử tạo: không Room Bounding (tường), không tự nối đầu, Comments "ARV-TratGoLogia <Id gờ>". Gờ đã có trát
#      của tool → bỏ qua (xoá để làm lại).
# INPUT
#   IN[0] (float) Dày trát (mm), mặc định 15
#   IN[1] (float) Chân trát mặt trong so với chân gờ (mm), mặc định 50
#   IN[2] (str)   Comments nhận gờ (bắt đầu bằng), mặc định "ARV-GoLogia"
#   IN[3] (str)   Id gờ, cách ';' (trống = đang chọn; không chọn = cả level của view)
#   IN[4] (str)   Type trát: "MATBEN=WA_M15;MATTREN=FA_FF_M15 (Trát gờ logia)"
#   IN[5] (float) Chân trát mặt ngoài so với chân gờ (mm), mặc định 0
#   IN[6] (bool)  Dry-run: True = chỉ báo cáo + xem trước (mặc định True)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo
#   OUT[1] (list[Line]) Xem trước: tim lớp trát mặt bên + biên lớp trát trên (mm)

import os
import io
import csv
import datetime
import traceback
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, Line, Transaction, UnitUtils, UnitTypeId,
                                   ModelPathUtils, BuiltInParameter, Floor, FloorType, Wall, WallType, WallUtils,
                                   ElementId, LocationCurve, HostObjectUtils, ShellLayerType, PlanarFace, CurveLoop,
                                   CompoundStructureLayer, MaterialFunctionAssignment, ViewType)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Trát gờ logia"
COMMENT_TAG = u"ARV-TratGoLogia"
FLOOR_TAG = u"ARV-SanCanHo"
PROBE_MM = 100.0         # Dò sàn logia cách mặt gờ
LOG_HEADER = [u"Id gờ", u"Dài (mm)", u"Mặt", u"Chân → đỉnh (mm so với chân gờ)", u"Kết quả", u"ElementId"]


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def id_value(eid):
    return eid.Value


def type_name(t):
    p = t.get_Parameter(BuiltInParameter.SYMBOL_NAME_PARAM)
    return p.AsString() if p is not None and p.AsString() else t.Name


def comments(el):
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return (p.AsString() or u"") if p is not None else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def point_in(pt, poly):
    x, y = pt
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def parse_map(text):
    result = {}
    for part in (text or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            result[k.strip().upper()] = v.strip()
    return result


def logia_polys(level):
    """Vòng biên (mm) các sàn logia của tool 06 trên level."""
    polys = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        parts = comments(fl).split()
        if fl.LevelId != level.Id or len(parts) < 3 or parts[0] != FLOOR_TAG or parts[-1].upper() != u"LOGIA":
            continue
        sk = doc.GetElement(fl.SketchId)
        for ca in sk.Profile:
            pts = []
            for c in ca:
                p = c.GetEndPoint(0)
                pts.append((to_mm(p.X), to_mm(p.Y)))
            if len(pts) >= 3:
                polys.append(pts)
    return polys


def side_faces(w):
    """[(PlanarFace, pháp tuyến ngang)] hai mặt bên của tường."""
    out = []
    for side in (ShellLayerType.Interior, ShellLayerType.Exterior):
        for ref in HostObjectUtils.GetSideFaces(w, side):
            f = w.GetGeometryObjectFromReference(ref)
            if isinstance(f, PlanarFace) and abs(f.FaceNormal.Z) < 1e-6:
                n = XYZ(f.FaceNormal.X, f.FaceNormal.Y, 0).Normalize()
                out.append((f, n))
                break
    return out


def collect_curbs(id_text, prefix):
    if id_text:
        elems = [doc.GetElement(ElementId(int(s))) for s in id_text.replace(u",", u";").split(u";") if s.strip()]
        how = u"Id nhập ở IN[3]"
    else:
        elems = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
        how = u"phần tử đang chọn"
    elems = [e for e in elems if isinstance(e, Wall) and comments(e).startswith(prefix)]
    if not elems:
        view = doc.ActiveView
        level = view.GenLevel if view.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan) else None
        elems = [w for w in FilteredElementCollector(doc).OfClass(Wall).ToElements()
                 if comments(w).startswith(prefix) and (level is None or w.LevelId == level.Id)]
        how = u"mọi gờ '{}' {}".format(prefix, u"trên " + level.Name if level is not None else
                                       u"trong mô hình (view đang mở không phải mặt bằng)")
    return elems, how


def existing_plaster():
    done = {}
    for cls in (Wall, Floor):
        for e in FilteredElementCollector(doc).OfClass(cls).ToElements():
            c = comments(e)
            if c.startswith(COMMENT_TAG + u" "):
                done.setdefault(c[len(COMMENT_TAG) + 1:].strip(), []).append(id_value(e.Id))
    return done


def plan_curb(w, t_mm, in_base_mm, out_base_mm, polys):
    """Kế hoạch trát một gờ → dict hoặc chuỗi lý do bỏ qua."""
    lc = w.Location
    if not isinstance(lc, LocationCurve) or not isinstance(lc.Curve, Line):
        return u"Bỏ qua: gờ không thẳng"
    bb = w.get_BoundingBox(None)
    a, b = lc.Curve.GetEndPoint(0), lc.Curve.GetEndPoint(1)
    faces = side_faces(w)
    if len(faces) != 2:
        return u"Bỏ qua: không đọc được 2 mặt bên"
    mid = XYZ((a.X + b.X) / 2.0, (a.Y + b.Y) / 2.0, 0)
    sides = []
    for f, n in faces:
        o = f.Origin
        dist = (mid.X - o.X) * n.X + (mid.Y - o.Y) * n.Y        # < 0: tâm gờ nằm phía trong mặt
        probe = (to_mm(mid.X - n.X * dist + n.X * from_mm(PROBE_MM)),
                 to_mm(mid.Y - n.Y * dist + n.Y * from_mm(PROBE_MM)))
        logia = any(point_in(probe, p) for p in polys)
        sides.append(dict(n=n, d=-dist, logia=logia))
    if sides[0]["logia"] == sides[1]["logia"]:
        return u"Bỏ qua: không xác định được phía logia ({} mặt giáp sàn logia)".format(
            u"cả 2" if sides[0]["logia"] else u"không")
    base_mm, top_mm = to_mm(bb.Min.Z), to_mm(bb.Max.Z)
    u = XYZ(b.X - a.X, b.Y - a.Y, 0).Normalize()
    plan = dict(wall=w, length=to_mm(lc.Curve.Length), base=base_mm, top=top_mm, sides=[], u=u, a=a, b=b)
    for s in sides:
        off = s["d"] + from_mm(t_mm) / 2.0          # tim lớp trát cách tim định vị gờ
        p0 = XYZ(a.X + s["n"].X * off, a.Y + s["n"].Y * off, 0)
        p1 = XYZ(b.X + s["n"].X * off, b.Y + s["n"].Y * off, 0)
        z0 = base_mm + (in_base_mm if s["logia"] else out_base_mm)
        plan["sides"].append(dict(label=u"Mặt trong (logia)" if s["logia"] else u"Mặt ngoài", p0=p0, p1=p1,
                                  n=s["n"], z0=z0, z1=top_mm + t_mm, d=s["d"]))
    # Lớp trát trên: chữ nhật dọc gờ, ngang từ mặt ngoài lớp trát bên này tới mặt ngoài lớp trát bên kia
    s0, s1 = plan["sides"]
    e0 = s0["d"] + from_mm(t_mm)
    e1 = s1["d"] + from_mm(t_mm)
    n0, n1 = s0["n"], s1["n"]
    plan["top_pts"] = [XYZ(a.X + n0.X * e0, a.Y + n0.Y * e0, 0), XYZ(b.X + n0.X * e0, b.Y + n0.Y * e0, 0),
                       XYZ(b.X + n1.X * e1, b.Y + n1.Y * e1, 0), XYZ(a.X + n1.X * e1, a.Y + n1.Y * e1, 0)]
    return plan


def make_floor_type(name, t_mm, mat_id):
    base = None
    for ft in FilteredElementCollector(doc).OfClass(FloorType).ToElements():
        if ft.GetCompoundStructure() is not None and not ft.IsFoundationSlab:
            base = ft
            break
    nt = base.Duplicate(name)
    # Giữ cấu tạo của floor type gốc (điều kiện EndCap của sàn), chỉ thay lớp: CreateSingleLayerCompoundStructure
    # cho EndCap của tường → SetCompoundStructure báo "wrong EndCap condition" (thử 2026-10-29)
    cs = nt.GetCompoundStructure()
    cs.SetLayers(List[CompoundStructureLayer]([
        CompoundStructureLayer(from_mm(t_mm), MaterialFunctionAssignment.Structure, mat_id)]))
    cs.SetNumberOfShellLayers(ShellLayerType.Exterior, 0)
    cs.SetNumberOfShellLayers(ShellLayerType.Interior, 0)
    try:
        cs.StructuralMaterialIndex = 0
    except Exception:
        pass
    nt.SetCompoundStructure(cs)
    return nt


def set_comment(el, text):
    p = el.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if p is not None and not p.IsReadOnly:
        p.Set(text)


def write_log(rows, dry_run, settings):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TraGoLogia_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Thiết lập: {}\n".format(settings))
        f.write(u"# Đơn vị: mm\n")
        wr = csv.writer(f)
        wr.writerow(LOG_HEADER)
        wr.writerows(rows)
    return path


def preview(plans):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for pl in plans:
            for s in pl["sides"]:
                out.append(DSLine.ByStartPointEndPoint(
                    DSPoint.ByCoordinates(to_mm(s["p0"].X), to_mm(s["p0"].Y), s["z1"]),
                    DSPoint.ByCoordinates(to_mm(s["p1"].X), to_mm(s["p1"].Y), s["z1"])))
            pts = pl["top_pts"]
            for i in range(4):
                p, q = pts[i], pts[(i + 1) % 4]
                out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(to_mm(p.X), to_mm(p.Y), pl["top"]),
                                                       DSPoint.ByCoordinates(to_mm(q.X), to_mm(q.Y), pl["top"])))
        return out
    except Exception:
        return []


def main(t_mm, in_base_mm, prefix, id_text, type_text, out_base_mm, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if t_mm <= 0 or t_mm > 50:
        raise StopReport([u"DỪNG: dày trát IN[0] phải trong khoảng 0–50 mm."])
    tmap = parse_map(type_text)
    wtypes = dict((norm(type_name(t)), t) for t in FilteredElementCollector(doc).OfClass(WallType).ToElements())
    ftypes = dict((norm(type_name(t)), t) for t in FilteredElementCollector(doc).OfClass(FloorType).ToElements())
    wt = wtypes.get(norm(tmap.get(u"MATBEN", u"")))
    if wt is None:
        raise StopReport([u"DỪNG: không có wall type trát '{}' (IN[4] MATBEN=…).".format(tmap.get(u"MATBEN", u""))])
    warns = []
    if abs(to_mm(wt.Width) - t_mm) > 0.5:
        warns.append(u"wall type '{}' dày {:.0f} mm ≠ dày trát {:.0f} mm – lớp trát bên dày theo type".format(
            type_name(wt), to_mm(wt.Width), t_mm))
    ft_name = tmap.get(u"MATTREN", u"")
    if not ft_name:
        raise StopReport([u"DỪNG: chưa khai báo floor type trát mặt trên (IN[4] MATTREN=…)."])
    ft = ftypes.get(norm(ft_name))
    mat_id = None
    if ft is None:
        layers = list(wt.GetCompoundStructure().GetLayers())
        mat_id = layers[0].MaterialId if layers else ElementId.InvalidElementId

    curbs, how = collect_curbs(id_text, prefix)
    if not curbs:
        raise StopReport([u"DỪNG: không tìm thấy gờ '{}' ({}).".format(prefix, how)])
    polys_by_level = {}
    done = existing_plaster()
    plans, rows, skipped = [], [], 0
    for w in curbs:
        key = str(id_value(w.Id))
        if key in done:
            rows.append([key, u"", u"", u"", u"Bỏ qua: đã có trát (Id {}) – xoá để làm lại".format(
                u", ".join(str(i) for i in done[key][:5])), u""])
            skipped += 1
            continue
        lid = id_value(w.LevelId)
        if lid not in polys_by_level:
            polys_by_level[lid] = logia_polys(doc.GetElement(w.LevelId))
        pl = plan_curb(w, t_mm, in_base_mm, out_base_mm, polys_by_level[lid])
        if not isinstance(pl, dict):
            rows.append([key, u"", u"", u"", pl, u""])
            skipped += 1
            continue
        plans.append(pl)

    if not dry_run and plans:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            if ft is None:
                ft = make_floor_type(ft_name, t_mm, mat_id)
            for pl in plans:
                w = pl["wall"]
                lev = doc.GetElement(w.LevelId)
                for s in pl["sides"]:
                    h = from_mm(s["z1"] - s["z0"])
                    off = from_mm(s["z0"]) - lev.Elevation
                    nw = Wall.Create(doc, Line.CreateBound(XYZ(s["p0"].X, s["p0"].Y, lev.Elevation),
                                                           XYZ(s["p1"].X, s["p1"].Y, lev.Elevation)),
                                     wt.Id, lev.Id, h, off, False, False)
                    rb = nw.get_Parameter(BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)
                    if rb is not None and not rb.IsReadOnly:
                        rb.Set(0)
                    WallUtils.DisallowWallJoinAtEnd(nw, 0)
                    WallUtils.DisallowWallJoinAtEnd(nw, 1)
                    set_comment(nw, u"{} {}".format(COMMENT_TAG, id_value(w.Id)))
                    s["id"] = id_value(nw.Id)
                pts = pl["top_pts"]
                loop = CurveLoop()
                for i in range(4):
                    p, q = pts[i], pts[(i + 1) % 4]
                    loop.Append(Line.CreateBound(XYZ(p.X, p.Y, lev.Elevation), XYZ(q.X, q.Y, lev.Elevation)))
                fl = Floor.Create(doc, List[CurveLoop]([loop]), ft.Id, lev.Id)
                fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(
                    from_mm(pl["top"] + t_mm) - lev.Elevation)
                set_comment(fl, u"{} {}".format(COMMENT_TAG, id_value(w.Id)))
                pl["top_id"] = id_value(fl.Id)
            doc.Regenerate()
            for pl in plans:
                for s in pl["sides"]:
                    nw = doc.GetElement(ElementId(s["id"]))
                    o = nw.Orientation
                    if o.X * s["n"].X + o.Y * s["n"].Y < 0:
                        nw.Flip()
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo lớp trát, mọi thay đổi đã được hoàn tác: {}".format(ex), traceback.format_exc()], []

    n_wall = 0
    for pl in plans:
        key = id_value(pl["wall"].Id)
        for s in pl["sides"]:
            n_wall += 1
            rows.append([key, u"{:.0f}".format(pl["length"]), s["label"],
                         u"{:+.0f} → {:+.0f}".format(s["z0"] - pl["base"], s["z1"] - pl["base"]),
                         u"Sẽ tạo" if dry_run else u"Đã tạo", s.get("id", u"")])
        rows.append([key, u"{:.0f}".format(pl["length"]), u"Mặt trên",
                     u"{:+.0f} → {:+.0f}".format(pl["top"] - pl["base"], pl["top"] - pl["base"] + t_mm),
                     u"Sẽ tạo" if dry_run else u"Đã tạo", pl.get("top_id", u"")])

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"Phạm vi: {} – {} gờ, trát {} gờ, bỏ qua {}".format(how, len(curbs), len(plans), skipped))
    report.append(u"Trát dày {:.0f} mm: mặt bên = wall type '{}' ({} lớp), mặt trên = floor type '{}' ({} tấm)".format(
        t_mm, type_name(wt), n_wall, ft_name, len(plans)))
    report.append(u"Chân trát mặt trong = chân gờ {:+.0f} mm (mặt sàn logia), mặt ngoài = chân gờ {:+.0f} mm; "
                  u"đỉnh trát bên = đỉnh gờ + {:.0f} mm".format(in_base_mm, out_base_mm, t_mm))
    if mat_id is not None:
        m = doc.GetElement(mat_id)
        report.append(u"Floor type '{}' chưa có → {} (1 lớp {:.0f} mm, vật liệu '{}' = vật liệu '{}')".format(
            ft_name, u"sẽ nhân bản khi chạy thật" if dry_run else u"đã nhân bản", t_mm,
            m.Name if m is not None else u"—", type_name(wt)))
    for w in warns:
        report.append(u"CẢNH BÁO: " + w)
    settings = u"dày {} mm, chân trong {}, chân ngoài {}, {}".format(t_mm, in_base_mm, out_base_mm, type_text)
    try:
        report.append(u"Log: " + write_log(rows, dry_run, settings))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra xem trước (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview(plans)


if DYNAMO:
    def _num(v, default):
        try:
            return float(v) if v is not None and u"{}".format(v).strip() != u"" else default
        except Exception:
            return default

    try:
        OUT = list(main(
            _num(IN[0], 15.0),
            _num(IN[1], 50.0),
            (IN[2] or u"ARV-GoLogia").strip(),
            (IN[3] or u"").strip(),
            (IN[4] or u"MATBEN=WA_M15;MATTREN=FA_FF_M15 (Trát gờ logia)").strip(),
            _num(IN[5], 0.0),
            True if IN[6] is None else bool(IN[6]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
