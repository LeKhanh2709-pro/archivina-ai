# TRẠNG THÁI: ĐÃ DUYỆT (BIM Manager, 2026-10-29)
# Mã nguồn của Python node trong ARV_TaoSanCanHoTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
# Revit 2026 / Dynamo 3.6 (CPython3)
#
# Tạo sàn hoàn thiện kiến trúc (Floor) cho phòng ngủ, phòng khách, WC, logia của các căn hộ trên level của view
# mặt bằng đang mở, lấy thông tin từ bản CAD mặt bằng đã Link (không cần đường bo phòng / hatch trong CAD):
#   1. Căn hộ  = polyline kín layer IN[1] (mặc định "00 do dt", > 20 m²); tên căn = TEXT/MTEXT layer IN[2] khớp mẫu
#      IN[3] (mặc định CH01…), gán cho polyline gần nhất. Chữ đọc từ bản sao DWG qua AutoCAD Core Console.
#   2. Biên sàn = mặt hoàn thiện tường Revit (tường thẳng, tường liền qua ô cửa): vùng bao các căn trừ khối tường
#      (dài tới mặt tường nối ở hai đầu) và trừ cột CAD layer IN[4] nới thêm IN[5] mm (lớp trát, mặc định 15)
#      → tách thành các vùng rời. Vùng kín nằm trong căn giữ nguyên; vùng hở (logia không có tường lan can, sảnh hở
#      ra hành lang, phía ngoài nhà) cắt theo polyline căn.
#   3. Loại phòng: có điểm dò cửa ra logia (family chứa IN[6], dò IN[7] mm về phía Facing) → LOGIA; có ≥ 5 điểm nét
#      thiết bị CAD layer IN[8] → WC (> 10 m² → chỉ báo "KIỂM TRA", không tạo); vùng hở ≤ 6 m² (không có tường
#      Revit bao kín, VD logia giặt có máy giặt, cửa đi mở quay) → LOGIA; còn lại → phòng khô (lớn nhất căn
#      = khách, ≥ 6 m² = ngủ, nhỏ hơn = sảnh / kho). Phòng khô dùng chung một floor type.
#   4. WC lùi biên thêm IN[11] = 10 mm khỏi mặt trát (= dày gạch ốp, KTS chốt 2026-10-20). Tường ốp mỏng < 12 mm
#      (VD "GO-Gạch ốp-300x600" 10 mm) không làm biên sàn → biên WC trùng mặt gạch ốp.
#   5. Floor type / cao độ mặt sàn theo loại (IN[9], IN[10]). Bỏ qua vùng < 0,5 m² (hộp kỹ thuật) và dải mảnh
#      rộng TB < 300 mm. Bỏ qua phòng đã có sàn tạo bởi tool này. Comments = "ARV-SanCanHo <căn> <loại>".
# INPUT
#   IN[0]  (str)  Một phần tên bản CAD (trống = bản CAD duy nhất)
#   IN[1]  (str)  Layer polyline căn hộ (khớp chuỗi con, cách ';'), VD "00 do dt"
#   IN[2]  (str)  Layer chữ tên căn, VD "A-Text"
#   IN[3]  (str)  Mẫu tên căn (regex), VD "^CH\d+"
#   IN[4]  (str)  Layer cột CAD khoét khỏi sàn, VD "A-Column" (trống = không khoét)
#   IN[5]  (num)  Sàn cách mặt cột CAD (mm), VD 15
#   IN[6]  (str)  Nhận cửa ra logia theo tên family/type (chuỗi con, cách ';'), VD "trượt"
#   IN[7]  (num)  Điểm dò logia cách tâm cửa về phía Facing (mm), VD 400
#   IN[8]  (str)  Layer thiết bị WC trong CAD, VD "A-Interior WC"
#   IN[9]  (str)  Floor type theo loại: "KHO=…;WC=…;LOGIA=…". Thêm "KHACH=…" (tuỳ chọn) để phòng khách dùng type
#                 riêng (VD sàn gỗ); không khai báo KHACH → phòng khách dùng type KHO, gộp chung sàn khô như cũ.
#                 Có KHACH: ô cửa ngủ ↔ khách lát đá chân cửa (type CHANCUA).
#                 Thêm "HANHLANG=…" (tuỳ chọn): sàn hành lang = biên Room tên chứa "Hành lang" (mặt hoàn thiện) trên
#                 level, trừ tường / vách KC; thang bộ, sảnh thang ("Khu vực chung"…) không lát. Chỉ tạo khi IN[12]
#                 trống (cả tầng).
#   IN[10] (str)  Cao độ ĐÁY sàn so với Level = SFL (mm): "KHO=0;KHACH=0;WC=0;LOGIA=0;CHANCUA=0". Mọi tấm sàn đặt
#                 trên SFL: mặt = Level + dày floor type + IN[10] (KTS chốt 2026-10-29: đáy mọi sàn = SFL).
#   IN[11] (num)  WC lùi biên khỏi mặt trát (mm) = dày gạch ốp, VD 10
#   IN[12] (str)  Chỉ làm các căn (cách ';', VD "CH01;CH02"; trống = tất cả)
#   IN[13] (bool) Dry-run: True = chỉ báo cáo + xem trước (mặc định True)
#   IN[14] (str)  Floor type kiến trúc mẫu: type ở IN[9] chưa có → nhân bản từ type này đúng tên đó, giữ cấu tạo lớp
#                 (chỉ khi chạy thật và có tấm sàn dùng). Trống = dừng khi thiếu type.
#   IN[15] (str)  Line style vẽ đường bo phòng (Detail Line trên view đang mở, theo đúng biên từng tấm sàn tạo,
#                 kể cả lỗ), VD "AV.Nét Hatch Lát Sàn" – phải có sẵn trong file. Trống = không vẽ.
#   Ô cửa (luôn làm): lỗ cửa đo trên tường Revit × bề dày tường. Phòng khô ↔ phòng khô (ngủ ↔ khách) → sàn phòng
#   khô (Comments …KHO-CUA); phòng khô ↔ WC → đá chân cửa CHANCUA (IN[9]/IN[10], kéo thêm IN[11] mm về phía WC).
#   Chiều hatch: Revit đặt hatch song song cạnh dài nhất của biên → sàn khô của căn được chia cạnh (force_dir) để
#   cùng chiều cạnh dài nhất phòng khách.
#   IN[16] (bool) Tạo lại: xoá sàn cũ của tool (Comments ARV-SanCanHo) trong các căn đang làm + mọi Detail Line
#                 line style IN[15] trên view nằm trong các căn đó (cách polyline căn ≤ 300 mm), rồi tạo lại
#                 (mặc định False). Không bật: nét bo đã có trùng vị trí được giữ, không vẽ chồng.
#                 Dù không bật: sàn cũ của tool KHÁC floor type IN[9] (VD đổi phòng khách sang gỗ) vẫn tự xoá + tạo lại
#                 (liệt kê Id trong báo cáo dry-run).
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, cảnh báo, đường dẫn log, từng tấm sàn
#   OUT[1] (list[Line]) Xem trước: biên các tấm sàn sẽ tạo (mm, tại cao độ Level)

import os
import io
import re
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
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, CADLinkType, XYZ, Line, Arc, CurveLoop,
                                   PolyLine, Transaction, UnitUtils, UnitTypeId, ModelPathUtils, BuiltInParameter,
                                   BuiltInCategory, Floor, FloorType, Wall, LocationCurve, LocationPoint,
                                   FamilyInstance, Options, GeometryInstance, PlanarFace, ViewPlan,
                                   GeometryCreationUtilities, BooleanOperationsUtils, BooleanOperationsType,
                                   SolidUtils, GraphicsStyleType, Solid, SolidCurveIntersectionOptions,
                                   SolidCurveIntersectionMode, ElementId, RevitLinkInstance,
                                   SpatialElementBoundaryOptions, SpatialElementBoundaryLocation)
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    from System.Collections.Generic import List
    doc = DocumentManager.Instance.CurrentDBDocument
    uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument

TRANSACTION_NAME = u"ARV - Tạo sàn căn hộ từ CAD"
SCRIPT_TAG = u"ARV_TaoSanCanHoTuCAD_v1"
COMMENT_TAG = u"ARV-SanCanHo"
KINDS = ("KHO", "KHACH", "WC", "LOGIA", "CHANCUA", "HANHLANG")   # CHANCUA = đá chân cửa WC (ô cửa phòng khô ↔ WC)
DRY_KINDS = ("KHO", "KHACH")   # KHACH = phòng khách tách type riêng (tuỳ chọn, IN[9])
CORE_TIMEOUT_S = 180
MIN_APT_M2 = 20.0         # Polyline căn tối thiểu
MAX_LABEL_MM = 6000.0     # Tên căn cách polyline căn tối đa (chữ thường đặt ngoài mặt bằng)
MIN_PIECE_M2 = 0.5        # Vùng nhỏ hơn = hộp kỹ thuật, bỏ
MIN_WIDTH_MM = 300.0      # Dải mảnh (rộng TB = 2·DT/chu vi) nhỏ hơn → bỏ
OPEN_MM = 250.0           # Đỉnh vùng ra ngoài polyline căn quá giá trị này → vùng hở, cắt theo polyline căn
MARGIN_MM = 2000.0        # Nới vùng bao các căn
HALL_ROOM_KEY = u"hanhlang"  # Room tên chứa "Hành lang" (so bỏ dấu) = biên sàn hành lang
LOGIA_EXT_MM = 400.0      # Logia hở: kéo cạnh ra tới mặt ngoài tường ôm góc tối đa chừng này
WC_MIN_PTS = 5            # Số điểm nét thiết bị WC tối thiểu trong phòng
WC_MAX_M2 = 10.0
BEDROOM_MIN_M2 = 6.0
OPEN_LOGIA_MAX_M2 = 6.0   # Vùng hở (không có tường Revit bao kín) nhỏ hơn, không có thiết bị WC → logia
THIN_WALL_MM = 12.0       # Tường mỏng hơn = tường ốp (gạch ốp WC 10 mm), không làm biên sàn. Lớp trát 15 mm
                          # (WA_M15 quanh vách BTCT ở mô hình KC link) vẫn làm biên – 30 mm cũ làm hở phòng (2026-10-28)
PROBE_Z_MM = 300.0       # Tường được tính nếu cắt qua cao độ Level + 300
DUP_PT_MM = 2.0
COLLINEAR_MM = 0.5
INNER_MM = 20.0


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def signed_area(pts):
    return sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
               for i in range(len(pts))) / 2.0


def perimeter(pts):
    return sum(math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0], pts[(i + 1) % len(pts)][1] - pts[i][1])
               for i in range(len(pts)))


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


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def dist_outside(p, pts):
    """0 nếu p nằm trong đa giác, ngược lại khoảng cách tới cạnh gần nhất."""
    if point_in(p, pts):
        return 0.0
    return min(seg_dist(p, pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts)))


def clean_poly(pts):
    """Bỏ đỉnh trùng (≤ DUP_PT_MM) và đỉnh thẳng hàng, đưa về ngược chiều kim đồng hồ.
    Đỉnh thẳng hàng làm Floor.Create báo lỗi nội bộ (vòng biên có hai cạnh nối tiếp cùng phương)."""
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
            if ab == 0 or abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / ab < COLLINEAR_MM:
                out.pop(i)
                changed = True
                break
    if len(out) >= 3 and signed_area(out) < 0:
        out.reverse()
    return out


def interior_point(pts, holes=()):
    """Điểm chắc chắn nằm trong đa giác (CCW), ngoài các lỗ: trung điểm cạnh dài nhất lùi vào trong INNER_MM."""
    edges = sorted(range(len(pts)), key=lambda i: -math.hypot(pts[(i + 1) % len(pts)][0] - pts[i][0],
                                                              pts[(i + 1) % len(pts)][1] - pts[i][1]))
    for i in edges:
        a, b = pts[i], pts[(i + 1) % len(pts)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l < 3 * INNER_MM:
            continue
        p = ((a[0] + b[0]) / 2.0 - (b[1] - a[1]) / l * INNER_MM, (a[1] + b[1]) / 2.0 + (b[0] - a[0]) / l * INNER_MM)
        if point_in(p, pts) and not any(point_in(p, h) for h in holes):
            return p
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def bbox_overlap(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def in_region(p, outer, holes):
    return point_in(p, outer) and not any(point_in(p, h) for h in holes)


def match_names(labels, apts):
    """labels: [(tên, (x, y))], apts: [đa giác] → {chỉ số đa giác: tên}. Ghép cặp gần nhất trước, mỗi bên một lần."""
    pairs = sorted((dist_outside(p, poly), name, i) for name, p in labels for i, poly in enumerate(apts))
    used_n, result = set(), {}
    for d, name, i in pairs:
        if d > MAX_LABEL_MM or name in used_n or i in result:
            continue
        used_n.add(name)
        result[i] = name
    return result


def parse_map(text):
    result = {}
    for part in (text or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            if k.strip():
                result[k.strip().upper()] = v.strip()
    return result


def split_filters(text):
    return [s.strip() for s in (text or u"").split(u";") if s.strip()]


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def loose_key(s):
    """Khoá so khớp nới cho tên line style: bỏ dấu (kể cả đ), chữ thường, chỉ giữ chữ + số."""
    t = unicodedata.normalize("NFD", (s or u"")).replace(u"đ", u"d").replace(u"Đ", u"d")
    return u"".join(c for c in t if c.isalnum() and not unicodedata.combining(c)).lower()


def matches(layer, filters):
    l = norm(layer).lower()
    return any(norm(f).lower() in l for f in filters)


# --- Đọc chữ trong DWG bằng AutoCAD Core Console --------------------------------------
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


# Đọc TEXT/MTEXT ở model space VÀ trong block (lồng nhau, tối đa 8 cấp): toạ độ đổi về WCS theo ma trận affine của
# từng INSERT. Chữ trên layer "0" trong block lấy layer của INSERT cha. (Giống ARV_TaoDamTuCAD_v1.)
DUMP_LISP = u"""(setq f (open "{out}" "w" "utf8"))
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
(defun _txt (d m lay / p q)
  (setq p (if (and (= (cdr (assoc 0 d)) "TEXT") (or (/= 0 (cdr (assoc 72 d))) (/= 0 (cdr (assoc 73 d)))))
            (cdr (assoc 11 d)) (cdr (assoc 10 d))))
  (setq q (_ap m p))
  (write-line (strcat (substr (cdr (assoc 0 d)) 1 1) "|" lay "|" (rtos (car q) 2 3) "," (rtos (cadr q) 2 3) "|"
                      (cdr (assoc 1 d))) f))
(defun _walk (name m parent depth / e d)
  (setq e (cdr (assoc -2 (tblsearch "BLOCK" name))))
  (while e
    (setq d (entget e))
    (cond ((member (cdr (assoc 0 d)) '("TEXT" "MTEXT")) (_txt d m (_lay d parent)))
          ((and (= (cdr (assoc 0 d)) "INSERT") (< depth 8))
            (_walk (cdr (assoc 2 d)) (_mul m (_ins d)) (_lay d parent) (1+ depth))))
    (setq e (entnext e))))
(if (setq ss (ssget "_X" '((0 . "TEXT,MTEXT,INSERT") (410 . "Model"))))
  (progn (setq i 0)
    (repeat (sslength ss)
      (setq d (entget (ssname ss i)) i (1+ i))
      (if (= (cdr (assoc 0 d)) "INSERT")
        (_walk (cdr (assoc 2 d)) (_ins d) (cdr (assoc 8 d)) 1)
        (_txt d '(1.0 0.0 0.0 1.0 0.0 0.0) (cdr (assoc 8 d)))))))
(close f)
"""


def read_dwg_texts(dwg_path, core):
    """[(layer, text, x, y)] theo toạ độ DWG (mm). Chạy trên bản sao trong thư mục tạm – không mở file gốc."""
    work = tempfile.mkdtemp(prefix="ARV_SanCanHo_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "texts.txt")
        scr = os.path.join(work, "dump.scr")
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được danh sách chữ")
        texts = []
        with io.open(out, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f.read().splitlines():
                parts = line.split("|")
                if len(parts) < 4:
                    continue
                kind, layer, xy = parts[0], parts[1], parts[2]
                text = u"|".join(parts[3:])
                if kind == "M":
                    text = clean_mtext(text)
                try:
                    x, y = [float(v) for v in xy.split(",")]
                except ValueError:
                    continue
                if text.strip():
                    texts.append((layer, text.strip(), x, y))
        return texts
    finally:
        shutil.rmtree(work, ignore_errors=True)


# --- Revit: tiện ích -------------------------------------------------------------------
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
        ref = link.GetExternalFileReference()
        return ModelPathUtils.ConvertModelPathToUserVisiblePath(ref.GetAbsolutePath())
    except Exception:
        return None


def layer_of(obj):
    gs = doc.GetElement(obj.GraphicsStyleId)
    cat = gs.GraphicsStyleCategory if gs is not None else None
    return cat.Name if cat is not None else u""


def read_link_geometry(inst, apt_filters, col_filters, wc_filters):
    """Hình học bản CAD link theo toạ độ mô hình (mm): polyline kín căn, polyline kín cột, điểm nét thiết bị WC."""
    apts, cols, wc_pts = [], [], []

    def closed_pts(pl):
        c = [(to_mm(p.X), to_mm(p.Y)) for p in pl.GetCoordinates()]
        if len(c) > 3 and math.hypot(c[0][0] - c[-1][0], c[0][1] - c[-1][1]) < 1.0:
            return clean_poly(c[:-1])
        return None

    def walk(geo):
        for o in geo:
            if isinstance(o, GeometryInstance):
                walk(o.GetInstanceGeometry())
                continue
            lay = layer_of(o)
            if wc_filters and matches(lay, wc_filters):
                if isinstance(o, PolyLine):
                    wc_pts.extend((to_mm(p.X), to_mm(p.Y)) for p in o.GetCoordinates())
                elif isinstance(o, Arc) and not o.IsBound:
                    wc_pts.append((to_mm(o.Center.X), to_mm(o.Center.Y)))
                elif hasattr(o, "Evaluate") and getattr(o, "IsBound", False):
                    p = o.Evaluate(0.5, True)
                    wc_pts.append((to_mm(p.X), to_mm(p.Y)))
                continue
            if not isinstance(o, PolyLine):
                continue
            if matches(lay, apt_filters):
                c = closed_pts(o)
                if c and len(c) >= 3 and abs(signed_area(c)) / 1e6 >= MIN_APT_M2:
                    apts.append(c)
            elif col_filters and matches(lay, col_filters):
                c = closed_pts(o)
                if c and len(c) >= 3:
                    cols.append(c)

    geo = inst.get_Geometry(Options())
    if geo is not None:
        walk(geo)
    return apts, cols, wc_pts


def poly_loop(pts_mm, z):
    loop = CurveLoop()
    ps = [XYZ(from_mm(x), from_mm(y), z) for x, y in pts_mm]
    for i in range(len(ps)):
        loop.Append(Line.CreateBound(ps[i], ps[(i + 1) % len(ps)]))
    return loop


def prism(loop, height):
    return GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop]([loop]), XYZ.BasisZ, height)


def loop_pts(loop):
    pts = []
    for c in loop:
        if isinstance(c, Line):
            p = c.GetEndPoint(0)
            pts.append((to_mm(p.X), to_mm(p.Y)))
        else:
            pts.extend((to_mm(p.X), to_mm(p.Y)) for p in list(c.Tessellate())[:-1])
    return pts


def joined_half_width(loc, end, self_id):
    """Nửa bề dày lớn nhất của tường nối ở đầu end (0 nếu đầu tự do) – khối tường kéo tới đúng mặt tường kia."""
    try:
        others = loc.get_ElementsAtJoin(end)
    except Exception:
        try:
            others = loc.ElementsAtJoin[end]
        except Exception:
            return 0.0
    best = 0.0
    for o in others:
        if isinstance(o, Wall) and o.Id != self_id:
            best = max(best, o.Width / 2.0)
    return best


def wall_cutters(level, z, warns):
    """Khối đặc bề dày toàn phần (gồm lớp trát) của tường cắt qua cao độ Level + PROBE_Z_MM; không có lỗ cửa."""
    zc = z + from_mm(PROBE_Z_MM)
    cutters, skipped, thin = [], 0, 0
    for w in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        bb = w.get_BoundingBox(None)
        loc = w.Location
        if bb is None or not isinstance(loc, LocationCurve) or bb.Min.Z > zc or bb.Max.Z < zc:
            continue
        if w.Width < from_mm(THIN_WALL_MM):
            # Tường ốp mỏng (gạch ốp WC 10 mm…) không làm biên sàn: biên WC lấy mặt trát − IN[11] (= dày gạch ốp),
            # như nhau dù chỗ đó đã dựng tường ốp hay chưa
            thin += 1
            continue
        crv = loc.Curve
        t = w.Width / 2.0
        if isinstance(crv, Line):
            ext = [joined_half_width(loc, 0, w.Id), joined_half_width(loc, 1, w.Id)]
            chords = [(crv.GetEndPoint(0), crv.GetEndPoint(1), ext[0], ext[1])]
        else:
            pts = list(crv.Tessellate())
            if len(pts) < 2:
                skipped += 1
                continue
            chords = [(pts[i], pts[i + 1], t if i > 0 else 0.0, t if i < len(pts) - 2 else 0.0)
                      for i in range(len(pts) - 1)]
        for a, b, e0, e1 in chords:
            d = XYZ(b.X - a.X, b.Y - a.Y, 0)
            if d.GetLength() < from_mm(1):
                continue
            d = d.Normalize()
            n = XYZ(-d.Y, d.X, 0)
            a = XYZ(a.X, a.Y, z - 0.5).Subtract(d.Multiply(e0))
            b = XYZ(b.X, b.Y, z - 0.5).Add(d.Multiply(e1))
            ps = [a.Add(n.Multiply(t)), a.Subtract(n.Multiply(t)), b.Subtract(n.Multiply(t)), b.Add(n.Multiply(t))]
            loop = CurveLoop()
            for i in range(4):
                loop.Append(Line.CreateBound(ps[i], ps[(i + 1) % 4]))
            cutters.append(prism(loop, 2.0))
    if skipped:
        warns.append(u"Bỏ qua {} tường không đọc được đường định vị".format(skipped))
    if thin:
        warns.append(u"{} tường ốp mỏng < {:.0f} mm không làm biên sàn (biên WC = mặt trát − IN[11])".format(
            thin, THIN_WALL_MM))
    return cutters


def link_struct_cutters(z, box_mm, warns):
    """Khối vách + cột kết cấu trong các link Revit (mô hình KC) cắt qua cao độ Level + PROBE_Z_MM, trong vùng box_mm.
    Mô hình KT chỉ có lớp trát mỏng quanh vách BTCT → không trừ vách KC thì sàn chạy vào trong vách. Chỉ đọc link."""
    zc = z + from_mm(PROBE_Z_MM)
    x0, y0, x1, y1 = [from_mm(v) for v in box_mm]
    opt = Options()
    cutters, n_links = [], 0
    for li in FilteredElementCollector(doc).OfClass(RevitLinkInstance).ToElements():
        ldoc = li.GetLinkDocument()
        if ldoc is None:
            continue
        n_links += 1
        tf = li.GetTotalTransform()
        els = list(FilteredElementCollector(ldoc).OfClass(Wall).ToElements()) +             list(FilteredElementCollector(ldoc).OfCategory(BuiltInCategory.OST_StructuralColumns)
                 .WhereElementIsNotElementType().ToElements())
        for e in els:
            bb = e.get_BoundingBox(None)
            if bb is None:
                continue
            cs = [tf.OfPoint(XYZ(x, y, zz)) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)
                  for zz in (bb.Min.Z, bb.Max.Z)]
            if min(c.Z for c in cs) > zc or max(c.Z for c in cs) < zc or                     max(c.X for c in cs) < x0 or min(c.X for c in cs) > x1 or                     max(c.Y for c in cs) < y0 or min(c.Y for c in cs) > y1:
                continue
            geo = e.get_Geometry(opt)
            if geo is None:
                continue
            stack = list(geo)
            while stack:
                g = stack.pop()
                if isinstance(g, GeometryInstance):
                    stack.extend(g.GetInstanceGeometry())
                elif isinstance(g, Solid) and g.Volume > 1e-6:
                    try:
                        cutters.append(SolidUtils.CreateTransformed(g, tf))
                    except Exception:
                        pass
    if not n_links:
        warns.append(u"Không có link Revit kết cấu đã tải – vách / cột BTCT không trừ khỏi sàn, soát biên quanh vách")
    return cutters


def cutter_boxes(cutters):
    """[(khối, (x0, y0, x1, y1) mm)] – bbox mặt bằng của từng khối cắt."""
    result = []
    for c in cutters:
        try:
            bb = c.GetBoundingBox()
            a, b = bb.Transform.OfPoint(bb.Min), bb.Transform.OfPoint(bb.Max)
            result.append((c, (to_mm(min(a.X, b.X)), to_mm(min(a.Y, b.Y)), to_mm(max(a.X, b.X)), to_mm(max(a.Y, b.Y)))))
        except Exception:
            pass
    return result


def covered(spans, lo, hi):
    """Tỉ lệ đoạn [lo, hi] được phủ bởi các khoảng spans."""
    if hi - lo <= 0:
        return 0.0
    total, cur = 0.0, lo
    for a, b in sorted((max(a, lo), min(b, hi)) for a, b in spans if b > lo and a < hi):
        if b > cur:
            total += b - max(a, cur)
            cur = b
    return total / (hi - lo)


def extend_logia(p, cut_boxes, z, others):
    """Logia hở cắt theo polyline căn (đường đo DT) có thể hụt so với mặt tường phía sau polyline (VD khe 100 mm giữa
    logia và vách lõi thang) → kéo cạnh bbox ra tới mép ngoài tường ôm góc (≤ LOGIA_EXT_MM), trừ lại tường.
    Chỉ kéo cạnh mà dải thêm có tường che phía sau ≥ 60 % chiều dài cạnh; cạnh trông ra lan can / không gian ngoài
    (lan can chỉ có trong CAD) giữ theo polyline (KTS chốt 2026-10-29). Phần thêm ≤ 35 %, không lấn phòng khác;
    không được → None (giữ nguyên)."""
    x0, y0, x1, y1 = p.box
    tol = 30.0
    near = [cb for c, cb in cut_boxes
            if cb[0] <= x1 + LOGIA_EXT_MM and cb[2] >= x0 - LOGIA_EXT_MM and
            cb[1] <= y1 + LOGIA_EXT_MM and cb[3] >= y0 - LOGIA_EXT_MM]
    corner = [cb for cb in near if cb[0] <= x1 + tol and cb[2] >= x0 - tol and cb[1] <= y1 + tol and cb[3] >= y0 - tol]
    nx0 = min([cb[0] for cb in corner if cb[2] > x0 + tol and x0 - LOGIA_EXT_MM <= cb[0] < x0] + [x0])
    nx1 = max([cb[2] for cb in corner if cb[0] < x1 - tol and x1 < cb[2] <= x1 + LOGIA_EXT_MM] + [x1])
    ny0 = min([cb[1] for cb in corner if cb[3] > y0 + tol and y0 - LOGIA_EXT_MM <= cb[1] < y0] + [y0])
    ny1 = max([cb[3] for cb in corner if cb[1] < y1 - tol and y1 < cb[3] <= y1 + LOGIA_EXT_MM] + [y1])
    # Tường phía sau dải thêm: nằm trong dải (bỏ phần trùng bbox logia), phủ dọc cạnh
    if nx0 < x0 - 5 and covered([(cb[1], cb[3]) for cb in near if cb[0] < x0 - 5 and cb[2] > nx0], y0, y1) < 0.6:
        nx0 = x0
    if nx1 > x1 + 5 and covered([(cb[1], cb[3]) for cb in near if cb[2] > x1 + 5 and cb[0] < nx1], y0, y1) < 0.6:
        nx1 = x1
    if ny0 < y0 - 5 and covered([(cb[0], cb[2]) for cb in near if cb[1] < y0 - 5 and cb[3] > ny0], x0, x1) < 0.6:
        ny0 = y0
    if ny1 > y1 + 5 and covered([(cb[0], cb[2]) for cb in near if cb[3] > y1 + 5 and cb[1] < ny1], x0, x1) < 0.6:
        ny1 = y1
    if max(x0 - nx0, nx1 - x1, y0 - ny0, ny1 - y1) < 5.0:
        return None
    sol = prism(poly_loop([(nx0, ny0), (nx1, ny0), (nx1, ny1), (nx0, ny1)], z), 1.0)
    for c, cb in cut_boxes:
        if cb[0] < nx1 and cb[2] > nx0 and cb[1] < ny1 and cb[3] > ny0:
            try:
                sol = BooleanOperationsUtils.ExecuteBooleanOperation(sol, c, BooleanOperationsType.Difference)
            except Exception:
                return None
    best = None
    for sub in SolidUtils.SplitVolumes(sol):
        for o, h in solid_regions(sub):
            if in_region(p.ip, o, h):
                best = (o, h)
    if best is None:
        return None
    q = Piece(p.apt, best[0], best[1], p.is_open)
    if q.area < p.area - 0.01 or q.area > p.area * 1.35 or any(in_region(o.ip, q.outer, q.holes) for o in others):
        return None
    q.kind, q.label = p.kind, p.label
    q.status = u"Logia: kéo cạnh hở tới mặt ngoài tường (+{:.2f} m²)".format(q.area - p.area)
    return q


def column_cutters(cols, gap_mm, z):
    cutters = []
    for c in cols:
        loop = poly_loop(c, z - 0.5)
        best = None
        for s in ((1.0, -1.0) if gap_mm > 0 else (0.0,)):
            try:
                l = CurveLoop.CreateViaOffset(loop, from_mm(gap_mm) * s, XYZ.BasisZ) if s else loop
                sol = prism(l, 2.0)
                if best is None or sol.Volume > best.Volume:
                    best = sol
            except Exception:
                pass
        if best is not None:
            cutters.append(best)
    return cutters


def solid_regions(solid):
    """Mặt đáy của khối → [(vòng ngoài, [vòng lỗ])] theo mm, đã làm sạch."""
    result = []
    for f in solid.Faces:
        if not isinstance(f, PlanarFace) or f.FaceNormal.Z > -0.9:
            continue
        loops = [clean_poly(loop_pts(l)) for l in f.GetEdgesAsCurveLoops()]
        loops = [l for l in loops if len(l) >= 3]
        if not loops:
            continue
        loops.sort(key=lambda l: -abs(signed_area(l)))
        result.append((loops[0], loops[1:]))
    return result


def offset_outer(outer, dist_mm, z):
    """Lùi vòng ngoài vào trong dist_mm (chọn chiều cho diện tích nhỏ hơn)."""
    loop = poly_loop(outer, z)
    best = None
    for s in (1.0, -1.0):
        try:
            l = CurveLoop.CreateViaOffset(loop, from_mm(dist_mm) * s, XYZ.BasisZ)
            p = clean_poly(loop_pts(l))
            if len(p) >= 3 and (best is None or abs(signed_area(p)) < abs(signed_area(best))):
                best = p
        except Exception:
            pass
    return best


def existing_floor_polys(level):
    """Các sàn đã tạo bởi tool này trên level: [(vòng biên mm, Id, tên căn, Floor)] – mỗi vòng sketch một dòng."""
    polys = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId != level.Id:
            continue
        cm = fl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
        text = (cm.AsString() or u"") if cm is not None else u""
        if not text.startswith(COMMENT_TAG):
            continue
        parts = text.split()
        apt = parts[1] if len(parts) > 1 else u""
        try:
            sk = doc.GetElement(fl.SketchId)
            for arr in sk.Profile:
                pts = []
                for c in arr:
                    pts.extend((to_mm(p.X), to_mm(p.Y)) for p in list(c.Tessellate())[:-1])
                if len(pts) >= 3:
                    polys.append((pts, id_value(fl.Id), apt, fl))
        except Exception:
            pass
    return polys


def seg_key(a, b):
    """Khoá đoạn thẳng không phân biệt chiều, làm tròn mm – nhận nét đường bo trùng vị trí."""
    return frozenset([(int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1])))])


def edge_dir(pts):
    """Góc (rad, mod π) của cạnh dài nhất."""
    best, ang = -1.0, 0.0
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l > best:
            best, ang = l, math.atan2(b[1] - a[1], b[0] - a[0])
    return ang % math.pi


def force_dir(pts, ang):
    """Revit đặt mẫu hatch sàn SONG SONG CẠNH DÀI NHẤT của biên (đã thử 2026-10-20: thứ tự cạnh, SpanDirectionAngle
    không có tác dụng). Muốn hatch theo hướng ang: chia các cạnh khác hướng thành nhiều đoạn thẳng hàng ngắn hơn
    cạnh dài nhất cùng hướng ang (Floor.Create nhận đỉnh thẳng hàng). Không có cạnh cùng hướng → giữ nguyên."""
    def par(a, b):
        return abs(math.sin(math.atan2(b[1] - a[1], b[0] - a[0]) - ang)) < 0.02
    n = len(pts)
    lmax = max([math.hypot(pts[(i + 1) % n][0] - pts[i][0], pts[(i + 1) % n][1] - pts[i][1])
                for i in range(n) if par(pts[i], pts[(i + 1) % n])] or [0.0])
    if lmax < 50.0:
        return pts
    out = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        out.append(a)
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if par(a, b) or l < 0.95 * lmax:
            continue
        k = int(math.ceil(l / (0.8 * lmax)))
        out += [(a[0] + (b[0] - a[0]) * j / k, a[1] + (b[1] - a[1]) * j / k) for j in range(1, k)]
    return out


def extend_toward(rect, pt, dist):
    """Dời cạnh của chữ nhật gần điểm pt nhất ra ngoài thêm dist (mm) về phía pt."""
    n = len(rect)
    best, bi = None, 0
    for i in range(n):
        d = seg_dist(pt, rect[i], rect[(i + 1) % n])
        if best is None or d < best:
            best, bi = d, i
    a, b = rect[bi], rect[(bi + 1) % n]
    l = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    nx, ny = -(b[1] - a[1]) / l, (b[0] - a[0]) / l
    if (pt[0] - a[0]) * nx + (pt[1] - a[1]) * ny < 0:
        nx, ny = -nx, -ny
    out = list(rect)
    out[bi] = (a[0] + nx * dist, a[1] + ny * dist)
    out[(bi + 1) % n] = (b[0] + nx * dist, b[1] + ny * dist)
    return out


def door_strips(level, z, kept, outside):
    """Ô cửa đi trên level: chữ nhật = lỗ cửa đo trên khối tường Revit (dọc tim tường, cao Level + PROBE_Z_MM; đo
    không được – tường dừng ngay mép cửa / lớp trát cạnh vách KC – thì lấy bề rộng bbox cửa) × bề dày tường.
    → [(đỉnh mm, phòng +n, phòng −n, cửa)]; một phía có thể None khi phía đó là hành lang (outside(pt) = True)."""
    opts = SolidCurveIntersectionOptions()
    opts.ResultType = SolidCurveIntersectionMode.CurveSegmentsInside
    zc = z + from_mm(PROBE_Z_MM)
    span = from_mm(3000)

    def piece_at(pt):
        for p in kept:
            if p.box[0] <= pt[0] <= p.box[2] and p.box[1] <= pt[1] <= p.box[3] and in_region(pt, p.outer, p.holes):
                return p
        return None

    result = []
    for d in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType():
        w = getattr(d, "Host", None)
        if not isinstance(d, FamilyInstance) or not isinstance(w, Wall) or not isinstance(d.Location, LocationPoint):
            continue
        if d.LevelId != level.Id:
            continue
        if not isinstance(w.Location, LocationCurve) or not isinstance(w.Location.Curve, Line):
            continue
        lc = w.Location.Curve
        u = XYZ(lc.Direction.X, lc.Direction.Y, 0).Normalize()
        n = XYZ(-u.Y, u.X, 0)
        p0 = lc.GetEndPoint(0)
        p = d.Location.Point
        t = (p.X - p0.X) * u.X + (p.Y - p0.Y) * u.Y
        c = XYZ(p0.X + u.X * t, p0.Y + u.Y * t, zc)
        probe = Line.CreateBound(c.Subtract(u.Multiply(span)), c.Add(u.Multiply(span)))
        lo, hi, blocked = -span, span, False
        for o in w.get_Geometry(Options()):
            if not isinstance(o, Solid) or o.Volume <= 0:
                continue
            r = o.IntersectWithCurve(probe, opts)
            for i in range(r.SegmentCount):
                sg = r.GetCurveSegment(i)
                s0 = sg.GetEndPoint(0).Subtract(c).DotProduct(u)
                s1 = sg.GetEndPoint(1).Subtract(c).DotProduct(u)
                s0, s1 = min(s0, s1), max(s0, s1)
                if s1 <= 1e-6:
                    lo = max(lo, s1)
                elif s0 >= -1e-6:
                    hi = min(hi, s0)
                else:
                    blocked = True
        bb = d.get_BoundingBox(None)
        if (blocked or lo <= -span or hi >= span) and bb is not None:
            ss = [(x - c.X) * u.X + (y - c.Y) * u.Y for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
            lo, hi, blocked = min(ss), max(ss), False
        if blocked or not (from_mm(300) <= hi - lo <= from_mm(3000)):
            continue
        h = w.Width / 2.0
        cx, cy = to_mm(c.X), to_mm(c.Y)
        sides = []
        for sg in (1.0, -1.0):
            hit, out = None, False
            for extra in (150.0, 300.0, 500.0):
                pt = (cx + sg * n.X * (to_mm(h) + extra), cy + sg * n.Y * (to_mm(h) + extra))
                hit = piece_at(pt)
                if hit is not None:
                    break
                out = out or outside(pt)
            sides.append((hit, out and hit is None))
        (pa, out_a), (pb, out_b) = sides
        if (pa is None and not out_a) or (pb is None and not out_b) or (pa is None and pb is None):
            continue
        rect = [(to_mm(c.X + u.X * s + n.X * k), to_mm(c.Y + u.Y * s + n.Y * k))
                for s, k in ((lo, -h), (hi, -h), (hi, h), (lo, h))]
        result.append((clean_poly(rect), pa, pb, d))
    return result


def door_solids(door):
    """Các khối đặc của cửa (toạ độ mô hình), kể cả family lồng."""
    result, stack = [], list(door.get_Geometry(Options()) or [])
    while stack:
        g = stack.pop()
        if isinstance(g, GeometryInstance):
            stack.extend(g.GetInstanceGeometry())
        elif isinstance(g, Solid) and g.Volume > 1e-9:
            result.append(g)
    return result


def split_at_frame(rect, door):
    """Ô cửa (4 đỉnh theo door_strips: (lo,−h), (hi,−h), (hi,+h), (lo,+h)) → (dải phía +n, dải phía −n) từ mặt tường
    tới mặt khung cửa; dải mỏng < 5 mm → None. Bề dày khung đo trên các khối chính của cửa (≥ 5 % khối lớn nhất) –
    bỏ tay nắm / phụ kiện nhô qua mặt tường (bbox cả cửa phủ kín bề dày tường)."""
    if len(rect) != 4:
        return None, None
    p0, p1, p3 = rect[0], rect[1], rect[3]
    ln = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    th = math.hypot(p3[0] - p0[0], p3[1] - p0[1])
    if ln < 1 or th < 1:
        return None, None
    uv = ((p1[0] - p0[0]) / ln, (p1[1] - p0[1]) / ln)
    nv = ((p3[0] - p0[0]) / th, (p3[1] - p0[1]) / th)
    o = ((p0[0] + p3[0]) / 2.0, (p0[1] + p3[1]) / 2.0)
    sols = door_solids(door)
    ks = []
    if sols:
        vmax = max(s.Volume for s in sols)
        for s in sols:
            if s.Volume < 0.05 * vmax:
                continue
            for e in s.Edges:
                for q in e.Tessellate():
                    ks.append((to_mm(q.X) - o[0]) * nv[0] + (to_mm(q.Y) - o[1]) * nv[1])
    if not ks:
        bb = door.get_BoundingBox(None)
        if bb is None:
            return None, None
        ks = [(to_mm(x) - o[0]) * nv[0] + (to_mm(y) - o[1]) * nv[1]
              for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)]
    h = th / 2.0
    f0, f1 = max(min(ks), -h), min(max(ks), h)

    def band(k0, k1):
        if k1 - k0 < 5.0:
            return None
        return [(o[0] + uv[0] * s + nv[0] * k, o[1] + uv[1] * s + nv[1] * k)
                for s, k in ((0.0, k0), (ln, k0), (ln, k1), (0.0, k1))]
    return band(f1, h), band(-h, f0)


def merge_into(p, rect, z):
    """Gộp dải chữ nhật vào tấm p (Union) → Piece mới cùng loại, hoặc None nếu không gộp được."""
    try:
        loops = [poly_loop(p.outer, z)] + [poly_loop(h[::-1], z) for h in p.holes]
        a = GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop](loops), XYZ.BasisZ, 1.0)
        u = BooleanOperationsUtils.ExecuteBooleanOperation(a, prism(poly_loop(rect, z), 1.0),
                                                           BooleanOperationsType.Union)
        for o, h in solid_regions(u):
            if in_region(p.ip, o, h):
                q = Piece(p.apt, o, h, p.is_open)
                q.kind, q.label, q.status, q.tag = p.kind, p.label, p.status, p.tag
                return q
    except Exception:
        pass
    return None


def preview_lines(regions, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        out = []
        for outer, holes in regions:
            for loop in [outer] + holes:
                for i in range(len(loop)):
                    a, b = loop[i], loop[(i + 1) % len(loop)]
                    out.append(DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                                           DSPoint.ByCoordinates(b[0], b[1], z_mm)))
        return out
    except Exception:
        return []


LOG_HEADER = [u"Căn", u"Phòng", u"Loại", u"Điểm trong phòng (mm)", u"Floor type", u"Cao độ (mm)",
              u"DT vùng (m²)", u"DT sàn (m²)", u"Vùng", u"Kết quả", u"ElementId"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoSanCanHoTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Bản CAD: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm, m²\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


class Piece(object):
    def __init__(self, apt, outer, holes, is_open):
        self.apt = apt
        self.outer = outer
        self.holes = holes
        self.is_open = is_open
        self.area = (abs(signed_area(outer)) - sum(abs(signed_area(h)) for h in holes)) / 1e6
        self.ip = interior_point(outer, holes)
        self.box = bbox(outer)
        self.kind = None
        self.label = u""
        self.status = u""
        self.floor_outer = outer
        self.floor_area = self.area
        self.id = u""
        self.tag = None           # Hậu tố Comments (mặc định = loại)
        self.bo_loops = None      # Vòng vẽ đường bo (mặc định = biên sàn); sàn gộp → bo theo từng phòng thành phần
        self.merged = False       # Phòng đã gộp vào tấm sàn khô chung của căn (không tạo tấm riêng)


# --- Chương trình chính -----------------------------------------------------------
def main(cad_filter, apt_filters, name_filters, name_pattern, col_filters, col_gap, logia_filters, logia_probe,
         wc_filters, type_text, offset_text, wc_extra, only_text, dry_run, template_name=u"", line_style_name=u"", rebuild=False):
    if is_central_file(doc):
        raise StopReport([u"DỪNG: đang mở file CENTRAL. Mở file local / bản sao rồi chạy lại."])
    view = doc.ActiveView
    if not isinstance(view, ViewPlan) or view.GenLevel is None:
        raise StopReport([u"DỪNG: mở view MẶT BẰNG của tầng cần tạo sàn (sàn tạo trên level của view) rồi Run."])
    level = view.GenLevel
    z = level.Elevation
    warns = []

    # Floor type + cao độ
    type_map = parse_map(type_text)
    offsets = {}
    for k, v in parse_map(offset_text).items():
        try:
            offsets[k] = float(v)
        except ValueError:
            raise StopReport([u"DỪNG: cao độ '{}={}' ở IN[10] không phải số.".format(k, v)])
    all_types = {norm(type_name(t)): t for t in FilteredElementCollector(doc).OfClass(FloorType).ToElements()}
    loose_types = {loose_key(n): t for n, t in all_types.items()}

    def find_type(name):
        # Khớp đúng tên trước, sau đó khớp nới (bỏ dấu, hoa/thường, ký tự phân cách)
        return all_types.get(norm(name)) or loose_types.get(loose_key(name))

    def type_list():
        # Mỗi floor type một dòng để đọc được trong Watch của Dynamo
        return [u"   - " + n for n in sorted(all_types.keys())]

    template = find_type(template_name) if template_name else None
    if template_name and template is None:
        # Chỉ cần type mẫu khi có type ở IN[9] chưa có trong file → kiểm tra ở vòng dưới
        warns.append(u"Không có floor type mẫu '{}' (IN[14]) – chỉ dùng được các type IN[9] đã có sẵn".format(
            template_name))
    ftypes, pending, missing = {}, {}, []
    for k in KINDS:
        name = norm(type_map.get(k, u""))
        if not name and k in ("KHACH", "HANHLANG"):
            continue   # Không tách phòng khách → dùng type KHO
        if not name:
            warns.append(u"Chưa gán floor type cho {} (IN[9]) – phòng loại này chỉ báo cáo".format(k))
            continue
        hit = find_type(name)
        if hit is not None:
            ftypes[k] = hit
        elif template is not None:
            # Chưa có → nhân bản từ type mẫu khi ghi; dry-run tạm dùng type mẫu
            pending[k] = name
            ftypes[k] = template
        else:
            missing.append(u"   - {} = '{}'".format(k, name))
    if missing:
        head = [u"DỪNG: các floor type ở IN[9] chưa có trong file:"] + missing
        if template_name:
            head.append(u"và cũng không có floor type mẫu '{}' (IN[14]) để nhân bản.".format(template_name))
        else:
            head.append(u"và IN[14] (floor type mẫu để nhân bản) đang trống.")
        raise StopReport(head + [u"Cách sửa: đổi IN[9] sang type có sẵn, HOẶC đặt IN[14] = một type có sẵn "
                                 u"để tool nhân bản ra các type còn thiếu. Floor type trong file:"] + type_list())

    # Level = SFL; đáy mọi tấm sàn = Level + IN[10] → mặt = Level + dày floor type của loại + IN[10]
    thick = {}
    for k, ft in ftypes.items():
        try:
            thick[k] = to_mm(ft.GetCompoundStructure().GetWidth())
        except Exception:
            thick[k] = 0.0
            warns.append(u"Không đọc được bề dày floor type {} – mặt sàn {} đặt theo Level + IN[10]".format(
                type_name(ft), k))

    def top_mm(k):
        return thick.get(k, 0.0) + offsets.get(k, 0.0)

    def ft_label(k):
        if k in pending:
            return u"{} (sẽ nhân bản từ {})".format(pending[k], type_name(template))
        return type_name(ftypes[k])

    # CAD
    inst = pick_cad(cad_filter)
    cad_name = get_name(doc.GetElement(inst.GetTypeId()))
    apts, cols, wc_pts = read_link_geometry(inst, apt_filters, col_filters, wc_filters)
    if not apts:
        raise StopReport([u"DỪNG: bản CAD '{}' không có polyline kín ≥ {:.0f} m² trên layer '{}' (IN[1]).".format(
            cad_name, MIN_APT_M2, u";".join(apt_filters))])

    # Tên căn
    names = {}
    path = cad_file_path(inst)
    core = find_accoreconsole()
    if path and os.path.isfile(path) and core:
        tf = inst.GetTotalTransform()
        rx = re.compile(name_pattern or u".+", re.IGNORECASE)
        labels = []
        for lay, text, x, y in read_dwg_texts(path, core):
            text = norm(text)
            if matches(lay, name_filters) and rx.search(text):
                p = tf.OfPoint(XYZ(from_mm(x), from_mm(y), 0))
                labels.append((text, (to_mm(p.X), to_mm(p.Y))))
        names = match_names(labels, apts)
        if not labels:
            warns.append(u"Không có chữ tên căn khớp '{}' trên layer '{}' – đặt tên căn theo vị trí".format(
                name_pattern, u";".join(name_filters)))
        else:
            if len(names) < len(labels):
                warns.append(u"{} tên căn không ghép được polyline (cách > {:.0f} mm): {}".format(
                    len(labels) - len(names), MAX_LABEL_MM,
                    u", ".join(sorted(set(t for t, _ in labels) - set(names.values())))))
            unnamed = [i for i in range(len(apts)) if i not in names]
            if unnamed:
                warns.append(u"Bỏ {} polyline không có tên căn (hành lang / sảnh): {}".format(
                    len(unnamed), u", ".join(u"{:.1f} m²".format(abs(signed_area(apts[i])) / 1e6) for i in unnamed)))
    else:
        warns.append(u"Không đọc được chữ trong DWG (thiếu file gốc hoặc AutoCAD Core Console) – đặt tên căn theo vị trí")
    if not names:
        order = sorted(range(len(apts)), key=lambda i: (-round(bbox(apts[i])[3] / 1000.0), bbox(apts[i])[0]))
        names = {i: u"CAN-{:02d}".format(n) for n, i in enumerate(order, 1)}

    only = set(norm(s).upper() for s in split_filters(only_text))
    targets = [i for i in sorted(names) if not only or names[i].upper() in only]
    if not targets:
        raise StopReport([u"DỪNG: không có căn nào khớp IN[12] '{}'. Các căn: {}".format(
            only_text, u", ".join(sorted(names.values())))])

    # Vùng bao các căn − tường − cột → các vùng rời
    boxes = [bbox(apts[i]) for i in targets]
    x0 = min(b[0] for b in boxes) - MARGIN_MM
    y0 = min(b[1] for b in boxes) - MARGIN_MM
    x1 = max(b[2] for b in boxes) + MARGIN_MM
    y1 = max(b[3] for b in boxes) + MARGIN_MM
    region = prism(poly_loop([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z), 1.0)
    link_cut = link_struct_cutters(z, (x0, y0, x1, y1), warns)
    cutters = wall_cutters(level, z, warns) + column_cutters(cols, col_gap, z) + link_cut
    fails = 0
    for c in cutters:
        try:
            region = BooleanOperationsUtils.ExecuteBooleanOperation(region, c, BooleanOperationsType.Difference)
        except Exception:
            fails += 1
    if fails:
        warns.append(u"{} khối tường / cột không trừ được (lỗi boolean) – soát biên sàn quanh đó".format(fails))

    apt_prisms = {i: prism(poly_loop(apts[i], z - 0.5), 2.0) for i in targets}
    pieces, skipped = [], []
    free_region = region      # Vùng trống sau khi trừ tường / cột / vách KC (cắt sàn hành lang)
    for sol in SolidUtils.SplitVolumes(region):
        for outer, holes in solid_regions(sol):
            ip = interior_point(outer)
            home = [i for i in targets if point_in(ip, apts[i])]
            if home and max(dist_outside(p, apts[home[0]]) for p in outer) <= OPEN_MM:
                pieces.append(Piece(home[0], outer, holes, False))
                continue
            # Vùng hở: cắt theo từng polyline căn chạm tới (phần cắt ra bằng nguyên vùng → thực chất là vùng kín)
            whole = (abs(signed_area(outer)) - sum(abs(signed_area(h)) for h in holes)) / 1e6
            bb = bbox(outer)
            for i in targets:
                if not bbox_overlap(bb, boxes[targets.index(i)]):
                    continue
                try:
                    part = BooleanOperationsUtils.ExecuteBooleanOperation(sol, apt_prisms[i],
                                                                          BooleanOperationsType.Intersect)
                except Exception:
                    warns.append(u"Không cắt được vùng hở theo căn {}".format(names[i]))
                    continue
                if part is None or part.Volume <= 0:
                    continue
                for sub in SolidUtils.SplitVolumes(part):
                    for o2, h2 in solid_regions(sub):
                        p = Piece(i, o2, h2, True)
                        p.is_open = abs(p.area - whole) > 0.05
                        pieces.append(p)

    # Lọc vùng nhỏ / dải mảnh
    kept = []
    for p in pieces:
        if p.area < MIN_PIECE_M2:
            skipped.append((p, u"< {:.1f} m² (hộp kỹ thuật)".format(MIN_PIECE_M2)))
        elif 2.0 * p.area * 1e6 / perimeter(p.outer) < MIN_WIDTH_MM:
            skipped.append((p, u"dải mảnh rộng TB < {:.0f} mm".format(MIN_WIDTH_MM)))
        else:
            kept.append(p)

    # Phân loại
    logia_pts = []
    for d in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Doors).WhereElementIsNotElementType():
        if not isinstance(d, FamilyInstance) or not isinstance(d.Location, LocationPoint):
            continue
        if d.LevelId != level.Id or not matches(d.Symbol.Family.Name + u" " + type_name(d.Symbol), logia_filters):
            continue
        p = d.Location.Point.Add(d.FacingOrientation.Multiply(from_mm(logia_probe)))
        logia_pts.append((to_mm(p.X), to_mm(p.Y)))
    if logia_filters and not logia_pts:
        warns.append(u"Không có cửa ra logia khớp '{}' (IN[6]) trên level – không nhận được logia".format(
            u";".join(logia_filters)))
    def count_in(pts, p):
        x0, y0, x1, y1 = p.box
        return sum(1 for q in pts if x0 <= q[0] <= x1 and y0 <= q[1] <= y1 and in_region(q, p.outer, p.holes))

    for p in kept:
        n_wc = count_in(wc_pts, p)
        n_lg = count_in(logia_pts, p)
        if n_lg:
            p.kind, p.label = "LOGIA", u"Logia"
        elif n_wc >= WC_MIN_PTS:
            p.kind, p.label = "WC", u"WC"
            if p.area > WC_MAX_M2:
                p.kind, p.status = None, u"KIỂM TRA: có thiết bị WC nhưng {:.2f} m² > {:.0f} m² (thiếu tường?)".format(
                    p.area, WC_MAX_M2)
        elif p.is_open and p.area <= OPEN_LOGIA_MAX_M2:
            # Vùng nhỏ không có tường Revit bao kín (hở ra ngoài, đóng theo polyline căn) = logia giặt / phơi
            # (KTS chốt 2026-10-19: khu đặt máy giặt G19 là logia – cửa đi mở quay, không phải cửa trượt)
            p.kind, p.label = "LOGIA", u"Logia (vùng hở)"
            p.status = u"Lưu ý: logia nhận theo vùng hở ≤ {:.0f} m² – soát".format(OPEN_LOGIA_MAX_M2)
        else:
            p.kind = "KHO"
    # Logia hở: bo kín tới mặt ngoài tường như logia kín (KTS chốt 2026-10-29), không dừng ở polyline đo DT
    cut_boxes = cutter_boxes(cutters)
    for k, p in enumerate(kept):
        if p.kind == "LOGIA" and p.is_open:
            q = extend_logia(p, cut_boxes, z, [o for o in kept if o is not p and o.apt == p.apt])
            if q is not None:
                kept[k] = q
    for i in targets:
        dry = sorted([p for p in kept if p.apt == i and p.kind == "KHO"], key=lambda p: -p.area)
        for n, p in enumerate(dry):
            p.label = u"Khách" if n == 0 else (u"Ngủ" if p.area >= BEDROOM_MIN_M2 else u"Sảnh / kho")
            if n == 0 and "KHACH" in ftypes:
                p.kind = "KHACH"
            if p.is_open:
                p.label += u" (vùng hở)"
                if n > 0:
                    p.status = u"Lưu ý: vùng hở theo polyline căn – soát tường / cửa"

    # Sàn ô cửa: hai bên phòng khô (ngủ ↔ khách) → sàn phòng khô; đá chân cửa (CHANCUA) ở cửa WC, cửa logia 1 cánh
    # (không ở cửa trượt IN[6]) và cửa chính căn hộ ra hành lang (KTS chốt 2026-10-29)
    n_doors = n_sills = 0
    sill_count = {}
    tgt_polys = [apts[i] for i in targets]

    def outside(pt):
        return not any(point_in(pt, a) for a in tgt_polys)

    replaced_logia = {}
    hall_pts = []
    for rect, pa, pb, d in door_strips(level, z, kept, outside):
        if len(rect) < 3:
            continue
        if pa is None or pb is None:
            # Cửa chính căn hộ: một phía hành lang (ngoài mọi polyline căn)
            room = pa or pb
            if room.kind not in DRY_KINDS:
                continue
            s = Piece(room.apt, rect, [], False)
            s.kind, s.label, s.tag = "CHANCUA", u"Đá chân cửa căn hộ", u"CHANCUA"
            n_sills += 1
            sill_count[u"căn hộ"] = sill_count.get(u"căn hộ", 0) + 1
            kept.append(s)
            # Điểm dò phía hành lang: tâm ô cửa lùi ra ngoài nửa bề dày tường + 300 mm
            if len(rect) == 4:
                mx = sum(q[0] for q in rect) / 4.0
                my = sum(q[1] for q in rect) / 4.0
                nx, ny = rect[3][0] - rect[0][0], rect[3][1] - rect[0][1]
                th = math.hypot(nx, ny)
                if th > 1:
                    nx, ny = nx / th, ny / th
                    sg = -1.0 if (room.ip[0] - mx) * nx + (room.ip[1] - my) * ny > 0 else 1.0
                    hall_pts.append(((mx + sg * nx * (th / 2.0 + 300.0), my + sg * ny * (th / 2.0 + 300.0)), room.apt))
            continue
        if pa.apt != pb.apt:
            continue
        if "LOGIA" in (pa.kind, pb.kind) and (pa.kind in DRY_KINDS or pb.kind in DRY_KINDS):
            # Cửa logia: cửa trượt (khớp IN[6]) không làm đá – sàn gỗ và sàn logia kéo vào sát mặt khung cửa hai bên
            # (KTS chốt 2026-10-29); cửa đi 1 cánh → đá chân cửa
            if matches(d.Symbol.Family.Name + u" " + type_name(d.Symbol), logia_filters):
                band_a, band_b = split_at_frame(rect, d)
                sill_count[u"cửa trượt (không đá)"] = sill_count.get(u"cửa trượt (không đá)", 0) + 1
                if band_a is None and band_b is None:
                    warns.append(u"Cửa trượt {}: khung cửa phủ kín bề dày tường – không kéo được sàn vào sát khung".format(
                        id_value(d.Id)))
                for room, band in ((pa, band_a), (pb, band_b)):
                    if band is None:
                        continue
                    if room.kind in DRY_KINDS:
                        s = Piece(room.apt, band, [], False)
                        s.kind, s.label, s.tag = room.kind, u"Ô cửa trượt phía {}".format(room.label),                             u"{}-CUA".format(room.kind)
                        kept.append(s)
                        n_doors += 1
                    else:
                        lg = replaced_logia.get(id(room), room)
                        q = merge_into(lg, band, z)
                        if q is not None:
                            kept[kept.index(lg)] = q
                            replaced_logia[id(room)] = q
                            replaced_logia[id(lg)] = q
                continue
            s = Piece(pa.apt, rect, [], False)
            s.kind, s.label, s.tag = "CHANCUA", u"Đá chân cửa logia", u"CHANCUA"
            n_sills += 1
            sill_count[u"logia"] = sill_count.get(u"logia", 0) + 1
            kept.append(s)
            continue
        if pa.kind in DRY_KINDS and pb.kind in DRY_KINDS and pa.kind != pb.kind:
            # Ô cửa ngủ (KHO) ↔ khách (KHACH) khác vật liệu → đá chân cửa (KTS chốt 2026-10-28)
            s = Piece(pa.apt, rect, [], False)
            s.kind, s.label, s.tag = "CHANCUA", u"Đá chân cửa {} ↔ {}".format(pa.label, pb.label), u"CHANCUA"
            n_sills += 1
        elif pa.kind in DRY_KINDS and pb.kind in DRY_KINDS:
            s = Piece(pa.apt, rect, [], False)
            s.kind, s.label, s.tag = pa.kind, u"Ô cửa {} ↔ {}".format(pa.label, pb.label), u"{}-CUA".format(pa.kind)
            n_doors += 1
        elif "WC" in (pa.kind, pb.kind) and pa.kind != pb.kind and None not in (pa.kind, pb.kind):
            wc, dry = (pa, pb) if pa.kind == "WC" else (pb, pa)
            if wc_extra > 0:
                # Kéo đá thêm wc_extra về phía WC cho khít mép sàn WC (WC lùi biên thêm wc_extra)
                rect = extend_toward(rect, wc.ip, wc_extra)
            s = Piece(dry.apt, rect, [], False)
            s.kind, s.label, s.tag = "CHANCUA", u"Đá chân cửa WC", u"CHANCUA"
            n_sills += 1
            sill_count[u"WC"] = sill_count.get(u"WC", 0) + 1
        else:
            continue
        kept.append(s)

    # Sàn hành lang: biên Room "Hành lang" (mặt hoàn thiện) ∩ vùng trống (đã trừ tường / cột / vách KC) – thang bộ,
    # sảnh thang là Room "Khu vực chung" riêng nên không lát (KTS chốt 2026-10-29). Comments gắn theo căn có cửa
    # chính mở ra Room đó.
    n_hall = 0
    if "HANHLANG" in ftypes:
        if only:
            warns.append(u"Sàn hành lang chỉ tạo khi chạy cả tầng (IN[12] trống) – lần này bỏ qua")
        else:
            bopt = SpatialElementBoundaryOptions()
            bopt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
            halls = []
            for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms).WhereElementIsNotElementType():
                pn = r.get_Parameter(BuiltInParameter.ROOM_NAME)
                if r.LevelId == level.Id and r.Area > 0 and pn is not None and                         HALL_ROOM_KEY in loose_key(pn.AsString() or u""):
                    halls.append(r)
            for r in halls:
                loops = []
                for segs in r.GetBoundarySegments(bopt):
                    pts = []
                    for sg in segs:
                        pts.extend((to_mm(q.X), to_mm(q.Y)) for q in list(sg.GetCurve().Tessellate())[:-1])
                    pts = clean_poly(pts)
                    if len(pts) >= 3:
                        loops.append(pts)
                if not loops:
                    continue
                loops.sort(key=lambda l: -abs(signed_area(l)))
                outer = loops[0] if signed_area(loops[0]) > 0 else loops[0][::-1]
                holes = [h if signed_area(h) < 0 else h[::-1] for h in loops[1:]]
                apt = next((a for pt, a in hall_pts if in_region(pt, outer, holes)), targets[0])
                try:
                    cl = [poly_loop(outer, z)] + [poly_loop(h, z) for h in holes]
                    rs = GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop](cl), XYZ.BasisZ, 1.0)
                    part = BooleanOperationsUtils.ExecuteBooleanOperation(rs, free_region, BooleanOperationsType.Intersect)
                except Exception as ex:
                    warns.append(u"Room {} '{}': không cắt được theo tường ({}) – bỏ qua".format(
                        r.Number, pn.AsString(), ex))
                    continue
                for sub in SolidUtils.SplitVolumes(part):
                    for o, h in solid_regions(sub):
                        s = Piece(apt, o, h, False)
                        if s.area < MIN_PIECE_M2:
                            continue
                        s.kind, s.label, s.tag = "HANHLANG", u"Hành lang (Room {})".format(r.Number), u"HANHLANG"
                        kept.append(s)
                        n_hall += 1
            if not halls:
                warns.append(u"Không có Room tên 'Hành lang' trên level '{}' – không tạo sàn hành lang".format(level.Name))

    # Gộp sàn khô mỗi căn (khách + ô cửa + phòng ngủ nối qua cửa) thành 1 tấm → mạch ván liền nhau
    # (KTS chốt 2026-10-20: mỗi tấm Revit tự đặt gốc mẫu hatch theo hình của nó, API không dời được gốc mẫu)
    # Chiều hatch: song song cạnh dài nhất phòng khách (force_dir).
    merge_warns = []
    for i in targets:
        rooms = [p for p in kept if p.apt == i and p.kind in DRY_KINDS and p.tag is None]
        if not rooms:
            continue
        ang = edge_dir(max(rooms, key=lambda p: p.area).outer)
        dry = [p for p in kept if p.apt == i and p.kind == "KHO"]
        groups = []
        if len(dry) > 1:
            try:
                sol = None
                for p in dry:
                    loops = [poly_loop(p.outer, z)] + [poly_loop(h[::-1], z) for h in p.holes]
                    s = GeometryCreationUtilities.CreateExtrusionGeometry(List[CurveLoop](loops), XYZ.BasisZ, 1.0)
                    sol = s if sol is None else BooleanOperationsUtils.ExecuteBooleanOperation(
                        sol, s, BooleanOperationsType.Union)
                for comp in SolidUtils.SplitVolumes(sol):
                    for outer, holes in solid_regions(comp):
                        members = [p for p in dry if in_region(p.ip, outer, holes)]
                        if len(members) > 1:
                            groups.append((outer, holes, members))
            except Exception as ex:
                groups = []
                merge_warns.append(u"{}: không gộp được sàn khô ({}) – để tấm riêng, mạch có thể lệch".format(
                    names[i], ex))
        for outer, holes, members in groups:
            g = Piece(i, outer, holes, any(p.is_open for p in members))
            has_living = any(p.tag is None and p.label.startswith(u"Khách") for p in members)
            n_bed = sum(1 for p in members if p.tag is None) - (1 if has_living else 0)
            n_cua = sum(1 for p in members if p.tag is not None)
            g.kind, g.label = "KHO", u"Sàn khô gộp ({}{} phòng + {} ô cửa)".format(
                u"khách + " if has_living else u"", n_bed, n_cua)
            g.bo_loops = [l for p in members if p.tag is None for l in [p.outer] + p.holes]
            g.members = members
            for p in members:
                p.merged = True
                p.status = u"Gộp vào sàn khô chung của căn"
            kept.append(g)
        for p in kept:
            if p.apt == i and p.kind in DRY_KINDS and not p.merged:
                p.floor_outer = force_dir(p.floor_outer, ang)

    # Sàn đã có (hoặc xoá để tạo lại), WC lùi biên
    existing = existing_floor_polys(level)
    target_names = set(names[i] for i in targets)
    old_floors = {}
    if rebuild:
        for poly, fid, apt, fl in existing:
            if apt in target_names:
                old_floors[fid] = fl
        existing = [e for e in existing if e[1] not in old_floors]
    # Sàn cũ của tool khác floor type IN[9] (VD vừa đổi phòng khách sang gỗ) → tự xoá + tạo lại, không cần IN[16].
    # Tấm gộp: dò tại từng phòng thành phần; nằm trên > 1 sàn cũ (cách chia tấm đã đổi) → thay tất cả sàn đó.
    replaced = {}
    for p in kept:
        if p.kind is None or p.merged or p.kind not in ftypes:
            continue
        want = pending.get(p.kind) or type_name(ftypes[p.kind])
        pts = [p.ip] + [m.ip for m in getattr(p, "members", [])]
        hits = {}
        for poly, fid, apt, fl in existing:
            if any(point_in(q, poly) for q in pts):
                hits[fid] = fl
        if len(hits) > 1 or any(norm(type_name(doc.GetElement(fl.GetTypeId()))) != norm(want)
                                for fl in hits.values()):
            replaced.update(hits)
    old_floors.update(replaced)
    existing = [e for e in existing if e[1] not in old_floors]
    warns += merge_warns
    jobs = []
    for p in kept:
        if p.kind is None or p.merged:
            continue
        if p.kind not in ftypes:
            p.status = u"Chưa gán floor type"
            continue
        old = [e[1] for e in existing if point_in(p.ip, e[0])]
        if old:
            p.status, p.id = u"Bỏ qua: đã có sàn", old[0]
            continue
        if p.kind == "WC" and wc_extra > 0:
            o = offset_outer(p.outer, wc_extra, z)
            if o is None:
                p.status = u"LỖI lùi biên WC"
                continue
            p.floor_outer = o
            p.floor_area = (abs(signed_area(o)) - sum(abs(signed_area(h)) for h in p.holes)) / 1e6
        p.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
        jobs.append(p)

    # Line style đường bo (phải có sẵn – không tạo mới)
    line_style = None
    if line_style_name:
        subs = list(doc.Settings.Categories.get_Item(BuiltInCategory.OST_Lines).SubCategories)
        hit = [s for s in subs if norm(s.Name) == norm(line_style_name)]
        if not hit:
            # So khớp nới: bỏ dấu tiếng Việt, hoa/thường, dấu chấm/gạch/khoảng trắng
            hit = [s for s in subs if loose_key(s.Name) == loose_key(line_style_name)]
        if hit:
            line_style = hit[0].GetGraphicsStyle(GraphicsStyleType.Projection)
            line_style_name = hit[0].Name
        else:
            # Không dừng: vẫn tạo sàn, chỉ bỏ vẽ đường bo phòng
            av = sorted(s.Name for s in subs if loose_key(s.Name).startswith(u"av"))
            warns.append(u"Không có line style '{}' (IN[15]) trong file – KHÔNG vẽ đường bo phòng, sàn vẫn tạo. "
                         u"Tạo line style này (Manage > Additional Settings > Line Styles) hoặc đổi IN[15] "
                         u"sang line style có sẵn{}".format(
                             line_style_name, u": " + u"; ".join(av) if av else u""))

    # Ghi vào mô hình
    created_errors, created_types, line_errors = [], [], []
    n_lines = n_del_lines = n_kept_lines = 0
    drawn = set()
    step = [u"chuẩn bị"]
    if not dry_run and jobs:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            # Đường bo đã có: Detail Line cùng line style trên view đang mở, theo vị trí 2 đầu mút (mm)
            old_lines = {}
            if line_style is not None:
                step[0] = u"đọc đường bo đã có"
                for ce in FilteredElementCollector(doc, view.Id).OfCategory(BuiltInCategory.OST_Lines) \
                        .WhereElementIsNotElementType():
                    try:
                        if ce.LineStyle.Id != line_style.Id:
                            continue
                        gc = ce.GeometryCurve
                    except Exception:
                        continue
                    a, b = gc.GetEndPoint(0), gc.GetEndPoint(1)
                    old_lines.setdefault(seg_key((to_mm(a.X), to_mm(a.Y)), (to_mm(b.X), to_mm(b.Y))), []).append(ce.Id)
            if rebuild or old_floors:
                # Xoá sàn cũ của tool + mọi nét đường bo trùng cạnh sàn cũ / sàn sắp tạo (kể cả nét bị nhân đôi)
                step[0] = u"xoá sàn + đường bo cũ"
                edges = set()
                loops = [e[0] for e in existing_floor_polys(level) if e[1] in old_floors]
                for p in jobs:
                    loops += [p.floor_outer] + p.holes + (p.bo_loops or [])
                for pts in loops:
                    for k in range(len(pts)):
                        edges.add(seg_key(pts[k], pts[(k + 1) % len(pts)]))
                # + mọi nét cùng line style nằm trong các căn đang làm (2 đầu mút cách polyline căn ≤ 300 mm):
                # nét bo của lần chạy trước có thể lệch vị trí (sàn đã xoá tay) → không còn trùng cạnh nào
                for k in list(old_lines.keys()):
                    ends = list(k) if len(k) == 2 else list(k) * 2
                    if any(all(dist_outside(e, apts[i]) <= 300.0 for e in ends) for i in targets):
                        edges.add(k)
                line_ids = [i for k in edges for i in old_lines.pop(k, [])]
                n_del_lines = len(line_ids)
                dels = [old_floors[f].Id for f in old_floors] + line_ids
                if dels:
                    doc.Delete(List[ElementId](dels))
            drawn = set(old_lines.keys())
            step[0] = u"nhân bản floor type"
            for k in sorted(set(pending) & set(p.kind for p in jobs)):
                name = pending.pop(k)
                ftypes[k] = template.Duplicate(name)
                created_types.append(u"{} = '{}' (nhân bản từ '{}')".format(k, name, type_name(template)))
            for p in jobs:
                step[0] = u"tạo sàn {} {} {}".format(names[p.apt], p.label or p.kind, fmt(p.ip))
                loops = [poly_loop(p.floor_outer, z)] + [poly_loop(h[::-1], z) for h in p.holes]
                try:
                    try:
                        fl = Floor.Create(doc, List[CurveLoop](loops), ftypes[p.kind].Id, level.Id)
                    except Exception:
                        # Biên đã chia cạnh (chỉnh chiều hatch) bị Revit từ chối → tạo theo biên gốc, báo lệch chiều
                        clean = clean_poly(p.floor_outer)
                        if len(clean) == len(p.floor_outer):
                            raise
                        p.floor_outer = clean
                        loops = [poly_loop(p.floor_outer, z)] + [poly_loop(h[::-1], z) for h in p.holes]
                        fl = Floor.Create(doc, List[CurveLoop](loops), ftypes[p.kind].Id, level.Id)
                        line_errors.append(u"{} {} {}: không chỉnh được chiều hatch – xoay tay (Align)".format(
                            names[p.apt], p.label, fmt(p.ip)))
                except Exception as ex:
                    p.status = u"LỖI Floor.Create: {}".format(ex)
                    created_errors.append(p)
                    continue
                fl.get_Parameter(BuiltInParameter.FLOOR_HEIGHTABOVELEVEL_PARAM).Set(from_mm(top_mm(p.kind)))
                cm = fl.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
                if cm is not None and not cm.IsReadOnly:
                    cm.Set(u"{} {} {}".format(COMMENT_TAG, names[p.apt], p.tag or p.kind))
                p.status, p.id = u"Đã tạo", id_value(fl.Id)
                if line_style is not None:
                    # Đường bo phòng = biên tấm sàn vừa tạo, vẽ Detail Line trên view đang mở.
                    # Đoạn đã có nét cùng line style trùng đúng vị trí (lần chạy trước, sàn bị xoá tay) → không vẽ lại.
                    for loop in (p.bo_loops if p.bo_loops is not None else [p.floor_outer] + p.holes):
                        for i in range(len(loop)):
                            a, b = loop[i], loop[(i + 1) % len(loop)]
                            key = seg_key(a, b)
                            if key in drawn:
                                n_kept_lines += 1
                                continue
                            try:
                                dc = doc.Create.NewDetailCurve(view, Line.CreateBound(
                                    XYZ(from_mm(a[0]), from_mm(a[1]), z), XYZ(from_mm(b[0]), from_mm(b[1]), z)))
                                dc.LineStyle = line_style
                                drawn.add(key)
                                n_lines += 1
                            except Exception as ex:
                                line_errors.append(u"{} {}–{}: {}".format(names[p.apt], fmt(a), fmt(b), ex))
            tx.Commit()
        except Exception as ex:
            import traceback
            tx.RollBack()
            lines = [u"LỖI khi ghi vào mô hình (bước: {}), mọi thay đổi đã được hoàn tác: {}".format(step[0], ex),
                     traceback.format_exc()]
            try:
                folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
                path = os.path.join(folder, "TaoSanCanHoTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
                with io.open(path, "w", encoding="utf-8-sig") as f:
                    f.write(u"\n".join(lines))
                lines.append(u"Log lỗi: " + path)
            except Exception:
                pass
            return lines, []

    # Báo cáo
    rows = []
    allp = sorted(kept, key=lambda p: (names[p.apt], {"KHACH": 0, "KHO": 1, "WC": 2, "LOGIA": 3, "CHANCUA": 4, "HANHLANG": 5}.get(p.kind, 6), -p.area))
    for p in allp:
        rows.append([names[p.apt], p.label or u"—", p.kind or u"—", fmt(p.ip),
                     ft_label(p.kind) if p.kind in ftypes else u"—",
                     u"{:.0f}".format(top_mm(p.kind)) if p.kind else u"—",
                     u"{:.2f}".format(p.area), u"{:.2f}".format(p.floor_area),
                     u"hở" if p.is_open else u"kín", p.status, p.id])
    for p, why in skipped:
        rows.append([names[p.apt], u"—", u"bỏ", fmt(p.ip), u"—", u"—", u"{:.2f}".format(p.area), u"—",
                     u"hở" if p.is_open else u"kín", u"Bỏ qua: " + why, u""])

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – level: {} – {} căn ({})".format(
        cad_name, level.Name, len(targets), u", ".join(sorted(names[i] for i in targets))))
    counts = {}
    for p in jobs:
        counts[p.kind] = counts.get(p.kind, 0) + 1
    report.append(u"Tấm sàn {}: {} (khô {}, khách {}, WC {}, logia {}, hành lang {}) – bỏ qua vùng nhỏ / mảnh: {}".format(
        u"sẽ tạo" if dry_run else u"đã tạo", len(jobs) - len(created_errors), counts.get("KHO", 0),
        counts.get("KHACH", 0), counts.get("WC", 0), counts.get("LOGIA", 0), counts.get("HANHLANG", 0),
        len(skipped)))
    report.append(u"Ô cửa: {} ô ngủ ↔ khách (sàn phòng khô, …KHO-CUA) + {} đá chân cửa CHANCUA ({})".format(
        n_doors, n_sills, u", ".join(u"{} {}".format(k, v) for k, v in sorted(sill_count.items())) or u"không"))
    report.append(u"Chiều hatch sàn khô: mỗi căn song song cạnh dài nhất của phòng khách (ngủ + khách + ô cửa)")
    report.append(u"Cao độ: Level '{}' = SFL; đáy sàn = SFL + IN[10], mặt = đáy + dày type ({})".format(
        level.Name, u", ".join(u"{} +{:.0f}".format(k, top_mm(k)) for k in KINDS if k in thick)))
    report.append(u"Biên sàn: tường KT (≥ {:.0f} mm) + cột CAD + {} khối vách / cột KC từ link Revit".format(
        THIN_WALL_MM, len(link_cut)))
    if rebuild:
        report.append(u"Tạo lại: {} {} sàn cũ của tool trong các căn đang làm{}".format(
            u"sẽ xoá" if dry_run else u"đã xoá", len(old_floors),
            u" + các đoạn đường bo trùng cạnh (kể cả nét nhân đôi)" if dry_run else
            u" + {} đoạn đường bo trùng cạnh".format(n_del_lines)))
    if replaced:
        report.append(u"Thay sàn khác floor type IN[9]: {} {} sàn cũ của tool – Id: {}".format(
            u"sẽ xoá + tạo lại" if dry_run else u"đã xoá + tạo lại", len(replaced),
            u", ".join(u"{}".format(f) for f in sorted(replaced))))
    if line_style is not None:
        report.append(u"Đường bo phòng (Detail Line '{}', view '{}'): {}".format(
            line_style_name, view.Name, u"vẽ theo biên các tấm sàn sẽ tạo" if dry_run else
            u"vẽ mới {} đoạn, giữ {} đoạn đã có trùng vị trí, quanh {} tấm sàn".format(
                n_lines, n_kept_lines, len(jobs) - len(created_errors))))
        for e in line_errors[:10]:
            report.append(u"CẢNH BÁO đường bo: " + e)
    if dry_run:
        report.insert(1, u">>> ĐANG CHẠY THỬ: chưa ghi gì vào mô hình. Muốn tạo sàn: đổi ô IN[13] Dry-run = False "
                         u"(không phải IN[16] Tạo lại) rồi Run.")
    for line in created_types:
        report.append(u"ĐÃ NHÂN BẢN floor type: " + line)
    for k in sorted(pending):
        report.append(u"Floor type {} = '{}' chưa có → {} từ '{}'".format(
            k, pending[k], u"sẽ nhân bản khi chạy thật" if dry_run else u"không có tấm sàn dùng, không nhân bản",
            type_name(template)))
    for i in targets:
        ks = [p.kind for p in kept if p.apt == i]
        if "LOGIA" not in ks:
            warns.append(u"{}: không nhận được logia".format(names[i]))
        if "WC" not in ks:
            warns.append(u"{}: không nhận được WC".format(names[i]))
    checks = [p for p in kept if p.status.startswith(u"KIỂM TRA") or p.status.startswith(u"LỖI")]
    for p in checks:
        warns.append(u"{} {}: {}".format(names[p.apt], fmt(p.ip), p.status))
    for w in warns:
        report.append(u"CẢNH BÁO: " + w)
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra biên sàn (OUT[1]) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines([(p.floor_outer, p.holes) for p in jobs], to_mm(z))


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


def num(v, default):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


if DYNAMO:
    import traceback
    try:
        OUT = list(main(
            (IN[0] or u"").strip(),
            split_filters(IN[1] or u"00 do dt"),
            split_filters(IN[2] or u"A-Text"),
            (IN[3] or u"^CH\\d+").strip(),
            split_filters(IN[4] if IN[4] is not None else u"A-Column"),
            num(IN[5], 15.0),
            split_filters(IN[6] if IN[6] is not None else u"trượt"),
            num(IN[7], 400.0),
            split_filters(IN[8] if IN[8] is not None else u"A-Interior WC"),
            IN[9] or (u"KHO=SHT-Gỗ Công Nghiệp;WC=SHT-Gach Lat WC-300x600;LOGIA=SHT-Gach Lat Logia-300x600;"
                      u"CHANCUA=FF-Đá Granite tự nhiên"),
            IN[10] or u"KHO=0;WC=-15;LOGIA=-30;CHANCUA=0",
            num(IN[11], 10.0),
            IN[12] or u"",
            True if IN[13] is None else bool(IN[13]),
            (IN[14] if len(IN) > 14 and IN[14] is not None else u"SHT-Gach Lat-600x600").strip(),
            (IN[15] if len(IN) > 15 and IN[15] is not None else u"AV.Nét Hatch Lát Sàn").strip(),
            False if len(IN) <= 16 or IN[16] is None else bool(IN[16]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoSanCanHoTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
