# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_DanTrangCanHo_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
# Revit 2026 / Dynamo 3.6 (CPython3)
#
# Dàn trang hồ sơ chi tiết căn hộ theo mẫu CAD CT1-CH02-CTCH (TAOVP / TAOVPWC / TAOVPLG bên ACA), trên level
# của view mặt bằng đang mở. Căn hộ nhận theo sàn hoàn thiện "ARV-SanCanHo <căn> <loại>" (ARV_TaoSanCanHoTuCAD_v1).
#   1. Room: mỗi vùng kín (PlanCircuit ≥ 1 m²) nằm trong sàn của căn mà chưa có Room → tạo Room.
#      Tên theo Room mẫu của template: sàn KHO lớn nhất = Phòng khách-ăn (KA), còn lại Phòng ngủ (NG);
#      WC = Vệ sinh; logia lớn nhất = Logia phòng khách (LG1), còn lại Logia phơi đồ (LG2).
#      Number = "<căn>-<mã>", Occupant = căn. KTS soát lại tên phòng sau khi chạy.
#   2. Sheet CTCH (khung A1, 2 cột + cột ghi chú bên phải), 3 hàng như mẫu FPT P5-04.01:
#      MC 1-1 | MC 2-2 căn hộ (4.6) · MB tường xây, định vị cửa (4.1) | MB trần (4.4) ·
#      MB bố trí nội thất (4.2) | MB lát sàn (4.3). MC 1-1 song song trục X, MC 2-2 song song trục Y: một mặt
#      cắt qua tâm logia (vuông góc cạnh dài logia), mặt kia qua tâm WC – KTS kéo lại đường cắt nếu cần.
#      Tỷ lệ chung: lớn nhất trong danh sách IN[1] mà cả 6 view vừa khung (hàng cao theo view thật).
#      Cột phải 592–742: SƠ ĐỒ VỊ TRÍ CĂN HỘ (MB cả tầng VFT 1.1, 1/200–1/1000, sàn của căn tô đỏ bằng override
#      riêng view) + legend ghi chú dùng chung (bảng tường xây / trần / lát sàn: mã = Type Mark như tag, cấu tạo
#      theo các lớp của type, hatch tường theo filled region type có sẵn trùng mẫu cắt vật liệu lõi).
#   3. Sheet WC: mỗi WC một hàng (tối đa 2) × 3 MB: thiết bị (5.1) · lát sàn (5.2) · trần (5.3); tỷ lệ chung của
#      sheet = lớn nhất trong danh sách IN[2] mà mọi view vừa ô (sheet logia / sheet gộp cũng vậy).
#   4. Sheet logia: mỗi logia một hàng (tối đa 2) × MB lát sàn + thiết bị (6.1) · MB trần (4.4) · MC 1-1 (6.2).
#      Mặt cắt vuông góc cạnh dài nhất của sàn logia, qua tâm, nhìn về một nửa logia.
#      Căn có đúng 1 WC + 1 logia → gộp chi tiết WC (hàng trên) và logia (hàng dưới) vào MỘT sheet số hiệu WC,
#      tên "CHI TIẾT VỆ SINH, LOGIA CĂN HỘ …" (KTS chốt 2026-10-22).
#   5. View tạo từ View Family Type của template công ty (tự gắn view template). Tỷ lệ khác tỷ lệ template →
#      chép thông số template vào view rồi bỏ gắn template (KHÔNG sửa view template).
#   6. Tag: Room (MB nội thất), cửa đi / cửa sổ / louver (MB tường xây, MB thiết bị WC, MB logia),
#      sàn (MB lát sàn, đá chân cửa có đường dẫn), trần (MB trần), thiết bị vệ sinh (MB thiết bị WC).
#   7. Chưa làm: dim tường / cửa, cao độ, ghi chú vật liệu tường (WF-…) – KTS bổ sung tay hoặc tool sau.
# INPUT
#   IN[0] (str)  Căn hộ (cách ';', VD "CH01;CH02")
#   IN[1] (str)  Tỷ lệ sheet căn hộ thử lần lượt (VD "50;60;65;70;75;80;90;100;125;150"; một số = cố định)
#   IN[2] (str)  Tỷ lệ chi tiết WC / logia thử lần lượt (VD "20;25;30;40;50")
#   IN[3] (str)  Số hiệu sheet: "CTCH=…;WC=…;LG=…", {nn} = số của căn (CH01 → 01)
#   IN[4] (str)  Tên family khung tên (title block)
#   IN[5] (str)  Viewport type
#   IN[6] (str)  Lề crop quanh căn / WC / logia (mm)
#   IN[7] (str)  Tên legend ghi chú cột phải sheet CTCH (mặc định "GHI CHÚ CĂN HỘ"; có sẵn → dùng lại, chưa có →
#                sinh 3 bảng tường xây / trần / lát sàn từ type đang dùng trong các căn; trống = không đặt)
#   IN[8] (bool) Dry-run: True = dựng thử rồi hoàn tác, chỉ báo cáo (mặc định True)
#   IN[9] (bool) Làm lại (mặc định False): căn đã có view '<căn> - …' / sheet số theo IN[3] → xóa đúng các view,
#                sheet đó (Room giữ nguyên) rồi dựng mới; legend ghi chú xóa nội dung, vẽ lại tại chỗ.
#                False → căn đã có kết quả bị bỏ qua.
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, cảnh báo, đường dẫn log, từng view / sheet
#   OUT[1] (list)       Trống (giữ chỗ cho đồng bộ với các tool khác)

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
    from Autodesk.Revit.DB import (FilteredElementCollector, XYZ, UV, Transform, Transaction, UnitUtils, UnitTypeId,
                                   ModelPathUtils, BuiltInParameter, BuiltInCategory, Floor, Ceiling, Level, Sketch,
                                   ViewType, ViewFamily, ViewFamilyType, ViewPlan, ViewSection, ViewSheet, Viewport,
                                   ViewportRotation, BoundingBoxXYZ, ElementId, IndependentTag, TagOrientation,
                                   Reference, LinkElementId, FamilySymbol, ElementType, LocationPoint, View,
                                   SpatialElement, FailureProcessingResult, IFailuresPreprocessor, FailureSeverity,
                                   FilledRegion, FilledRegionType, CurveLoop, Line, TextNote, TextNoteOptions,
                                   TextNoteType, HorizontalTextAlignment, OverrideGraphicSettings, Color,
                                   FillPatternElement, Category, ViewDuplicateOption, ViewDetailLevel, Wall,
                                   WallType, BoundingBoxIntersectsFilter, Outline, CurveElement, DocumentValidation,
                                   GraphicsStyleType)
    from System.Collections.Generic import List
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Dàn trang chi tiết căn hộ"
SCRIPT_TAG = u"ARV_DanTrangCanHo_v1"
FLOOR_TAG = u"ARV-SanCanHo"
CEIL_TAG = u"ARV-TranCanHo"
MIN_ROOM_M2 = 1.0

# Room mẫu trong template G19 / công ty: mã → tên
ROOM_NAMES = {"KA": u"Phòng khách-ăn", "NG": u"Phòng ngủ", "WC": u"Vệ sinh",
              "LG1": u"Logia phòng khách", "LG2": u"Logia phơi đồ"}

# Khung A1 AV-Khung A1(841x594): hộp bao family 0,5–841,5 × −1–593 gồm cả viền vô hình (PDF); khung NHÌN THẤY
# đo lại 2026-10-22 bằng nét chuẩn trên sheet: viền trong x 35,4 – cột khung tên 733,  y 16,3 – 576,5 mm.
AREA_X0, AREA_X1, AREA_Y0, AREA_Y1 = 36.0, 733.0, 17.0, 576.0
CTCH_X = (36.0, 309.5, 583.0)         # 2 cột viewport, cột phải 583–733 (key plan + ghi chú) như mẫu FPT
NOTE_X0, NOTE_X1 = 583.0, 733.0
NOTE_X = (NOTE_X0 + NOTE_X1) / 2.0
KEY_SCALES = (200, 250, 300, 400, 500, 600, 800, 1000)
KEY_MAX_H = 120.0                    # mm giấy, chiều cao tối đa key plan
KEY_MARGIN = 1500.0                  # mm, lề crop quanh các căn của tầng
TABLE_W = (14.0, 92.0, 24.0)         # mm giấy: cột ký hiệu / cấu tạo / dày-cao độ
KIND_LABEL = {"KHO": u"ngủ, khách", "WC": u"WC", "LOGIA": u"logia", "CHANCUA": u"chân cửa"}
TEXT_TITLE = u"AV_Text 3mm_Arial-Bold"
TEXT_BODY = u"AV_Arial_2 mm_Dot"
CELL_PAD = 8.0                       # mm giấy, khoảng hở tối thiểu quanh viewport trong ô
TITLE_ROOM = 14.0                    # mm giấy dành cho tên hình dưới viewport
TITLE_LABEL_GAP = 7.0                # mm giấy từ đáy hình thấp nhất của hàng tới tâm tên hình
DIVIDER_STYLES = (u"AV.Nét Khuất.W1", u"<Hidden>")   # line style nét đứt chia ô (có sẵn trong template)

# Tag (family : type) – template công ty
TAG_ROOM = (u"AV_Room Tag", u"Room Tag Name+ area")
TAG_DOOR = (u"AV_Door Tag", u"AV_Door Tag")
TAG_WIN = (u"AV_Window Tag", u"Window Tag")
TAG_LOUVER = (u"AV_Louver Tag", u"Louver Tag")
TAG_FLOOR = (u"AV_Floor Tag", u"Plan")
TAG_CEIL = (u"AV_Celling Tag", u"Section Tag")
TAG_PLUMB = (u"AV_Plumbing Fixture Tag", u"AV_Plumbing Fixture Tag")


# --- Hình học 2D thuần (mm) ---------------------------------------------------------
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


def interior_point(outer, holes, inner=150.0):
    """Điểm trong vòng ngoài, ngoài các lỗ: tâm hộp bao nếu lọt, không thì trung điểm cạnh dài lùi vào trong."""
    xs, ys = [p[0] for p in outer], [p[1] for p in outer]
    c = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    if point_in(c, outer) and not any(point_in(c, h) for h in holes):
        return c
    ccw = signed_area(outer) > 0
    s = 1.0 if ccw else -1.0
    edges = sorted(range(len(outer)), key=lambda i: -math.hypot(outer[(i + 1) % len(outer)][0] - outer[i][0],
                                                                outer[(i + 1) % len(outer)][1] - outer[i][1]))
    for i in edges:
        a, b = outer[i], outer[(i + 1) % len(outer)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l < 3 * inner:
            continue
        p = ((a[0] + b[0]) / 2.0 - s * (b[1] - a[1]) / l * inner, (a[1] + b[1]) / 2.0 + s * (b[0] - a[0]) / l * inner)
        if point_in(p, outer) and not any(point_in(p, h) for h in holes):
            return p
    return c


def bbox_of(loops, margin=0.0):
    xs = [p[0] for l in loops for p in l]
    ys = [p[1] for l in loops for p in l]
    return (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)


def longest_edge_dir(outer):
    best, d = -1.0, (1.0, 0.0)
    for i in range(len(outer)):
        a, b = outer[i], outer[(i + 1) % len(outer)]
        l = math.hypot(b[0] - a[0], b[1] - a[1])
        if l > best:
            best, d = l, ((b[0] - a[0]) / l, (b[1] - a[1]) / l)
    return d


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
    return [s.strip() for s in (text or u"").replace(u",", u";").split(u";") if s.strip()]


def apt_digits(apt):
    d = u"".join(ch for ch in apt if ch.isdigit())
    return d.zfill(2) if d else apt


def cells_row(n_cols, n_rows):
    """Tâm các ô (mm giấy) chia đều vùng vẽ: [hàng][cột] → (cx, cy, w, h)."""
    w = (AREA_X1 - AREA_X0) / n_cols
    h = (AREA_Y1 - AREA_Y0) / n_rows
    return [[(AREA_X0 + w * (c + 0.5), AREA_Y1 - h * (r + 0.5), w, h) for c in range(n_cols)] for r in range(n_rows)]


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


def P(x_mm, y_mm, z_ft=0.0):
    return XYZ(from_mm(x_mm), from_mm(y_mm), z_ft)


def get_name(element):
    try:
        return element.Name
    except Exception:
        p = element.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


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


def sketch_loops(el):
    """Biên sketch (sàn / trần) → [vòng điểm mm]; vòng ngoài = vòng diện tích lớn nhất."""
    try:
        sk = doc.GetElement(el.SketchId)
    except Exception:
        sk = None
    if not isinstance(sk, Sketch):
        return [], []
    loops = []
    for arr in sk.Profile:
        loop = []
        for c in list(arr):
            loop.extend([(to_mm(p.X), to_mm(p.Y)) for p in list(c.Tessellate())[:-1]])
        if len(loop) >= 3:
            loops.append(loop)
    if not loops:
        return [], []
    k = max(range(len(loops)), key=lambda i: abs(signed_area(loops[i])))
    return loops[k], [l for i, l in enumerate(loops) if i != k]


class Part(object):
    """Một tấm sàn / trần hoàn thiện của căn."""
    def __init__(self, el, kind):
        self.el = el
        self.kind = kind
        self.outer, self.holes = sketch_loops(el)
        self.area = (abs(signed_area(self.outer)) - sum(abs(signed_area(h)) for h in self.holes)) / 1e6 \
            if self.outer else 0.0
        self.ip = interior_point(self.outer, self.holes) if self.outer else None

    def contains(self, pt):
        return bool(self.outer) and point_in(pt, self.outer) and not any(point_in(pt, h) for h in self.holes)


class Ctx(object):
    """Type / view family type tra một lần."""
    def __init__(self, title_block, vp_type):
        self.vft = {}
        for t in FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements():
            self.vft.setdefault((t.ViewFamily, norm(get_name(t)).split(u" ")[0]), t)
        tbs = [t for t in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_TitleBlocks)
               .WhereElementIsElementType().ToElements() if norm(t.FamilyName) == norm(title_block)]
        if not tbs:
            names = sorted(set(t.FamilyName for t in FilteredElementCollector(doc)
                               .OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsElementType().ToElements()))
            raise StopReport([u"DỪNG: không có khung tên '{}' (IN[4]). Các khung tên: {}".format(
                title_block, u", ".join(names))])
        self.title_block = tbs[0]
        vpts = [t for t in FilteredElementCollector(doc).OfClass(ElementType).ToElements()
                if t.FamilyName == u"Viewport" and norm(get_name(t)) == norm(vp_type)]
        if not vpts:
            names = [get_name(t) for t in FilteredElementCollector(doc).OfClass(ElementType).ToElements()
                     if t.FamilyName == u"Viewport"]
            raise StopReport([u"DỪNG: không có viewport type '{}' (IN[5]). Các type: {}".format(
                vp_type, u", ".join(names))])
        self.vp_type = vpts[0]
        # Legend ghi chú đặt bằng viewport không tên (như mẫu); không có thì dùng type chính
        self.vp_notitle = next((t for t in FilteredElementCollector(doc).OfClass(ElementType).ToElements()
                                if t.FamilyName == u"Viewport" and norm(get_name(t)) == u"No Title"), self.vp_type)
        self.divider_style = None
        for sub in Category.GetCategory(doc, BuiltInCategory.OST_Lines).SubCategories:
            if sub.Name in DIVIDER_STYLES and (self.divider_style is None or sub.Name == DIVIDER_STYLES[0]):
                self.divider_style = sub.GetGraphicsStyle(GraphicsStyleType.Projection)
        self.tags = {}
        self.missing_tags = []
        for key, bic in ((TAG_ROOM, BuiltInCategory.OST_RoomTags), (TAG_DOOR, BuiltInCategory.OST_DoorTags),
                         (TAG_WIN, BuiltInCategory.OST_WindowTags), (TAG_LOUVER, BuiltInCategory.OST_WindowTags),
                         (TAG_FLOOR, BuiltInCategory.OST_FloorTags), (TAG_CEIL, BuiltInCategory.OST_CeilingTags),
                         (TAG_PLUMB, BuiltInCategory.OST_PlumbingFixtureTags)):
            found = [t for t in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsElementType().ToElements()
                     if norm(t.FamilyName) == norm(key[0]) and norm(get_name(t)) == norm(key[1])]
            if found:
                self.tags[key] = found[0].Id
            else:
                self.missing_tags.append(u"{} : {}".format(key[0], key[1]))

    def text_type(self, name):
        if not hasattr(self, "_text_types"):
            self._text_types = dict((norm(get_name(t)), t) for t in
                                    FilteredElementCollector(doc).OfClass(TextNoteType).ToElements())
        return self._text_types.get(norm(name))

    def family_type(self, family, code):
        t = self.vft.get((family, code))
        if t is None:
            raise StopReport([u"DỪNG: không có View Family Type '{} …' ({}) trong template.".format(code, family)])
        return t


class Apt(object):
    def __init__(self, name):
        self.name = name
        self.floors = []      # [Part]
        self.ceilings = []    # [Part]
        self.rooms = []       # [(code, Room)]
        self.views = []       # [(sheet key, View, tỷ lệ, kết quả)]
        self.sheets = []      # [(key, ViewSheet)]
        self.notes = []
        self.wc_labels = {}   # Part → "WC1"
        self.lg_labels = {}   # Part → "LG1"

    def of_kind(self, kind):
        return [f for f in self.floors if f.kind == kind]

    def bbox(self, margin):
        return bbox_of([f.outer for f in self.floors if f.outer], margin)


def collect_apartments(level, wanted):
    apts = dict((a.upper(), Apt(a.upper())) for a in wanted)
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId != level.Id:
            continue
        w = norm(comment_of(fl)).split()
        if len(w) >= 3 and w[0] == FLOOR_TAG and w[1].upper() in apts:
            part = Part(fl, w[-1].upper())
            if part.outer:
                apts[w[1].upper()].floors.append(part)
    for cg in FilteredElementCollector(doc).OfClass(Ceiling).ToElements():
        if cg.LevelId != level.Id:
            continue
        w = norm(comment_of(cg)).split()
        if len(w) >= 3 and w[0] == CEIL_TAG and w[1].upper() in apts:
            part = Part(cg, w[-1].upper())
            if part.outer:
                apts[w[1].upper()].ceilings.append(part)
    return [apts[a.upper()] for a in wanted]


# --- Room ------------------------------------------------------------------------------
def plan_circuits(level):
    try:
        topo = doc.get_PlanTopology(level)
    except Exception:
        topo = doc.PlanTopology[level]
    return list(topo.Circuits)


def make_rooms(apt, level, circuits, placed_rooms):
    """Gán mã phòng cho vùng kín trong sàn căn; tạo Room cho vùng chưa có. Trả về [(code, Room, mới?)]."""
    found = []    # (kind, area_m2, pt, room hoặc None)
    for c in circuits:
        p = c.GetPointInside()
        pt = (to_mm(p.U), to_mm(p.V))
        area = c.Area * 0.09290304
        if area < MIN_ROOM_M2:
            continue
        part = next((f for f in apt.floors if f.kind in ("KHO", "WC", "LOGIA") and f.contains(pt)), None)
        if part is None:
            continue
        room = None
        if c.IsRoomLocated:
            room = next((r for r in placed_rooms if r.IsPointInRoom(P(pt[0], pt[1], level.Elevation + 1.0))), None)
            if room is None:
                continue
        found.append((part.kind, area, pt, room))
    result = []
    kho = sorted([f for f in found if f[0] == "KHO"], key=lambda f: -f[1])
    lg = sorted([f for f in found if f[0] == "LOGIA"], key=lambda f: -f[1])
    wc = sorted([f for f in found if f[0] == "WC"], key=lambda f: (f[2][0], f[2][1]))
    plan = [("KA" if i == 0 else "NG", f) for i, f in enumerate(kho)]
    plan += [("LG1" if i == 0 else "LG2", f) for i, f in enumerate(lg)]
    plan += [("WC", f) for f in wc]
    n_code = {}
    for code, f in plan:
        n_code[code] = n_code.get(code, 0) + 1
        number = u"{}-{}{}".format(apt.name, code, n_code[code] if code in ("NG", "WC", "LG2") else u"")
        room = f[3]
        if room is None:
            room = doc.Create.NewRoom(level, UV(from_mm(f[2][0]), from_mm(f[2][1])))
            room.Name = ROOM_NAMES[code]
            room.Number = number
            occ = room.get_Parameter(BuiltInParameter.ROOM_OCCUPANCY)
            if occ is not None and not occ.IsReadOnly:
                occ.Set(apt.name)
            result.append((code, room, True))
        else:
            result.append((code, room, False))
    return result


# --- View ------------------------------------------------------------------------------
def set_scale(view, scale):
    """Đặt tỷ lệ; template khóa tỷ lệ khác → chép thông số template vào view rồi bỏ gắn template."""
    note = u""
    tid = view.ViewTemplateId
    if tid != ElementId.InvalidElementId and view.Scale != scale:
        tpl = doc.GetElement(tid)
        view.ViewTemplateId = ElementId.InvalidElementId
        view.ApplyViewTemplateParameters(tpl)
        note = u"bỏ gắn template '{}' (chép thông số) để đặt 1/{}".format(get_name(tpl), scale)
    view.Scale = scale
    return note


def make_plan(ctx, level, family, code, name, title, scale, box):
    view = ViewPlan.Create(doc, ctx.family_type(family, code).Id, level.Id)
    view.Name = name
    tpl_name = get_name(doc.GetElement(view.ViewTemplateId)) if view.ViewTemplateId != ElementId.InvalidElementId \
        else u"(không)"
    note = set_scale(view, scale)
    cb = view.CropBox
    cb.Min = XYZ(from_mm(box[0]), from_mm(box[1]), cb.Min.Z)
    cb.Max = XYZ(from_mm(box[2]), from_mm(box[3]), cb.Max.Z)
    view.CropBox = cb
    view.CropBoxActive = True
    view.CropBoxVisible = False
    annotation_crop(view)
    view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(title)
    return view, note or u"template '{}'".format(tpl_name)


def make_apt_section(ctx, level, name, title, scale, box, along_x, cut, height_mm):
    """Mặt cắt căn hộ (4.6): along_x = đường cắt song song trục X tại y = cut (nhìn về −Y), ngược lại song song
    trục Y tại x = cut (nhìn về +X). Rộng = hộp căn, sâu từ đường cắt tới mép hộp, cao −300 → tầng + 300."""
    t = Transform.Identity
    if along_x:
        t.Origin = XYZ(from_mm((box[0] + box[2]) / 2.0), from_mm(cut), level.Elevation)
        t.BasisX = XYZ(1, 0, 0)
        t.BasisZ = XYZ(0, -1, 0)          # = BasisX × BasisY
        w, depth = box[2] - box[0], cut - box[1]
    else:
        t.Origin = XYZ(from_mm(cut), from_mm((box[1] + box[3]) / 2.0), level.Elevation)
        t.BasisX = XYZ(0, 1, 0)
        t.BasisZ = XYZ(1, 0, 0)
        w, depth = box[3] - box[1], box[2] - cut
    t.BasisY = XYZ(0, 0, 1)
    bb = BoundingBoxXYZ()
    bb.Transform = t
    bb.Min = XYZ(from_mm(-w / 2.0), from_mm(-300), 0)          # mặt cắt ở Min.Z
    bb.Max = XYZ(from_mm(w / 2.0), from_mm(height_mm + 300), from_mm(max(depth, 300.0)))
    view = ViewSection.CreateSection(doc, ctx.family_type(ViewFamily.Section, u"4.6").Id, bb)
    view.Name = name
    annotation_crop(view)
    note = set_scale(view, scale)
    view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(title)
    return view, note or u"template 4.6"


def section_cuts(apt):
    """Vị trí 2 mặt cắt căn: một qua tâm logia vuông góc cạnh dài logia, một qua tâm WC theo phương còn lại.
    Trả về (y của MC 1-1 song song X, x của MC 2-2 song song Y)."""
    box = apt.bbox(0.0)
    cy, cx = (box[1] + box[3]) / 2.0, (box[0] + box[2]) / 2.0
    wc = apt.of_kind("WC")
    lg = sorted(apt.of_kind("LOGIA"), key=lambda f: -f.area)
    wc_c = bbox_of([wc[0].outer]) if wc else None
    lg_c = bbox_of([lg[0].outer]) if lg else None
    y11, x22 = cy, cx
    if lg_c is not None:
        d = longest_edge_dir(lg[0].outer)
        if abs(d[0]) >= abs(d[1]):        # logia nằm ngang → cắt dọc (MC 2-2) qua logia
            x22 = (lg_c[0] + lg_c[2]) / 2.0
            if wc_c is not None:
                y11 = (wc_c[1] + wc_c[3]) / 2.0
        else:
            y11 = (lg_c[1] + lg_c[3]) / 2.0
            if wc_c is not None:
                x22 = (wc_c[0] + wc_c[2]) / 2.0
    elif wc_c is not None:
        y11 = (wc_c[1] + wc_c[3]) / 2.0
    return y11, x22


def make_logia_section(ctx, level, part, name, title, scale, height_mm):
    d = longest_edge_dir(part.outer)
    u = (-d[1], d[0])
    pu = [p[0] * u[0] + p[1] * u[1] for p in part.outer]
    pd = [p[0] * d[0] + p[1] * d[1] for p in part.outer]
    cu, cd = (min(pu) + max(pu)) / 2.0, (min(pd) + max(pd)) / 2.0
    w, l = max(pu) - min(pu), max(pd) - min(pd)
    t = Transform.Identity
    t.Origin = XYZ(from_mm(cu * u[0] + cd * d[0]), from_mm(cu * u[1] + cd * d[1]), level.Elevation)
    t.BasisX = XYZ(u[0], u[1], 0)
    t.BasisY = XYZ(0, 0, 1)
    t.BasisZ = XYZ(u[1], -u[0], 0)        # = BasisX × BasisY
    bb = BoundingBoxXYZ()
    bb.Transform = t
    # Mặt cắt nằm ở Min.Z (đo qua MCP 2026-10-22) → Min.Z = 0 tại tâm logia, nhìn sâu nửa logia + 200
    bb.Min = XYZ(from_mm(-w / 2.0 - 600), from_mm(-600), 0)
    bb.Max = XYZ(from_mm(w / 2.0 + 600), from_mm(height_mm + 400), from_mm(l / 2.0 + 200))
    view = ViewSection.CreateSection(doc, ctx.family_type(ViewFamily.Section, u"6.2").Id, bb)
    view.Name = name
    annotation_crop(view)
    note = set_scale(view, scale)
    view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(title)
    return view, note or u"template 6.2"


# --- Tag -------------------------------------------------------------------------------
def set_type(el, type_id):
    """Đổi type. pythonnet (Dynamo CPython3) không khớp overload Element.ChangeTypeId cho RoomTag →
    gán qua tham số ELEM_TYPE_PARAM, cuối cùng RoomTag.RoomTagType."""
    try:
        el.ChangeTypeId(type_id)
        return
    except TypeError:
        pass
    p = el.get_Parameter(BuiltInParameter.ELEM_TYPE_PARAM)
    if p is not None and not p.IsReadOnly and p.Set(type_id):
        return
    if hasattr(el, "RoomTagType"):
        el.RoomTagType = doc.GetElement(type_id)
        return
    raise Exception(u"Không đổi được type của phần tử Id {}".format(id_value(el.Id)))


def in_box(pt, box):
    return box[0] <= pt[0] <= box[2] and box[1] <= pt[1] <= box[3]


def location_mm(el):
    loc = el.Location
    if isinstance(loc, LocationPoint):
        return (to_mm(loc.Point.X), to_mm(loc.Point.Y))
    bb = el.get_BoundingBox(None)
    if bb is None:
        return None
    return (to_mm((bb.Min.X + bb.Max.X) / 2.0), to_mm((bb.Min.Y + bb.Max.Y) / 2.0))


def tag(ctx, key, view, el, pt_mm, z, leader=False, head=None):
    tid = ctx.tags.get(key)
    if tid is None:
        return 0
    t = IndependentTag.Create(doc, tid, view.Id, Reference(el), leader, TagOrientation.Horizontal,
                              P(pt_mm[0], pt_mm[1], z))
    if leader and head is not None:
        try:
            t.TagHeadPosition = P(head[0], head[1], z)
        except Exception:
            pass
    return 1


def tag_openings(ctx, view, box, z):
    n = 0
    for bic in (BuiltInCategory.OST_Doors, BuiltInCategory.OST_Windows):
        for el in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType().ToElements():
            pt = location_mm(el)
            if pt is None or not in_box(pt, box):
                continue
            if bic == BuiltInCategory.OST_Doors:
                key = TAG_DOOR
            else:
                key = TAG_LOUVER if u"LanCan" in comment_of(el) or u"Louver" in get_name(el) else TAG_WIN
            n += tag(ctx, key, view, el, pt, z)
    return n


def tag_floors(ctx, view, parts, z):
    n = 0
    for f in parts:
        if f.kind == "CHANCUA":
            n += tag(ctx, TAG_FLOOR, view, f.el, f.ip, z, True, (f.ip[0] + 600, f.ip[1] + 600))
        else:
            n += tag(ctx, TAG_FLOOR, view, f.el, f.ip, z)
    return n


# --- Sheet -----------------------------------------------------------------------------
def new_sheet(ctx, number, name, ref_sheet):
    sh = ViewSheet.Create(doc, ctx.title_block.Id)
    sh.SheetNumber = number
    sh.Name = name
    if ref_sheet is not None:     # nhóm trong Project Browser như sheet mục A.5
        for pname in (u"Lọc Thư Mục Sheet", u"Lọc Giai Đoạn Hồ Sơ"):
            src, dst = ref_sheet.LookupParameter(pname), sh.LookupParameter(pname)
            if src is not None and dst is not None and not dst.IsReadOnly and src.AsString():
                dst.Set(src.AsString())
    return sh


def place(ctx, sheet, view, cell):
    cx, cy = cell[0], cell[1] + TITLE_ROOM / 2.0
    vp = Viewport.Create(doc, sheet.Id, view.Id, XYZ(from_mm(cx), from_mm(cy), 0))
    set_type(vp, ctx.vp_type.Id)
    return vp


def fits(vp, cell):
    o = vp.GetBoxOutline()
    w = to_mm(o.MaximumPoint.X - o.MinimumPoint.X)
    h = to_mm(o.MaximumPoint.Y - o.MinimumPoint.Y)
    return w <= cell[2] - 2 * CELL_PAD and h <= cell[3] - 2 * CELL_PAD - TITLE_ROOM, (w, h)


def recenter(vps, cells):
    for vp, cell in zip(vps, cells):
        vp.SetBoxCenter(XYZ(from_mm(cell[0]), from_mm(cell[1] + TITLE_ROOM / 2.0), 0))


def outline_size(vp):
    o = vp.GetBoxOutline()
    return to_mm(o.MaximumPoint.X - o.MinimumPoint.X), to_mm(o.MaximumPoint.Y - o.MinimumPoint.Y)


def grid_layout(vps, cells):
    """Đặt viewport vào tâm ô; True nếu tất cả vừa ô."""
    recenter(vps, cells)
    return all(fits(vp, cell)[0] for vp, cell in zip(vps, cells))


def fit_scale(views, scales, layout):
    """Thử tỷ lệ từ lớn (mẫu số nhỏ) đến nhỏ; dừng ở tỷ lệ đầu tiên layout() vừa khung.
    Trả về (tỷ lệ, vừa?) – không vừa ở tỷ lệ cuối thì giữ tỷ lệ cuối."""
    for s in scales:
        for v in views:
            if v.Scale != s:
                set_scale(v, s)
        doc.Regenerate()
        if layout():
            doc.Regenerate()
            return s, True
    doc.Regenerate()
    return scales[-1], False


def ctch_layout(rows, bounds=None):
    """Sheet CTCH: các hàng viewport (trên → dưới) trong 2 cột x 3–297,5–592, hàng cao theo view thật,
    khoảng thừa chia đều. True nếu vừa; bounds (list) nhận cao độ ranh giới giữa các hàng (mm giấy)."""
    col_w = CTCH_X[1] - CTCH_X[0]
    heights = []
    for row in rows:
        sizes = [outline_size(vp) for vp in row]
        if any(w > col_w - 2 * CELL_PAD for w, _h in sizes):
            return False
        heights.append(max(h for _w, h in sizes) + TITLE_ROOM + 2 * CELL_PAD)
    avail = AREA_Y1 - AREA_Y0
    if sum(heights) > avail:
        return False
    gap = (avail - sum(heights)) / len(rows)
    y = AREA_Y1
    if bounds is not None:
        del bounds[:]
    for row, h in zip(rows, heights):
        cy = y - (h + gap) / 2.0
        y -= h + gap
        if bounds is not None and y > AREA_Y0 + 1.0:
            bounds.append(y)
        for c, vp in enumerate(row):
            vp.SetBoxCenter(XYZ(from_mm((CTCH_X[c] + CTCH_X[c + 1]) / 2.0), from_mm(cy + TITLE_ROOM / 2.0), 0))
    return True


def annotation_crop(view):
    """Cắt chú thích theo khung crop: ký hiệu mặt cắt / tag ngoài crop không làm phình khung viewport."""
    p = view.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE)
    if p is not None and not p.IsReadOnly:
        p.Set(1)


def align_titles(rows):
    """Tên hình: giữa, ngay dưới hình vẽ; cùng hàng thẳng một cao độ; gạch dưới dài vừa chữ (ước tính 2,2 mm/ký tự
    – đo trên sheet G19: 43 ký tự ≈ 102 mm). Đo trên Revit 2026: nhãn từ (min.X + LabelOffset.X − 9) tới
    (min.X + LabelOffset.X + LabelLineLength), tâm nhãn theo phương đứng ≈ min.Y + LabelOffset.Y."""
    for row in rows:
        boxes = [vp.GetBoxOutline() for vp in row]
        bottom = min(to_mm(o.MinimumPoint.Y) for o in boxes)
        for vp, o in zip(row, boxes):
            w = to_mm(o.MaximumPoint.X - o.MinimumPoint.X)
            view = doc.GetElement(vp.ViewId)
            p = view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION)
            title = (p.AsString() if p else u"") or get_name(view)
            length = len(title) * 2.2 + 6.0
            try:
                vp.LabelLineLength = from_mm(length)
                vp.LabelOffset = XYZ(from_mm((w - length + 9.0) / 2.0),
                                     from_mm(bottom - TITLE_LABEL_GAP - to_mm(o.MinimumPoint.Y)), 0)
            except Exception:
                pass


def hide_elements(view, section_views):
    """Ẩn ký hiệu của các mặt cắt trong view. Ký hiệu là phần tử riêng category OST_Viewers, cùng tên nhưng KHÁC
    id với view mặt cắt (đo qua MCP 2026-10-22) – ẩn theo id view không có tác dụng."""
    names = set(get_name(s) for s in section_views if s.Id != view.Id)
    ids = List[ElementId]()
    for e in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Viewers).WhereElementIsNotElementType() \
            .ToElements():
        if get_name(e) in names and e.CanBeHidden(view) and not e.IsHidden(view):
            ids.Add(e.Id)
    if ids.Count:
        view.HideElements(ids)


def draw_dividers(ctx, sheet, segments):
    """Nét đứt chia ô trên sheet (line style có sẵn, không tạo mới). segments = [((x1, y1), (x2, y2))] mm giấy."""
    for a, b in segments:
        c = doc.Create.NewDetailCurve(sheet, Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), 0),
                                                              XYZ(from_mm(b[0]), from_mm(b[1]), 0)))
        if ctx.divider_style is not None:
            c.LineStyle = ctx.divider_style


# --- Cột phải: key plan + legend ghi chú -----------------------------------------------------
def floors_box(level):
    """Hộp bao (mm) mọi sàn ARV-SanCanHo trên level – vùng các căn của tầng."""
    loops = []
    for fl in FilteredElementCollector(doc).OfClass(Floor).ToElements():
        if fl.LevelId == level.Id and norm(comment_of(fl)).startswith(FLOOR_TAG):
            bb = fl.get_BoundingBox(None)
            if bb is not None:
                loops.append([(to_mm(bb.Min.X), to_mm(bb.Min.Y)), (to_mm(bb.Max.X), to_mm(bb.Max.Y))])
    return bbox_of(loops) if loops else None


def hide_category(view, bic):
    try:
        view.SetCategoryHidden(Category.GetCategory(doc, bic).Id, True)
    except Exception:
        pass


def make_key_plan(ctx, level, apt, bld):
    """Sơ đồ vị trí căn: MB cả tầng (VFT 1.1, bỏ gắn template), tỷ lệ lớn nhất vừa cột phải, sàn của căn tô đỏ
    (override riêng view – không tạo filter / style mới), ẩn trục / mặt cắt / cao độ, chữ tên căn."""
    view = ViewPlan.Create(doc, ctx.family_type(ViewFamily.FloorPlan, u"1.1").Id, level.Id)
    view.Name = u"{} - SĐ VỊ TRÍ".format(apt.name)
    tid = view.ViewTemplateId
    if tid != ElementId.InvalidElementId:
        view.ViewTemplateId = ElementId.InvalidElementId
        view.ApplyViewTemplateParameters(doc.GetElement(tid))
    box = (bld[0] - KEY_MARGIN, bld[1] - KEY_MARGIN, bld[2] + KEY_MARGIN, bld[3] + KEY_MARGIN)
    w, h = box[2] - box[0], box[3] - box[1]
    max_w = NOTE_X1 - NOTE_X0 - 2 * CELL_PAD - 6.0        # 6 mm: khung viewport rộng hơn crop
    view.Scale = next((s for s in KEY_SCALES if w / s <= max_w and h / s <= KEY_MAX_H), KEY_SCALES[-1])
    cb = view.CropBox
    cb.Min = XYZ(from_mm(box[0]), from_mm(box[1]), cb.Min.Z)
    cb.Max = XYZ(from_mm(box[2]), from_mm(box[3]), cb.Max.Z)
    view.CropBox = cb
    view.CropBoxActive = True
    view.CropBoxVisible = False
    p = view.get_Parameter(BuiltInParameter.VIEWER_ANNOTATION_CROP_ACTIVE)
    if p is not None and not p.IsReadOnly:
        p.Set(1)
    view.DetailLevel = ViewDetailLevel.Coarse
    for bic in (BuiltInCategory.OST_Grids, BuiltInCategory.OST_Sections, BuiltInCategory.OST_Elev,
                BuiltInCategory.OST_ElevationMarks, BuiltInCategory.OST_Callouts):
        hide_category(view, bic)
    solid = next((f for f in FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements()
                  if f.GetFillPattern().IsSolidFill), None)
    if solid is not None:
        ogs = OverrideGraphicSettings()
        red = Color(255, 0, 0)
        ogs.SetSurfaceForegroundPatternId(solid.Id)
        ogs.SetSurfaceForegroundPatternColor(red)
        ogs.SetCutForegroundPatternId(solid.Id)
        ogs.SetCutForegroundPatternColor(red)
        for f in apt.floors:
            view.SetElementOverrides(f.el.Id, ogs)
    tt = ctx.text_type(u"AV_Text 3.5mm_Arial")
    if tt is not None:
        abox = apt.bbox(0.0)
        TextNote.Create(doc, view.Id, P(abox[2] + 300, abox[3] + 300), u"CĂN HỘ {}".format(apt.name),
                        TextNoteOptions(tt.Id))
    view.get_Parameter(BuiltInParameter.VIEW_DESCRIPTION).Set(u"SƠ ĐỒ VỊ TRÍ CĂN HỘ {} – {}".format(
        apt.name, level.Name.upper()))
    return view


def strip_num(name):
    """'2.1 Vữa trát tường' → 'Vữa trát tường'."""
    s = (name or u"").strip()
    i = 0
    while i < len(s) and (s[i].isdigit() or s[i] in u". "):
        i += 1
    return s[i:] or s


def layers_text(cs, is_wall):
    """Mô tả cấu tạo theo các lớp của type (không dùng Type Comments vì đang ghi sai)."""
    if cs is None:
        return u""
    items = []
    for ly in cs.GetLayers():
        w = to_mm(ly.Width)
        if w < 0.5:
            continue
        m = doc.GetElement(ly.MaterialId)
        items.append((strip_num(get_name(m)) if m is not None else u"(không vật liệu)", w))
    if is_wall and items:
        core = max(items, key=lambda it: it[1])
        rest = [it for it in items if it is not core]
        parts = [u"{} dày {:.0f}".format(core[0], core[1])]
        seen = []
        for it in rest:
            if (it[0], round(it[1])) in seen:
                continue
            n = sum(1 for r in rest if r[0] == it[0] and round(r[1]) == round(it[1]))
            seen.append((it[0], round(it[1])))
            parts.append(u"{} dày {:.0f}{}".format(it[0], it[1], u" hai mặt" if n >= 2 else u""))
    else:
        parts = [u"{} dày {:.0f}".format(n, w) for n, w in items]
    return u", ".join(parts)          # giữ nguyên chữ hoa/thường tên vật liệu như trong mô hình


def type_mark(t):
    p = t.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_MARK)
    return ((p.AsString() if p else u"") or u"").strip()


def collect_note_rows(level, apts):
    """Các type tường / trần / sàn dùng trong các căn → 3 nhóm dòng bảng. Mỗi dòng
    {swatch, code, desc, val}. Trả về (walls, ceilings, floors, cảnh báo)."""
    warns = []
    frts = dict((id_value(t.ForegroundPatternId), t) for t in
                FilteredElementCollector(doc).OfClass(FilledRegionType).ToElements())
    floor_kinds, ceil_kinds, ceil_h, types = {}, {}, {}, {}
    for a in apts:
        for f in a.floors:
            tid = id_value(f.el.GetTypeId())
            types[tid] = doc.GetElement(f.el.GetTypeId())
            floor_kinds.setdefault(tid, set()).add(f.kind)
        for c in a.ceilings:
            tid = id_value(c.el.GetTypeId())
            types[tid] = doc.GetElement(c.el.GetTypeId())
            ceil_kinds.setdefault(tid, set()).add(c.kind)
            hp = c.el.get_Parameter(BuiltInParameter.CEILING_HEIGHTABOVELEVEL_PARAM)
            if hp is not None:
                ceil_h.setdefault(tid, set()).add(int(round(to_mm(hp.AsDouble()))))
    wall_types, len_h = {}, {}
    for a in apts:
        b = a.bbox(200.0)
        flt = BoundingBoxIntersectsFilter(Outline(XYZ(from_mm(b[0]), from_mm(b[1]), level.Elevation - 1.0),
                                                  XYZ(from_mm(b[2]), from_mm(b[3]), level.Elevation + 10.0)))
        for w in FilteredElementCollector(doc).OfClass(Wall).WherePasses(flt).ToElements():
            wt = doc.GetElement(w.GetTypeId())
            if isinstance(wt, WallType) and wt.GetCompoundStructure() is not None:
                wall_types[id_value(wt.Id)] = wt
                hp = w.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)
                if hp is not None:
                    len_h.setdefault(id_value(wt.Id), set()).add(int(round(to_mm(hp.AsDouble()))))

    def kinds_text(ks):
        order = ["KHO", "WC", "LOGIA", "CHANCUA"]
        return u", ".join(KIND_LABEL.get(k, k.lower()) for k in order if k in ks)

    walls, floors, ceilings, len_rows = [], [], [], []
    for tid, wt in sorted(wall_types.items(), key=lambda kv: -kv[1].GetCompoundStructure().GetWidth()):
        cs = wt.GetCompoundStructure()
        width = to_mm(cs.GetWidth())
        name = get_name(wt)
        mark = type_mark(wt)
        if name.upper().startswith(u"LCT"):        # len chân tường → bảng lát sàn như mẫu
            hs = sorted(len_h.get(tid, []))
            len_rows.append({"swatch": None, "code": mark, "val": u"{:.0f}".format(width),
                           "desc": u"Len chân tường: {}{}".format(layers_text(cs, False),
                                                                u", cao {}".format(u"/".join(str(h) for h in hs))
                                                                if hs else u"")})
            continue
        if width <= 30:                              # lớp ốp / hoàn thiện tường
            walls.append({"swatch": None, "code": mark, "val": u"{:.0f}".format(width),
                          "desc": u"Ốp / hoàn thiện tường: {}".format(layers_text(cs, False))})
            continue
        core = max(list(cs.GetLayers()), key=lambda ly: ly.Width)
        mat = doc.GetElement(core.MaterialId)
        frt = frts.get(id_value(mat.CutForegroundPatternId)) if mat is not None else None
        walls.append({"swatch": frt.Id if frt is not None else None, "code": mark, "val": u"{:.0f}".format(width),
                      "desc": (u"{} – ".format(mark) if mark and frt is not None else u"") + layers_text(cs, True)})
    for tid, ks in sorted(floor_kinds.items(), key=lambda kv: sorted(kv[1])):
        ft = types[tid]
        cs = ft.GetCompoundStructure()
        floors.append({"swatch": None, "code": type_mark(ft),
                       "val": u"{:.0f}".format(to_mm(cs.GetWidth())) if cs else u"",
                       "desc": u"{} – {}".format(layers_text(cs, False), kinds_text(ks))})
        if not type_mark(ft):
            warns.append(u"Floor type '{}' chưa có Type Mark – tag sàn và bảng ghi chú để trống mã.".format(
                get_name(ft)))
    floors += len_rows
    for tid, ks in sorted(ceil_kinds.items(), key=lambda kv: sorted(kv[1])):
        ct = types[tid]
        cs = ct.GetCompoundStructure()
        name = get_name(ct)
        label = name.split(u"-", 1)[1] if u"-" in name[:4] else name
        ceilings.append({"swatch": None, "code": type_mark(ct),
                         "val": u"/".join(u"+{}".format(h) for h in sorted(ceil_h.get(tid, []))),
                         "desc": u"{}: {} – {}".format(label, layers_text(cs, False), kinds_text(ks))})
        if not type_mark(ct):
            warns.append(u"Ceiling type '{}' chưa có Type Mark – bảng ghi chú để trống mã.".format(name))
    return walls, ceilings, floors, warns


def draw_table(ctx, view, x0, ytop, title, header, rows):
    """Vẽ một bảng (mm giấy) trong legend: tiêu đề, dòng tiêu đề cột, các dòng; trả về y đáy bảng."""
    s = view.Scale
    Q = lambda x, y: XYZ(from_mm(x * s), from_mm(y * s), 0)
    t_title, t_body = ctx.text_type(TEXT_TITLE), ctx.text_type(TEXT_BODY)
    total = sum(TABLE_W)
    xs = [x0, x0 + TABLE_W[0], x0 + TABLE_W[0] + TABLE_W[1], x0 + total]

    def text(x, y, width, value, tt, center=False):
        opts = TextNoteOptions(tt.Id)
        if center:
            opts.HorizontalAlignment = HorizontalTextAlignment.Center
        tn = TextNote.Create(doc, view.Id, Q(x, y), from_mm(width), value, opts)
        doc.Regenerate()
        bb = tn.get_BoundingBox(view)
        return to_mm(bb.Max.Y - bb.Min.Y) / s if bb is not None else 3.0

    def hline(y):
        doc.Create.NewDetailCurve(view, Line.CreateBound(Q(xs[0], y), Q(xs[3], y)))

    text(x0 + total / 2.0, ytop, total, title, t_title, True)
    y = ytop - 6.0
    hline(y)
    y_head = y
    for i, hd in enumerate(header):
        text((xs[i] + xs[i + 1]) / 2.0, y - 1.5, xs[i + 1] - xs[i] - 2, hd, t_body, True)
    y -= 6.0
    hline(y)
    for r in rows:
        hd = text(xs[1] + 1.5, y - 1.5, TABLE_W[1] - 3, r["desc"] or u"—", t_body)
        rh = max(7.0, hd + 3.0)
        if r["swatch"] is not None:
            loop = CurveLoop()
            pts = [Q(xs[0] + 2, y - 1.5), Q(xs[1] - 2, y - 1.5), Q(xs[1] - 2, y - rh + 1.5), Q(xs[0] + 2, y - rh + 1.5)]
            for i in range(4):
                loop.Append(Line.CreateBound(pts[i], pts[(i + 1) % 4]))
            loops = List[CurveLoop]()
            loops.Add(loop)
            FilledRegion.Create(doc, r["swatch"], view.Id, loops)
        elif r["code"]:
            text((xs[0] + xs[1]) / 2.0, y - 1.5, TABLE_W[0] - 2, r["code"], t_body, True)
        if r["val"]:
            text((xs[2] + xs[3]) / 2.0, y - 1.5, TABLE_W[2] - 2, r["val"], t_body, True)
        y -= rh
        hline(y)
    for x in xs:
        doc.Create.NewDetailCurve(view, Line.CreateBound(Q(x, y_head), Q(x, y)))
    return y


def ensure_notes_legend(ctx, level, apts, name, rebuild):
    """Legend ghi chú dùng chung các căn: có sẵn (tên trùng) → dùng lại, KHÔNG sửa (rebuild → xóa nội dung, vẽ lại
    tại chỗ để viewport trên sheet các căn khác vẫn giữ); chưa có → nhân bản một legend bất kỳ (bản trống) rồi vẽ
    3 bảng: tường xây, trần, lát sàn. Trả về (legend hoặc None, ghi chú)."""
    legends = [v for v in FilteredElementCollector(doc).OfClass(View).ToElements()
               if v.ViewType == ViewType.Legend and not v.IsTemplate]
    old = next((v for v in legends if norm(get_name(v)) == norm(name)), None)
    if old is not None and not rebuild:
        return old, [u"Dùng lại legend có sẵn '{}' (không vẽ lại – bật IN[9] Làm lại để vẽ lại).".format(name)]
    if ctx.text_type(TEXT_TITLE) is None or ctx.text_type(TEXT_BODY) is None:
        return old, [u"Thiếu text type '{}' / '{}' → không vẽ bảng ghi chú.".format(TEXT_TITLE, TEXT_BODY)]
    if old is not None:
        delete_ids([e for e in FilteredElementCollector(doc, old.Id).WhereElementIsNotElementType().ToElements()
                    if e.OwnerViewId == old.Id and isinstance(e, (TextNote, CurveElement, FilledRegion))])
        view = old
    else:
        src = next((v for v in legends if v.CanViewBeDuplicated(ViewDuplicateOption.Duplicate)), None)
        if src is None:
            return None, [u"Không có legend nào để nhân bản → bỏ qua bảng ghi chú (tạo 1 legend trống rồi chạy lại)."]
        view = doc.GetElement(src.Duplicate(ViewDuplicateOption.Duplicate))
        view.Name = name
    walls, ceilings, floors, warns = collect_note_rows(level, apts)
    y = draw_table(ctx, view, 0.0, 0.0, u"GHI CHÚ TƯỜNG XÂY CĂN HỘ", [u"Ký hiệu", u"Loại / cấu tạo", u"Dày"], walls)
    y = draw_table(ctx, view, 0.0, y - 8.0, u"GHI CHÚ TRẦN CĂN HỘ", [u"Mã", u"Loại / cấu tạo", u"Đáy trần"],
                   ceilings)
    draw_table(ctx, view, 0.0, y - 8.0, u"GHI CHÚ LÁT SÀN CĂN HỘ", [u"Mã", u"Loại / cấu tạo", u"Dày"], floors)
    return view, [u"Đã {} legend '{}' ({} dòng tường, {} trần, {} sàn) – KTS soát mô tả.".format(
        u"vẽ lại" if old is not None else u"tạo", name, len(walls), len(ceilings), len(floors))] + warns


def old_outputs(apt, numbers):
    """Kết quả lần chạy trước của căn: view tên '<căn> - …' và sheet có số hiệu theo mẫu IN[3]."""
    nn = apt_digits(apt.name)
    nums = set(norm(numbers[k].replace(u"{nn}", nn)) for k in ("CTCH", "WC", "LG"))
    prefix = norm(apt.name) + u" - "
    views = [v for v in FilteredElementCollector(doc).OfClass(View).ToElements()
             if not v.IsTemplate and not isinstance(v, ViewSheet) and norm(get_name(v)).startswith(prefix)]
    sheets = [s for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
              if norm(s.SheetNumber) in nums]
    return views, sheets


def delete_ids(elements):
    ids = List[ElementId]()
    for e in elements:
        ids.Add(e.Id)
    if ids.Count:
        doc.Delete(ids)


# --- Một căn ----------------------------------------------------------------------------
def build_apartment(ctx, apt, level, circuits, placed_rooms, scales_ch, scales_dt, numbers, margin, legend,
                    ref_sheet, height_mm, bld):
    z = level.Elevation
    nn = apt_digits(apt.name)
    num = dict((k, numbers[k].replace(u"{nn}", nn)) for k in ("CTCH", "WC", "LG"))
    wcs = sorted(apt.of_kind("WC"), key=lambda f: (f.ip[0], f.ip[1]))
    lgs = sorted(apt.of_kind("LOGIA"), key=lambda f: -f.area)
    for i, f in enumerate(wcs):
        apt.wc_labels[f] = u"WC{}".format(i + 1) if len(wcs) > 1 else u"WC"
    for i, f in enumerate(lgs):
        apt.lg_labels[f] = u"LG{}".format(i + 1)
    # Căn 1 WC + 1 logia → gộp chi tiết WC và logia vào một sheet (số hiệu WC): hàng trên WC, hàng dưới logia
    combined = len(wcs) == 1 and len(lgs) == 1

    # Trùng tên view / số sheet → bỏ cả căn (không ghi đè)
    existing_views = set(norm(get_name(v)) for v in FilteredElementCollector(doc).OfClass(View).ToElements()
                         if not v.IsTemplate)
    existing_sheets = set(norm(s.SheetNumber) for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements())
    clash = [n for k, n in num.items() if norm(n) in existing_sheets and
             (k == "CTCH" or (k == "WC" and wcs) or (k == "LG" and lgs and not combined))]
    clash += [n for n in existing_views if n.startswith(norm(apt.name) + u" - ")]
    if clash:
        apt.notes.append(u"BỎ QUA căn {}: đã có sheet / view {} – không ghi đè.".format(apt.name, u", ".join(clash[:5])))
        return False

    # 1. Room
    apt.rooms = make_rooms(apt, level, circuits, placed_rooms)
    doc.Regenerate()

    # 2. Sheet CTCH
    box = apt.bbox(margin)
    plans = [
        (ViewFamily.FloorPlan, u"4.2", u"MB BỐ TRÍ NỘI THẤT", u"MẶT BẰNG BỐ TRÍ NỘI THẤT CĂN HỘ {}"),
        (ViewFamily.FloorPlan, u"4.1", u"MB TƯỜNG XÂY", u"MẶT BẰNG TƯỜNG XÂY, ĐỊNH VỊ CỬA CĂN HỘ {}"),
        (ViewFamily.FloorPlan, u"4.3", u"MB LÁT SÀN", u"MẶT BẰNG LÁT SÀN CĂN HỘ {}"),
        (ViewFamily.CeilingPlan, u"4.4", u"MB TRẦN", u"MẶT BẰNG TRẦN CĂN HỘ {}"),
    ]
    views = []
    for fam, code, short, title in plans:
        v, note = make_plan(ctx, level, fam, code, u"{} - {}".format(apt.name, short), title.format(apt.name),
                            scales_ch[0], box)
        views.append(v)
        apt.views.append([u"CTCH", v, note])
    y11, x22 = section_cuts(apt)
    sections = []
    for along_x, cut, lab in ((True, y11, u"1-1"), (False, x22, u"2-2")):
        v, note = make_apt_section(ctx, level, u"{} - MC {}".format(apt.name, lab),
                                   u"MẶT CẮT {} CĂN HỘ {}".format(lab, apt.name), scales_ch[0], box, along_x, cut,
                                   height_mm)
        sections.append(v)
        apt.views.append([u"CTCH", v, note])
    doc.Regenerate()
    # Ký hiệu MC 1-1 / 2-2 chỉ hiện trên MB tường xây (như mẫu); Revit không cắt ký hiệu mặt cắt theo
    # annotation crop nên phải ẩn riêng ở các view khác (view đã bỏ gắn template nên ẩn được)
    for v in (views[0], views[2], views[3], sections[0], sections[1]):
        hide_elements(v, sections)
    n_tag = 0
    for code, room, _new in apt.rooms:
        lp = room.Location.Point if isinstance(room.Location, LocationPoint) else None
        if lp is not None and TAG_ROOM in ctx.tags:
            rt = doc.Create.NewRoomTag(LinkElementId(room.Id), UV(lp.X, lp.Y), views[0].Id)
            set_type(rt, ctx.tags[TAG_ROOM])
            n_tag += 1
    n_tag += tag_openings(ctx, views[1], box, z)
    n_tag += tag_floors(ctx, views[2], apt.floors, z)
    for c in apt.ceilings:
        n_tag += tag(ctx, TAG_CEIL, views[3], c.el, c.ip, z)

    sh = new_sheet(ctx, num["CTCH"], u"CHI TIẾT CĂN HỘ {}".format(apt.name), ref_sheet)
    apt.sheets.append((u"CTCH", sh))
    # Bố cục như mẫu: MC 1-1 | MC 2-2 · MB tường xây | MB trần · MB nội thất | MB lát sàn.
    # Tỷ lệ: lớn nhất trong danh sách IN[1] mà cả 6 view vừa khung (không quá nhỏ, không tràn).
    vps = [place(ctx, sh, v, (160.0, 300.0)) for v in views + sections]
    rows = [[vps[4], vps[5]], [vps[1], vps[3]], [vps[0], vps[2]]]
    bounds = []
    s, ok = fit_scale(views + sections, scales_ch, lambda: ctch_layout(rows, bounds))
    if not ok:
        apt.notes.append(u"{}: sheet CTCH không vừa khung kể cả 1/{} – KTS chỉnh tay.".format(apt.name, s))
    align_titles(rows)
    # Nét đứt chia ô: ngang giữa các hàng, dọc giữa 2 cột và trước cột phải
    draw_dividers(ctx, sh, [((CTCH_X[0], y), (CTCH_X[2], y)) for y in bounds] +
                  [((CTCH_X[1], AREA_Y0), (CTCH_X[1], AREA_Y1)), ((CTCH_X[2], AREA_Y0), (CTCH_X[2], AREA_Y1))])
    # Cột phải (như mẫu FPT): sơ đồ vị trí căn trên cùng, legend ghi chú bên dưới
    y_free = AREA_Y1 - 4.0
    if bld is not None:
        kv = make_key_plan(ctx, level, apt, bld)
        apt.views.append([u"CTCH", kv, u"sơ đồ vị trí, bỏ gắn template 1.1"])
        kvp = place(ctx, sh, kv, (NOTE_X, 400.0))
        doc.Regenerate()
        _w, h = outline_size(kvp)
        kvp.SetBoxCenter(XYZ(from_mm(NOTE_X), from_mm(y_free - h / 2.0), 0))
        align_titles([[kvp]])
        y_free -= h + TITLE_ROOM + 6.0
    if legend is not None:
        lvp = Viewport.Create(doc, sh.Id, legend.Id, XYZ(from_mm(NOTE_X), from_mm(300), 0))
        set_type(lvp, ctx.vp_notitle.Id)
        doc.Regenerate()
        _w, h = outline_size(lvp)
        lvp.SetBoxCenter(XYZ(from_mm(NOTE_X), from_mm(y_free - h / 2.0), 0))
        if y_free - h < AREA_Y0:
            apt.notes.append(u"{}: legend ghi chú dài hơn chỗ trống cột phải {:.0f} mm – KTS chỉnh.".format(
                apt.name, h - (y_free - AREA_Y0)))

    # 3. Sheet WC (+ logia khi gộp). Mỗi sheet: [sheet, views, vps, cells] – chọn tỷ lệ chung sau khi đặt hết
    detail_sheets = []
    if len(wcs) > 2:
        apt.notes.append(u"{}: {} WC – sheet WC chỉ dàn 2 WC đầu.".format(apt.name, len(wcs)))
    if wcs:
        if combined:
            sh = new_sheet(ctx, num["WC"], u"CHI TIẾT VỆ SINH, LOGIA CĂN HỘ {}".format(apt.name), ref_sheet)
            apt.sheets.append((u"WC+LG", sh))
            grid = cells_row(3, 2)
        else:
            sh = new_sheet(ctx, num["WC"], u"CHI TIẾT VỆ SINH CĂN HỘ {}".format(apt.name), ref_sheet)
            apt.sheets.append((u"WC", sh))
            grid = cells_row(3, len(wcs[:2]))
        detail_sheets.append([sh, [], [], []])
        for r, f in enumerate(wcs[:2]):
            lab = apt.wc_labels[f]
            wbox = bbox_of([f.outer], margin)
            row = []
            for fam, code, short, title in (
                    (ViewFamily.FloorPlan, u"5.1", u"MB THIẾT BỊ", u"MẶT BẰNG BỐ TRÍ THIẾT BỊ {} CĂN HỘ {}"),
                    (ViewFamily.FloorPlan, u"5.2", u"MB LÁT SÀN", u"MẶT BẰNG LÁT SÀN {} CĂN HỘ {}"),
                    (ViewFamily.CeilingPlan, u"5.3", u"MB TRẦN", u"MẶT BẰNG TRẦN {} CĂN HỘ {}")):
                v, note = make_plan(ctx, level, fam, code, u"{} - {} - {}".format(apt.name, lab, short),
                                    title.format(lab, apt.name), scales_dt[0], wbox)
                hide_elements(v, sections)
                row.append(v)
                apt.views.append([u"WC", v, note])
            doc.Regenerate()
            for el in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
                    .WhereElementIsNotElementType().ToElements():
                pt = location_mm(el)
                if pt is not None and f.contains(pt):
                    n_tag += tag(ctx, TAG_PLUMB, row[0], el, pt, z)
            n_tag += tag_openings(ctx, row[0], wbox, z)
            n_tag += tag_floors(ctx, row[1], [g for g in apt.floors if g is f or
                                              (g.kind == "CHANCUA" and in_box(g.ip, wbox))], z)
            for c in apt.ceilings:
                if c.kind == "WC" and f.contains(c.ip):
                    n_tag += tag(ctx, TAG_CEIL, row[2], c.el, c.ip, z)
            detail_sheets[-1][1].extend(row)
            detail_sheets[-1][2].extend(place(ctx, sh, v, cell) for v, cell in zip(row, grid[r]))
            detail_sheets[-1][3].extend(grid[r])

    # 4. Sheet logia
    if len(lgs) > 2:
        apt.notes.append(u"{}: {} logia – sheet logia chỉ dàn 2 logia đầu.".format(apt.name, len(lgs)))
    if lgs:
        if combined:      # dùng tiếp sheet WC, hàng dưới
            row0 = 1
        else:
            sh = new_sheet(ctx, num["LG"], u"CHI TIẾT LOGIA CĂN HỘ {}".format(apt.name), ref_sheet)
            apt.sheets.append((u"LG", sh))
            grid = cells_row(3, len(lgs[:2]))
            row0 = 0
            detail_sheets.append([sh, [], [], []])
        for r, f in enumerate(lgs[:2], row0):
            lab = apt.lg_labels[f]
            lbox = bbox_of([f.outer], margin)
            v1, n1 = make_plan(ctx, level, ViewFamily.FloorPlan, u"6.1", u"{} - {} - MB LÁT SÀN".format(apt.name, lab),
                               u"MẶT BẰNG LÁT SÀN, BỐ TRÍ THIẾT BỊ LOGIA {} CĂN HỘ {}".format(lab, apt.name),
                               scales_dt[0], lbox)
            v2, n2 = make_plan(ctx, level, ViewFamily.CeilingPlan, u"4.4", u"{} - {} - MB TRẦN".format(apt.name, lab),
                               u"MẶT BẰNG TRẦN LOGIA {} CĂN HỘ {}".format(lab, apt.name), scales_dt[0], lbox)
            v3, n3 = make_logia_section(ctx, level, f, u"{} - {} - MC 1-1".format(apt.name, lab),
                                        u"MẶT CẮT 1-1 LOGIA {} CĂN HỘ {}".format(lab, apt.name), scales_dt[0],
                                        height_mm)
            for v, note in ((v1, n1), (v2, n2), (v3, n3)):
                apt.views.append([u"LG", v, note])
            # MC căn hộ không hiện ở chi tiết logia; MC logia chỉ hiện trên MB lát sàn logia
            for v in (v1, v2, v3):
                hide_elements(v, sections)
            for v in list(views) + list(sections) + [v2]:
                hide_elements(v, [v3])
            doc.Regenerate()
            n_tag += tag_floors(ctx, v1, [f], z)
            n_tag += tag_openings(ctx, v1, lbox, z)
            for c in apt.ceilings:
                if c.kind == "LOGIA" and f.contains(c.ip):
                    n_tag += tag(ctx, TAG_CEIL, v2, c.el, c.ip, z)
            detail_sheets[-1][1].extend((v1, v2, v3))
            detail_sheets[-1][2].extend(place(ctx, sh, v, cell) for v, cell in zip((v1, v2, v3), grid[r]))
            detail_sheets[-1][3].extend(grid[r])

    # Tỷ lệ chung từng sheet chi tiết: lớn nhất trong IN[2] mà mọi view vừa ô
    for sh_, views_, vps_, cells_ in detail_sheets:
        s, ok = fit_scale(views_, scales_dt, lambda: grid_layout(vps_, cells_))
        if not ok:
            apt.notes.append(u"{} sheet {}: view chi tiết vượt ô kể cả 1/{} – KTS chỉnh tay.".format(
                apt.name, sh_.SheetNumber, s))
        n_rows = len(vps_) // 3
        align_titles([vps_[i * 3:(i + 1) * 3] for i in range(n_rows)])
        cw = (AREA_X1 - AREA_X0) / 3.0
        ch = (AREA_Y1 - AREA_Y0) / max(n_rows, 1)
        draw_dividers(ctx, sh_, [((AREA_X0 + cw * k, AREA_Y0), (AREA_X0 + cw * k, AREA_Y1)) for k in (1, 2)] +
                      [((AREA_X0, AREA_Y1 - ch * r), (AREA_X1, AREA_Y1 - ch * r)) for r in range(1, n_rows)])
    apt.n_tag = n_tag
    return True


# --- Log / chính --------------------------------------------------------------------------
LOG_HEADER = [u"Căn", u"Sheet", u"View", u"Tỷ lệ", u"Ghi chú template"]


def write_log(rows, level_name, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "DanTrangCanHo_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# Level: {}\n".format(level_name))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def make_warning_swallower():
    """Bộ nuốt cảnh báo (VD Room trùng số / không kín) để không bật hộp thoại; lỗi thật vẫn giữ.
    pythonnet không cho khai báo lại lớp .NET cùng tên trong một phiên Dynamo (lần Run thứ hai báo lỗi ngoài
    try → OUT null) → khai báo trong hàm, namespace riêng mỗi lần chạy. Không tạo được → None (bỏ qua)."""
    ns = "ARV.DanTrangCanHo.R" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
    try:
        class SwallowWarnings(IFailuresPreprocessor):
            __namespace__ = ns

            def PreprocessFailures(self, fa):
                for m in list(fa.GetFailureMessages()):
                    if m.GetSeverity() == FailureSeverity.Warning:
                        fa.DeleteWarning(m)
                return FailureProcessingResult.Continue
        return SwallowWarnings()
    except Exception:
        return None


def to_int(text, label):
    try:
        v = int(float(text))
    except (TypeError, ValueError):
        raise StopReport([u"DỪNG: {} '{}' không phải số.".format(label, text)])
    if v <= 0:
        raise StopReport([u"DỪNG: {} phải > 0.".format(label)])
    return v


def to_scales(text, label):
    """'50;60;75' → [50, 60, 75] tăng dần (thử từ hình lớn nhất). Một số = cố định tỷ lệ đó."""
    vals = sorted(set(to_int(s, label) for s in split_filters(text)))
    if not vals:
        raise StopReport([u"DỪNG: {} trống.".format(label)])
    return vals


def main(apt_text, scale_ch_text, scale_dt_text, number_text, title_block, vp_type, margin_text, legend_name,
         dry_run, rebuild):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    view = doc.ActiveView
    level = view.GenLevel if view.ViewType in (ViewType.FloorPlan, ViewType.CeilingPlan) else None
    if level is None:
        return [u"DỪNG: hãy mở view mặt bằng của tầng có căn hộ rồi Run lại."], []
    wanted = split_filters(apt_text)
    if not wanted:
        raise StopReport([u"DỪNG: IN[0] trống – nhập căn hộ (VD CH01)."])
    scales_ch = to_scales(scale_ch_text, u"IN[1] tỷ lệ MB căn hộ")
    scales_dt = to_scales(scale_dt_text, u"IN[2] tỷ lệ chi tiết")
    margin = float(to_int(margin_text, u"IN[6] lề crop"))
    numbers = parse_map(number_text)
    lack = [k for k in ("CTCH", "WC", "LG") if not numbers.get(k)]
    if lack:
        raise StopReport([u"DỪNG: IN[3] thiếu số hiệu sheet cho: {}.".format(u", ".join(lack))])
    ctx = Ctx(title_block, vp_type)
    above = sorted([l for l in FilteredElementCollector(doc).OfClass(Level).ToElements()
                    if l.Elevation > level.Elevation + 1e-6], key=lambda l: l.Elevation)
    height_mm = to_mm(above[0].Elevation - level.Elevation) if above else 3300.0

    apts = collect_apartments(level, wanted)
    warns = []
    for a in apts:
        if not a.floors:
            warns.append(u"{}: không có sàn '{} {} …' trên level {} – bỏ qua (chạy tool sàn hoàn thiện trước)."
                         .format(a.name, FLOOR_TAG, a.name, level.Name))
    todo = [a for a in apts if a.floors]
    if not todo:
        raise StopReport([u"DỪNG: không căn nào có sàn hoàn thiện."] + warns)

    TransactionManager.Instance.ForceCloseTransaction()
    tx = Transaction(doc, TRANSACTION_NAME)
    swallower = make_warning_swallower()
    if swallower is not None:
        opts = tx.GetFailureHandlingOptions()
        opts.SetFailuresPreprocessor(swallower)
        tx.SetFailureHandlingOptions(opts)
    tx.Start()
    done = []
    try:
        circuits = plan_circuits(level)
        placed = [r for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)
                  .WhereElementIsNotElementType().ToElements() if r.Location is not None and r.LevelId == level.Id]
        bld = floors_box(level)
        # Căn đã có view / sheet: bỏ qua, hoặc (IN[9] Làm lại) xóa đúng view / sheet của căn rồi dựng lại
        ready = []
        for a in todo:
            views, sheets = old_outputs(a, numbers)
            if not views and not sheets:
                ready.append(a)
                continue
            foreign = [s for s in sheets if norm(a.name) not in norm(s.Name)]
            if not rebuild:
                a.notes.append(u"BỎ QUA căn {}: đã có {} view / {} sheet ({}) – bật IN[9] Làm lại để dựng mới.".format(
                    a.name, len(views), len(sheets), u", ".join(s.SheetNumber for s in sheets)))
            elif foreign:
                a.notes.append(u"BỎ QUA căn {}: số sheet {} đang dùng cho nội dung khác – sửa IN[3].".format(
                    a.name, u", ".join(s.SheetNumber for s in foreign)))
            elif any(not DocumentValidation.CanDeleteElement(doc, e.Id) for e in views + sheets):
                # Revit không cho xóa view / sheet đang mở trong tab
                locked = [get_name(e) for e in views + sheets if not DocumentValidation.CanDeleteElement(doc, e.Id)]
                a.notes.append(u"BỎ QUA căn {}: không xóa được {} (đang mở trong Revit?) – đóng tab rồi chạy lại.".format(
                    a.name, u", ".join(locked)))
            else:
                # Đọc số sheet TRƯỚC khi xóa – sau Delete đối tượng không còn hợp lệ
                note = u"{}: Làm lại – đã xóa {} view, {} sheet cũ ({}).".format(
                    a.name, len(views), len(sheets), u", ".join(s.SheetNumber for s in sheets) or u"—")
                delete_ids(views + sheets)
                a.notes.append(note)
                ready.append(a)
        # Sheet cùng mục (VD "A.5-…") để chép tham số nhóm Project Browser – chọn SAU bước xóa
        group = numbers["CTCH"].split(u"-")[0] + u"-"
        ref_sheet = next((s for s in FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
                          if s.SheetNumber.startswith(group)), None)
        legend = None
        if legend_name.strip() and ready:
            # Bảng ghi chú dùng chung: lấy type của MỌI căn trên tầng, không chỉ các căn đang dàn
            all_names = sorted(set(norm(comment_of(f)).split()[1].upper() for f in
                                   FilteredElementCollector(doc).OfClass(Floor).ToElements()
                                   if f.LevelId == level.Id and len(norm(comment_of(f)).split()) >= 3
                                   and norm(comment_of(f)).split()[0] == FLOOR_TAG))
            legend, notes = ensure_notes_legend(ctx, level, collect_apartments(level, all_names), legend_name.strip(),
                                                rebuild)
            warns.extend(notes)
        for a in ready:
            if build_apartment(ctx, a, level, circuits, placed, scales_ch, scales_dt, numbers, margin, legend,
                               ref_sheet, height_mm, bld):
                done.append(a)
        # Ghi nhận trước khi hoàn tác (dry-run) vì sau RollBack phần tử không còn
        rows, summary = [], []
        for a in todo:
            for row in a.views:
                rows.append([a.name, row[0], get_name(row[1]), u"1/{}".format(row[1].Scale), row[2]])
            if a in done:
                scales = []
                for key in (u"CTCH", u"WC", u"LG"):
                    ss = sorted(set(r[1].Scale for r in a.views if r[0] == key))
                    if ss:
                        scales.append(u"{} 1/{}".format(key, u",".join(str(s) for s in ss)))
                summary.append(u"{}: Room {} ({}), sheet {}, {} view ({}), {} tag".format(
                    a.name, len(a.rooms), u", ".join(u"{}{}".format(c, u"*" if n else u"") for c, _r, n in a.rooms),
                    u" / ".join(s.SheetNumber for _k, s in a.sheets), len(a.views), u"; ".join(scales),
                    getattr(a, "n_tag", 0)))
            warns.extend(a.notes)
        if dry_run:
            tx.RollBack()
        else:
            tx.Commit()
    except Exception:
        if tx.HasStarted() and not tx.HasEnded():
            tx.RollBack()
        raise

    report = [u"{} – {} – Làm lại (IN[9]): {}".format(
        TRANSACTION_NAME, u"CHẠY THỬ (đã dựng rồi hoàn tác)" if dry_run else u"ĐÃ THỰC HIỆN",
        u"CÓ" if rebuild else u"KHÔNG")]
    report.append(u"Level: {} – tỷ lệ thử: căn hộ 1/{}, chi tiết 1/{} – khung {} – viewport '{}'".format(
        level.Name, u",".join(str(s) for s in scales_ch), u",".join(str(s) for s in scales_dt),
        ctx.title_block.FamilyName, get_name(ctx.vp_type)))
    report += summary
    report.append(u"(* = Room mới tạo. Mã: KA khách-ăn, NG ngủ, WC, LG1 logia khách, LG2 logia phơi – KTS soát lại)")
    if ctx.missing_tags:
        warns.append(u"Thiếu tag type (bỏ qua tag đó): " + u"; ".join(ctx.missing_tags))
    for w in warns:
        report.append(u"CẢNH BÁO: " + w)
    report.append(u"CHƯA LÀM: dim tường / cửa, cao độ, ghi chú vật liệu tường – bổ sung tay.")
    try:
        report.append(u"Log: " + write_log(rows, level.Name, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Đúng thì đổi Dry-run = False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, []


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
            IN[0] or u"",
            IN[1] or u"50;60;65;70;75;80;90;100;125;150",
            IN[2] or u"20;25;30;40;50",
            IN[3] or u"",
            (IN[4] or u"").strip(),
            (IN[5] or u"").strip(),
            IN[6] or u"300",
            u"GHI CHÚ CĂN HỘ" if IN[7] is None else IN[7],
            True if IN[8] is None else bool(IN[8]),
            bool(IN[9]) if len(IN) > 9 else False,
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "DanTrangCanHo_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
