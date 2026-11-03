# -*- coding: utf-8 -*-
# TRẠNG THÁI: CHƯA DUYỆT – BẢN THỬ NGHIỆM (chỉ chạy trên file copy)
"""Khoá cạnh sketch của sàn vào mặt tường để sàn chạy theo khi kéo tường.

Quy trình:
  1. Mở view mặt bằng của level sàn. Chọn sẵn các tấm sàn cần khoá; không chọn gì = toàn bộ sàn của level
     (hỏi xác nhận).
  2. Với mỗi cạnh thẳng trong sketch sàn: tìm mặt bên tường (mô hình KT, không phải link) song song,
     trùng vị trí (≤ ALIGN_TOL_MM) và phủ trung điểm cạnh. Bỏ tường len chân tường (SKIP_TYPE_PREFIXES); ưu tiên
     tường có lớp kết cấu, rồi đến mặt phủ cạnh dài nhất. Cạnh không nằm trên mặt tường (polyline CAD,
     lan can, ô cửa...) giữ nguyên, không khoá.
  3. Chạy thử (mặc định): chỉ báo cáo cạnh nào sẽ khoá vào tường nào.
  4. Chạy thật: mở sketch từng sàn bằng SketchEditScope, tạo ràng buộc canh hàng đã khoá
     (Document.Create.NewAlignment) giữa cạnh sketch và mặt tường, rồi đóng sketch. Revit từ chối mặt đầu tiên
     thì thử mặt tiếp theo.

Ghi chú (bản thử nghiệm):
  - Revit API không có hàm tạo cạnh sketch kiểu "Pick Walls"; công cụ dùng ràng buộc canh hàng khoá thay thế.
    Chưa chắc Revit 2027 cho NewAlignment trong SketchEditScope – lỗi từng cạnh được ghi vào báo cáo và log.
  - Mỗi tấm sàn là một bước Undo "ARV - Khoá sàn vào tường".
  - Ràng buộc khoá làm mô hình nặng hơn; xoá / kéo tường quá xa có thể sinh lỗi "Constraints are not satisfied".
  - Không chạy trên file central; bỏ qua sàn đang bị người khác mượn.
  - Khoá theo Id sàn: tạo lại sàn (Dynamo 06 với Tạo lại = True) thì mất khoá, phải chạy lại công cụ.
"""

import os
import io
import datetime

from pyrevit import revit, DB, forms, script
from System.Collections.Generic import List

__title__ = "Khoá sàn\nvào tường"
__author__ = "Archivina BIM"

doc = revit.doc
uidoc = revit.uidoc
output = script.get_output()

# --- Cấu hình ---------------------------------------------------------------------
ALIGN_TOL_MM = 2.0          # Cạnh sketch cách mặt tường tối đa chừng này mới coi là nằm trên mặt tường
END_TOL_MM = 5.0            # Trung điểm cạnh được phép vượt đầu tường chừng này
PARALLEL_TOL = 1e-3         # Sai số song song (cos góc)
SEARCH_MM = 1000.0          # Nới bbox sàn khi tìm tường
MAX_FLOORS = 300            # Chặn chạy nhầm trên quá nhiều sàn
MAX_TABLE_ROWS = 300        # Quá số dòng này chỉ ghi log CSV, không in bảng ra cửa sổ pyRevit
SKIP_TYPE_PREFIXES = (u"WF_",)  # Wall type không dùng làm đích khoá: len chân tường không chạy theo tường chính

TRANSACTION_NAME = u"ARV - Khoá sàn vào tường"
LOG_HEADER = [u"Sàn (ElementId)", u"Comments sàn", u"Cạnh sketch (ElementId)", u"Dài (mm)",
              u"Tường (ElementId)", u"Wall type", u"Mặt tường", u"Lệch (mm)", u"Kết quả"]
MM = DB.UnitTypeId.Millimeters


# --- Tiện ích ---------------------------------------------------------------------
def to_mm(feet):
    return DB.UnitUtils.ConvertFromInternalUnits(feet, MM)


def from_mm(mm):
    return DB.UnitUtils.ConvertToInternalUnits(mm, MM)


def id_value(element_id):
    return element_id.Value


def get_name(element):
    return revit.query.get_name(element)


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
    # Bộ môn theo tên file: ISO 19650 PRJ-ARV-T1-ZZ-M3-A-0001 (trường 6),
    # hoặc tên dự án dạng G19_A_L3-32 (trường 2 khi tách theo "_")
    title = document.Title or ""
    parts = title.split("-")
    if len(parts) >= 7:
        return parts[5].upper()
    parts = title.split("_")
    if len(parts) >= 2 and len(parts[1]) == 1:
        return parts[1].upper()
    return None


def require_role(document, role, role_name):
    actual = model_role(document)
    if actual != role:
        forms.alert(u"Công cụ này chỉ chạy trên mô hình {} ({}).\n"
                    u"Mã bộ môn đọc từ tên file '{}': {}.".format(
                        role_name, role, document.Title, actual or u"không xác định"), exitscript=True)


def ask_dry_run(apply_label):
    """Chọn chế độ chạy. Mặc định chạy thử; chế độ ghi phải xác nhận thêm một lần."""
    dry_label = u"Chạy thử (dry-run) – chỉ báo cáo"
    mode = forms.CommandSwitchWindow.show([dry_label, apply_label], message=u"Chế độ chạy:")
    if not mode:
        script.exit()
    if mode != apply_label:
        return True
    return not forms.alert(u"Chế độ GHI sẽ mở sketch và thêm ràng buộc khoá vào các sàn đã chọn trong '{}'.\n"
                           u"Đã chạy thử và kiểm tra báo cáo chưa? Đây có phải file COPY không?\n\n"
                           u"Chọn No để quay về chạy thử.".format(doc.Title), yes=True, no=True)


class WarningSwallower(DB.IFailuresPreprocessor):
    """Bỏ cảnh báo (warning) khi đóng sketch; lỗi (error) vẫn để Revit xử lý → Commit thất bại, sketch huỷ."""

    def PreprocessFailures(self, accessor):
        for f in accessor.GetFailureMessages():
            if f.GetSeverity() == DB.FailureSeverity.Warning:
                accessor.DeleteWarning(f)
        return DB.FailureProcessingResult.Continue


# --- Tìm mặt tường cho cạnh sketch ------------------------------------------------
def wall_has_core(wall):
    """True nếu wall type có lớp kết cấu (tường chính, không phải lớp trát / ốp tách riêng)."""
    structure = wall.WallType.GetCompoundStructure()
    if structure is None:
        return False
    return any(layer.Function == DB.MaterialFunctionAssignment.Structure for layer in structure.GetLayers())


def wall_faces_near(floor):
    """[(tường, Reference mặt bên, PlanarFace, 'Trong'/'Ngoài', có lớp kết cấu)] của tường KT quanh sàn."""
    bb = floor.get_BoundingBox(None)
    pad = from_mm(SEARCH_MM)
    outline = DB.Outline(DB.XYZ(bb.Min.X - pad, bb.Min.Y - pad, bb.Min.Z - pad),
                         DB.XYZ(bb.Max.X + pad, bb.Max.Y + pad, bb.Max.Z + pad))
    walls = DB.FilteredElementCollector(doc).OfClass(DB.Wall) \
        .WherePasses(DB.BoundingBoxIntersectsFilter(outline)).ToElements()
    result = []
    for w in walls:
        if not isinstance(w.Location, DB.LocationCurve) or not isinstance(w.Location.Curve, DB.Line):
            continue
        if get_name(w).startswith(SKIP_TYPE_PREFIXES):
            continue
        has_core = wall_has_core(w)
        for side, label in ((DB.ShellLayerType.Interior, u"Trong"), (DB.ShellLayerType.Exterior, u"Ngoài")):
            try:
                refs = DB.HostObjectUtils.GetSideFaces(w, side)
            except Exception:
                continue
            for ref in refs:
                face = w.GetGeometryObjectFromReference(ref)
                if isinstance(face, DB.PlanarFace) and abs(face.FaceNormal.Z) < 1e-6:
                    result.append((w, ref, face, label, has_core))
    return result


def match_faces(line, faces):
    """Các mặt tường chứa cạnh sketch (song song, lệch ≤ ALIGN_TOL_MM, trung điểm trong chiều dài tường), tốt
    nhất trước: tường có lớp kết cấu, rồi mặt phủ cạnh dài nhất. → [(tường, ref, nhãn mặt, lệch mm)]."""
    a, b = line.GetEndPoint(0), line.GetEndPoint(1)
    d = DB.XYZ(b.X - a.X, b.Y - a.Y, 0)
    if d.GetLength() < from_mm(1):
        return []
    d = d.Normalize()
    mid = DB.XYZ((a.X + b.X) / 2.0, (a.Y + b.Y) / 2.0, 0)
    found = []
    for w, ref, face, label, has_core in faces:
        nrm = DB.XYZ(face.FaceNormal.X, face.FaceNormal.Y, 0).Normalize()
        if abs(d.DotProduct(nrm)) > PARALLEL_TOL:
            continue
        o = face.Origin
        off = abs((mid.X - o.X) * nrm.X + (mid.Y - o.Y) * nrm.Y)
        if to_mm(off) > ALIGN_TOL_MM:
            continue
        wl = w.Location.Curve
        p0, p1 = wl.GetEndPoint(0), wl.GetEndPoint(1)
        u = DB.XYZ(p1.X - p0.X, p1.Y - p0.Y, 0)
        ln = u.GetLength()
        u = u.Normalize()
        t = (mid.X - p0.X) * u.X + (mid.Y - p0.Y) * u.Y
        tol = from_mm(END_TOL_MM)
        if t < -tol or t > ln + tol:
            continue
        # Độ phủ: phần cạnh nằm trong chiều dài tường
        ta = (a.X - p0.X) * u.X + (a.Y - p0.Y) * u.Y
        tb = (b.X - p0.X) * u.X + (b.Y - p0.Y) * u.Y
        cover = min(max(ta, tb), ln) - max(min(ta, tb), 0.0)
        found.append((0 if has_core else 1, -cover, (w, ref, label, to_mm(off))))
    found.sort(key=lambda item: item[:2])
    return [item[2] for item in found]


def sketch_lines(floor):
    """[(ModelCurve, Line)] các cạnh thẳng trong sketch sàn."""
    sk = doc.GetElement(floor.SketchId)
    result = []
    for eid in sk.GetAllElements():
        mc = doc.GetElement(eid)
        if isinstance(mc, DB.CurveElement) and isinstance(mc.GeometryCurve, DB.Line):
            result.append((mc, mc.GeometryCurve))
    return result


def curve_reference(mc):
    # Tham chiếu phần tử của chính đường sketch (như chọn cạnh bằng lệnh Align). Bản đầu dùng
    # GeometryCurve.Reference: Revit tạo được Alignment nhưng không hiện ổ khoá trong Edit Boundary (2026-10-29)
    return DB.Reference(mc)


def constraint_ref_ids(dim):
    """ElementId (long) các phần tử mà ràng buộc tham chiếu."""
    ids = set()
    try:
        for r in dim.References:
            ids.add(id_value(r.ElementId))
    except Exception:
        pass
    return ids


def constraint_index():
    """{ElementId (long) được tham chiếu: [ràng buộc]} của cả mô hình – quét một lần, dùng cho mọi sàn."""
    cat = DB.ElementId(DB.BuiltInCategory.OST_Constraints)
    index = {}
    for dim in DB.FilteredElementCollector(doc).OfClass(DB.Dimension).ToElements():
        if dim.Category is not None and dim.Category.Id == cat:
            for ref_id in constraint_ref_ids(dim):
                index.setdefault(ref_id, []).append(dim)
    return index


def old_constraints(sketch_ids, index):
    """Ràng buộc Alignment đã có trỏ vào cạnh sketch của sàn (lần chạy trước) → xoá trước khi khoá lại."""
    result = {}
    for sketch_id in sketch_ids:
        for dim in index.get(sketch_id, []):
            result[id_value(dim.Id)] = dim
    return list(result.values())


# --- Ghi log ----------------------------------------------------------------------
def write_log(rows, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "KhoaSanVaoTuong_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
    with io.open(path, "w", encoding="utf-8-sig") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# View: {}\n".format(doc.ActiveView.Name))
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

    view = doc.ActiveView
    if not isinstance(view, DB.ViewPlan) or view.GenLevel is None:
        forms.alert(u"Mở view MẶT BẰNG của level sàn rồi chạy lại.", exitscript=True)
    floors = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
    floors = [f for f in floors if isinstance(f, DB.Floor)]
    if not floors:
        floors = [f for f in DB.FilteredElementCollector(doc).OfClass(DB.Floor).ToElements()
                  if f.LevelId == view.GenLevel.Id]
        if not floors:
            forms.alert(u"Level của view không có sàn nào.", exitscript=True)
        if not forms.alert(u"Chưa chọn sàn nào. Xử lý toàn bộ {} sàn của level '{}'?".format(
                len(floors), view.GenLevel.Name), yes=True, no=True):
            script.exit()
    if len(floors) > MAX_FLOORS:
        forms.alert(u"Công cụ chỉ xử lý tối đa {} sàn mỗi lần (đang chọn {}).".format(
            MAX_FLOORS, len(floors)), exitscript=True)

    dry_run = ask_dry_run(u"Khoá cạnh sàn vào tường (GHI vào mô hình)")

    rows, n_match, n_free, n_ok, n_err, n_skip = [], 0, 0, 0, 0, 0
    plans = []
    constraints = constraint_index()
    for fl in floors:
        cm = fl.get_Parameter(DB.BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        comment = (cm.AsString() or u"") if cm is not None else u""
        if fl.LevelId != view.GenLevel.Id:
            rows.append([id_value(fl.Id), comment, u"", u"", u"", u"", u"", u"",
                         u"Bỏ qua: sàn không thuộc level của view"])
            n_skip += 1
            continue
        if doc.IsWorkshared and DB.WorksharingUtils.GetCheckoutStatus(doc, fl.Id) == \
                DB.CheckoutStatus.OwnedByOtherUser:
            rows.append([id_value(fl.Id), comment, u"", u"", u"", u"", u"", u"",
                         u"Bỏ qua: sàn đang bị người khác mượn"])
            n_skip += 1
            continue
        faces = wall_faces_near(fl)
        pairs = []
        for mc, line in sketch_lines(fl):
            candidates = match_faces(line, faces)
            if not candidates:
                n_free += 1
                rows.append([id_value(fl.Id), comment, id_value(mc.Id), u"{:.0f}".format(to_mm(line.Length)),
                             u"", u"", u"", u"", u"Không nằm trên mặt tường – giữ nguyên"])
                continue
            n_match += 1
            pairs.append((mc, candidates, line))
        sk_ids = set(id_value(i) for i in doc.GetElement(fl.SketchId).GetAllElements())
        olds = old_constraints(sk_ids, constraints)
        for dim in olds:
            rows.append([id_value(fl.Id), comment, u"", u"", u"", u"", u"", u"",
                         u"Khoá cũ {} – {}".format(id_value(dim.Id), u"sẽ xoá" if dry_run else u"xoá trước khi khoá lại")])
        plans.append((fl, comment, pairs, olds))

    n_verified, n_floor_ok, n_floor_none = 0, 0, 0
    for index, (fl, comment, pairs, olds) in enumerate(plans):
        output.update_progress(index + 1, len(plans))
        results, created, chosen = {}, {}, {}
        if not dry_run and pairs:
            scope = DB.SketchEditScope(doc, TRANSACTION_NAME)
            t = None
            try:
                scope.Start(fl.SketchId)
                t = DB.Transaction(doc, TRANSACTION_NAME)
                t.Start()
                if olds:
                    doc.Delete(List[DB.ElementId]([dim.Id for dim in olds]))
                for mc, candidates, line in pairs:
                    key = id_value(mc.Id)
                    for candidate in candidates:
                        try:
                            dim = doc.Create.NewAlignment(view, candidate[1], curve_reference(mc))
                            try:
                                if not dim.IsLocked:
                                    dim.IsLocked = True
                            except Exception:
                                pass
                            created[key] = dim.Id
                            chosen[key] = candidate
                            results[key] = u"Đã khoá"
                            break
                        except Exception as ex:
                            results[key] = u"LỖI khoá: {}".format(ex)
                t.Commit()
                scope.Commit(WarningSwallower())
            except Exception as ex:
                if t is not None and t.GetStatus() == DB.TransactionStatus.Started:
                    t.RollBack()
                if scope.IsActive:
                    scope.Cancel()
                created = {}
                for mc, candidates, line in pairs:
                    results[id_value(mc.Id)] = u"LỖI sketch (huỷ, sàn giữ nguyên): {}".format(ex)
            # Kiểm tra sau khi đóng sketch: ràng buộc còn không, có trỏ vào cạnh sketch hiện tại của sàn không
            if created:
                sk_now = set(id_value(i) for i in doc.GetElement(fl.SketchId).GetAllElements())
                for key, did in created.items():
                    dim = doc.GetElement(did)
                    if dim is None:
                        results[key] = u"LỖI: ràng buộc bị Revit xoá khi đóng sketch"
                    elif not (constraint_ref_ids(dim) & sk_now):
                        results[key] = u"LỖI: ràng buộc {} không trỏ vào cạnh sketch (tham chiếu {})".format(
                            id_value(did), u", ".join(str(i) for i in sorted(constraint_ref_ids(dim))))
                    else:
                        results[key] = u"Đã khoá (kiểm tra OK, ràng buộc {})".format(id_value(did))
                        n_verified += 1
        floor_ok = 0
        for mc, candidates, line in pairs:
            key = id_value(mc.Id)
            res = results.get(key, u"Sẽ khoá" if dry_run else u"Không thực hiện")
            if res.startswith(u"Đã khoá"):
                n_ok += 1
                floor_ok += 1
            elif res.startswith(u"LỖI"):
                n_err += 1
            w, ref, label, off = chosen.get(key, candidates[0])
            rows.append([id_value(fl.Id), comment, key, u"{:.0f}".format(to_mm(line.Length)),
                         id_value(w.Id), get_name(w), label, u"{:.1f}".format(off), res])
        if floor_ok or (dry_run and pairs):
            n_floor_ok += 1
        else:
            n_floor_none += 1

    # Báo cáo
    output.print_md(u"## {} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ" if dry_run else u"ĐÃ THỰC HIỆN"))
    output.print_md(u"File: **{}** – view: **{}** – {} sàn chọn, bỏ qua {}".format(
        doc.Title, view.Name, len(floors), n_skip))
    output.print_md(u"- Sàn có cạnh {}: **{}** – sàn không có cạnh nào khoá được: **{}**".format(
        u"sẽ khoá" if dry_run else u"đã khoá", n_floor_ok, n_floor_none))
    output.print_md(u"- Cạnh nằm trên mặt tường: **{}** ({})".format(
        n_match, u"sẽ khoá" if dry_run else u"đã khoá {} – kiểm tra trỏ đúng cạnh sketch {}, lỗi {}".format(
            n_ok, n_verified, n_err)))
    n_old = sum(len(p[3]) for p in plans)
    if n_old:
        output.print_md(u"- Khoá cũ trên các sàn này: **{}** ({})".format(
            n_old, u"sẽ xoá trước khi khoá lại" if dry_run else u"đã xoá"))
    output.print_md(u"- Cạnh không nằm trên mặt tường (giữ nguyên): **{}**".format(n_free))
    if not dry_run:
        output.print_md(u"- Mỗi sàn một bước Undo **{}**. Thử kéo một bức tường để kiểm tra sàn chạy theo.".format(
            TRANSACTION_NAME))
    try:
        output.print_md(u"- Log: `{}`".format(write_log(rows, dry_run)))
    except Exception as ex:
        output.print_md(u"- Không ghi được log: {}".format(ex))
    table_rows = [r for r in rows if r[4] != u"" or r[8].startswith(u"Bỏ qua")]
    if len(table_rows) > MAX_TABLE_ROWS:
        output.print_md(u"- Bảng chi tiết có {} dòng, xem trong file log.".format(len(table_rows)))
    else:
        output.print_table(table_rows, columns=LOG_HEADER)


main()
