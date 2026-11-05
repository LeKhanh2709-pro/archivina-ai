# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoTrucTuCSV_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo lưới trục (Grid) từ bản CAD đã Link/Import trong Revit.
#   - Đường trục: lấy từ layer trục của bản CAD, gộp các đoạn thẳng hàng, bỏ đoạn ngắn hơn 1 m.
#   - Tên trục: Revit API không đọc được chữ trong CAD, nên script gọi AutoCAD Core Console trên BẢN SAO
#     file DWG đang link, đọc attribute / TEXT / MTEXT trên layer ký hiệu trục rồi gán cho trục gần nhất.
#     Không có Core Console hoặc CAD dạng Import (không có file) → đánh tên tự động theo tiền tố:
#     trục đứng trái → phải, trục ngang trên → dưới.
# INPUT
#   IN[0] (str)  Một phần tên bản CAD (để trống nếu mô hình chỉ có 1 bản CAD)
#   IN[1] (str)  Layer trục, nhiều layer cách nhau dấu phẩy, khớp theo chuỗi con (mặc định "S-Truc")
#   IN[2] (str)  Layer ký hiệu trục chứa tên trục (mặc định "S-Kyhieu"; để trống = mọi layer)
#   IN[3] (bool) Dry-run: True = chỉ báo cáo, không ghi vào mô hình (mặc định True)
#   IN[4] (str)  Tiền tố tên trục đứng khi đánh tên tự động (mặc định "X")
#   IN[5] (str)  Tiền tố tên trục ngang khi đánh tên tự động (mặc định "Y")
# OUTPUT
#   OUT (list[str]) Báo cáo: dòng tóm tắt, nguồn tên trục, đường dẫn log, rồi từng trục:
#                   Tên | Loại | Điểm đầu | Điểm cuối | Kết quả | ElementId

import clr
import os
import io
import re
import csv
import glob
import shutil
import tempfile
import datetime
import subprocess

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, Grid, Line, Arc, PolyLine, XYZ,
                               GeometryInstance, Options, Transaction, UnitUtils, UnitTypeId,
                               ModelPathUtils, BuiltInParameter, CADLinkType)
clr.AddReference("RevitServices")
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager

doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = "ARV - Tạo lưới trục từ CAD"
MIN_LENGTH_MM = 1000.0       # Bỏ đoạn ngắn hơn giá trị này (nét ký hiệu, nét gạch)
COLLINEAR_TOL_MM = 1.0       # Sai số khoảng cách để coi hai đoạn là cùng một trục
ANGLE_TOL = 1e-4             # Sai số góc (rad) khi so sánh phương trục
LABEL_PERP_TOL_MM = 500.0    # Ký hiệu trục lệch khỏi đường trục tối đa
LABEL_END_TOL_MM = 3000.0    # Ký hiệu trục cách đầu trục tối đa
CORE_TIMEOUT_S = 180         # Thời gian chờ AutoCAD Core Console

cad_filter = (IN[0] or "").strip()
axis_layers = [s.strip().lower() for s in (IN[1] or "S-Truc").split(",") if s.strip()]
label_layer = (IN[2] or "").strip().lower()
dry_run = True if IN[3] is None else bool(IN[3])
prefix_v = (IN[4] or "X").strip()
prefix_h = (IN[5] or "Y").strip()


def to_mm(feet):
    return UnitUtils.ConvertFromInternalUnits(feet, UnitTypeId.Millimeters)


def from_mm(mm):
    return UnitUtils.ConvertToInternalUnits(mm, UnitTypeId.Millimeters)


def fmt_xy(p):
    return "({:.0f}, {:.0f})".format(to_mm(p.X), to_mm(p.Y))


def flatten(p):
    return XYZ(p.X, p.Y, 0)


def canonical_direction(p0, p1):
    d = p1.Subtract(p0).Normalize()
    # Chuẩn hoá chiều để hai đoạn ngược chiều vẫn được coi là cùng phương
    if d.X < -1e-9 or (abs(d.X) <= 1e-9 and d.Y < 0):
        d = d.Negate()
    return d


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def model_role(document):
    # Trường Bộ môn (Role) theo tên file ISO 19650: PRJ-ARV-T1-ZZ-M3-A-0001
    parts = (document.Title or "").split("-")
    return parts[5].upper() if len(parts) >= 7 else None


# --- Bản CAD -------------------------------------------------------------------------
def cad_type_name(inst):
    t = doc.GetElement(inst.GetTypeId())
    p = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME) if t else None
    return (p.AsString() if p else "") or ""


def pick_cad():
    instances = list(FilteredElementCollector(doc).OfClass(ImportInstance).ToElements())
    if cad_filter:
        instances = [i for i in instances if cad_filter.lower() in cad_type_name(i).lower()]
    if len(instances) == 1:
        return instances[0]
    if not instances:
        raise Exception(u"Không tìm thấy bản CAD nào{}.".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u" được Link/Import trong mô hình"))
    raise Exception(u"Tìm thấy {} bản CAD: {}. Nhập một phần tên vào ô 'Tên bản CAD' để chọn đúng 1 bản."
                    .format(len(instances), u"; ".join(cad_type_name(i) for i in instances)))


def cad_file_path(inst):
    link = doc.GetElement(inst.GetTypeId())
    if not inst.IsLinked or not isinstance(link, CADLinkType):
        return None
    try:
        ref = link.GetExternalFileReference()
        path = ModelPathUtils.ConvertModelPathToUserVisiblePath(ref.GetAbsolutePath())
    except Exception:
        return None
    return path if path and os.path.isfile(path) else None


def layer_name(geom_obj):
    style = doc.GetElement(geom_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return ""


def iter_cad_curves(geom_elem):
    # Duyệt toàn bộ curve (kể cả trong block lồng nhau), toạ độ mô hình
    for g in geom_elem:
        if isinstance(g, GeometryInstance):
            for item in iter_cad_curves(g.GetInstanceGeometry()):
                yield item
        elif isinstance(g, PolyLine):
            name = layer_name(g)
            pts = list(g.GetCoordinates())
            for p0, p1 in zip(pts[:-1], pts[1:]):
                # đoạn ngắn hơn dung sai của Revit (~0,8 mm) thì Line.CreateBound báo lỗi → bỏ qua
                if p0.DistanceTo(p1) > doc.Application.ShortCurveTolerance:
                    yield name, Line.CreateBound(p0, p1)
        elif isinstance(g, (Line, Arc)):
            yield layer_name(g), g


def on_axis_layer(name):
    n = (name or "").lower()
    return any(l in n for l in axis_layers)


# --- Gộp đoạn thẳng hàng -----------------------------------------------------------
class Axis(object):
    def __init__(self, d, offset, t0, t1):
        self.d, self.offset, self.t0, self.t1 = d, offset, t0, t1
        self.count = 1
        self.name = None
        self.note = u""

    @property
    def n(self):
        return XYZ(-self.d.Y, self.d.X, 0)

    def point_at(self, t):
        return self.n.Multiply(self.offset).Add(self.d.Multiply(t))

    @property
    def start(self):
        return self.point_at(self.t0)

    @property
    def end(self):
        return self.point_at(self.t1)

    @property
    def mid(self):
        return self.point_at((self.t0 + self.t1) / 2.0)

    @property
    def is_vertical(self):
        return abs(self.d.Y) > abs(self.d.X)


def merge_lines(lines, tol):
    axes = []
    for line in lines:
        p0, p1 = flatten(line.GetEndPoint(0)), flatten(line.GetEndPoint(1))
        d = canonical_direction(p0, p1)
        offset = p0.DotProduct(XYZ(-d.Y, d.X, 0))
        t0, t1 = sorted((p0.DotProduct(d), p1.DotProduct(d)))
        target = None
        for ax in axes:
            if abs(ax.d.CrossProduct(d).Z) < ANGLE_TOL and abs(ax.offset - offset) < tol:
                target = ax
                break
        if target is None:
            axes.append(Axis(d, offset, t0, t1))
        else:
            target.t0, target.t1 = min(target.t0, t0), max(target.t1, t1)
            target.count += 1
    return axes


# --- Đọc tên trục từ DWG bằng AutoCAD Core Console --------------------------------
def find_accoreconsole():
    found = glob.glob(r"C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe")
    return sorted(found)[-1] if found else None


def core_env(core):
    """Môi trường sạch cho AutoCAD Core Console. Gọi từ Revit, tiến trình con kế thừa Path có thư mục Revit 2026
    → Core Console nạp nhầm DLL của Revit, báo "Unable to load the Modeler DLLs" và thoát, không xuất file
    (đã kiểm 2026-10-19). Chỉ giữ biến hệ thống, Path = thư mục AutoCAD + Windows."""
    keep = ("SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "USERNAME",
            "USERDOMAIN", "PROGRAMDATA", "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "COMMONPROGRAMFILES",
            "COMMONPROGRAMFILES(X86)", "COMMONPROGRAMW6432", "ALLUSERSPROFILE", "COMPUTERNAME", "HOMEDRIVE",
            "HOMEPATH", "OS", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "PUBLIC", "COMSPEC", "PATHEXT")
    env = dict((k, v) for k, v in os.environ.items() if k.upper() in keep)
    root = env.get("SYSTEMROOT") or os.environ.get("SystemRoot") or r"C:\Windows"
    temp = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "Temp")
    env["TEMP"] = env["TMP"] = temp if os.path.isdir(temp) else tempfile.gettempdir()
    env["PATH"] = u";".join([os.path.dirname(core), os.path.join(root, "System32"), root,
                             os.path.join(root, "System32", "Wbem")])
    return env


def clean_mtext(s):
    s = re.sub(r"\\[A-Za-z][^;\\{}]*;", "", s)   # \fArial|b0;  \H2.5;  \C1; ...
    s = re.sub(r"\\[Pp~]", " ", s)
    return s.replace("{", "").replace("}", "").strip()


DUMP_LISP = u"""(setq f (open "{out}" "w" "utf8"))
(defun _w (k ly s p) (write-line (strcat k "|" ly "|" s "|" (rtos (car p) 2 3) "," (rtos (cadr p) 2 3)) f))
(if (setq ss (ssget "_X" '((0 . "INSERT,TEXT,MTEXT") (410 . "Model"))))
  (progn (setq i 0)
    (repeat (sslength ss)
      (setq e (ssname ss i) d (entget e) i (1+ i))
      (cond
        ((= (cdr (assoc 0 d)) "INSERT")
          (if (= (cdr (assoc 66 d)) 1)
            (progn (setq a (entnext e))
              (while (and a (= (cdr (assoc 0 (entget a))) "ATTRIB"))
                (_w "A" (cdr (assoc 8 d)) (cdr (assoc 1 (entget a))) (cdr (assoc 10 d)))
                (setq a (entnext a))))))
        ((= (cdr (assoc 0 d)) "TEXT")
          (_w "T" (cdr (assoc 8 d)) (cdr (assoc 1 d))
              (if (or (/= 0 (cdr (assoc 72 d))) (/= 0 (cdr (assoc 73 d)))) (cdr (assoc 11 d)) (cdr (assoc 10 d)))))
        ((= (cdr (assoc 0 d)) "MTEXT")
          (_w "M" (cdr (assoc 8 d)) (cdr (assoc 1 d)) (cdr (assoc 10 d))))))))
(close f)
"""


def read_dwg_labels(dwg_path, core):
    # Chạy trên bản sao trong thư mục tạm – không mở / không ghi file DWG gốc
    work = tempfile.mkdtemp(prefix="ARV_TaoTruc_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "labels.txt")
        scr = os.path.join(work, "dump.scr")
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được danh sách chữ")
        labels = []
        with io.open(out, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f.read().splitlines():
                parts = line.split("|")
                if len(parts) < 4:
                    continue
                kind, layer, xy = parts[0], parts[1], parts[-1]
                text = u"|".join(parts[2:-1])
                if kind == "M":
                    text = clean_mtext(text)
                try:
                    x, y = [float(v) for v in xy.split(",")]
                except ValueError:
                    continue
                if text.strip():
                    labels.append((layer, text.strip(), x, y))
        return labels
    finally:
        shutil.rmtree(work, ignore_errors=True)


def assign_names(axes, labels, transform):
    perp_tol, end_tol = from_mm(LABEL_PERP_TOL_MM), from_mm(LABEL_END_TOL_MM)
    pts = []
    for layer, text, x, y in labels:
        if label_layer and label_layer not in layer.lower():
            continue
        pts.append((text, flatten(transform.OfPoint(XYZ(from_mm(x), from_mm(y), 0)))))
    for ax in axes:
        names = []
        for text, p in pts:
            if abs(p.DotProduct(ax.n) - ax.offset) > perp_tol:
                continue
            t = p.DotProduct(ax.d)
            if min(abs(t - ax.t0), abs(t - ax.t1)) <= end_tol and text not in names:
                names.append(text)
        if len(names) == 1:
            ax.name = names[0]
        elif len(names) > 1:
            ax.note = u"nhiều tên: " + u", ".join(names)
    return len(pts)


def auto_names(axes):
    vertical = sorted([a for a in axes if a.is_vertical], key=lambda a: a.mid.X)
    horizontal = sorted([a for a in axes if not a.is_vertical], key=lambda a: -a.mid.Y)
    for i, ax in enumerate(vertical):
        ax.name = u"{}{}".format(prefix_v, i + 1)
    for i, ax in enumerate(horizontal):
        ax.name = u"{}{}".format(prefix_h, i + 1)


# --- Log ------------------------------------------------------------------------------
def write_log(rows, source):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoTrucTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    # CSV UTF-8 có BOM để Excel đọc đúng tiếng Việt
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Bản CAD: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow([u"Tên trục", u"Loại", u"Điểm đầu (mm)", u"Điểm cuối (mm)", u"Kết quả",
                    u"ElementId", u"Giá trị cũ", u"Giá trị mới"])
        w.writerows(rows)
    return path


def main():
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."]

    warnings = []
    if model_role(doc) == "A":
        warnings.append(u"CẢNH BÁO: đây có vẻ là mô hình Kiến trúc (A). Grid do Kết cấu (S) làm chủ, "
                        u"Kiến trúc nên dùng Copy/Monitor.")

    cad = pick_cad()
    cad_name = cad_type_name(cad)
    geom = cad.get_Geometry(Options())
    if geom is None:
        return [u"DỪNG: không đọc được hình học của bản CAD '{}'.".format(cad_name)]

    min_len, tol = from_mm(MIN_LENGTH_MM), from_mm(COLLINEAR_TOL_MM)
    lines, layers_seen, arcs = [], set(), 0
    for name, c in iter_cad_curves(geom):
        layers_seen.add(name)
        if not on_axis_layer(name):
            continue
        if isinstance(c, Line) and c.Length >= min_len:
            lines.append(c)
        elif isinstance(c, Arc) and c.IsBound:
            arcs += 1
    if not lines:
        return [u"DỪNG: không có đường trục nào trên layer '{}' của bản CAD '{}'. Layer có trong bản CAD: {}"
                .format(u", ".join(axis_layers), cad_name, u", ".join(sorted(layers_seen)))]
    axes = merge_lines(lines, tol)

    # Tên trục
    dwg = cad_file_path(cad)
    core = find_accoreconsole()
    if dwg and core:
        try:
            labels = read_dwg_labels(dwg, core)
            used = assign_names(axes, labels, cad.GetTotalTransform())
            source = u"đọc từ DWG ({} chữ trên layer ký hiệu, Core Console: {})".format(used, core)
        except Exception as ex:
            auto_names(axes)
            source = u"tự động theo tiền tố – không đọc được DWG: {}".format(ex)
    else:
        auto_names(axes)
        source = u"tự động theo tiền tố ({})".format(
            u"không tìm thấy AutoCAD Core Console" if not core else u"bản CAD dạng Import / không thấy file DWG")

    existing, existing_names = [], set()
    for g in FilteredElementCollector(doc).OfClass(Grid).ToElements():
        existing_names.add(g.Name)
        c = g.Curve
        if isinstance(c, Line):
            p0, p1 = flatten(c.GetEndPoint(0)), flatten(c.GetEndPoint(1))
            d = canonical_direction(p0, p1)
            existing.append((g, d, p0.DotProduct(XYZ(-d.Y, d.X, 0))))

    vertical = sorted([a for a in axes if a.is_vertical], key=lambda a: a.mid.X)
    horizontal = sorted([a for a in axes if not a.is_vertical], key=lambda a: -a.mid.Y)
    rows, to_create, planned = [], [], set()
    for kind, group in ((u"Trục đứng", vertical), (u"Trục ngang", horizontal)):
        for ax in group:
            match = None
            for g, gd, goffset in existing:
                if abs(gd.CrossProduct(ax.d).Z) < ANGLE_TOL and abs(goffset - ax.offset) < tol:
                    match = g
                    break
            name, eid = ax.name, u""
            if not name:
                name = u"?"
                result = u"Bỏ qua – " + (ax.note or u"không tìm thấy ký hiệu tên trục")
            elif name in planned:
                result = u"Bỏ qua – tên '{}' trùng với trục khác trong bản CAD".format(name)
            elif match is not None:
                result = u"Bỏ qua – trùng trục có sẵn '{}'".format(match.Name)
                eid = match.Id.Value
            elif name in existing_names:
                result = u"Bỏ qua – tên '{}' đã có ở vị trí khác".format(name)
            else:
                result = u"Sẽ tạo" if dry_run else u"Chờ tạo"
                planned.add(name)
                to_create.append((name, ax, len(rows)))
            rows.append([name, kind, fmt_xy(ax.start), fmt_xy(ax.end), result, eid, u"—", name])

    if not dry_run and to_create:
        # Đóng transaction của Dynamo để dùng Transaction có tên riêng (Undo được trong Revit)
        TransactionManager.Instance.ForceCloseTransaction()
        t = Transaction(doc, TRANSACTION_NAME)
        t.Start()
        try:
            for name, ax, idx in to_create:
                grid = Grid.Create(doc, Line.CreateBound(ax.start, ax.end))
                grid.Name = name
                rows[idx][4] = u"Đã tạo"
                rows[idx][5] = grid.Id.Value
            t.Commit()
        except Exception as ex:
            t.RollBack()
            return warnings + [u"LỖI khi tạo lưới trục, mọi thay đổi đã được hoàn tác: {}".format(ex)]

    created = sum(1 for r in rows if r[4] in (u"Sẽ tạo", u"Đã tạo"))
    summary = u"{} – {}: bản CAD '{}', {} đoạn → {} trục, {} {}, {} bỏ qua.".format(
        TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN",
        cad_name, len(lines), len(rows), created, u"sẽ tạo" if dry_run else u"đã tạo", len(rows) - created)
    if arcs:
        warnings.append(u"CẢNH BÁO: {} cung tròn trên layer trục không được xử lý (chỉ hỗ trợ trục thẳng).".format(arcs))
    try:
        log_line = u"Log: " + write_log(rows, cad_name)
    except Exception as ex:
        log_line = u"Không ghi được file log: {}".format(ex)
    return warnings + [summary, u"Tên trục: " + source, log_line] + \
        [u" | ".join(u"{}".format(v) for v in r[:6]) for r in rows]


try:
    OUT = main()
except Exception as ex:
    OUT = [u"LỖI: {}".format(ex)]
