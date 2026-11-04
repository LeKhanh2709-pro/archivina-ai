# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 18. ARV_TaoVoiXitLoGiayWC_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo vòi xịt + lô giấy (Plumbing Fixtures) cạnh bồn cầu ĐÃ ĐẶT trong mô hình (không cần CAD):
#   1. Mốc = bồn cầu trên level IN[0]: family tên chứa "toilet" / "bon cau" hoặc Comments của tool 16, trong Room có tên
#      chứa một chuỗi trong IN[3]. Hướng + lưng + trục đọc từ KHỐI ĐẶC thật (như tool 16, không tin gốc / hướng family):
#      két nước = phần cao ≥ 550 mm nằm phía lưng; thân dài = chiều sâu; trục = qua gốc family (AV-Toilet1 lệch khung
#      9,5 mm), gốc lệch khung > 30 mm thì lấy tâm khung. Không thấy két nước → bỏ qua, báo cần soát.
#   2. Quy tắc (người dùng 2026-10-30): vòi xịt BÊN PHẢI cách trục bồn cầu IN[4] (300 mm), lô giấy BÊN TRÁI cách trục IN[9]
#      (350 mm – 300 quá gần bồn cầu), đo tới GỐC FAMILY, trên
#      tường sau lưng bồn cầu. Phải / trái theo NGƯỜI NGỒI trên bồn cầu nhìn ra phòng; IN[7] = True đổi hai bên.
#   3. Tường gắn: tường Revit song song cách mặt dựa ≤ 60 mm, phủ đúng vị trí thiết bị; thử lần lượt từ mặt NHÔ RA PHÒNG NHẤT
#      (lớp ốp WA_F1_10 trước WB 15-100-15) để áp mặt hoàn thiện. Lần chạy 2026-10-30 16:59 chọn mặt gần lưng bồn cầu nhất nên
#      phần lớn gắn vào tường thô, lấn 10 mm vào lớp ốp.
#   4. Family mẫu G19: "AV_Voi xit : Polished Chrome" (người dùng load 2026-10-30; Host = Face; khối −30…30 × −615…93 × 0…90
#      – dựng trên mặt host, Z ra phòng, dây xuống −Y) và "AV-Lô Giấy1 : Type 1" (Host = Wall, tham số Height 790). Tool hỗ
#      trợ cả ba kiểu đặt:
#      - Face-based / Work Plane Based: đặt lên mặt tường phía phòng (HostObjectUtils.GetSideFaces), xoay trên mặt tường
#        cho dây treo thẳng đứng, đầu giá treo (gốc family) ở trên. Dời đứng bằng MoveElement: Offset from Host của family
#        này là khoảng cách RA KHỎI mặt tường, không phải cao độ;
#      - gắn tường (OneLevelBasedHosted): Revit luôn đặt family về BÊN TRÁI chiều vẽ của tường gắn (G19: 17 đúng, 15 sai, khớp
#        hết theo chiều vẽ); AV-Lô Giấy1 không có Flip Control. Sai phía → flipFacing; không lật được → thử tường gắn kế tiếp
#        (lớp ốp vẽ ngược chiều); hết tường thì đặt ở tường đầu, báo "CÒN SAI PHÍA TƯỜNG" (thêm Flip Control vào family).
#        Lần chạy 2026-10-31 08:14: tạo mới lật không được 14/31 (8 sai phía, 6 rơi về tường thô), 08:16 xoá rồi tạo lại đúng
#        14/14 cùng code, chưa rõ nguyên nhân Revit → cuối Transaction tự xoá + tạo lại các thiết bị này một lần;
#      - đặt theo level: đặt rồi dời theo khối.
#   5. Căn sau khi đặt: dọc tường theo GỐC FAMILY (Location.Point = IN[4] / IN[9], tim người dùng đo; khối AV-Lô Giấy1 lệch gốc 16,4 mm,
#      căn theo tâm khối cho 283,6 / 316,4 mm – lần chạy 16:59), đỉnh khối = IN[5] / IN[6] so với level. Family hosted kiểu
#      AV- Shower có bbox type tính sẵn cao độ – không đặt theo số trong family mà đo lại rồi bù.
#   6. Dry-run ĐẶT THỬ rồi RollBack: số đo trong log là số thật của family (tim cách trục, lưng cách mặt, đỉnh / chân khối).
#      Thiết bị của tool đã có (Comments) cách vị trí đích ≤ 800 mm → dời / đổi type tại chỗ; lưng không áp mặt gắn (sai phía tường,
#      gắn tường thô sau lớp ốp) → xoá Id đó, tạo lại trong cùng Transaction; cùng family người dùng tự đặt → bỏ qua.
#      Biên hai bên (vách kính, lavabo, tường) cách tim < 100 mm → vẫn đặt, báo "CẦN SOÁT". Tường bên gần trục hơn khoảng cách
#      quy định (vị trí rơi ra ngoài phòng – G19: bồn cầu 3379638 còn 317 mm) → đặt xa nhất có thể: mép khối sát tường bên,
#      báo "cần soát" (bản 2026-10-30 bỏ qua nên WC này mất lô giấy khi tạo mới, người dùng báo 2026-10-31).
# INPUT
#   IN[0] (str)   Tên level, VD "TẦNG 3"
#   IN[1] (FamilyType | str) Type vòi xịt (node Family Types, hoặc "AV_Voi xit : Polished Chrome")
#   IN[2] (FamilyType | str) Type lô giấy (node Family Types, hoặc "AV-Lô Giấy1 : Type 1")
#   IN[3] (str)   Tên Room chứa bồn cầu, nhiều chuỗi cách ';', VD "WC;vệ sinh" (trống = mọi phòng)
#   IN[4] (float) Khoảng cách tim vòi xịt – trục bồn cầu (mm), VD 300
#   IN[5] (float) Cao độ đỉnh khối vòi xịt so với level (mm), VD 750
#   IN[6] (float) Cao độ đỉnh khối lô giấy so với level (mm), VD 820
#   IN[7] (bool)  Đổi bên: False = vòi xịt phải, lô giấy trái theo người ngồi; True = ngược lại
#   IN[8] (bool)  Dry-run: True = đặt thử rồi hoàn tác, chỉ báo cáo (mặc định True)
#   IN[9] (float) Khoảng cách tim lô giấy – trục bồn cầu (mm), VD 350
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng thiết bị
#   OUT[1] (list[Line]) Xem trước: dấu chữ thập tại từng vị trí, đoạn nối về trục bồn cầu (mm)

import os
import io
import re
import csv
import math
import datetime
import unicodedata

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, Options, GeometryInstance, Line, XYZ, Transaction,
                                   SubTransaction, TransactionStatus, UnitUtils, UnitTypeId, ModelPathUtils,
                                   BuiltInParameter, BuiltInCategory, Level, Wall, LocationCurve, FamilySymbol,
                                   FamilyPlacementType, ElementTransformUtils, SpatialElementBoundaryOptions,
                                   SpatialElementBoundaryLocation, Solid, ViewDetailLevel, HostObjectUtils,
                                   ShellLayerType, PlanarFace)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo vòi xịt, lô giấy cạnh bồn cầu"
SCRIPT_TAG = u"ARV_TaoVoiXitLoGiayWC_v1"
TOILET_TAG = u"ARV-TaoBonCauTuCAD"
LAVABO_TAG = u"ARV-TaoLavaboTuCAD"
GLASS_TAG = u"ARV-TaoVachKinhTamTuCAD"
SPRAY = u"Vòi xịt"
PAPER = u"Lô giấy"
TAGS = {SPRAY: u"ARV-TaoVoiXitWC", PAPER: u"ARV-TaoLoGiayWC"}
PARALLEL_COS = 0.995             # Mặt song song / vuông góc mặt dựa: |cos| ≥ chừng này
MOUNT_TOL_MM = 150.0             # Mặt dựa cách lưng bồn cầu tối đa (phía sau)
MOUNT_FRONT_MM = 50.0            # … hoặc lấn vào trong bồn cầu tối đa
HOST_GAP_MM = 60.0               # Mặt tường gắn cách mặt dựa tối đa (mặt tường thô sau lớp ốp)
STRIP_MM = 300.0                 # Biên hai bên phải chạm dải này trước mặt dựa
SIDE_RANGE_MM = 1500.0           # Tìm biên hai bên trong khoảng này tính từ trục bồn cầu
CLEAR_MM = 100.0                 # Biên cách tim thiết bị ít hơn chừng này → báo cần soát
PANEL_MIN_MM = 200.0             # Tấm kính trong family vách kính dài tối thiểu (bỏ thanh, tay nắm)
GLASS_T_MM = 30.0                # Khối mỏng hơn chừng này trong family vách kính = tấm kính
BODY_MAX_MM = 1500.0             # Khối đặc của family lớn hơn (trên mặt bằng) = vùng thông thủy – bỏ
TANK_Z_MM = 550.0                # Phần khối cao hơn chừng này so với level = két nước (phía lưng)
AXIS_TOL_MM = 30.0               # Gốc family lệch tâm khung khối ≤ chừng này → coi gốc nằm trên trục bồn cầu
EXIST_TOL_MM = 800.0             # Thiết bị của tool cách vị trí đích ≤ chừng này → sửa tại chỗ (đủ nhận lật bên 2 × 300)
Z_BAND_MM = (-100.0, 2500.0)     # Thiết bị thuộc level: tâm khối trong dải này so với level (Work Plane Based có thể không có Level)
MOVE_TOL_MM = 1.0                # Lệch ≤ chừng này coi là đúng vị trí
FACE_TOL_MM = 2.0                # Lưng thiết bị của tool lệch mặt gắn hơn chừng này → tạo lại


# --- Hình học 2D thuần (mm) – chạy được ngoài Revit để thử --------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def unit(v):
    l = math.hypot(v[0], v[1])
    return (v[0] / l, v[1] / l)


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def norm(s):
    return unicodedata.normalize("NFC", (s or u"")).strip()


def loose(s):
    """So tên không phân biệt dấu / hoa thường: "Vệ sinh" ≈ "VE SINH"."""
    s = unicodedata.normalize("NFD", norm(s).replace(u"đ", u"d").replace(u"Đ", u"D"))
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def is_toilet_name(name):
    n = loose(name)
    return u"toilet" in n or u"bon cau" in n


class Seg(object):
    """Một mặt trên mặt bằng (mm): kind = "room" (biên Room Finish), "wall", "glass", "lavabo"."""

    def __init__(self, a, b, kind, name=u""):
        self.a, self.b, self.kind, self.name = a, b, kind, name


class HostWall(object):
    """Tường Revit trên mặt bằng (mm): trục a → b, pháp tuyến n (bên trái chiều vẽ)."""

    def __init__(self, wid, a, b, width, name=u""):
        self.id, self.a, self.b, self.width, self.name = wid, a, b, width, name
        self.length = math.hypot(b[0] - a[0], b[1] - a[1])
        self.u = unit(sub(b, a))
        self.n = (-self.u[1], self.u[0])

    def faces(self):
        h = self.width / 2.0
        return [Seg((self.a[0] + self.n[0] * k * h, self.a[1] + self.n[1] * k * h),
                    (self.b[0] + self.n[0] * k * h, self.b[1] + self.n[1] * k * h), u"wall", self.name) for k in (1, -1)]


class Toilet(object):
    """Bồn cầu đã đặt. Hệ trục riêng: gốc = giao trục bồn cầu với lưng khối, dir = hướng mặt trước (ra phòng), u = trái của
    dir (dọc tường); s = toạ độ dọc tường, d = toạ độ ra phòng. Người ngồi nhìn theo dir: tay trái +u, tay phải −u."""

    def __init__(self, eid, back, d, width, length):
        self.eid, self.back, self.width, self.length = eid, back, width, length
        self.dir = d
        self.u = (-d[1], d[0])
        self.c = self.world(0.0, length / 2.0)
        self.mount_d = 0.0
        self.room = u""
        self.status = u""
        self.note = u""
        self.lo = self.hi = None

    def local(self, p):
        q = sub(p, self.back)
        return dot(q, self.u), dot(q, self.dir)

    def world(self, s, d):
        return (self.back[0] + self.u[0] * s + self.dir[0] * d, self.back[1] + self.u[1] * s + self.dir[1] * d)


class Fixture(object):
    """Một thiết bị cần đặt: kind (SPRAY / PAPER), bồn cầu tb, s dọc tường, tường gắn host, mặt gắn face_d."""

    def __init__(self, kind, tb, s, side):
        self.kind, self.tb, self.s, self.side = kind, tb, s, side
        self.host = None
        self.hosts = []          # [(tường, mặt gắn d)] thử lần lượt, mặt nhô ra phòng nhất trước
        self.face_d = tb.mount_d
        self.limit = None        # s của tường bên chặn vị trí quy định; None = không bị chặn
        self.want = abs(s)

    def use(self, cand):
        self.host, self.face_d = cand

    def point(self):
        return self.tb.world(self.s, self.face_d)


def toilet_frame(eid, pts3, origin, facing, level_z):
    """Bồn cầu từ đỉnh khối đặc (x, y, z mm), gốc family và FacingOrientation (chỉ dùng làm hệ trục, không dùng làm hướng).
    Trả về Toilet, hoặc None nếu không thấy két nước."""
    a = unit(facing)
    b = (-a[1], a[0])
    pts = [(p[0], p[1]) for p in pts3]
    pa = [dot(sub(p, origin), a) for p in pts]
    pb = [dot(sub(p, origin), b) for p in pts]
    axis, vals = (a, pa) if max(pa) - min(pa) >= max(pb) - min(pb) else (b, pb)
    tall = [vals[i] for i, p in enumerate(pts3) if p[2] - level_z >= TANK_Z_MM]
    if not tall:
        return None
    tank = sum(tall) / len(tall)
    d = (-axis[0], -axis[1]) if tank > (min(vals) + max(vals)) / 2.0 else axis
    u = (-d[1], d[0])
    ss = [dot(sub(p, origin), u) for p in pts]
    ds = [dot(sub(p, origin), d) for p in pts]
    mid = (min(ss) + max(ss)) / 2.0
    axis_s = 0.0 if abs(mid) <= AXIS_TOL_MM else mid
    back = (origin[0] + u[0] * axis_s + d[0] * min(ds), origin[1] + u[1] * axis_s + d[1] * min(ds))
    return Toilet(eid, back, d, max(ss) - min(ss), max(ds) - min(ds))


def fit_mount(tb, segs):
    """Mặt dựa: mặt song song tường gần lưng bồn cầu nhất, phủ trục bồn cầu. Trả về lỗi hoặc None."""
    best = None
    for sg in segs:
        if sg.kind == u"glass":
            continue
        sa, da = tb.local(sg.a)
        sb, db = tb.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(sb - sa) / ln < PARALLEL_COS:
            continue
        if not (min(sa, sb) - 1.0 <= 0.0 <= max(sa, sb) + 1.0):
            continue
        d = (da + db) / 2.0
        if -MOUNT_TOL_MM <= d <= MOUNT_FRONT_MM and (best is None or abs(d) < abs(best)):
            best = d
    if best is None:
        return u"không có mặt tường / hoàn thiện sau lưng bồn cầu (≤ {:.0f} mm)".format(MOUNT_TOL_MM)
    tb.mount_d = best
    return None


def fit_host(fx, walls):
    """Tường gắn: song song, phủ vị trí thiết bị, mặt phía phòng cách mặt dựa ≤ HOST_GAP_MM. fx.hosts xếp mặt nhô ra phòng
    nhất trước (lớp ốp thắng tường thô sau nó, kể cả khi lưng bồn cầu áp tường thô)."""
    tb = fx.tb
    p = tb.world(fx.s, tb.mount_d)
    fx.hosts = []
    for w in walls:
        if abs(dot(w.u, tb.u)) < PARALLEL_COS:
            continue
        ws = dot(sub(p, w.a), w.u)
        if not (0.0 <= ws <= w.length):
            continue
        k = 1.0 if dot(w.n, tb.dir) > 0 else -1.0
        face_d = tb.local((w.a[0] + w.n[0] * k * w.width / 2.0, w.a[1] + w.n[1] * k * w.width / 2.0))[1]
        if abs(face_d - tb.mount_d) <= HOST_GAP_MM:
            fx.hosts.append((w, face_d))
    if not fx.hosts:
        return False
    fx.hosts.sort(key=lambda c: -c[1])
    fx.use(fx.hosts[0])
    return True


def fit_sides(tb, segs):
    """Biên gần nhất hai bên trục bồn cầu: (s, kind, tên) phía s < 0, s > 0 – mặt vuông góc mặt dựa, chạm dải STRIP_MM."""
    sides = ([], [])
    for sg in segs:
        sa, da = tb.local(sg.a)
        sb, db = tb.local(sg.b)
        ln = math.hypot(sb - sa, db - da)
        if ln < 1.0 or abs(db - da) / ln < PARALLEL_COS:
            continue
        s = (sa + sb) / 2.0
        if abs(s) > SIDE_RANGE_MM or abs(s) < 1.0:
            continue
        if max(da, db) < tb.mount_d + 1.0 or min(da, db) > tb.mount_d + STRIP_MM:
            continue
        sides[0 if s < 0 else 1].append((s, sg.kind, sg.name))
    tb.lo = min(sides[0], key=lambda c: abs(c[0])) if sides[0] else None
    tb.hi = min(sides[1], key=lambda c: abs(c[0])) if sides[1] else None


def side_note(fx):
    """Biên lấn vào chỗ đặt thiết bị → ghi chú, không có thì chuỗi rỗng."""
    b = fx.tb.hi if fx.s > 0 else fx.tb.lo
    if b is None or abs(b[0]) - abs(fx.s) >= CLEAR_MM:
        return u""
    return u"biên {} cách tim thiết bị {:.0f} mm, cần soát".format(
        {u"glass": u"vách kính", u"lavabo": u"lavabo"}.get(b[1], u"tường"), abs(b[0]) - abs(fx.s))


def wall_blocked(fx):
    """Tường bên gần trục bồn cầu hơn vị trí thiết bị → khoảng cách tường bên – trục (mm), không thì None."""
    b = fx.tb.hi if fx.s > 0 else fx.tb.lo
    if b is None or b[1] not in (u"wall", u"room") or abs(b[0]) >= abs(fx.s):
        return None
    return abs(b[0])


def clamp_to_wall(fx, blocked):
    """Tường bên chặn vị trí quy định: tạm đặt trong phòng, fit_body căn lại cho mép khối sát tường."""
    sign = 1.0 if fx.s > 0 else -1.0
    fx.limit = sign * blocked
    fx.s = sign * max(blocked - 60.0, 0.0)


def plan(toilets, walls, room_at, room_keys, spray_dist, paper_dist, swap, extra_segs=()):
    """Gán mặt dựa, biên, tường gắn cho từng bồn cầu. Trả về [Fixture] của bồn cầu hợp lệ; tb.status ghi lý do bỏ qua."""
    wall_segs = [f for w in walls for f in w.faces()]
    jobs, room_segs = [], {}
    for tb in toilets:
        hit = room_at(tb.c) if room_at is not None else None
        tb.room = hit[0] if hit else u""
        if room_at is not None and room_keys and not any(k in loose(tb.room) for k in room_keys):
            tb.status = u"Bỏ qua – không nằm trong phòng {} (phòng: {})".format(
                u"/".join(room_keys), tb.room or u"không có Room")
            continue
        key = id(hit[1]) if hit else None
        if key not in room_segs:
            segs = list(wall_segs)
            for pts in (hit[1] if hit else []):
                segs += [Seg(pts[i - 1], pts[i], u"room", u"biên Room") for i in range(len(pts))]
            room_segs[key] = segs
        segs = room_segs[key]
        err = fit_mount(tb, segs)
        if err:
            tb.status = u"Bỏ qua – " + err
            continue
        fit_sides(tb, segs + list(extra_segs))
        tb.status = u"OK"
        # Người ngồi nhìn theo tb.dir: tay phải = −u
        spray_s, paper_s = (spray_dist, -paper_dist) if swap else (-spray_dist, paper_dist)
        jobs.append(Fixture(SPRAY, tb, spray_s, u"trái" if swap else u"phải"))
        jobs.append(Fixture(PAPER, tb, paper_s, u"phải" if swap else u"trái"))
    return jobs


def measure(pts3, origin, fx, level_z):
    """Đo thiết bị so với bồn cầu: (gốc family s, lưng khối d so với mặt gắn, chân, đỉnh so với level, rộng khối s)."""
    ss = [fx.tb.local((p[0], p[1]))[0] for p in pts3]
    ds = [fx.tb.local((p[0], p[1]))[1] for p in pts3]
    zs = [p[2] - level_z for p in pts3]
    return fx.tb.local(origin)[0], min(ds) - fx.face_d, min(zs), max(zs), max(ss) - min(ss)


def inside_loops(p, loops):
    """Điểm trong vùng giới hạn bởi các vòng biên (chẵn lẻ – lỗ trong Room tự trừ)."""
    c = False
    for pts in loops:
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i - 1], pts[i]
            if (y1 > p[1]) != (y2 > p[1]) and p[0] < x1 + (p[1] - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c


# --- Revit ---------------------------------------------------------------------------
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
        if norm(l.Name).lower() == norm(name).lower():
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def level_walls(level):
    """Tường thẳng trên level (mọi chiều dày, gồm lớp ốp mỏng) → ([HostWall], {id: Wall})."""
    result, by_id = [], {}
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line):
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            if hw.length >= 1.0:
                result.append(hw)
                by_id[hw.id] = wl
    return result, by_id


def room_finder(level):
    """Hàm room_at(pt mm) → (tên Room, [vòng biên Finish mm]) trên level chứa điểm, None nếu không có."""
    opt = SpatialElementBoundaryOptions()
    opt.SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish
    rooms = []
    for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms) \
            .WhereElementIsNotElementType().ToElements():
        if r.LevelId != level.Id or r.Area <= 0:
            continue
        loops = []
        for segs in r.GetBoundarySegments(opt) or []:
            pts = []
            for seg in segs:
                pts.extend(xy(q) for q in list(seg.GetCurve().Tessellate())[:-1])
            if len(pts) >= 3:
                loops.append(pts)
        if not loops:
            continue
        xs = [q[0] for l in loops for q in l]
        ys = [q[1] for l in loops for q in l]
        prm = r.get_Parameter(BuiltInParameter.ROOM_NAME)
        rooms.append(((min(xs), min(ys), max(xs), max(ys)), loops, prm.AsString() if prm is not None else u""))

    def room_at(p):
        for box, loops, name in rooms:
            if box[0] <= p[0] <= box[2] and box[1] <= p[1] <= box[3] and inside_loops(p, loops):
                return name, loops
        return None
    return room_at, len(rooms)


def fixture_symbols():
    return [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures)
            .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]


def pick_type(value, slot, label):
    """Ô IN: FamilyType của node Family Types (Dynamo) hoặc chuỗi "Family : Type" → FamilySymbol."""
    symbols = fixture_symbols()
    families = u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có"
    if isinstance(value, str):
        parts = [norm(p) for p in value.split(u":")]
        if len(parts) != 2 or not all(parts):
            raise StopReport([u"DỪNG: ô {} phải là type chọn từ node Family Types hoặc chuỗi 'Family : Type' "
                              u"(đang là '{}').".format(slot, value)])
        hits = [s for s in symbols if norm(s.FamilyName) == parts[0] and norm(get_name(s)) == parts[1]]
        if not hits:
            raise StopReport([u"DỪNG: không có type {} '{}'. Family thiết bị vệ sinh: {}".format(label, value, families)])
        return hits[0]
    sym = UnwrapElement(value) if value is not None else None
    if not isinstance(sym, FamilySymbol):
        raise StopReport([u"DỪNG: chưa chọn type {} ở {}.".format(label, slot)])
    if sym.Category is None or sym.Category.BuiltInCategory != BuiltInCategory.OST_PlumbingFixtures:
        raise StopReport([u"DỪNG: type '{} : {}' không thuộc Plumbing Fixtures. Family thiết bị vệ sinh: {}".format(
            sym.FamilyName, get_name(sym), families)])
    return sym


def check_placement(sym):
    p = sym.Family.FamilyPlacementType
    if p not in (FamilyPlacementType.OneLevelBased, FamilyPlacementType.OneLevelBasedHosted,
                 FamilyPlacementType.WorkPlaneBased):
        raise StopReport([u"DỪNG: family '{}' kiểu đặt {} – công cụ chỉ hỗ trợ Work Plane Based, gắn tường hoặc đặt theo "
                          u"level.".format(sym.FamilyName, p)])
    return p


def placement_label(p):
    if p == FamilyPlacementType.WorkPlaneBased:
        return u"Face-based / Work Plane Based, đặt lên mặt tường"
    return u"gắn tường" if p == FamilyPlacementType.OneLevelBasedHosted else u"đặt theo level"


def body_points(fi):
    """Đỉnh (x, y, z mm) các khối đặc của instance; bỏ khối lớn hơn BODY_MAX_MM trên mặt bằng (vùng thông thủy).
    Family không có Solid (mesh) → 8 góc khung bao."""
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    result = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, Solid) and obj.Volume > 1e-6:
                pts = []
                for e in obj.Edges:
                    pts.extend(e.Tessellate())
                if not pts:
                    continue
                xs, ys = [to_mm(p.X) for p in pts], [to_mm(p.Y) for p in pts]
                if max(max(xs) - min(xs), max(ys) - min(ys)) > BODY_MAX_MM:
                    continue
                result.extend((x, y, to_mm(p.Z)) for x, y, p in zip(xs, ys, pts))

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    if result:
        return result
    bb = fi.get_BoundingBox(None)
    if bb is None:
        return []
    return [(to_mm(x), to_mm(y), to_mm(z)) for x in (bb.Min.X, bb.Max.X) for y in (bb.Min.Y, bb.Max.Y)
            for z in (bb.Min.Z, bb.Max.Z)]


def glass_panels(fi):
    """Hai mặt dài (Seg "glass") của mỗi tấm kính trong instance (như tool 16)."""
    opt = Options()
    opt.DetailLevel = ViewDetailLevel.Fine
    segs = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            elif isinstance(obj, Solid) and obj.Volume > 1e-6:
                pts = []
                for e in obj.Edges:
                    pts.extend(xy(p) for p in e.Tessellate())
                if not pts:
                    continue
                x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
                y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
                w, h = x1 - x0, y1 - y0
                if min(w, h) > GLASS_T_MM or max(w, h) < PANEL_MIN_MM:
                    continue
                if w >= h:
                    segs.extend(Seg((x0, y), (x1, y), u"glass", u"vách kính") for y in (y0, y1))
                else:
                    segs.extend(Seg((x, y0), (x, y1), u"glass", u"vách kính") for x in (x0, x1))

    geo = fi.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return segs


def level_fixtures(level):
    """Mọi thiết bị vệ sinh trên level. Family Work Plane Based đặt trên mặt level: LevelId có thể trống, host là level."""
    result = []
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        sym = getattr(fi, "Symbol", None)
        if sym is None:
            continue
        host = getattr(fi, "Host", None)
        if fi.LevelId == level.Id or (host is not None and host.Id == level.Id):
            result.append(fi)
    return result


def comment_of(fi):
    cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    return cm.AsString() if cm is not None else None


def read_toilets(fixtures, level_z):
    """Bồn cầu đã đặt → ([Toilet], số bồn cầu không đọc được két nước)."""
    result, missed = [], 0
    for fi in fixtures:
        if not is_toilet_name(fi.Symbol.FamilyName) and comment_of(fi) != TOILET_TAG:
            continue
        loc = getattr(fi.Location, "Point", None)
        pts = body_points(fi)
        tb = None
        if loc is not None and pts:
            f = fi.FacingOrientation
            tb = toilet_frame(fi.Id.Value, pts, xy(loc), (f.X, f.Y), level_z)
        if tb is None:
            missed += 1
        else:
            result.append(tb)
    result.sort(key=lambda x: (-round(x.c[1]), round(x.c[0])))
    return result, missed


def side_segs(fixtures):
    """Vách kính, lavabo đã đặt → biên hai bên. Trả về (segs, số vách kính, số lavabo)."""
    segs, n_glass, n_lav = [], 0, 0
    for fi in fixtures:
        name = loose(fi.Symbol.FamilyName)
        tag = comment_of(fi)
        if u"vach kinh" in name or u"vach tam" in name or tag == GLASS_TAG:
            n_glass += 1
            segs += glass_panels(fi)
        elif u"lavabo" in name or tag == LAVABO_TAG:
            bb = fi.get_BoundingBox(None)
            if bb is None:
                continue
            x0, y0 = xy(bb.Min)
            x1, y1 = xy(bb.Max)
            box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            segs += [Seg(box[i - 1], box[i], u"lavabo", u"lavabo") for i in range(4)]
            n_lav += 1
    return segs, n_glass, n_lav


def existing_of(sym, kind, level_z):
    """[(tâm khối mm, FamilyInstance, có Comments của tool)]: cùng family hoặc của tool, tâm khối trong dải cao độ của level.
    Lọc theo cao độ thay cho LevelId: instance đặt trên mặt tường có thể không có Level."""
    result = []
    family = norm(sym.FamilyName)
    for fi in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures) \
            .WhereElementIsNotElementType().ToElements():
        fs = getattr(fi, "Symbol", None)
        if fs is None:
            continue
        mine = comment_of(fi) == TAGS[kind]
        if norm(fs.FamilyName) != family and not mine:
            continue
        pts = body_points(fi)
        if not pts:
            continue
        z = (min(p[2] for p in pts) + max(p[2] for p in pts)) / 2.0 - level_z
        if not (Z_BAND_MM[0] <= z <= Z_BAND_MM[1]):
            continue
        c = ((min(p[0] for p in pts) + max(p[0] for p in pts)) / 2.0,
             (min(p[1] for p in pts) + max(p[1] for p in pts)) / 2.0)
        result.append((c, fi, mine))
    return result


def shift_z(fi, dz_mm, placement):
    """Dời đứng: "Elevation from Level" nếu ghi được (family gắn tường, đặt theo level), không thì MoveElement.
    Không dùng Offset from Host: family Face-based đặt trên tường sẽ bị đẩy ra khỏi mặt tường thay vì lên xuống."""
    if abs(dz_mm) <= 0.1:
        return
    p = fi.get_Parameter(BuiltInParameter.INSTANCE_ELEVATION_PARAM)
    if placement != FamilyPlacementType.WorkPlaneBased and p is not None and not p.IsReadOnly:
        p.Set(p.AsDouble() + from_mm(dz_mm))
    else:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(0.0, 0.0, from_mm(dz_mm)))


def wall_face_ref(wall, n):
    """Reference mặt bên của tường có pháp tuyến cùng hướng n (2D) – mặt phía phòng."""
    for shell in (ShellLayerType.Interior, ShellLayerType.Exterior):
        for ref in HostObjectUtils.GetSideFaces(wall, shell):
            face = wall.GetGeometryObjectFromReference(ref)
            if isinstance(face, PlanarFace) and face.FaceNormal.X * n[0] + face.FaceNormal.Y * n[1] > PARALLEL_COS:
                return ref
    return None


def on_room_side(fi, fx):
    """Family gắn tường nằm đúng phía phòng: tâm bbox ở phía mặt gắn so với tim tường gắn."""
    bb = fi.get_BoundingBox(None)
    if bb is None or fx.host is None:
        return True
    c = ((to_mm(bb.Min.X) + to_mm(bb.Max.X)) / 2.0, (to_mm(bb.Min.Y) + to_mm(bb.Max.Y)) / 2.0)
    w = fx.host
    return dot(sub(c, w.a), w.n) * dot(fx.tb.dir, w.n) > 0


def put_room_side(fi, fx):
    """Đưa family gắn tường về phía phòng bằng flipFacing (như tool 15). Trả về ghi chú."""
    doc.Regenerate()
    if on_room_side(fi, fx):
        return u""
    if fi.CanFlipFacing:
        st = SubTransaction(doc)
        st.Start()
        try:
            fi.flipFacing()
            doc.Regenerate()
            if on_room_side(fi, fx):
                st.Commit()
                return u""
        except Exception:
            pass
        st.RollBack()
    return (u"CÒN SAI PHÍA TƯỜNG: không tường gắn nào đưa family về phía phòng, family không lật được – thêm Flip Control "
            u"(Double Flip Vertical) vào family rồi Run lại")


def orient(fi, want, pivot):
    """Xoay instance quanh trục đứng qua pivot cho FacingOrientation trùng hướng want (2D)."""
    doc.Regenerate()
    f = fi.FacingOrientation
    ang = math.atan2(f.X * want[1] - f.Y * want[0], f.X * want[0] + f.Y * want[1])
    if abs(ang) > 1e-6:
        axis = Line.CreateBound(pivot, XYZ(pivot.X, pivot.Y, pivot.Z + 1.0))
        ElementTransformUtils.RotateElement(doc, fi.Id, axis, ang)


def hang_upright(fi, fx):
    """Vòi xịt Work Plane Based: xoay trên mặt tường cho khối treo thẳng đứng, gốc family (giá treo) ở trên."""
    n = fx.tb.dir
    pivot = fi.Location.Point
    axis = Line.CreateBound(pivot, XYZ(pivot.X + n[0], pivot.Y + n[1], pivot.Z))
    doc.Regenerate()
    pts = body_points(fi)
    ss = [fx.tb.local((p[0], p[1]))[0] for p in pts]
    zs = [p[2] for p in pts]
    if max(zs) - min(zs) < max(ss) - min(ss):
        ElementTransformUtils.RotateElement(doc, fi.Id, axis, math.pi / 2.0)
        doc.Regenerate()
        zs = [p[2] for p in body_points(fi)]
    z0 = to_mm(fi.Location.Point.Z)
    if max(zs) - z0 > z0 - min(zs):
        ElementTransformUtils.RotateElement(doc, fi.Id, axis, math.pi)


def place(fx, sym, placement, level, wall_by_id):
    """Tạo instance, thử lần lượt fx.hosts tới khi đúng phía phòng; không tường nào đúng thì đặt ở tường đầu + ghi chú.
    Trả về (fi, ghi chú)."""
    if placement == FamilyPlacementType.OneLevelBased:
        return place_on(fx, sym, placement, level, wall_by_id)
    wrong, err = False, None
    for cand in fx.hosts:
        fx.use(cand)
        st = SubTransaction(doc)
        st.Start()
        try:
            fi, note = place_on(fx, sym, placement, level, wall_by_id)
        except Exception as ex:
            st.RollBack()
            err = ex
            continue
        if not note:
            st.Commit()
            return fi, u""
        st.RollBack()
        wrong = True
    if wrong:
        fx.use(fx.hosts[0])
        return place_on(fx, sym, placement, level, wall_by_id)
    raise ValueError(err or u"không có tường Revit để gắn")


def place_on(fx, sym, placement, level, wall_by_id):
    """Tạo instance trên tường fx.host. Trả về (fi, ghi chú)."""
    p = fx.point()
    tb = fx.tb
    if placement == FamilyPlacementType.WorkPlaneBased:
        if fx.host is None:
            raise ValueError(u"không có tường Revit để gắn")
        ref = wall_face_ref(wall_by_id[fx.host.id], tb.dir)
        if ref is None:
            raise ValueError(u"không lấy được mặt tường Id {}".format(fx.host.id))
        pt = XYZ(from_mm(p[0]), from_mm(p[1]), level.Elevation + from_mm(700.0))
        fi = doc.Create.NewFamilyInstance(ref, pt, XYZ(tb.u[0], tb.u[1], 0.0), sym)
        slv = fi.get_Parameter(BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM)
        if slv is not None and not slv.IsReadOnly:
            slv.Set(level.Id)
        if fx.kind == SPRAY:
            hang_upright(fi, fx)
        return fi, u""
    pt = XYZ(from_mm(p[0]), from_mm(p[1]), 0.0)
    if placement == FamilyPlacementType.OneLevelBasedHosted:
        if fx.host is None:
            raise ValueError(u"không có tường Revit để gắn")
        fi = doc.Create.NewFamilyInstance(pt, sym, wall_by_id[fx.host.id], level, StructuralType.NonStructural)
        return fi, put_room_side(fi, fx)
    fi = doc.Create.NewFamilyInstance(pt, sym, level, StructuralType.NonStructural)
    orient(fi, tb.dir, pt)
    return fi, u""


def fit_body(fi, fx, placement, level_z, top_mm):
    """Căn: gốc family dọc tường = fx.s, đỉnh khối = top_mm; family đặt theo level dời thêm lưng áp mặt gắn.
    Trả về (số đo sau căn, độ dời mm)."""
    doc.Regenerate()
    pts = body_points(fi)
    if not pts:
        raise ValueError(u"không đọc được khối của family")
    m_s, gap, _, top, _ = measure(pts, xy(fi.Location.Point), fx, level_z)
    if fx.limit is not None:
        sign = 1.0 if fx.limit > 0 else -1.0
        reach = max(sign * (fx.tb.local((p[0], p[1]))[0] - m_s) for p in pts)
        fx.s = sign * min(abs(fx.limit) - reach, fx.want)
    ds = fx.s - m_s
    dd = -gap if placement == FamilyPlacementType.OneLevelBased else 0.0
    dz = top_mm - top
    u, d = fx.tb.u, fx.tb.dir
    move = (u[0] * ds + d[0] * dd, u[1] * ds + d[1] * dd)
    if math.hypot(*move) > 0.1:
        ElementTransformUtils.MoveElement(doc, fi.Id, XYZ(from_mm(move[0]), from_mm(move[1]), 0.0))
    shift_z(fi, dz, placement)
    doc.Regenerate()
    return measure(body_points(fi), xy(fi.Location.Point), fx, level_z), math.hypot(math.hypot(*move), dz)


def needs_rebuild(fi, fx, placement, level_z):
    """Thiết bị gắn tường / mặt tường của tool mà lưng không áp mặt gắn đầu tiên (sai phía, gắn tường thô sau lớp ốp) hoặc
    tường đang gắn không phủ vị trí mới.
    Không dời ngang qua tường được – phải tạo lại."""
    if placement == FamilyPlacementType.OneLevelBased or not fx.hosts:
        return False
    fx.use(fx.hosts[0])
    host = getattr(fi, "Host", None)
    if host is not None and host.Id.Value not in [c[0].id for c in fx.hosts]:
        return True              # tường đang gắn không phủ vị trí mới
    pts = body_points(fi)
    return bool(pts) and abs(measure(pts, xy(fi.Location.Point), fx, level_z)[1]) > FACE_TOL_MM


def set_tag(fi, kind):
    cm = fi.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS)
    if cm is not None and not cm.IsReadOnly:
        cm.Set(TAGS[kind])


def retry_side(old, fx, sym, placement, level, level_z, top_mm, wall_by_id):
    """Xoá thiết bị vừa tạo sai phía / rơi về tường sau, tạo lại trên tường đầu. Không đạt thì RollBack, giữ thiết bị cũ.
    Trả về (fi, số đo) hoặc None."""
    st = SubTransaction(doc)
    st.Start()
    try:
        doc.Delete(old.Id)
        fi, note = place(fx, sym, placement, level, wall_by_id)
        if note or fx.host is not fx.hosts[0][0]:
            raise ValueError(note)
        set_tag(fi, fx.kind)
        m, _ = fit_body(fi, fx, placement, level_z, top_mm)
        st.Commit()
        return fi, m
    except Exception:
        st.RollBack()
        return None


def preview_lines(jobs, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine

        def seg(a, e):
            return DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                               DSPoint.ByCoordinates(e[0], e[1], z_mm))
        lines = []
        for fx in jobs:
            t = fx.tb
            lines.append(seg(t.world(0.0, fx.face_d), t.world(fx.s, fx.face_d)))
            lines.append(seg(t.world(fx.s - 40.0, fx.face_d + 40.0), t.world(fx.s + 40.0, fx.face_d - 40.0)))
            lines.append(seg(t.world(fx.s - 40.0, fx.face_d - 40.0), t.world(fx.s + 40.0, fx.face_d + 40.0)))
        return lines
    except Exception:
        return []


def host_label(w):
    return u"{} ({:.0f} mm, Id {})".format(w.name, w.width, w.id)


LOG_HEADER = [u"STT", u"Bồn cầu Id", u"Phòng", u"Thiết bị", u"Bên", u"Điểm đặt (mm)", u"Tường gắn", u"Type", u"Kết quả",
              u"ElementId", u"Đo khối (tim / lưng / chân–đỉnh)", u"Ghi chú"]


def write_log(rows, source, dry_run):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoVoiXitLoGiayWC_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
    return path


def main(level_name, spray_in, paper_in, room_keys, spray_dist, paper_dist, spray_top, paper_top, swap, dry_run):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    if re.search(r"[-_]S[-_]", doc.Title or u""):
        return [u"DỪNG: tên file '{}' là mô hình Kết cấu (S) – thiết bị vệ sinh chỉ dựng trên mô hình Kiến trúc (A).".format(
            doc.Title)], []
    syms = {SPRAY: pick_type(spray_in, u"IN[1]", u"vòi xịt"), PAPER: pick_type(paper_in, u"IN[2]", u"lô giấy")}
    tops = {SPRAY: spray_top, PAPER: paper_top}
    dists = {SPRAY: spray_dist, PAPER: paper_dist}
    modes = dict((k, check_placement(s)) for k, s in syms.items())
    labels = dict((k, u"{} : {}".format(norm(s.FamilyName), get_name(s))) for k, s in syms.items())
    level = find_level(level_name)
    level_z = to_mm(level.Elevation)
    walls, wall_by_id = level_walls(level)
    room_at, n_rooms = room_finder(level)
    keys = [loose(k) for k in room_keys if k.strip()]
    if keys and not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để lọc bồn cầu trong WC (hoặc để trống IN[3])."
                          .format(level_name)])
    fixtures = level_fixtures(level)
    toilets, missed = read_toilets(fixtures, level_z)
    extra, n_glass, n_lav = side_segs(fixtures)
    jobs = plan(toilets, walls, room_at, keys, spray_dist, paper_dist, swap, extra)
    existing = dict((k, existing_of(syms[k], k, level_z)) for k in syms)

    rows, todo = [], []
    for idx, fx in enumerate(jobs, 1):
        tb = fx.tb
        note = [side_note(fx)]
        blocked = wall_blocked(fx)
        if blocked is not None:
            note = [u"tường bên cách trục {:.0f} mm < {:.0f} mm: đặt sát tường bên, cần soát".format(blocked, abs(fx.s))]
            clamp_to_wall(fx, blocked)
        has_host = fit_host(fx, walls)
        if not has_host and modes[fx.kind] != FamilyPlacementType.OneLevelBased:
            status = u"Bỏ qua – không có tường Revit phủ vị trí (mặt cách mặt dựa ≤ {:.0f} mm)".format(HOST_GAP_MM)
            fi = None
        else:
            target = fx.point()
            near = sorted(((math.hypot(*sub(c, target)), i) for i, (c, _, _) in enumerate(existing[fx.kind])
                           if math.hypot(*sub(c, target)) <= EXIST_TOL_MM))
            fi, status = None, u"Chờ tạo"
            if near:
                _, found, mine = existing[fx.kind][near[0][1]]
                fi = found
                status = u"Chờ sửa" if mine else u"Bỏ qua – đã có {} cùng family (Id {})".format(fx.kind.lower(), found.Id.Value)
        rows.append([idx, tb.eid, tb.room or u"—", fx.kind, fx.side, fmt(fx.point()),
                     host_label(fx.host) if fx.host else u"—",
                     labels[fx.kind], status, fi.Id.Value if fi is not None else u"", u"",
                     u"; ".join(v for v in note if v)])
        if status in (u"Chờ tạo", u"Chờ sửa"):
            todo.append((fx, len(rows) - 1, fi))

    done = {u"tạo": 0, u"tạo lại": 0, u"sửa": 0, u"lỗi": 0}
    if todo:
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        created, retry = [], []
        try:
            for s in syms.values():
                if not s.IsActive:
                    s.Activate()
            doc.Regenerate()
            for fx, ri, fi in todo:
                kind = fx.kind
                st = SubTransaction(doc)
                st.Start()
                try:
                    note = u""
                    verb = u"tạo"
                    if fi is not None:
                        verb = u"sửa"
                        if fi.Symbol.Id != syms[kind].Id:
                            fi.ChangeTypeId(syms[kind].Id)
                            note = u"đổi type"
                            doc.Regenerate()
                        if needs_rebuild(fi, fx, modes[kind], level_z):
                            verb = u"tạo lại"
                            note = u"xoá Id {} của tool (không áp mặt gắn)".format(fi.Id.Value)
                            doc.Delete(fi.Id)
                            fi = None
                    if fi is None:
                        fi, placed = place(fx, syms[kind], modes[kind], level, wall_by_id)
                        note = u"; ".join(v for v in (note, placed) if v)
                        set_tag(fi, kind)
                    m, moved = fit_body(fi, fx, modes[kind], level_z, tops[kind])
                    st.Commit()
                    if verb != u"sửa":
                        created.append((fi, ri))
                except Exception as ex:
                    st.RollBack()
                    rows[ri][8] = u"LỖI: {}".format(ex)
                    done[u"lỗi"] += 1
                    continue
                if verb == u"sửa" and moved <= MOVE_TOL_MM and not note:
                    rows[ri][8] = u"Bỏ qua – đã đúng vị trí"
                else:
                    rows[ri][8] = (u"Sẽ " if dry_run else u"Đã ") + verb
                    done[verb] += 1
                    if verb == u"sửa" and moved > MOVE_TOL_MM:
                        note = u"; ".join(v for v in (note, u"dời {:.0f} mm".format(moved)) if v)
                rows[ri][9] = u"" if dry_run and verb != u"sửa" else fi.Id.Value
                rows[ri][5] = fmt(fx.point())
                if fx.host is not None:
                    rows[ri][6] = host_label(fx.host)
                rows[ri][10] = u"gốc cách trục {:.0f}, lưng cách mặt gắn {:.0f}, chân–đỉnh {:.0f}–{:.0f}, rộng {:.0f}".format(
                    abs(m[0]), m[1], m[2], m[3], m[4])
                if (fx.limit is None and abs(abs(m[0]) - dists[kind]) > MOVE_TOL_MM) or abs(m[1]) > 15.0:
                    note = u"; ".join(v for v in (note, u"đo khối lệch quy tắc, cần soát") if v)
                if note:
                    rows[ri][11] = u"; ".join(v for v in (rows[ri][11], note) if v)
                if verb != u"sửa" and modes[kind] == FamilyPlacementType.OneLevelBasedHosted and fx.hosts and \
                        (u"CÒN SAI" in note or fx.host is not fx.hosts[0][0]):
                    retry.append((fx, ri, fi))
            for fx, ri, old in retry:
                got = retry_side(old, fx, syms[fx.kind], modes[fx.kind], level, level_z, tops[fx.kind], wall_by_id)
                if got is None:
                    continue
                fi, m = got
                created = [(fi if c[1] == ri else c[0], c[1]) for c in created]
                rows[ri][5], rows[ri][6] = fmt(fx.point()), host_label(fx.host)
                rows[ri][9] = u"" if dry_run else fi.Id.Value
                rows[ri][10] = u"gốc cách trục {:.0f}, lưng cách mặt gắn {:.0f}, chân–đỉnh {:.0f}–{:.0f}, rộng {:.0f}".format(
                    abs(m[0]), m[1], m[2], m[3], m[4])
                rows[ri][11] = u"; ".join(v for v in rows[ri][11].split(u"; ")
                                          if not v.startswith(u"CÒN SAI") and not v.startswith(u"đo khối lệch"))
            if dry_run:
                tx.RollBack()
            else:
                status = tx.Commit()
                if status != TransactionStatus.Committed:
                    return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
                for fi, ri in created:
                    if not fi.IsValidObject:
                        rows[ri][8] = u"Revit đã xoá sau khi tạo"
        except Exception as ex:
            if tx.HasStarted() and not tx.HasEnded():
                tx.RollBack()
            return [u"LỖI khi đặt thiết bị, mọi thay đổi đã được hoàn tác: {}".format(ex)], []

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (đã đặt thử rồi hoàn tác, không ghi vào mô hình)" if dry_run
                                else u"ĐÃ THỰC HIỆN")]
    report.append(u"Level {} – {} bồn cầu trong mô hình – phòng chứa: {}".format(
        level.Name, len(toilets), u"; ".join(room_keys) if keys else u"mọi phòng"))
    report.append(u"Vòi xịt: {} ({}) – bên {}, cách trục {:.0f} mm, đỉnh khối {:.0f} mm".format(
        labels[SPRAY], placement_label(modes[SPRAY]), u"trái" if swap else u"phải", spray_dist, spray_top))
    report.append(u"Lô giấy: {} ({}) – bên {}, cách trục {:.0f} mm, đỉnh khối {:.0f} mm".format(
        labels[PAPER], placement_label(modes[PAPER]), u"phải" if swap else u"trái", paper_dist, paper_top))
    report.append(u"Phải / trái theo người ngồi trên bồn cầu nhìn ra phòng (IN[7] = True đổi hai bên).")
    report.append(u"Thiết bị {}: {}".format(u"sẽ tạo" if dry_run else u"đã tạo", done[u"tạo"]))
    if done[u"tạo lại"]:
        report.append(u"Thiết bị của tool {} (xoá Id cũ, xem cột Ghi chú): {}".format(
            u"sẽ tạo lại" if dry_run else u"đã tạo lại", done[u"tạo lại"]))
    if done[u"sửa"]:
        report.append(u"Thiết bị của tool {}: {}".format(u"sẽ sửa" if dry_run else u"đã sửa", done[u"sửa"]))
    if done[u"lỗi"]:
        report.append(u"LỖI: {} thiết bị không đặt được – xem cột Kết quả".format(done[u"lỗi"]))
    if missed:
        report.append(u"CẦN SOÁT: {} bồn cầu không đọc được két nước (khối cao ≥ {:.0f} mm) – bỏ qua".format(missed, TANK_Z_MM))
    review = [r for r in rows if u"cần soát" in r[11] or u"CÒN SAI" in r[11]]
    if review:
        report.append(u"CẦN SOÁT: {} thiết bị – xem cột Ghi chú".format(len(review)))
    side_bad = len([r for r in rows if u"CÒN SAI" in r[11]])
    if side_bad:
        report.append(u"CÒN SAI PHÍA TƯỜNG: {} thiết bị – thêm Flip Control (Double Flip Vertical) vào family, load lại rồi Run "
                      u"lại".format(side_bad))
    counts = {}
    for tb in toilets:
        if tb.status.startswith(u"Bỏ qua"):
            k = re.sub(r"\(.*", u"", tb.status.split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for r in rows:
        if r[8].startswith(u"Bỏ qua"):
            k = re.sub(r"[\d(].*", u"", r[8].split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {}: {}".format(counts[k], k))
    report.append(u"Biên hai bên: {} vách kính, {} lavabo, {} tường trên level, {} Room".format(
        n_glass, n_lav, len(walls), n_rooms))
    try:
        report.append(u"Log: " + write_log(rows, doc.Title, dry_run))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra cột 'Đo khối' (số đo thật khi đặt thử) và dấu chữ thập trong Dynamo. Đúng thì đổi Dry-run = "
                      u"False và Run lại. Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    else:
        report.append(u"Soát vài WC (vòi treo thẳng, lô giấy đúng phía phòng). Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    return report, preview_lines(jobs, level_z)


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


def num(i, default):
    return float(IN[i]) if len(IN) > i and IN[i] is not None else default


if DYNAMO:
    import traceback
    try:
        OUT = list(main(
            (IN[0] or u"TẦNG 3"),
            IN[1] if IN[1] is not None else u"AV_Voi xit : Polished Chrome",
            IN[2] if IN[2] is not None else u"AV-Lô Giấy1 : Type 1",
            (u"WC;vệ sinh" if IN[3] is None else IN[3]).split(u";"),
            num(4, 300.0),
            num(9, 350.0),
            num(5, 750.0),
            num(6, 820.0),
            False if IN[7] is None else bool(IN[7]),
            True if IN[8] is None else bool(IN[8]),
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoVoiXitLoGiayWC_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
