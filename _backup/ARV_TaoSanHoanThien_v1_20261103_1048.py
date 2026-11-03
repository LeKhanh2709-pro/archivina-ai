# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoSanHoanThien_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo sàn hoàn thiện (Floor) cho từng CĂN HỘ theo bản CAD mặt bằng lát sàn đã Link (chuẩn CAD công ty):
#   1. Đọc bản sao DWG qua AutoCAD Core Console (model space + block lồng nhau):
#        - polyline kín layer bo phòng (IN[2], mặc định "A-duong bo phong") = biên sàn hoàn thiện từng phòng;
#        - polyline kín layer căn hộ (IN[3], mặc định "A-Area") = phạm vi căn;
#        - hatch layer lát sàn (IN[4], mặc định "A-Hoan thien san"): mẫu hatch → loại phòng (IN[5]),
#          hatch AR-CONC = đá chân cửa FP-06 (cửa WC, cửa vào căn).
#   2. Phạm vi: phần tử đang chọn trong Revit (hoặc Id ở IN[1]) – thường chọn CỬA VÀO CĂN. Căn = polyline IN[3]
#      chứa phía trong cửa (hoặc chứa điểm của phần tử). Không có layer căn → lan từ phòng chứa điểm qua các cửa
#      Revit, không đi qua cửa vào căn (IN[8]).
#   3. Mỗi phòng một tấm sàn: type + cao độ theo loại (IN[6], IN[7]; mặc định khô 0 / WC −15 / logia −30).
#      Phòng không có hatch trong IN[5] → "chưa rõ loại", không tạo.
#   4. Ô cửa (đo trên hình khối tường Revit, không theo tham số family):
#        - hai bên đều phòng khô (cửa phòng ngủ) → sàn mỗi bên kéo vào ô cửa tới tim tường;
#        - một bên logia, một bên phòng khô       → sàn trong nhà phủ hết ô tường, sàn logia dừng ở bo phòng;
#        - cửa WC / cửa vào căn                    → không kéo sàn; tấm đá chân cửa lấy theo hatch AR-CONC của CAD
#          (thiếu hatch → báo "thiếu đá chân cửa").
#   5. Bỏ qua phòng / ô đá đã có sàn (cùng level). Comments = "ARV-SanHoanThien".
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất trong mô hình)
#   IN[1] (str)   Id phần tử trong căn, cách nhau ';' (để trống = các phần tử đang chọn trong Revit)
#   IN[2] (str)   Lọc layer đường bo phòng (khớp chuỗi con, VD "A-duong bo phong")
#   IN[3] (str)   Lọc layer polyline căn hộ (VD "A-Area"; để trống = lan theo cửa)
#   IN[4] (str)   Lọc layer hatch lát sàn (VD "A-Hoan thien san")
#   IN[5] (str)   Mẫu hatch = loại: "WOODS_BOARD_WIDE=KHO;300X600=WC;2X4=LOGIA;AR-CONC=CHANCUA"
#   IN[6] (str)   Floor type theo loại: "KHO=…;WC=…;LOGIA=…;CHANCUA=FF-Đá Granite tự nhiên"
#   IN[7] (str)   Cao độ mặt sàn so với Level (mm) theo loại: "KHO=0;WC=-15;LOGIA=-30;CHANCUA=0"
#   IN[8] (str)   Nhận cửa vào căn theo tên family/type, cách nhau ';' (VD "khóa thông minh;DW03")
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
#   IN[10] (str)  Floor type kiến trúc mẫu: type ở IN[6] chưa có → nhân bản từ type này (giữ cấu tạo lớp; đá chân
#                 cửa đổi vật liệu lớp hoàn thiện sang vật liệu có tên chứa "granite" nếu mô hình có). Trống = dừng.
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng phòng / ô cửa
#   OUT[1] (list[Line]) Xem trước: biên các tấm sàn sẽ tạo (mm, tại cao độ Level)

import os
import io
import csv
import glob
import math
import shutil
import tempfile
import datetime
import subprocess
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, CADLinkType, XYZ, Line, CurveLoop,
                                   Transaction, UnitUtils, UnitTypeId, ModelPathUtils, BuiltInParameter,
                                   BuiltInCategory, Floor, FloorType, Wall, LocationCurve, LocationPoint,
                                   FamilyInstance, Options, ViewDetailLevel, Solid, GeometryInstance, ElementId,
                                   SolidCurveIntersectionOptions, SolidCurveIntersectionMode, PlanarFace,
                                   GeometryCreationUtilities, BooleanOperationsUtils, BooleanOperationsType,
                                   HostObjectUtils, Face, ViewType, Material, MaterialFunctionAssignment)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Tạo sàn hoàn thiện"
SCRIPT_TAG = u"ARV_TaoSanHoanThien_v1"
COMMENT_TAG = u"ARV-SanHoanThien"
KINDS = ("KHO", "WC", "LOGIA", "CHANCUA")
KIND_LABEL = {"KHO": u"Phòng khô", "WC": u"WC", "LOGIA": u"Logia", "CHANCUA": u"Đá chân cửa"}
ARC_STEP_DEG = 10.0
CORE_TIMEOUT_S = 180
DUP_PT_MM = 1.0           # Đỉnh polyline trùng
INNER_MM = 20.0           # Điểm đại diện phòng: lùi vào trong từ trung điểm cạnh
SIDE_PROBE_MM = 300.0     # Điểm dò hai bên cửa cách mặt tường
STRIP_OVERLAP_MM = 30.0   # Dải ô cửa chồng vào phòng (bù lệch giữa mặt tường Revit và bo phòng CAD)
THRESHOLD_NEAR_MM = 100.0 # Ô đá chân cửa cách bo phòng của căn ≤ giá trị này → thuộc căn
PROBE_Z_MM = 300.0        # Cao độ tia dò ô cửa (trên Level)
MIN_OPENING_MM = 300.0
MAX_OPENING_MM = 4000.0
SCAN_MM = 5000.0          # Nửa chiều dài tia dò dọc tường
TOL_MM = 1.0


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
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


def point_in_evenodd(pt, loops):
    return sum(1 for l in loops if point_in(pt, l)) % 2 == 1


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def poly_dist(p1, p2):
    """Khoảng cách nhỏ nhất giữa hai đa giác (0 nếu chồng nhau)."""
    if point_in(p1[0], p2) or point_in(p2[0], p1):
        return 0.0
    best = float("inf")
    for a, b in ((p1, p2), (p2, p1)):
        for p in a:
            for i in range(len(b)):
                best = min(best, seg_dist(p, b[i], b[(i + 1) % len(b)]))
    return best


def clean_poly(pts):
    """Bỏ đỉnh trùng / thẳng hàng, đưa về ngược chiều kim đồng hồ."""
    out = []
    for p in pts:
        if not out or math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > DUP_PT_MM:
            out.append(p)
    if len(out) > 1 and math.hypot(out[0][0] - out[-1][0], out[0][1] - out[-1][1]) <= DUP_PT_MM:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            ab = math.hypot(b[0] - a[0], b[1] - a[1])
            if ab > 0 and abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / ab < 0.1:
                if (b[0] - a[0]) * (c[0] - b[0]) + (b[1] - a[1]) * (c[1] - b[1]) > 0:
                    out.pop(i)
                    changed = True
                    break
    if len(out) >= 3 and signed_area(out) < 0:
        out.reverse()
    return out


def interior_point(pts):
    """Điểm chắc chắn nằm trong đa giác (CCW): trung điểm cạnh dài nhất lùi vào trong INNER_MM."""
    edges = sorted(range(len(pts)), key=lambda i: -math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0],
                                                              pts[(i + 1) % len(pts)][1] - pts[i][1]))
    for i in edges:
        a, b = pts[i], pts[(i + 1) % len(pts)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l < 3 * INNER_MM:
            continue
        p = ((a[0] + b[0]) / 2.0 - (b[1] - a[1]) / l * INNER_MM, (a[1] + b[1]) / 2.0 + (b[0] - a[0]) / l * INNER_MM)
        if point_in(p, pts):
            return p
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def parse_map(text, upper_key=True):
    result = {}
    for part in (text or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            k = k.strip().upper() if upper_key else k.strip()
            if k:
                result[k] = v.strip()
    return result


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def split_filters(text):
    return [s.strip() for s in (text or u"").split(u";") if s.strip()]


def matches(layer, filters):
    l = (layer or u"").lower()
    return any(f.lower() in l for f in filters)


# --- Đọc DWG qua Core Console ---------------------------------------------------------
def _xy(v):
    parts = v.split(",")
    return float(parts[0]), float(parts[1])


def _arc(c, r, s, e, ccw):
    """Cung tròn biên hatch (độ) → các điểm. Cung thuận chiều kim đồng hồ: góc lưu dạng đảo (360 - góc)."""
    if ccw:
        while e <= s:
            e += 360.0
    else:
        s, e = 360.0 - s, 360.0 - e
        while e >= s:
            e -= 360.0
    n = max(2, int(math.ceil(abs(e - s) / ARC_STEP_DEG)))
    return [(c[0] + r * math.cos(math.radians(s + (e - s) * i / n)), c[1] + r * math.sin(math.radians(s + (e - s) * i / n)))
            for i in range(n + 1)]


def _bulge(p, q, b):
    """Đoạn polyline có bulge → các điểm từ p tới q (không gồm q)."""
    if abs(b) < 1e-9:
        return [p]
    sweep = 4.0 * math.atan(b)
    d = math.hypot(q[0] - p[0], q[1] - p[1])
    if d < 1e-9:
        return [p]
    r = d / (2.0 * math.sin(abs(sweep) / 2.0))
    mx, my = (p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0
    h = math.sqrt(max(r * r - d * d / 4.0, 0.0)) * (1 if abs(sweep) <= math.pi else -1)
    nx, ny = -(q[1] - p[1]) / d, (q[0] - p[0]) / d
    s = 1 if b > 0 else -1
    cx, cy = mx + s * nx * h, my + s * ny * h
    a0 = math.atan2(p[1] - cy, p[0] - cx)
    n = max(2, int(math.ceil(math.degrees(abs(sweep)) / ARC_STEP_DEG)))
    return [(cx + r * math.cos(a0 + sweep * i / n), cy + r * math.sin(a0 + sweep * i / n)) for i in range(n)]


def _mirrored(codes):
    for k, v in codes:
        if k == 210:
            parts = v.split(",")
            return len(parts) > 2 and float(parts[2]) < 0
    return False


def parse_hatch(codes):
    """codes: [(mã, chuỗi)] của HATCH. Trả về (pattern, [vòng [(x, y)]] theo OCS)."""
    pattern, i = None, 0
    mirror = _mirrored(codes)
    while i < len(codes) and codes[i][0] != 91:
        if codes[i][0] == 2 and pattern is None:
            pattern = codes[i][1]
        i += 1
    if i >= len(codes):
        raise ValueError(u"không có biên")
    npath = int(codes[i][1])
    i += 1
    loops = []
    for _ in range(npath):
        flag = int(codes[i][1])
        i += 1
        pts = []
        if flag & 2:
            hasb = int(codes[i][1])
            n = int(codes[i + 2][1])
            i += 3
            verts = []
            for _ in range(n):
                p = _xy(codes[i][1])
                i += 1
                b = 0.0
                if hasb and i < len(codes) and codes[i][0] == 42:
                    b = float(codes[i][1])
                    i += 1
                verts.append((p, b))
            for k in range(len(verts)):
                pts += _bulge(verts[k][0], verts[(k + 1) % len(verts)][0], verts[k][1])
        else:
            n = int(codes[i][1])
            i += 1
            for _ in range(n):
                t = int(codes[i][1])
                i += 1
                if t == 1:
                    pts.append(_xy(codes[i][1]))
                    i += 2
                elif t == 2:
                    c, r = _xy(codes[i][1]), float(codes[i + 1][1])
                    s, e, ccw = float(codes[i + 2][1]), float(codes[i + 3][1]), int(codes[i + 4][1])
                    pts += _arc(c, r, s, e, ccw)[:-1]
                    i += 5
                else:
                    raise ValueError(u"biên hatch có cạnh {} (ellipse/spline) chưa hỗ trợ".format(
                        u"ellipse" if t == 3 else u"spline"))
        while i < len(codes) and codes[i][0] == 97:
            i += 1
        if mirror:
            pts = [(-x, y) for x, y in pts]
        if len(pts) >= 3:
            loops.append(pts)
    return pattern, loops


def parse_lwpolyline(codes):
    """codes của LWPOLYLINE → ([(x, y)] theo OCS, kín?)."""
    closed = False
    verts = []
    for k, v in codes:
        if k == 70:
            closed = bool(int(v) & 1)
        elif k == 10:
            verts.append([_xy(v), 0.0])
        elif k == 42 and verts:
            verts[-1][1] = float(v)
    pts = []
    for i in range(len(verts)):
        if not closed and i == len(verts) - 1:
            pts.append(verts[i][0])
            break
        pts += _bulge(verts[i][0], verts[(i + 1) % len(verts)][0], verts[i][1])
    if not closed and len(pts) > 2 and math.hypot(pts[0][0] - pts[-1][0], pts[0][1] - pts[-1][1]) <= DUP_PT_MM:
        closed = True
    if _mirrored(codes):
        pts = [(-x, y) for x, y in pts]
    return pts, closed


# Đọc HATCH + LWPOLYLINE (lọc layer bằng wcmatch) ở model space VÀ trong block (lồng nhau, tối đa 8 cấp),
# kèm ma trận affine (a b c d e f) của INSERT cha. Đối tượng trên layer "0" trong block lấy layer INSERT cha.
DUMP_LISP = u"""(setq f (open "{out}" "w" "utf8") pat "{pat}")
(defun _ap (m p) (list (+ (* (nth 0 m) (car p)) (* (nth 1 m) (cadr p)) (nth 4 m))
                       (+ (* (nth 2 m) (car p)) (* (nth 3 m) (cadr p)) (nth 5 m))))
(defun _mul (p c) (list (+ (* (nth 0 p) (nth 0 c)) (* (nth 1 p) (nth 2 c)))
                        (+ (* (nth 0 p) (nth 1 c)) (* (nth 1 p) (nth 3 c)))
                        (+ (* (nth 2 p) (nth 0 c)) (* (nth 3 p) (nth 2 c)))
                        (+ (* (nth 2 p) (nth 1 c)) (* (nth 3 p) (nth 3 c)))
                        (+ (* (nth 0 p) (nth 4 c)) (* (nth 1 p) (nth 5 c)) (nth 4 p))
                        (+ (* (nth 2 p) (nth 4 c)) (* (nth 3 p) (nth 5 c)) (nth 5 p))))
(defun _ins (d / a sx sy ip bp ca sa m)
  (setq a (cdr (assoc 50 d)) sx (cdr (assoc 41 d)) sy (cdr (assoc 42 d)) ip (cdr (assoc 10 d))
        bp (cdr (assoc 10 (tblsearch "BLOCK" (cdr (assoc 2 d))))) ca (cos a) sa (sin a))
  (setq m (list (* ca sx) (- (* sa sy)) (* sa sx) (* ca sy) 0.0 0.0) bp (_ap m bp))
  (list (nth 0 m) (nth 1 m) (nth 2 m) (nth 3 m) (- (car ip) (car bp)) (- (cadr ip) (cadr bp))))
(defun _lay (d parent / l) (setq l (cdr (assoc 8 d))) (if (and parent (= l "0")) parent l))
(defun _v (x) (cond ((= (type x) 'REAL) (rtos x 2 6)) ((= (type x) 'INT) (itoa x)) ((= (type x) 'STR) x)
                    ((and (= (type x) 'LIST) (numberp (car x)))
                      (strcat (rtos (car x) 2 6) "," (rtos (cadr x) 2 6) (if (caddr x) (strcat "," (rtos (caddr x) 2 6)) "")))
                    (T "?")))
(defun _out (tag keys d m lay / s)
  (if (wcmatch (strcase lay) pat)
    (progn
      (setq s (strcat tag "|" lay "|" (rtos (nth 0 m) 2 9) "," (rtos (nth 1 m) 2 9) "," (rtos (nth 2 m) 2 9) ","
                      (rtos (nth 3 m) 2 9) "," (rtos (nth 4 m) 2 6) "," (rtos (nth 5 m) 2 6) "|"))
      (foreach g d (if (member (car g) keys) (setq s (strcat s (itoa (car g)) "=" (_v (cdr g)) ";"))))
      (write-line s f))))
(defun _ent (d m parent depth / typ)
  (setq typ (cdr (assoc 0 d)))
  (cond ((= typ "HATCH") (_out "H" '(2 91 92 93 72 73 10 11 40 42 50 51 97 210) d m (_lay d parent)))
        ((= typ "LWPOLYLINE") (_out "P" '(70 10 42 210) d m (_lay d parent)))
        ((and (= typ "INSERT") (< depth 8))
          (_walk (cdr (assoc 2 d)) (_mul m (_ins d)) (_lay d parent) (1+ depth)))))
(defun _walk (name m parent depth / e)
  (setq e (cdr (assoc -2 (tblsearch "BLOCK" name))))
  (while e (_ent (entget e) m parent depth) (setq e (entnext e))))
(if (setq ss (ssget "_X" '((0 . "HATCH,LWPOLYLINE,INSERT") (410 . "Model"))))
  (progn (setq i 0)
    (repeat (sslength ss)
      (_ent (entget (ssname ss i)) '(1.0 0.0 0.0 1.0 0.0 0.0) nil 0)
      (setq i (1+ i)))))
(close f)
"""


def wc_escape(text):
    return u"".join(u"`" + ch if ch in u"#@.*?~[]," else ch for ch in text.upper())


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


def read_dwg(dwg_path, core, layer_filters):
    """Đọc hatch + polyline của các layer khớp chuỗi con. Trả về (hatches, polylines, lỗi), toạ độ DWG:
    hatches = [(layer, pattern, [vòng])], polylines = [(layer, [(x, y)])] (chỉ polyline kín)."""
    work = tempfile.mkdtemp(prefix="ARV_SanHT_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "dump.txt")
        scr = os.path.join(work, "dump.scr")
        pat = u",".join(u"*" + wc_escape(f) + u"*" for f in layer_filters)
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")).replace("{pat}", pat))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được dữ liệu bản vẽ")
        with io.open(out, "r", encoding="utf-8-sig", errors="replace") as f:
            return parse_dump(f.read().splitlines())
    finally:
        shutil.rmtree(work, ignore_errors=True)


def parse_dump(lines):
    hatches, polys, errors = [], [], []
    for line in lines:
        parts = line.split("|", 3)
        if len(parts) < 4 or parts[0] not in ("H", "P"):
            continue
        layer = parts[1]
        try:
            a, b, c, d, e, g = [float(v) for v in parts[2].split(",")]
            codes = []
            for kv in parts[3].split(";"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    codes.append((int(k), v))
            if parts[0] == "H":
                pattern, loops = parse_hatch(codes)
                loops = [[(a * x + b * y + e, c * x + d * y + g) for x, y in l] for l in loops]
                hatches.append((layer, (pattern or u"").upper(), loops))
            else:
                pts, closed = parse_lwpolyline(codes)
                if closed and len(pts) >= 3:
                    polys.append((layer, [(a * x + b * y + e, c * x + d * y + g) for x, y in pts]))
        except Exception as ex:
            errors.append((layer, u"{}".format(ex)))
    return hatches, polys, errors


# --- Phân tích căn hộ (thuần, mm) -----------------------------------------------------
class Room(object):
    def __init__(self, idx, pts):
        self.idx = idx
        self.pts = clean_poly(pts)
        self.area = abs(signed_area(self.pts)) / 1e6
        self.ip = interior_point(self.pts)
        self.kind = None
        self.pattern = u""
        self.note = u""
        self.strips = []      # dải ô cửa (feet, do phần Revit thêm)
        self.status = u""
        self.ids = []
        self.floor_area = 0.0


def classify_rooms(rooms, hatches, pattern_map):
    """Gán loại phòng theo mẫu hatch phủ điểm đại diện. Trả về danh sách ô đá chân cửa [(pts, pattern)]."""
    thresholds = []
    floor_hatches = []
    for layer, pattern, loops in hatches:
        kind = pattern_map.get(pattern)
        if kind == "CHANCUA":
            for l in loops:
                thresholds.append(clean_poly(l))
        elif kind in KINDS:
            floor_hatches.append((pattern, kind, loops))
    for r in rooms:
        found = [(p, k) for p, k, loops in floor_hatches if point_in_evenodd(r.ip, loops)]
        kinds = sorted(set(k for _, k in found))
        if len(kinds) == 1:
            r.kind, r.pattern = kinds[0], found[0][0]
        elif len(kinds) > 1:
            r.note = u"Nhiều mẫu hatch khác loại: {}".format(u", ".join(sorted(set(p for p, _ in found))))
        else:
            r.note = u"Không có hatch lát sàn trong IN[5]"
    return [t for t in thresholds if len(t) >= 3]


def apartment_rooms(rooms, areas, seeds, door_links):
    """rooms: [Room]; areas: [[(x, y)]] polyline căn; seeds: [[(x, y)]] các điểm dò của từng phần tử chọn;
    door_links: [(i, j)] cặp phòng nối bởi cửa (không gồm cửa vào căn).
    Trả về (danh sách chỉ số phòng thuộc căn, cách xác định, cảnh báo)."""
    chosen, how, warn = set(), [], []
    for pts in seeds:
        area = None
        for p in pts:
            hit = [a for a in areas if point_in(p, a)]
            if hit:
                area = min(hit, key=lambda a: abs(signed_area(a)))
                break
        if area is not None:
            got = [r.idx for r in rooms if point_in(r.ip, area)]
            chosen.update(got)
            how.append(u"polyline căn ({} phòng)".format(len(got)))
            continue
        start = [r.idx for r in rooms for p in pts if point_in(p, r.pts)]
        if not start:
            warn.append(u"Điểm {} không nằm trong căn / phòng nào".format(fmt(pts[0])))
            continue
        adj = {}
        for i, j in door_links:
            adj.setdefault(i, set()).add(j)
            adj.setdefault(j, set()).add(i)
        seen, stack = set(start[:1]), list(start[:1])
        while stack:
            i = stack.pop()
            for j in adj.get(i, ()):
                if j not in seen:
                    seen.add(j)
                    stack.append(j)
        chosen.update(seen)
        how.append(u"lan theo cửa ({} phòng)".format(len(seen)))
    return sorted(chosen), how, warn


def door_action(kind_a, kind_b, is_entry):
    """Cách xử lý ô cửa theo loại hai bên (None = vùng ngoài căn / chưa rõ).
    Trả về (mã, mô tả): STRIP_BOTH / STRIP_A / STRIP_B / THRESHOLD / NONE."""
    kinds = (kind_a, kind_b)
    if "WC" in kinds or is_entry:
        return "THRESHOLD", u"Cửa WC / cửa vào căn – đá chân cửa theo hatch CAD, sàn hai bên dừng ở bo phòng"
    if kind_a is not None and kind_a == kind_b:
        return "STRIP_BOTH", u"Sàn hai bên kéo vào ô cửa tới tim tường"
    if set(kinds) == set(["KHO", "LOGIA"]):
        return ("STRIP_A" if kind_a == "KHO" else "STRIP_B"), \
            u"Sàn trong nhà phủ hết ô tường, sàn logia dừng ở bo phòng"
    return "NONE", u"Không xử lý – một bên ngoài căn hoặc chưa rõ loại"


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


def pick_cad(cad_filter):
    all_cad = list(FilteredElementCollector(doc).OfClass(ImportInstance).ToElements())
    instances = all_cad
    if cad_filter:
        instances = [i for i in all_cad if cad_filter.lower() in get_name(doc.GetElement(i.GetTypeId())).lower()]
    if len(instances) != 1:
        names = [get_name(doc.GetElement(i.GetTypeId())) for i in all_cad]
        raise StopReport([u"DỪNG: tìm thấy {} bản CAD khớp '{}'. Nhập tên bản CAD vào ô IN[0]. Các bản CAD: {}".format(
            len(instances), cad_filter, u", ".join(names) or u"không có")])
    return instances[0]


def cad_file_path(inst):
    link = doc.GetElement(inst.GetTypeId())
    if not inst.IsLinked or not isinstance(link, CADLinkType):
        return None
    try:
        path = ModelPathUtils.ConvertModelPathToUserVisiblePath(link.GetExternalFileReference().GetAbsolutePath())
    except Exception:
        return None
    return path if path and os.path.isfile(path) else None


def floor_types_by_name():
    return dict((norm(type_name(t)), t) for t in FilteredElementCollector(doc).OfClass(FloorType).ToElements())


MATERIAL_HINT = {"CHANCUA": u"granite"}   # Loại → chuỗi con tên vật liệu gán cho lớp hoàn thiện của type nhân bản


def hint_material(kind):
    hint = MATERIAL_HINT.get(kind)
    if not hint:
        return None
    mats = [m for m in FilteredElementCollector(doc).OfClass(Material).ToElements() if hint in norm(m.Name).lower()]
    return sorted(mats, key=lambda m: len(m.Name))[0] if mats else None


def duplicate_floor_type(template, name, kind):
    """Nhân bản floor type kiến trúc mẫu thành `name`, giữ cấu tạo lớp; đổi vật liệu lớp hoàn thiện theo MATERIAL_HINT.
    Gọi trong Transaction."""
    new = template.Duplicate(name)
    mat = hint_material(kind)
    if mat is not None:
        cs = new.GetCompoundStructure()
        if cs is not None and cs.LayerCount > 0:
            finish = [i for i in range(cs.LayerCount) if cs.GetLayerFunction(i) in (
                MaterialFunctionAssignment.Finish1, MaterialFunctionAssignment.Finish2)]
            cs.SetMaterialId(finish[0] if finish else 0, mat.Id)
            new.SetCompoundStructure(cs)
    return new


# --- Ô cửa (Revit) ----------------------------------------------------------------
SCI_OPT = None


def element_solids(element):
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    result = []

    def walk(geo):
        for g in geo:
            if isinstance(g, Solid) and g.Volume > 0:
                result.append(g)
            elif isinstance(g, GeometryInstance):
                walk(g.GetInstanceGeometry())

    geo = element.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def ray_hits(solids, a, b):
    """Các đoạn [t0, t1] (feet, tính từ a) của tia a→b nằm trong khối, đã gộp."""
    global SCI_OPT
    if SCI_OPT is None:
        SCI_OPT = SolidCurveIntersectionOptions()
        SCI_OPT.ResultType = SolidCurveIntersectionMode.CurveSegmentsInside
    line = Line.CreateBound(a, b)
    spans = []
    for s in solids:
        try:
            res = s.IntersectWithCurve(line, SCI_OPT)
        except Exception:
            continue
        for i in range(res.SegmentCount):
            c = res.GetCurveSegment(i)
            t0, t1 = c.GetEndPoint(0).DistanceTo(a), c.GetEndPoint(1).DistanceTo(a)
            spans.append((min(t0, t1), max(t0, t1)))
    spans.sort()
    tol = from_mm(TOL_MM)
    merged = []
    for s in spans:
        if merged and s[0] <= merged[-1][1] + tol:
            merged[-1] = (merged[-1][0], max(merged[-1][1], s[1]))
        else:
            merged.append(s)
    return merged


class Opening(object):
    """Ô cửa: tim (giữa ô, trên tim tường), u dọc tường, n pháp tuyến, nửa dày h, ô s0..s1 (feet)."""

    def __init__(self, door):
        self.door = door
        self.center = self.u = self.n = None
        self.h = self.s0 = self.s1 = 0.0
        self.note = u""
        self.sides = [None, None]   # chỉ số phòng phía +n, phía -n

    def label(self):
        sym = self.door.Symbol
        return u"{} : {}".format(sym.FamilyName, type_name(sym))

    def side_points_mm(self):
        pts = []
        for sign in (1.0, -1.0):
            p = self.center.Add(self.n.Multiply(sign * (self.h + from_mm(SIDE_PROBE_MM))))
            pts.append((to_mm(p.X), to_mm(p.Y)))
        return pts


def measure_opening(door, level):
    """Đo ô cửa trên hình khối tường chủ. Trả về Opening hoặc None."""
    op = Opening(door)
    wall = door.Host
    if not isinstance(wall, Wall):
        return None
    loc = wall.Location
    if not isinstance(loc, LocationCurve) or not isinstance(loc.Curve, Line):
        return None
    d = loc.Curve.Direction
    u = XYZ(d.X, d.Y, 0).Normalize()
    n = XYZ(-u.Y, u.X, 0)
    p = door.Location.Point
    solids = element_solids(wall)
    head_p = door.get_Parameter(BuiltInParameter.INSTANCE_HEAD_HEIGHT_PARAM)
    head = head_p.AsDouble() if head_p else from_mm(2200.0)

    # Hai mặt tường: tia ngang tường phía trên đầu cửa (lanh tô)
    big = from_mm(1000.0)
    a = XYZ(p.X, p.Y, level.Elevation + head + from_mm(100.0)).Subtract(n.Multiply(big))
    perp = ray_hits(solids, a, a.Add(n.Multiply(2 * big)))
    if perp:
        f0, f1 = perp[0][0] - big, perp[-1][1] - big
    else:
        f0, f1 = -wall.Width / 2.0, wall.Width / 2.0
        op.note = u"Không có lanh tô – lấy chiều dày type"
    c = (f0 + f1) / 2.0
    op.h = (f1 - f0) / 2.0
    op.u, op.n = u, n

    # Ô cửa: tia dọc tim tường, cao 300 trên Level
    scan = from_mm(SCAN_MM)
    q = XYZ(p.X, p.Y, level.Elevation + from_mm(PROBE_Z_MM)).Add(n.Multiply(c))
    a = q.Subtract(u.Multiply(scan))
    spans = ray_hits(solids, a, a.Add(u.Multiply(2 * scan)))
    before = [s[1] for s in spans if s[1] <= scan]
    after = [s[0] for s in spans if s[0] >= scan]
    inside = any(s[0] < scan < s[1] for s in spans)
    g0 = max(before) if before else None
    g1 = min(after) if after else None
    width = None if (inside or g0 is None or g1 is None) else g1 - g0
    if width is None or not (from_mm(MIN_OPENING_MM) <= width <= from_mm(MAX_OPENING_MM)):
        wp = door.Symbol.get_Parameter(BuiltInParameter.DOOR_WIDTH) or door.get_Parameter(BuiltInParameter.DOOR_WIDTH)
        if wp is None or wp.AsDouble() <= 0:
            return None
        g0, g1 = scan - wp.AsDouble() / 2.0, scan + wp.AsDouble() / 2.0
        op.note = (op.note + u"; " if op.note else u"") + u"Không đo được ô tường – lấy Width family"
    op.s0, op.s1 = g0 - scan, g1 - scan
    op.center = XYZ(p.X, p.Y, 0).Add(n.Multiply(c))
    return op


def element_points_mm(el, level):
    """Các điểm dò (mm) của một phần tử chọn: cửa → hai bên cửa; khác → điểm đặt / tâm hộp bao."""
    if isinstance(el, FamilyInstance) and el.Category is not None and \
            el.Category.Id.Equals(ElementId(BuiltInCategory.OST_Doors)):
        op = measure_opening(el, level)
        if op is not None:
            return op.side_points_mm()
    loc = el.Location
    if isinstance(loc, LocationPoint):
        p = loc.Point
    elif isinstance(loc, LocationCurve):
        p = loc.Curve.Evaluate(0.5, True)
    else:
        bb = el.get_BoundingBox(None)
        if bb is None:
            return []
        p = bb.Min.Add(bb.Max).Divide(2.0)
    return [(to_mm(p.X), to_mm(p.Y))]


# --- Dựng biên sàn (Revit) -----------------------------------------------------------
def loop_area(loop):
    pts = []
    for c in loop:
        pts.extend(list(c.Tessellate())[:-1])
    return signed_area([(p.X, p.Y) for p in pts])


def orient_loops(loops):
    """Vòng ngoài (diện tích lớn nhất) ngược chiều kim đồng hồ, vòng lỗ cùng chiều."""
    if not loops:
        return loops
    areas = [loop_area(l) for l in loops]
    outer = max(range(len(loops)), key=lambda i: abs(areas[i]))
    for i, l in enumerate(loops):
        if (areas[i] > 0) != (i == outer):
            l.Flip()
    return loops


def poly_loop(pts_mm, z):
    loop = CurveLoop()
    ps = [XYZ(from_mm(x), from_mm(y), z) for x, y in pts_mm]
    for i in range(len(ps)):
        loop.Append(Line.CreateBound(ps[i], ps[(i + 1) % len(ps)]))
    return loop


def make_strip(op, k, far, z):
    """Dải ô cửa phía k (0: +n, 1: -n): từ mặt tường phía đó (chồng STRIP_OVERLAP_MM vào phòng) tới far (theo n,
    tính từ tim tường, cùng dấu phía k: 0 = tim tường, -h = mặt tường phía bên kia)."""
    sign = 1.0 if k == 0 else -1.0
    a, b = sign * far, sign * (op.h + from_mm(STRIP_OVERLAP_MM))
    lo, hi = min(a, b), max(a, b)
    base = XYZ(op.center.X, op.center.Y, z)
    ps = [base.Add(op.u.Multiply(s)).Add(op.n.Multiply(t)) for s, t in
          ((op.s0, lo), (op.s1, lo), (op.s1, hi), (op.s0, hi))]
    loop = CurveLoop()
    for i in range(4):
        loop.Append(Line.CreateBound(ps[i], ps[(i + 1) % 4]))
    if not loop.IsCounterclockwise(XYZ.BasisZ):
        loop.Flip()
    return loop


def floor_profiles(room, z):
    """Hợp bo phòng với các dải ô cửa → danh sách profile (mỗi profile là list CurveLoop)."""
    base = poly_loop(room.pts, z)
    if not room.strips:
        return [orient_loops([base])]
    h = from_mm(100.0)
    solid = GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop]([base]), XYZ.BasisZ, h)
    for s in room.strips:
        rs = GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop]([s]), XYZ.BasisZ, h)
        solid = BooleanOperationsUtils.ExecuteBooleanOperation(solid, rs, BooleanOperationsType.Union)
    profiles = []
    tol = from_mm(TOL_MM)
    for f in solid.Faces:
        if isinstance(f, PlanarFace) and f.FaceNormal.Z < -0.99 and abs(f.Origin.Z - z) < tol:
            profiles.append(orient_loops(list(f.GetEdgesAsCurveLoops())))
    return profiles


def profile_area_m2(profile):
    return abs(sum(loop_area(l) for l in profile)) * 0.09290304


def existing_floor_at(level, p_mm):
    p = XYZ(from_mm(p_mm[0]), from_mm(p_mm[1]), 0)
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId != level.Id:
            continue
        bb = fl.get_BoundingBox(None)
        if bb is None or not (bb.Min.X <= p.X <= bb.Max.X and bb.Min.Y <= p.Y <= bb.Max.Y):
            continue
        for ref in HostObjectUtils.GetTopFaces(fl):
            face = fl.GetGeometryObjectFromReference(ref)
            # Face.Project trả về None khi hình chiếu nằm ngoài mặt
            if isinstance(face, Face) and face.Project(XYZ(p.X, p.Y, bb.Max.Z)) is not None:
                return fl
    return None


def create_floor(profile, ftype, level, offset_mm):
    fl = Floor.Create(doc, List[CurveLoop](profile), ftype.Id, level.Id)
    fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(from_mm(offset_mm))
    cm = fl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if cm is not None and not cm.IsReadOnly:
        cm.Set(COMMENT_TAG)
    return fl


def preview_lines(profiles, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for prof in profiles:
            for loop in prof:
                for c in loop:
                    a, b = c.GetEndPoint(0), c.GetEndPoint(1)
                    out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(to_mm(a.X), to_mm(a.Y), z_mm),
                                                           DSPoint.ByCoordinates(to_mm(b.X), to_mm(b.Y), z_mm)))
        return out
    except Exception:
        return []


ROOM_HEADER = [u"STT", u"Điểm trong phòng (mm)", u"Loại", u"Mẫu hatch", u"Floor type", u"Cao độ (mm)",
               u"DT bo phòng (m²)", u"DT sàn (m²)", u"Số ô cửa ghép", u"Kết quả", u"ElementId"]
DOOR_HEADER = [u"Id cửa", u"Family : Type", u"Rộng ô (mm)", u"Dày tường (mm)", u"Hai bên", u"Xử lý", u"Ghi chú"]


def write_log(room_rows, door_rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoSanHoanThien_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm, m²\n")
        w = csv.writer(f)
        w.writerow(ROOM_HEADER)
        w.writerows(room_rows)
        w.writerow([])
        w.writerow(DOOR_HEADER)
        w.writerows(door_rows)
    return path


def main(cad_filter, id_text, room_filters, area_filters, hatch_filters, pattern_text, type_text, offset_text,
         entry_keys, dry_run, template_name=u""):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    view = doc.ActiveView
    level = view.GenLevel if view.ViewType in (ViewType.FloorPlan, ViewType.EngineeringPlan) else None
    if level is None:
        return [u"DỪNG: hãy mở view mặt bằng (Floor Plan) của tầng cần tạo sàn rồi Run lại."], []

    # Phần tử chọn → phạm vi căn
    if id_text:
        elems = [doc.GetElement(ElementId(int(s))) for s in id_text.replace(u",", u";").split(u";") if s.strip()]
    else:
        elems = [doc.GetElement(i) for i in uidoc.Selection.GetElementIds()]
    elems = [e for e in elems if e is not None]
    if not elems:
        return [u"DỪNG: chưa chọn căn hộ. Trong Revit chọn CỬA VÀO CĂN (hoặc phần tử bất kỳ nằm trong căn; chọn "
                u"nhiều căn được) rồi Run lại, hoặc nhập Id vào ô IN[1]."], []

    pattern_map = dict((k, v.upper()) for k, v in parse_map(pattern_text).items())
    bad = [k for k, v in pattern_map.items() if v not in KINDS]
    if bad:
        raise StopReport([u"DỪNG: IN[5] có loại không hợp lệ ở mẫu {} (chỉ dùng {}).".format(
            u", ".join(bad), u"/".join(KINDS))])
    type_names = dict((k, norm(v)) for k, v in parse_map(type_text).items())
    offsets = {}
    for k, v in parse_map(offset_text).items():
        try:
            offsets[k] = float(v)
        except ValueError:
            raise StopReport([u"DỪNG: IN[7] cao độ '{}={}' không phải số.".format(k, v)])
    all_types = floor_types_by_name()
    template = all_types.get(norm(template_name)) if template_name else None
    if template_name and template is None:
        raise StopReport([u"DỪNG: không có floor type mẫu '{}' (IN[10]). Các floor type: {}".format(
            template_name, u", ".join(sorted(all_types.keys())))])
    ftypes, missing, pending = {}, [], {}
    for k in KINDS:
        name = type_names.get(k, u"")
        if name and name in all_types:
            ftypes[k] = all_types[name]
        elif name and template is not None:
            # Chưa có → nhân bản từ type mẫu khi ghi; dry-run tạm dùng type mẫu để tính
            pending[k] = name
            ftypes[k] = template
        elif name:
            missing.append(u"{}='{}'".format(k, name))
    if missing:
        raise StopReport([u"DỪNG: không có floor type {} (IN[6]) và chưa có type mẫu để nhân bản (IN[10]). "
                          u"Các floor type: {}".format(u", ".join(missing), u", ".join(sorted(all_types.keys())))])

    def ft_label(k):
        if k in pending:
            return u"{} (sẽ nhân bản từ {})".format(pending[k], type_name(template))
        return type_name(ftypes[k])

    # Đọc CAD
    cad = pick_cad(cad_filter)
    cad_name = get_name(doc.GetElement(cad.GetTypeId()))
    path = cad_file_path(cad)
    if not path:
        return [u"DỪNG: bản CAD '{}' phải là Link (không Import) và file DWG còn ở đường dẫn gốc.".format(cad_name)], []
    core = find_accoreconsole()
    if not core:
        return [u"DỪNG: không tìm thấy AutoCAD Core Console (C:\\Program Files\\Autodesk\\AutoCAD *\\accoreconsole.exe)."], []
    hatches, polys, errors = read_dwg(path, core, room_filters + area_filters + hatch_filters)
    tf = cad.GetTotalTransform()

    def to_model(pts):
        out = []
        for x, y in pts:
            p = tf.OfPoint(XYZ(from_mm(x), from_mm(y), 0))
            out.append((to_mm(p.X), to_mm(p.Y)))
        return out

    room_polys = [to_model(p) for l, p in polys if matches(l, room_filters)]
    area_polys = [clean_poly(to_model(p)) for l, p in polys if area_filters and matches(l, area_filters)]
    hatches = [(l, pat, [to_model(lp) for lp in loops]) for l, pat, loops in hatches if matches(l, hatch_filters)]
    rooms = [Room(i, p) for i, p in enumerate(room_polys)]
    rooms = [r for r in rooms if len(r.pts) >= 3 and r.area > 0.05]
    for i, r in enumerate(rooms):
        r.idx = i
    if not rooms:
        raise StopReport([u"DỪNG: bản CAD không có polyline kín nào trên layer chứa '{}' (IN[2]).".format(
            u"; ".join(room_filters))])
    thresholds = classify_rooms(rooms, hatches, pattern_map)

    # Cửa trên level: đo ô, tìm phòng hai bên
    openings = []
    for door in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType() \
            .ToElements():
        if door.LevelId != level.Id or not isinstance(door, FamilyInstance):
            continue
        op = measure_opening(door, level)
        if op is None:
            continue
        for k, p in enumerate(op.side_points_mm()):
            hit = [r.idx for r in rooms if point_in(p, r.pts)]
            op.sides[k] = hit[0] if hit else None
        if op.sides[0] is not None or op.sides[1] is not None:
            openings.append(op)

    def is_entry(op):
        text = op.label().lower()
        return any(k.lower() in text for k in entry_keys)

    links = [tuple(op.sides) for op in openings if None not in op.sides and op.sides[0] != op.sides[1]
             and not is_entry(op)]
    seeds = [element_points_mm(e, level) for e in elems]
    chosen, how, warns = apartment_rooms(rooms, area_polys, [s for s in seeds if s], links)
    if not chosen:
        raise StopReport([u"DỪNG: không xác định được căn hộ từ phần tử đã chọn."] + warns)
    in_apt = set(chosen)
    apt_rooms = [rooms[i] for i in chosen]

    # Ô cửa → dải ghép vào phòng
    z = level.Elevation
    door_rows, wc_doors = [], []
    for op in openings:
        if not any(i in in_apt for i in op.sides if i is not None):
            continue
        kinds = [rooms[i].kind if i is not None and i in in_apt else None for i in op.sides]
        code, text = door_action(kinds[0], kinds[1], is_entry(op))
        if code == "STRIP_BOTH":
            rooms[op.sides[0]].strips.append(make_strip(op, 0, 0.0, z))
            rooms[op.sides[1]].strips.append(make_strip(op, 1, 0.0, z))
        elif code in ("STRIP_A", "STRIP_B"):
            k = 0 if code == "STRIP_A" else 1
            rooms[op.sides[k]].strips.append(make_strip(op, k, -op.h, z))
        elif code == "THRESHOLD":
            wc_doors.append((op, len(door_rows)))
        side_txt = u" | ".join(u"#{} {}".format(chosen.index(i) + 1, KIND_LABEL.get(rooms[i].kind, u"chưa rõ"))
                               if i is not None and i in in_apt else u"ngoài căn" for i in op.sides)
        door_rows.append([id_value(op.door.Id), op.label(), u"{:.0f}".format(to_mm(op.s1 - op.s0)),
                          u"{:.0f}".format(to_mm(2 * op.h)), side_txt, text, op.note])

    # Đá chân cửa: hatch AR-CONC sát bo phòng của căn
    apt_thresholds = [t for t in thresholds if any(poly_dist(t, r.pts) <= THRESHOLD_NEAR_MM for r in apt_rooms)]
    for op, ri in wc_doors:
        c = (to_mm(op.center.X), to_mm(op.center.Y))
        if not any(point_in(c, t) for t in apt_thresholds):
            door_rows[ri][6] = (door_rows[ri][6] + u"; " if door_rows[ri][6] else u"") + \
                u"THIẾU đá chân cửa (không có hatch CHANCUA tại ô cửa)"

    # Lập kế hoạch
    room_jobs, th_jobs, all_profiles = [], [], []
    for r in apt_rooms:
        if r.kind is None:
            r.status = u"Bỏ qua – chưa rõ loại ({})".format(r.note)
            continue
        if r.kind not in ftypes:
            r.status = u"Bỏ qua – chưa gán floor type cho {} (IN[6])".format(r.kind)
            continue
        old = existing_floor_at(level, r.ip)
        if old is not None:
            r.status = u"Bỏ qua – đã có sàn Id {} ({})".format(id_value(old.Id), type_name(doc.GetElement(old.GetTypeId())))
            continue
        try:
            profs = floor_profiles(r, z)
        except Exception as ex:
            r.status = u"Lỗi hình học: {}".format(ex)
            continue
        if not profs:
            r.status = u"Lỗi – không dựng được biên sàn"
            continue
        r.floor_area = sum(profile_area_m2(p) for p in profs)
        r.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
        room_jobs.append((r, profs))
        all_profiles += profs
    th_rows = []
    for t in apt_thresholds:
        ip = interior_point(t)
        old = existing_floor_at(level, ip)
        status = u"Bỏ qua – đã có sàn Id {}".format(id_value(old.Id)) if old is not None else \
            (u"Bỏ qua – chưa gán floor type CHANCUA (IN[6])" if "CHANCUA" not in ftypes else
             (u"Sẽ tạo" if dry_run else u"Chờ tạo"))
        row = [u"Đá", fmt(ip), KIND_LABEL["CHANCUA"], u"", ft_label("CHANCUA") if "CHANCUA" in ftypes else u"—",
               u"{:.0f}".format(offsets.get("CHANCUA", 0.0)), u"{:.2f}".format(abs(signed_area(t)) / 1e6),
               u"{:.2f}".format(abs(signed_area(t)) / 1e6), 0, status, u""]
        th_rows.append(row)
        if status.startswith(u"Sẽ") or status.startswith(u"Chờ"):
            prof = orient_loops([poly_loop(t, z)])
            th_jobs.append((prof, row))
            all_profiles.append(prof)

    # Ghi vào mô hình
    created_types = []
    if not dry_run and (room_jobs or th_jobs):
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            used = set(r.kind for r, _ in room_jobs) | (set(["CHANCUA"]) if th_jobs else set())
            for k in sorted(set(pending) & used):
                ftypes[k] = duplicate_floor_type(template, pending.pop(k), k)
                mat = hint_material(k)
                created_types.append(u"{} = '{}' (nhân bản từ '{}'{})".format(
                    k, type_name(ftypes[k]), type_name(template),
                    u", vật liệu hoàn thiện '{}'".format(mat.Name) if mat is not None else
                    (u", CHƯA có vật liệu chứa '{}' – giữ vật liệu type mẫu".format(MATERIAL_HINT[k])
                     if k in MATERIAL_HINT else u"")))
            for r, profs in room_jobs:
                for prof in profs:
                    fl = create_floor(prof, ftypes[r.kind], level, offsets.get(r.kind, 0.0))
                    r.ids.append(id_value(fl.Id))
                r.status = u"Đã tạo"
            for prof, row in th_jobs:
                fl = create_floor(prof, ftypes["CHANCUA"], level, offsets.get("CHANCUA", 0.0))
                row[9], row[10] = u"Đã tạo", id_value(fl.Id)
            tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo sàn, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    # Báo cáo
    room_rows = []
    for n, r in enumerate(apt_rooms, 1):
        room_rows.append([n, fmt(r.ip), KIND_LABEL.get(r.kind, u"chưa rõ"), r.pattern or u"—",
                          ft_label(r.kind) if r.kind in ftypes else u"—",
                          u"{:.0f}".format(offsets.get(r.kind, 0.0)) if r.kind else u"—",
                          u"{:.2f}".format(r.area), u"{:.2f}".format(r.floor_area) if r.floor_area else u"—",
                          len(r.strips), r.status, u", ".join(str(i) for i in r.ids)])
    room_rows += th_rows
    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – level: {} – căn xác định theo: {}".format(cad_name, level.Name, u"; ".join(how)))
    counts = {}
    for r in apt_rooms:
        counts[r.kind] = counts.get(r.kind, 0) + 1
    report.append(u"Phòng trong căn: {} ({}) – đá chân cửa: {} – ô cửa liên quan: {}".format(
        len(apt_rooms), u", ".join(u"{} {}".format(KIND_LABEL.get(k, u"chưa rõ"), v) for k, v in sorted(
            counts.items(), key=lambda x: str(x[0]))), len(apt_thresholds), len(door_rows)))
    report.append(u"Tấm sàn {}: {} phòng + {} đá chân cửa".format(
        u"sẽ tạo" if dry_run else u"đã tạo", len(room_jobs), len(th_jobs)))
    for line in created_types:
        report.append(u"ĐÃ NHÂN BẢN floor type: " + line)
    for k in sorted(pending):
        report.append(u"Floor type {} = '{}' chưa có → {} từ '{}'".format(
            k, pending[k], u"sẽ nhân bản khi chạy thật" if dry_run else u"không dùng, không nhân bản",
            type_name(template)))
    missing_th = [r for r in door_rows if u"THIẾU" in r[6]]
    if missing_th:
        report.append(u"CẢNH BÁO: {} cửa WC / cửa vào căn chưa có hatch đá chân cửa trong CAD".format(len(missing_th)))
    for w in warns:
        report.append(u"CẢNH BÁO: " + w)
    if errors:
        report.append(u"Bỏ qua {} đối tượng CAD đọc lỗi (VD: {})".format(len(errors), errors[0][1]))
    try:
        report.append(u"Log: " + write_log(room_rows, door_rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra biên sàn (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(ROOM_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in room_rows]
    report.append(u" | ".join(DOOR_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in door_rows]
    return report, preview_lines(all_profiles, to_mm(z))


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
            (IN[0] or u"").strip(),
            (IN[1] or u"").strip(),
            split_filters(IN[2] or u"A-duong bo phong"),
            split_filters(IN[3] if IN[3] is not None else u"A-Area"),
            split_filters(IN[4] or u"A-Hoan thien san"),
            IN[5] or u"WOODS_BOARD_WIDE=KHO;300X600=WC;2X4=LOGIA;AR-CONC=CHANCUA",
            IN[6] or u"CHANCUA=FF-Đá Granite tự nhiên",
            IN[7] or u"KHO=0;WC=-15;LOGIA=-30;CHANCUA=0",
            split_filters(IN[8] or u"khóa thông minh;DW03"),
            True if IN[9] is None else bool(IN[9]),
            (IN[10] if len(IN) > 10 and IN[10] is not None else u"SHT-Gach Lat-600x600").strip(),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoSanHoanThien_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
