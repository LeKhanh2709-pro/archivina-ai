# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong 13. ARV_TaoCuaSoTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo cửa sổ nhỏ cho phòng ngủ và WC, gắn vào tường Revit có sẵn, từ mặt bằng DWG đã Link:
#   1. Nét thẳng / polyline trên layer cửa sổ IN[1] (mặc định "A-Window") nằm trong dải bề dày một tường Revit
#      (tường thẳng trên level IN[2], dày ≥ 50 mm) → chiếu lên trục tường, gộp các đoạn chồng / cách ≤ 20 mm thành
#      một ô cửa sổ. Ưu tiên tường song song với nét. Tường Revit đứt tại ô cửa sổ (dựng theo nét tường CAD dừng ở
#      má cửa sổ) → nét vẫn gán cho trục tường đó nếu cách đầu tường ≤ 1500 mm. Bề rộng = độ dài ô (làm tròn IN[8]
#      mm). Ô rộng > IN[3] (mặc định 1500 – cửa sổ lớn W2 cùng layer) hoặc < 300 mm → bỏ qua, ghi vào báo cáo.
#      Nét không gán được cho tường nào → liệt kê vị trí trong báo cáo để soát.
#   2. Loại phòng: dò Room Revit hai bên tường (cách mặt tường 250 mm, cao Level + 1000 mm). Phía có Room tên chứa
#      IN[4] (mặc định "WC") → family:type IN[5]; tên chứa IN[6] (mặc định "Phòng ngủ") → family:type IN[7].
#      Phía còn lại là phía ngoài. Không có hoặc cả hai phía đều là phòng cần làm → báo cáo, không tạo.
#   3. Type: type có sẵn của family có Width khớp (±IN[8]/2) và Height = type mẫu → dùng; chưa có → nhân bản type mẫu,
#      đổi số bề rộng trong tên (VD "SA01-600x1000" → "SA01-800x1000"), đặt Width. Cao độ bệ (Sill Height) đặt
#      theo IN[10] (WC, mặc định 1450) / IN[11] (phòng ngủ, mặc định 450) – người dùng chốt 2026-10-29.
#      Cửa sổ phòng ngủ: đỉnh = IN[12] (mặc định 2800 = đỉnh cửa sổ W2 / đáy dầm, người dùng chốt) → chiều cao
#      = IN[12] − IN[11]; type mang chiều cao này (chưa có thì nhân bản, đổi cả số chiều cao trong tên, VD
#      W1_740X2350). IN[12] = 0 → giữ chiều cao type mẫu. WC giữ chiều cao type mẫu.
#   4. Tường cùng trục bị chia nhiều đoạn tại ô (Revit xoá cửa sổ có lỗ vượt quá đầu tường chủ): như tool 10, chọn
#      đoạn chứa phần lớn ô làm tường chủ, kéo dài phủ hết ô, cắt ngắn đoạn kế bên tới mép ô (sửa Location Curve,
#      không xoá tường); đoạn nằm trọn trong ô → báo cáo, không tạo. Tường đứt tại ô: kéo dài đoạn gần nhất qua ô;
#      còn hở tới đoạn cùng trục kế tiếp ≤ 300 mm thì kéo tới chạm đoạn đó (tường liền).
#   5. Đặt cửa sổ giữa ô trên tim tường chủ, lật Facing ra phía ngoài (FACING_TO_OUTSIDE), đặt Sill Height. Ô đã có
#      cửa sổ của family IN[5] / IN[7] → SỬA cửa sổ đó: lật hướng nếu ngược, đặt lại Sill nếu khác, đổi type nếu
#      chiều cao khác (dry-run báo trước);
#      ô đã có cửa sổ / cửa đi khác → bỏ qua. Tường / cửa sổ đang bị người khác mượn → bỏ qua.
#      Sau khi Commit kiểm tra lại cửa sổ vừa tạo; cửa sổ bị Revit xoá → báo trong log.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (để trống = bản CAD duy nhất có layer khớp IN[1])
#   IN[1] (str)   Layer cửa sổ, nhiều chuỗi cách ';' (khớp chuỗi con), VD "A-Window"
#   IN[2] (str)   Tên level tường chủ, VD "TẦNG 3"
#   IN[3] (float) Bề rộng tối đa (mm), VD 1500 – ô lớn hơn là cửa sổ loại khác, bỏ qua
#   IN[4] (str)   Tên Room WC chứa, VD "WC"
#   IN[5] (str)   Family : type mẫu cửa sổ WC, VD "AV-CuaSowc : SA01-600x1000"
#   IN[6] (str)   Tên Room phòng ngủ chứa, VD "Phòng ngủ"
#   IN[7] (str)   Family : type mẫu cửa sổ phòng ngủ, VD "SA.1 : W1_600X2500"
#   IN[8] (float) Làm tròn bề rộng (mm), VD 10
#   IN[9] (bool)  Dry-run: True = chỉ báo cáo + xem trước, không ghi vào mô hình (mặc định True)
#   IN[10] (float) Cao độ bệ cửa sổ WC so với level (mm), VD 1450
#   IN[11] (float) Cao độ bệ cửa sổ phòng ngủ so với level (mm), VD 450
#   IN[12] (float) Cao độ đỉnh cửa sổ phòng ngủ so với level (mm), VD 2800 (0 = theo chiều cao type mẫu)
# OUTPUT
#   OUT[0] (list[str])  Báo cáo: tóm tắt, đường dẫn log, rồi từng ô cửa sổ
#   OUT[1] (list[Line]) Xem trước: đoạn ô cửa sổ trên tim tường (mm)

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
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, Options, GeometryInstance, PolyLine,
                                   Line, XYZ, Transaction, TransactionStatus, UnitUtils, UnitTypeId, ModelPathUtils,
                                   BuiltInParameter, BuiltInCategory, Level, Wall, LocationCurve, LocationPoint,
                                   FamilySymbol, FamilyInstance, WorksharingUtils, CheckoutStatus, ElementId)
    from Autodesk.Revit.DB.Structure import StructuralType
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager
    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo cửa sổ từ CAD"
SCRIPT_TAG = u"ARV_TaoCuaSoTuCAD_v1"
MIN_WIDTH_MM = 300.0             # Ô hẹp hơn = nét lẻ, không phải cửa sổ
BAND_TOL_MM = 30.0               # Nét cửa sổ nằm trong dải bề dày tường + chừng này mỗi bên
MERGE_GAP_MM = 20.0              # Hai đoạn chiếu cách nhau ≤ chừng này → cùng một ô
PROBE_MM = 250.0                 # Điểm dò Room cách mặt tường
PROBE_Z_MM = 1000.0              # Cao độ điểm dò Room so với Level
COLLINEAR_MM = 5.0               # Đoạn tường cùng trục: tim lệch tối đa
MIN_HOST_WIDTH_MM = 50.0         # Tường mỏng hơn là lớp hoàn thiện / len / gạch ốp, không làm tường chủ
MIN_PIECE_MM = 20.0              # Đoạn tường còn lại sau khi cắt ngắn tối thiểu
GAP_SEARCH_MM = 1500.0           # Nét cửa sổ ở chỗ tường đứt: cách đầu tường cùng trục tối đa
GAP_FILL_MM = 300.0              # Sau khi kéo tường chủ qua ô, còn hở tới đoạn cùng trục ≤ chừng này → kéo chạm
PARALLEL_COS = 0.98              # Nét song song tường (lệch ≤ ~11°)
SILL_TOL_MM = 1.0
KINDS = ("WC", "NGU")


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
    """So tên không phân biệt dấu / hoa thường: "Phòng ngủ" ≈ "PHONG NGU"."""
    s = unicodedata.normalize("NFD", norm(s).replace(u"đ", u"d").replace(u"Đ", u"D"))
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").lower()


class HostWall(object):
    """Tường trên mặt bằng (mm). Gốc toạ độ dọc tường cố định tại a; đoạn tường là [s0, s1] (đổi khi kéo dài /
    cắt ngắn tường để phủ ô cửa sổ)."""

    def __init__(self, wid, a, b, width, name=u""):
        self.id, self.a, self.b, self.width, self.name = wid, a, b, width, name
        self.length = math.hypot(b[0] - a[0], b[1] - a[1])
        self.u = unit(sub(b, a))
        self.n = (-self.u[1], self.u[0])
        self.s0, self.s1 = 0.0, self.length

    def local(self, p):
        d = sub(p, self.a)
        return dot(d, self.u), dot(d, self.n)

    def point(self, s, d=0.0):
        return (self.a[0] + self.u[0] * s + self.n[0] * d, self.a[1] + self.u[1] * s + self.n[1] * d)


class Opening(object):
    def __init__(self, ref, lo, hi):
        self.ref, self.lo, self.hi = ref, lo, hi     # ô theo toạ độ tường tham chiếu ref
        self.host = ref
        self.s_center = (lo + hi) / 2.0              # theo toạ độ tường chủ
        self.raw_width = hi - lo
        self.width = None
        self.kind = None
        self.room = u""
        self.inside = 0                              # +1 / -1: phía phòng theo pháp tuyến n của tường chủ
        self.status = u""
        self.type_name = u""
        self.eid = u""
        self.note = u""
        self.edits = []

    def center(self):
        return self.host.point(self.s_center)


def collinear_walls(wall, walls):
    """Các đoạn tường (kể cả chính nó) nằm trên cùng trục tim với wall."""
    return [x for x in walls if abs(abs(dot(x.u, wall.u)) - 1.0) <= 1e-4
            and abs(wall.local(x.a)[1]) <= COLLINEAR_MM and abs(wall.local(x.b)[1]) <= COLLINEAR_MM]


def extent_in(w, x):
    """Đoạn [lo, hi] của tường x theo toạ độ dọc tường w."""
    sa, sb = w.local(x.point(x.s0))[0], w.local(x.point(x.s1))[0]
    return min(sa, sb), max(sa, sb)


def set_extent(x, w, lo, hi):
    """Đặt đoạn tường x = [lo, hi] cho theo toạ độ tường w."""
    sa, sb = x.local(w.point(lo))[0], x.local(w.point(hi))[0]
    x.s0, x.s1 = min(sa, sb), max(sa, sb)


def wall_of_segment(a, b, walls):
    """Tường có dải bề dày chứa cả hai đầu nét → (key, tường, lo, hi), None nếu không có. Ưu tiên tường song song
    với nét, rồi nét nằm trên tường (không ở chỗ tường đứt), rồi chồng nhiều nhất. Nét ở chỗ tường đứt được nhận nếu
    cách đầu tường ≤ GAP_SEARCH_MM; nét vuông góc tường chỉ nhận khi ngắn (má cửa sổ)."""
    seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
    if seg_len < 1.0:
        return None
    su = unit(sub(b, a))
    best = None
    for w in walls:
        sa, da = w.local(a)
        sb, db = w.local(b)
        h = w.width / 2.0 + BAND_TOL_MM
        if abs(da) > h or abs(db) > h:
            continue
        par = abs(dot(su, w.u)) >= PARALLEL_COS
        if not par and seg_len > 2.0 * h:
            continue
        lo, hi = min(sa, sb), max(sa, sb)
        ov = min(hi, w.s1) - max(lo, w.s0)
        if ov < -GAP_SEARCH_MM:
            continue
        key = (par, ov >= -MERGE_GAP_MM, ov, -max(abs(da), abs(db)))
        if best is None or key > best[0]:
            best = (key, w, lo, hi)
    return best


def merge_intervals(ivs, gap):
    out = []
    for lo, hi in sorted(ivs):
        if out and lo <= out[-1][1] + gap:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return out


def find_openings(segs, walls):
    """Gom nét cửa sổ theo trục tường → ([Opening], [nét không thuộc tường nào]) (ô theo toạ độ tường tham chiếu
    = đoạn Id nhỏ nhất cùng trục)."""
    groups, ref_of, loose_segs = {}, {}, []
    for a, b in segs:
        hit = wall_of_segment(a, b, walls)
        if hit is None:
            loose_segs.append((a, b))
            continue
        _, w, lo, hi = hit
        if w.id not in ref_of:
            ref_of[w.id] = min(collinear_walls(w, walls), key=lambda x: x.id)
        ref = ref_of[w.id]
        la, lb = ref.local(w.point(lo))[0], ref.local(w.point(hi))[0]
        groups.setdefault(ref.id, (ref, []))[1].append((min(la, lb), max(la, lb)))
    result = []
    for ref, ivs in groups.values():
        for lo, hi in merge_intervals(ivs, MERGE_GAP_MM):
            result.append(Opening(ref, lo, hi))
    return result, loose_segs


def fit_host(o, pieces):
    """Ô cửa sổ phải nằm trọn trong tường chủ. Chọn đoạn cùng trục chứa phần lớn ô làm tường chủ, kéo dài nó phủ
    hết ô, cắt ngắn các đoạn khác lấn vào ô tới mép ô. Ghi o.edits và áp ngay vào HostWall. Trả về lỗi hoặc None."""
    ref = o.ref
    hits = []
    for x in pieces:
        lo, hi = extent_in(ref, x)
        ov = min(hi, o.hi) - max(lo, o.lo)
        if ov > 0.5:
            hits.append((ov, x))
    if hits:
        hits.sort(key=lambda h: -h[0])
        w = hits[0][1]
    else:
        # Tường đứt tại ô: kéo dài đoạn cùng trục gần ô nhất
        near = []
        for x in pieces:
            lo, hi = extent_in(ref, x)
            near.append((o.lo - hi if hi <= o.lo else lo - o.hi, x))
        near = [n for n in near if n[0] <= GAP_SEARCH_MM]
        if not near:
            return u"không có đoạn tường nào dưới hoặc gần ô cửa sổ"
        w = min(near, key=lambda n: n[0])[1]
    pa, pb = w.local(ref.point(o.lo))[0], w.local(ref.point(o.hi))[0]
    o0, o1 = min(pa, pb), max(pa, pb)
    o.host, o.s_center = w, (o0 + o1) / 2.0
    h0, h1 = min(w.s0, o0), max(w.s1, o1)
    # Còn hở ≤ GAP_FILL_MM tới đoạn cùng trục kế tiếp → kéo tường chủ tới chạm đoạn đó (tường liền qua ô)
    for x in pieces:
        if x is w or any(x is y for _, y in hits):
            continue
        lo, hi = extent_in(w, x)
        if 0 < lo - h1 <= GAP_FILL_MM:
            h1 = lo
        elif 0 < h0 - hi <= GAP_FILL_MM:
            h0 = hi
    trims = []
    for _, x in hits[1:]:
        lo, hi = extent_in(w, x)
        if lo < h0 - 0.5 and hi > h1 + 0.5:
            return u"tường cùng trục Id {} chồng lên tường chủ Id {}".format(x.id, w.id)
        if lo < h0 - 0.5 and h0 - lo >= MIN_PIECE_MM:
            trims.append((x, lo, h0))
        elif hi > h1 + 0.5 and hi - h1 >= MIN_PIECE_MM:
            trims.append((x, h1, hi))
        else:
            return u"tường cùng trục Id {} nằm trọn trong ô cửa sổ – cần xoá đoạn này".format(x.id)
    for x, lo, hi in trims:     # cắt ngắn trước, kéo dài sau → tường không chồng nhau giữa chừng
        set_extent(x, w, lo, hi)
        o.edits.append((x, x.s0, x.s1))
    if (h0, h1) != (w.s0, w.s1):
        w.s0, w.s1 = h0, h1
        o.edits.append((w, w.s0, w.s1))
    return None


def round_to(x, step):
    return int(round(x / step) * step) if step > 0 else int(round(x))


def analyse(segs, walls, round_mm, max_w, room_at, room_keys, existing=None, own_families=()):
    """segs: nét cửa sổ CAD [(a, b)] mm; walls: [HostWall]; room_at(pt) → tên Room hoặc None;
    room_keys: {"WC": "wc", "NGU": "phong ngu"} (đã loose); existing: {wall_id: [(tâm mm, Id, tên, family,
    là cửa sổ)]} cửa sổ / cửa đi đã có; own_families: family cửa sổ của tool (ô đã có cửa sổ family này → SỬA).
    Trả về ([Opening], [nét không thuộc tường nào])."""
    openings, loose_segs = find_openings(segs, walls)
    line_cache = {}
    for o in openings:
        o.width = round_to(o.raw_width, round_mm)
        if o.raw_width > max_w:
            o.status = u"Bỏ qua – rộng {:.0f} > {:.0f} mm (cửa sổ loại khác)".format(o.raw_width, max_w)
            continue
        if o.raw_width < MIN_WIDTH_MM:
            o.status = u"Bỏ qua – rộng {:.0f} < {:.0f} mm (nét lẻ)".format(o.raw_width, MIN_WIDTH_MM)
            continue
        ref = o.ref
        if ref.id not in line_cache:
            line_cache[ref.id] = collinear_walls(ref, walls)
        pieces = line_cache[ref.id]
        # Loại phòng: dò Room hai bên tường
        sides = {}
        for sg in (1, -1):
            off = sg * (ref.width / 2.0 + PROBE_MM)
            name = room_at(ref.point((o.lo + o.hi) / 2.0, off)) or u""
            kind = next((k for k in KINDS if room_keys.get(k) and room_keys[k] in loose(name)), None)
            sides[sg] = (name, kind)
        hits = [sg for sg in (1, -1) if sides[sg][1]]
        if not hits:
            o.status = u"Bỏ qua – không phải phòng ngủ / WC (hai bên: {} / {})".format(
                sides[1][0] or u"ngoài", sides[-1][0] or u"ngoài")
            continue
        if len(hits) == 2:
            o.status = u"Bỏ qua – cả hai bên đều là phòng cần làm ({} / {}) – không biết phía ngoài".format(
                sides[1][0], sides[-1][0])
            continue
        sg = hits[0]
        o.room, o.kind = sides[sg][0], sides[sg][1]
        old = []
        for x in pieces:
            for p, eid, name, fam, is_win in (existing or {}).get(x.id, []):
                s, d = ref.local(p)
                if o.lo - 1 <= s <= o.hi + 1 and abs(d) <= ref.width:
                    old.append((eid, name, fam, is_win))
        if old:
            eid, name, fam, is_win = old[0]
            o.eid = eid
            if is_win and norm(fam) in own_families:
                # Cửa sổ của tool đã có → kiểm tra / sửa hướng và cao độ bệ (ở main)
                o.inside = sg
                o.status = u"SỬA"
                o.type_name = name
            else:
                o.status = u"Bỏ qua – ô đã có cửa sổ / cửa đi ({})".format(name)
            continue
        err = fit_host(o, pieces)
        if err:
            o.status = u"Bỏ qua – " + err
            continue
        w = o.host
        o.inside = sg if dot(w.n, ref.n) > 0 else -sg
        if not (w.s0 <= o.s_center <= w.s1):
            o.status = u"Bỏ qua – tâm ô nằm ngoài tường chủ"
            continue
        if o.edits:
            o.note = u"; ".join(u"tường {} {} đoạn {:.0f}→{:.0f}".format(
                x.id, u"kéo dài" if x is w else u"cắt ngắn", s0, s1) for x, s0, s1 in o.edits)
        o.status = u"OK"
    openings.sort(key=lambda o: (-round(o.center()[1]), round(o.center()[0])))
    return openings, loose_segs


def cluster_points(segs, gap):
    """Gom nét rời thành cụm theo khoảng cách trung điểm ≤ gap → [(tâm, số nét)] (để báo vị trí cần soát)."""
    groups = []
    for a, b in segs:
        m = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
        for g in groups:
            if math.hypot(m[0] - g[0][0] / g[1], m[1] - g[0][1] / g[1]) <= gap:
                g[0][0] += m[0]
                g[0][1] += m[1]
                g[1] += 1
                break
        else:
            groups.append([[m[0], m[1]], 1])
    return [((g[0][0] / g[1], g[0][1] / g[1]), g[1]) for g in groups]


def renamed(template_name, width, height=None):
    """Đổi số bề rộng (và chiều cao nếu có) trong tên type mẫu dạng "<rộng>x<cao>" (VD SA01-600x1000, W1_600X2500)."""
    m = re.search(r"(\d+)([xX])(\d+)", template_name)
    if not m:
        return u"{}_{}{}".format(template_name, int(width), u"x{}".format(int(height)) if height else u"")
    h = str(int(round(height))) if height else m.group(3)
    return template_name[:m.start()] + str(int(width)) + m.group(2) + h + template_name[m.end():]


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


def layer_of(geo_obj):
    style = doc.GetElement(geo_obj.GraphicsStyleId)
    if style is not None and style.GraphicsStyleCategory is not None:
        return style.GraphicsStyleCategory.Name
    return None


def cad_objects(cad):
    """Mọi đối tượng hình học của CAD, kể cả trong block lồng nhau."""
    opt = Options()
    if cad.ViewSpecific:
        opt.View = doc.GetElement(cad.OwnerViewId)
    result = []

    def walk(geo):
        for obj in geo:
            if isinstance(obj, GeometryInstance):
                walk(obj.GetInstanceGeometry())
            else:
                result.append(obj)

    geo = cad.get_Geometry(opt)
    if geo is not None:
        walk(geo)
    return result


def match_layers(all_layers, filters):
    # So khớp không phân biệt hoa thường, chuẩn hoá Unicode
    return set(l for l in all_layers if any(norm(f).lower() in norm(l).lower() for f in filters))


class StopReport(Exception):
    def __init__(self, lines):
        Exception.__init__(self, lines[0])
        self.lines = lines


def pick_cad(cad_filter, filters):
    """Chọn bản CAD theo tên; để trống thì lấy bản CAD duy nhất có layer khớp. Trả về (cad, tên, objects, layers)."""
    found = []
    for inst in FilteredElementCollector(doc).OfClass(ImportInstance).ToElements():
        name = get_name(doc.GetElement(inst.GetTypeId()))
        if cad_filter and cad_filter.lower() not in name.lower():
            continue
        objects = cad_objects(inst)
        all_layers = sorted(set(l for l in (layer_of(o) for o in objects) if l))
        found.append((inst, name, objects, all_layers))
    hits = [f for f in found if match_layers(f[3], filters)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise StopReport([u"DỪNG: không có bản CAD{} nào có layer chứa '{}'.".format(
            u" khớp '{}'".format(cad_filter) if cad_filter else u"", u"; ".join(filters))])
    raise StopReport([u"DỪNG: {} bản CAD có layer khớp – nhập tên bản CAD vào ô IN[0]: {}".format(
        len(hits), u", ".join(h[1] for h in hits))])


def find_level(name):
    levels = list(FilteredElementCollector(doc).OfClass(Level).ToElements())
    for l in levels:
        if norm(l.Name).lower() == norm(name).lower():
            return l
    raise StopReport([u"DỪNG: không có level '{}'. Các level: {}".format(
        name, u", ".join(l.Name for l in sorted(levels, key=lambda x: x.Elevation)))])


def xy(p):
    return (to_mm(p.X), to_mm(p.Y))


def read_segments(objects, layers):
    segs = []
    for obj in objects:
        if layer_of(obj) not in layers:
            continue
        if isinstance(obj, Line):
            pts = [obj.GetEndPoint(0), obj.GetEndPoint(1)]
        elif isinstance(obj, PolyLine):
            pts = list(obj.GetCoordinates())
        else:
            continue
        pts = [xy(p) for p in pts]
        segs.extend(zip(pts[:-1], pts[1:]))
    return segs


def host_walls(level):
    result, by_id = [], {}
    for wl in FilteredElementCollector(doc).OfClass(Wall).ToElements():
        loc = wl.Location
        if wl.LevelId == level.Id and isinstance(loc, LocationCurve) and isinstance(loc.Curve, Line) \
                and to_mm(wl.Width) >= MIN_HOST_WIDTH_MM:
            c = loc.Curve
            hw = HostWall(wl.Id.Value, xy(c.GetEndPoint(0)), xy(c.GetEndPoint(1)), to_mm(wl.Width), get_name(wl))
            result.append(hw)
            by_id[hw.id] = wl
    return result, by_id


def existing_openings():
    """{id tường chủ: [(tâm mm, Id, "family : type", family, là cửa sổ)]} của mọi cửa sổ và cửa đi có tường chủ
    (cửa trượt logia cũng vẽ trên layer A-Window – ô đã có cửa đi thì không đặt cửa sổ)."""
    result = {}
    for bic in (BuiltInCategory.OST_Windows, BuiltInCategory.OST_Doors):
        for fi in FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType().ToElements():
            host = getattr(fi, "Host", None)
            loc = getattr(fi, "Location", None)
            if host is None or not isinstance(loc, LocationPoint):
                continue
            sym = fi.Symbol
            result.setdefault(host.Id.Value, []).append(
                (xy(loc.Point), fi.Id.Value, u"{} : {}".format(sym.FamilyName, get_name(sym)), sym.FamilyName,
                 bic == BuiltInCategory.OST_Windows))
    return result


def room_finder(level):
    """Hàm room_at(pt mm) → tên Room trên level chứa điểm (cao Level + PROBE_Z_MM), None nếu không có."""
    rooms = [r for r in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Rooms)
             .WhereElementIsNotElementType().ToElements() if r.LevelId == level.Id and r.Area > 0]
    z = level.Elevation + from_mm(PROBE_Z_MM)

    def room_at(p):
        pt = XYZ(from_mm(p[0]), from_mm(p[1]), z)
        for r in rooms:
            if r.IsPointInRoom(pt):
                prm = r.get_Parameter(BuiltInParameter.ROOM_NAME)
                return prm.AsString() if prm is not None else u""
        return None
    return room_at, len(rooms)


def parse_family_type(text, label):
    parts = [norm(p) for p in (text or u"").split(u":")]
    if len(parts) != 2 or not all(parts):
        raise StopReport([u"DỪNG: ô {} phải có dạng 'Family : Type' (đang là '{}').".format(label, text)])
    return parts


def window_symbols(family_name, label):
    symbols = [s for s in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Windows)
               .WhereElementIsElementType().ToElements() if isinstance(s, FamilySymbol)]
    result = [s for s in symbols if norm(s.FamilyName) == family_name]
    if not result:
        raise StopReport([u"DỪNG: không có family cửa sổ '{}' ({}). Các family cửa sổ: {}".format(
            family_name, label, u", ".join(sorted(set(s.FamilyName for s in symbols))) or u"không có")])
    return result


def size_param(s, which):
    if which == "w":
        return s.get_Parameter(BuiltInParameter.WINDOW_WIDTH) or s.get_Parameter(BuiltInParameter.GENERIC_WIDTH) \
            or s.LookupParameter("Width")
    return s.get_Parameter(BuiltInParameter.WINDOW_HEIGHT) or s.get_Parameter(BuiltInParameter.DOOR_HEIGHT) \
        or s.get_Parameter(BuiltInParameter.GENERIC_HEIGHT) or s.LookupParameter("Height")


def symbol_size(s):
    w, h = size_param(s, "w"), size_param(s, "h")
    return (to_mm(w.AsDouble()) if w else None, to_mm(h.AsDouble()) if h else None)


def match_symbol(symbols, width, height, tol):
    for s in symbols:
        w, h = symbol_size(s)
        if w is not None and h is not None and abs(w - width) <= tol and abs(h - height) <= 1.0:
            return s
    return None


def set_size(symbol, width, height):
    for which, name, v in (("w", u"Width", width), ("h", u"Height", height)):
        p = size_param(symbol, which)
        if p is None or p.IsReadOnly:
            raise Exception(u"Type '{}' không đặt được tham số {}.".format(get_name(symbol), name))
        p.Set(from_mm(v))


def wall_xyz(wall):
    c = wall.Location.Curve
    return c.GetEndPoint(0), c.GetEndPoint(1)


def set_wall_extent(wall, hw, s0, s1):
    """Đặt Location Curve của tường theo đoạn [s0, s1] dọc trục hw, giữ chiều vẽ và cao độ."""
    p0, p1 = wall_xyz(wall)
    z = p0.Z
    if hw.local(xy(p0))[0] > hw.local(xy(p1))[0]:
        s0, s1 = s1, s0
    a, b = hw.point(s0), hw.point(s1)
    wall.Location.Curve = Line.CreateBound(XYZ(from_mm(a[0]), from_mm(a[1]), z), XYZ(from_mm(b[0]), from_mm(b[1]), z))


def owned_by_other(element_id):
    return doc.IsWorkshared and WorksharingUtils.GetCheckoutStatus(doc, element_id) == CheckoutStatus.OwnedByOtherUser


# Quy ước hướng của family (+1 / -1): +1 = FacingOrientation chỉ ra phía ngoài nhà. Với AV-CuaSowc / SA.1,
# FacingOrientation chỉ VÀO phòng (lần chạy 2026-10-29 15:57 với +1 → 16 cửa sổ quay ngược, người dùng báo) → -1.
FACING_TO_OUTSIDE = -1


def facing_wrong(fi, o):
    w = o.host
    out = (-w.n[0] * o.inside, -w.n[1] * o.inside)
    f = fi.FacingOrientation
    return FACING_TO_OUTSIDE * dot((f.X, f.Y), out) < 0


def orient(fi, o):
    """Lật Facing nếu ngược. Trả về True nếu đã lật."""
    doc.Regenerate()
    if facing_wrong(fi, o):
        fi.flipFacing()
        return True
    return False


def sill_param(fi):
    return fi.get_Parameter(BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)


def sill_mm(fi):
    p = sill_param(fi)
    return to_mm(p.AsDouble()) if p is not None else None


def set_sill(fi, mm):
    p = sill_param(fi)
    if p is None or p.IsReadOnly:
        raise Exception(u"Cửa sổ Id {} không đặt được Sill Height.".format(fi.Id.Value))
    p.Set(from_mm(mm))


def preview_lines(pairs, z_mm):
    try:
        clr.AddReference("ProtoGeometry")
        from Autodesk.DesignScript.Geometry import Point as DSPoint, Line as DSLine
        return [DSLine.ByStartPointEndPoint(DSPoint.ByCoordinates(a[0], a[1], z_mm),
                                            DSPoint.ByCoordinates(b[0], b[1], z_mm)) for a, b in pairs]
    except Exception:
        return []


LOG_HEADER = [u"STT", u"Tâm ô (mm)", u"Rộng CAD (mm)", u"Rộng (mm)", u"Phòng", u"Tường chủ", u"Type", u"Kết quả",
              u"ElementId", u"Ghi chú"]
WALL_LOG_HEADER = [u"Ô STT", u"Tường (ElementId)", u"Việc", u"Tim tường cũ (mm)", u"Tim tường mới (mm)"]


def write_log(rows, source, dry_run, wall_rows=()):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoCuaSoTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n".format(doc.Title))
        f.write(u"# File nguồn: {}\n".format(source))
        f.write(u"# Ngày xuất: {}\n".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        f.write(u"# Chế độ: {}\n".format(u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        f.write(u"# Đơn vị: mm\n")
        w = csv.writer(f)
        w.writerow(LOG_HEADER)
        w.writerows(rows)
        if wall_rows:
            f.write(u"# Tường sửa đầu mút để phủ ô cửa sổ\n")
            w.writerow(WALL_LOG_HEADER)
            w.writerows(wall_rows)
    return path


def main(cad_filter, layer_filters, level_name, max_w, wc_key, wc_ft, bed_key, bed_ft, round_mm, dry_run, sills,
         heads):
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."], []
    cad, cad_name, objects, all_layers = pick_cad(cad_filter, layer_filters)
    win_layers = match_layers(all_layers, layer_filters)
    level = find_level(level_name)
    walls, wall_by_id = host_walls(level)
    if not walls:
        raise StopReport([u"DỪNG: level '{}' chưa có tường thẳng nào để gắn cửa sổ.".format(level_name)])

    spec = {}   # kind → (family, type mẫu, [symbols], symbol mẫu)
    for kind, ft, label in (("WC", wc_ft, u"IN[5]"), ("NGU", bed_ft, u"IN[7]")):
        fam, tname = parse_family_type(ft, label)
        symbols = window_symbols(fam, label)
        tpl = [s for s in symbols if norm(get_name(s)) == tname]
        if not tpl:
            raise StopReport([u"DỪNG: family '{}' không có type mẫu '{}' ({}). Các type: {}".format(
                fam, tname, label, u", ".join(sorted(get_name(s) for s in symbols)))])
        spec[kind] = (fam, tname, symbols, tpl[0])
    room_at, n_rooms = room_finder(level)
    if not n_rooms:
        raise StopReport([u"DỪNG: level '{}' chưa có Room – cần Room để biết phòng ngủ / WC.".format(level_name)])

    segs = read_segments(objects, win_layers)
    openings, loose_segs = analyse(segs, walls, round_mm, max_w, room_at,
                                   {"WC": loose(wc_key), "NGU": loose(bed_key)}, existing_openings(),
                                   set(norm(spec[k][0]) for k in spec))

    tol = max(round_mm / 2.0, 1.0)
    heights = {}   # kind → chiều cao cửa sổ (mm)
    for kind in spec:
        h_tpl = symbol_size(spec[kind][3])[1]
        heights[kind] = heads[kind] - sills[kind] if heads.get(kind) else h_tpl
        if heights[kind] is None or heights[kind] <= 0:
            raise StopReport([u"DỪNG: chiều cao cửa sổ {} không hợp lệ (đỉnh {} − bệ {}).".format(
                kind, heads.get(kind), sills[kind])])
    planned = {}   # (kind, rộng) → FamilySymbol có sẵn hoặc tên type sẽ nhân bản

    def plan_type(kind, width):
        key = (kind, width)
        if key not in planned:
            fam, tname, symbols, tpl = spec[kind]
            s = match_symbol(symbols, width, heights[kind], tol)
            planned[key] = s if s is not None else renamed(tname, width, heights[kind])
        t = planned[key]
        return get_name(t) if not isinstance(t, (str, type(u""))) else t + u" (mới)"

    rows, jobs, wall_rows, fixes = [], [], [], []
    for idx, o in enumerate(openings, 1):
        if o.status == u"SỬA":
            # Cửa sổ của tool đã có: lật hướng nếu ngược, đặt lại cao độ bệ nếu khác
            fi = doc.GetElement(ElementId(o.eid))
            todo = []
            if fi is not None and facing_wrong(fi, o):
                todo.append(u"lật hướng")
            old_sill = sill_mm(fi) if fi is not None else None
            if old_sill is None or abs(old_sill - sills[o.kind]) > SILL_TOL_MM:
                todo.append(u"bệ {} → {:.0f}".format(u"?" if old_sill is None else u"{:.0f}".format(old_sill),
                                                    sills[o.kind]))
            retype = False
            if fi is not None:
                cw, ch = symbol_size(fi.Symbol)
                if ch is None or abs(ch - heights[o.kind]) > 1.0:
                    o.width = int(round(cw)) if cw is not None else o.width
                    todo.append(u"type {} → {}".format(get_name(fi.Symbol), plan_type(o.kind, o.width)))
                    retype = True
            if fi is None:
                o.status = u"Bỏ qua – không đọc được cửa sổ Id {}".format(o.eid)
            elif not todo:
                o.status = u"Bỏ qua – ô đã có cửa sổ đúng hướng và cao độ bệ"
            elif owned_by_other(fi.Id):
                o.status = u"Bỏ qua – cửa sổ Id {} đang bị người khác mượn".format(o.eid)
            else:
                o.note = u"; ".join(todo)
                o.status = u"Sẽ sửa" if dry_run else u"Chờ sửa"
                fixes.append((o, fi, len(rows), retype))
        if o.status == u"OK":
            busy = [i for i in set([o.host.id] + [x.id for x, _, _ in o.edits]) if owned_by_other(wall_by_id[i].Id)]
            if busy:
                o.status = u"Bỏ qua – tường đang bị người khác mượn (Id {})".format(u", ".join(str(i) for i in busy))
                o.edits = []
        if o.status == u"OK":
            o.type_name = u"{} : {}".format(spec[o.kind][0], plan_type(o.kind, o.width))
            o.status = u"Sẽ tạo" if dry_run else u"Chờ tạo"
            jobs.append((o, len(rows)))
            for x, s0, s1 in o.edits:
                p0, p1 = wall_xyz(wall_by_id[x.id])
                a, b = (x.point(s0), x.point(s1)) if x.local(xy(p0))[0] <= x.local(xy(p1))[0] else \
                    (x.point(s1), x.point(s0))
                wall_rows.append([idx, x.id, u"kéo dài (tường chủ)" if x is o.host else u"cắt ngắn",
                                  u"{} → {}".format(fmt(xy(p0)), fmt(xy(p1))), u"{} → {}".format(fmt(a), fmt(b))])
        rows.append([idx, fmt(o.center()), u"{:.0f}".format(o.raw_width), o.width if o.width is not None else u"—",
                     o.room or u"—", u"{} ({})".format(o.host.id, o.host.name), o.type_name or u"—", o.status, o.eid,
                     o.note])

    created, lost = [], 0
    if not dry_run and (jobs or fixes):
        TransactionManager.Instance.ForceCloseTransaction()
        tx = Transaction(doc, TRANSACTION_NAME)
        tx.Start()
        try:
            for key in sorted(planned):
                t = planned[key]
                if isinstance(t, (str, type(u""))):
                    symbols, tpl = spec[key[0]][2], spec[key[0]][3]
                    same = [s for s in symbols if norm(get_name(s)) == norm(t)]
                    new_type = same[0] if same else tpl.Duplicate(t)
                    set_size(new_type, key[1], heights[key[0]])
                    planned[key] = new_type
            for o, ri in jobs:
                for x, s0, s1 in o.edits:
                    set_wall_extent(wall_by_id[x.id], x, s0, s1)
                if o.edits:
                    doc.Regenerate()
                sym = planned[(o.kind, o.width)]
                if not sym.IsActive:
                    sym.Activate()
                    doc.Regenerate()
                wall = wall_by_id[o.host.id]
                c = o.center()
                z = wall.Location.Curve.GetEndPoint(0).Z
                fi = doc.Create.NewFamilyInstance(XYZ(from_mm(c[0]), from_mm(c[1]), z), sym, wall, level,
                                                  StructuralType.NonStructural)
                set_sill(fi, sills[o.kind])
                orient(fi, o)
                rows[ri][7] = u"Đã tạo"
                rows[ri][8] = fi.Id.Value
                rows[ri][9] = u"; ".join(v for v in (o.note, u"bệ {:.0f}".format(sills[o.kind])) if v)
                created.append((fi, ri))
            for o, fi, ri, retype in fixes:
                done = []
                if retype:
                    sym = planned[(o.kind, o.width)]
                    if not sym.IsActive:
                        sym.Activate()
                    old_name = get_name(fi.Symbol)
                    fi.ChangeTypeId(sym.Id)
                    done.append(u"type {} → {}".format(old_name, get_name(sym)))
                if orient(fi, o):
                    done.append(u"lật hướng")
                old_sill = sill_mm(fi)
                if old_sill is None or abs(old_sill - sills[o.kind]) > SILL_TOL_MM:
                    set_sill(fi, sills[o.kind])
                    done.append(u"bệ {} → {:.0f}".format(u"?" if old_sill is None else u"{:.0f}".format(old_sill),
                                                        sills[o.kind]))
                rows[ri][7] = u"Đã sửa"
                rows[ri][9] = u"; ".join(done) or u"không cần sửa"
            status = tx.Commit()
        except Exception as ex:
            tx.RollBack()
            return [u"LỖI khi tạo cửa sổ, mọi thay đổi đã được hoàn tác: {}".format(ex)], []
        if status != TransactionStatus.Committed:
            return [u"LỖI: Revit không lưu được Transaction ({}), mọi thay đổi đã được hoàn tác.".format(status)], []
        for fi, ri in created:
            if not fi.IsValidObject:
                rows[ri][7] = u"Revit đã xoá sau khi tạo (không cắt được tường)"
                lost += 1

    report = [u"{} – {}".format(TRANSACTION_NAME, u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else u"ĐÃ THỰC HIỆN")]
    report.append(u"CAD: {} – layer cửa sổ: {} – {} nét".format(cad_name, u"; ".join(sorted(win_layers)), len(segs)))
    for kind, label, key in (("WC", u"WC", wc_key), ("NGU", u"Phòng ngủ", bed_key)):
        fam, tname, _, tpl = spec[kind]
        report.append(u"{} (Room chứa '{}'): {} : {} – cao {:.0f} mm, bệ {:.0f} mm, đỉnh {:.0f} mm".format(
            label, key, fam, tname, heights[kind], sills[kind], sills[kind] + heights[kind]))
    report.append(u"Level: {} – ô cửa sổ CAD: {} – {}: {} (WC {}, phòng ngủ {}) – {} cửa sổ đã có: {} – làm tròn "
                  u"rộng {:.0f} mm".format(
                      level.Name, len(openings), u"sẽ tạo" if dry_run else u"đã tạo", len(jobs),
                      len([1 for o, _ in jobs if o.kind == "WC"]), len([1 for o, _ in jobs if o.kind == "NGU"]),
                      u"sẽ sửa" if dry_run else u"đã sửa", len(fixes), round_mm))
    counts = {}
    for o in openings:
        if o.status.startswith(u"Bỏ qua"):
            k = re.sub(r"\(.*", u"", o.status.split(u" – ", 1)[1]).strip()
            counts[k] = counts.get(k, 0) + 1
    for k in sorted(counts):
        report.append(u"Bỏ qua {} ô: {}".format(counts[k], k))
    if loose_segs:
        spots = cluster_points(loose_segs, 1500.0)
        report.append(u"SOÁT: {} nét cửa sổ không nằm trên / gần tường Revit nào ({} chỗ) – có thể thiếu tường: {}".format(
            len(loose_segs), len(spots), u", ".join(u"{} ({} nét)".format(fmt(p), n) for p, n in spots[:30])))
    if lost:
        report.append(u"CẢNH BÁO: Revit đã xoá {} cửa sổ ngay sau khi tạo (không cắt được tường) – xem cột Kết quả."
                      .format(lost))
    if wall_rows:
        report.append(u"Tường {} đầu mút để ô nằm trọn trong tường chủ: {} lượt (không xoá tường) – chi tiết cuối log:"
                      .format(u"sẽ sửa" if dry_run else u"đã sửa", len(wall_rows)))
        report += [u"  Ô {} – tường {} {}: {} ⇒ {}".format(*r) for r in wall_rows]
    new_types = sorted(set(o.type_name for o, _ in jobs if o.type_name.endswith(u"(mới)")))
    if new_types:
        report.append(u"Type {} (nhân bản từ type mẫu, đổi Width): {}".format(
            u"sẽ tạo" if dry_run else u"đã tạo", u", ".join(new_types)))
    try:
        report.append(u"Log: " + write_log(rows, cad_name, dry_run, wall_rows))
    except Exception as ex:
        report.append(u"Không ghi được file log: {}".format(ex))
    if dry_run:
        report.append(u"Kiểm tra ô cửa sổ (đoạn xanh trong Dynamo) + log. Đúng thì đổi Dry-run = False và Run lại. "
                      u"Undo bằng mục \"{}\".".format(TRANSACTION_NAME))
    else:
        report.append(u"Soát hướng trong / ngoài và cao độ bệ của vài cửa sổ. Undo bằng mục \"{}\".".format(
            TRANSACTION_NAME))
    report.append(u" | ".join(LOG_HEADER))
    report += [u" | ".join(u"{}".format(v) for v in r) for r in rows]
    z_mm = to_mm(level.Elevation)
    pairs = [(o.host.point(o.s_center - o.width / 2.0), o.host.point(o.s_center + o.width / 2.0)) for o, _ in jobs]
    return report, preview_lines(pairs, z_mm)


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
            [s.strip() for s in (IN[1] or u"A-Window").split(u";") if s.strip()],
            (IN[2] or u"TẦNG 3"),
            float(IN[3] or 1500.0),
            (IN[4] or u"WC"),
            (IN[5] or u"AV-CuaSowc : SA01-600x1000"),
            (IN[6] or u"Phòng ngủ"),
            (IN[7] or u"SA.1 : W1_600X2500"),
            float(IN[8] if IN[8] is not None else 10.0),
            True if IN[9] is None else bool(IN[9]),
            {"WC": float(IN[10] if len(IN) > 10 and IN[10] is not None else 1450.0),
             "NGU": float(IN[11] if len(IN) > 11 and IN[11] is not None else 450.0)},
            {"WC": 0.0, "NGU": float(IN[12] if len(IN) > 12 and IN[12] is not None else 2800.0)},
        ))
    except StopReport as ex:
        OUT = [ex.lines, []]
    except Exception as ex:
        OUT = [[u"LỖI: {}".format(ex), traceback.format_exc()], []]
        try:
            folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(os.path.join(folder, "TaoCuaSoTuCAD_LOI_{}.txt".format(
                    datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))), "w", encoding="utf-8-sig") as f:
                f.write(u"\n".join(OUT[0]))
        except Exception:
            pass
    note = force_rerun_next_time()
    if note:
        OUT[0].append(u"LƯU Ý: " + note)
