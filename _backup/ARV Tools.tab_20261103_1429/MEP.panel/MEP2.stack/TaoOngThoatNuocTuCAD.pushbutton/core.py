# TRẠNG THÁI: CHƯA DUYỆT
# Mã nguồn của Python node trong ARV_TaoOngThoatNuocTuCAD_v1.dyn (bản để review; .dyn nhúng đúng nội dung này).
#
# Tạo ống thoát nước uPVC + phụ kiện (co, Y 45°, tê, côn) từ mặt bằng cấp thoát nước (DWG CTN đã Link vào Revit).
#   Đọc từ BẢN SAO DWG qua AutoCAD Core Console (chữ, dim, block trong bản link Revit không đọc được):
#   - Ống: LINE 1 nét trên các layer IN[1]. Đoạn tách tại nút T, khe hở cùng layer ≤ 50 mm được nối.
#   - DN: dimension có dimstyle chứa "Dxxx" (VD "AV-Dim 1-75 (D160)", "0.T D110 (1-200)") gán cho đoạn giữa 2 điểm đo;
#     chữ "D75-2%" gán DN + độ dốc cho ống gần nhất; còn lại lan theo tuyến, rồi theo ống hạ lưu; không có → D75.
#     DN không được giảm về hạ lưu: đoạn nhỏ hơn ống đổ vào nó được nâng lên (ghi log).
#   - Hướng chảy: block mũi tên IN[5]. Điểm xả của mỗi cụm ống = tổ hợp đầu cụt (ống đứng R100, điểm rơi
#     xuống lớp dưới, đầu cụt có mũi tên chỉ vào) khớp mũi tên nhiều nhất.
#   - Cao độ: dốc theo chữ ghi chú, mặc định DN ≤ 90 → 2 %, còn lại 1 %; điểm cao nhất mỗi cụm cách level trên IN[4].
#   - Nhóm cao độ theo hậu tố layer (IN[3]): VD "T5" = dưới sàn TẦNG 5; layer không hậu tố = dưới sàn TẦNG chuyển.
#     Đầu cụt lớp có hậu tố trùng ống lớp thường cùng loại → ống đứng rơi xuống, nối tê.
#   - Ống đứng: tại điểm xả xuống tới level dưới; tại vòng tròn ống đứng là đầu thượng lưu → lên tới level trên.
#   Phụ kiện: co / côn dùng routing preference của pipe type; Y 45° và tê đặt thủ công (xoay theo 3 ống, đặt bán
#   kính từng cổng) vì NewTeeFitting không làm góc 45° (đã thử cả family công ty u.PVC_WYE) và tra bảng kích
#   thước family thư viện thiếu cỡ uPVC. Family Y / tê lấy từ rule Junctions của pipe type (nhận theo góc nhánh
#   45° / 90°); pipe type chưa có thì tạo type uPVC + nạp family thư viện ở IN[6].
#   Mỗi phụ kiện trong một SubTransaction: ống bị cắt lẹm / đổi chiều → hoàn tác phụ kiện đó, ghi vào báo cáo.
# INPUT
#   IN[0] (str)   Một phần tên bản CAD (VD "ctn"; trống = bản CAD duy nhất)
#   IN[1] (str)   Layer ống, cách ';' (khớp đúng tên). Mặc định 7 layer DR + VE-Hơi.
#   IN[2] (str)   Piping system theo chuỗi con trong tên layer (lấy luật đầu tiên khớp, '*' = còn lại)
#   IN[3] (str)   Nhóm cao độ theo hậu tố layer: "T5=TẦNG 5>TẦNG chuye;*=TẦNG chuye>TẦNG 4" (level trên > level dưới);
#                 level kèm độ lệch mm được: "Test+3000>Test"; "CAD" = level của mặt bằng chứa link CAD.
#                 Level không có trong mô hình → tự vẽ trên mặt bằng chứa link CAD (level trên = level kế trên
#                 hoặc +3000 mm), ghi trong báo cáo.
#   IN[4] (float) Khoảng cách level trên → tâm ống tại điểm cao nhất của cụm (mm), mặc định 400
#   IN[5] (str)   Tên block mũi tên hướng nước chảy
#   IN[6] (str)   Thư mục family phụ kiện PVC DWV (chỉ dùng khi phải tạo pipe type mới)
#   IN[7] (str)   Pipe type: có sẵn thì dùng (VD "AV_u.PVC PN6"), chưa có thì tạo (segment uPVC, OD 60…315)
#   IN[8] (bool)  Dry-run: True = chỉ báo cáo (mặc định True)
#   IN[9] (str)   Chỉ dựng tuyến đi qua điểm DWG "x,y" (mm, cách ';' nhiều điểm; trống = toàn bộ). Ống rơi xuống
#                 lớp dưới không nằm trong phạm vi dựng → thay bằng ống đứng xuống level dưới.
#   IN[10] (str)  Màu trong view đang mở theo chuỗi con tên layer: "phân=255,255,0;Hơi=128,0,128" (trống = không tô)
#   IN[11] (str)  DN theo layer: "phân=110;*=75" – luật có tên = DN tối thiểu của layer đó, '*' = DN cho đoạn không nhãn
#   IN[12] (str)  Layer dựng phẳng, không dốc (chuỗi con, cách ';'), VD "Nước xả" = ống đẩy bơm
# OUTPUT
#   OUT (list[str]) Báo cáo: tóm tắt, log, danh sách phụ kiện không đặt được, mũi tên ngược.

import os
import io
import re
import csv
import glob
import math
import heapq
import shutil
import itertools
import tempfile
import datetime
import subprocess
import collections

DYNAMO = "IN" in globals()

if DYNAMO:
    import clr
    clr.AddReference("RevitAPI")
    from Autodesk.Revit.DB import (FilteredElementCollector, ImportInstance, CADLinkType, XYZ, Line, Transaction,
                                   SubTransaction, ModelPathUtils, BuiltInParameter, Level, Material, Family,
                                   FamilySymbol, MEPSize, RoutingPreferenceRule, RoutingPreferenceRuleGroupType,
                                   ElementTransformUtils, Color, OverrideGraphicSettings,
                                   FillPatternElement)
    from Autodesk.Revit.DB.Plumbing import Pipe, PipeType, PipeSegment, PipeScheduleType, PipingSystemType
    from Autodesk.Revit.DB.Structure import StructuralType
    from System.Collections.Generic import List
    from Autodesk.Revit.DB import (IFailuresPreprocessor, FailureProcessingResult, FailureSeverity, TransactionStatus,
                                   FamilyInstance)

    import uuid
    # Dynamo giữ phiên Python giữa các lần Run → tên kiểu .NET phải khác nhau mỗi lần, không thì
    # "TypeError: Duplicate type name within an assembly" (2026-10-21)
    _CTN_NS = "ARV_TaoOngThoatNuoc_" + uuid.uuid4().hex

    class CommitFailures(IFailuresPreprocessor):
        """Lỗi lúc commit (VD 'family … can no longer keep the connectivity') → chọn cách xử lý mặc định của Revit
        (ngắt kết nối phụ kiện) thay vì bật hộp thoại làm hủy cả lần chạy; cảnh báo thì bỏ qua."""
        __namespace__ = _CTN_NS

        def __init__(self):
            self.resolved = collections.Counter()
            self.all = collections.Counter()      # (mức độ, nội dung) → số lần, mọi lỗi kể cả không xử lý được
            self.ids = collections.defaultdict(set)
            self.warnings = collections.Counter()
            self.calls = 0

        def PreprocessFailures(self, fa):
            # Chỉ trả ProceedWithCommit khi đã ResolveFailure một lỗi; xoá cảnh báo xong mà trả ProceedWithCommit
            # thì Revit xử lý lại, cảnh báo sinh lại → lặp (666 lần, 2026-10-21) rồi hủy transaction.
            self.calls += 1
            resolved_any = False
            for f in list(fa.GetFailureMessages()):
                sev = str(f.GetSeverity())
                text = f.GetDescriptionText()
                if f.GetSeverity() == FailureSeverity.Warning:
                    self.warnings[text[:100]] += 1
                    fa.DeleteWarning(f)
                    continue
                self.all[(sev, text[:120])] += 1
                try:
                    for eid in f.GetFailingElementIds():
                        self.ids[text[:120]].add(eid.Value)
                except Exception:
                    pass
                if f.HasResolutions():
                    self.resolved[text[:80]] += 1
                    fa.ResolveFailure(f)
                    resolved_any = True
            if resolved_any and self.calls < 20:
                return FailureProcessingResult.ProceedWithCommit
            return FailureProcessingResult.Continue
    clr.AddReference("RevitServices")
    from RevitServices.Persistence import DocumentManager
    from RevitServices.Transactions import TransactionManager

    doc = DocumentManager.Instance.CurrentDBDocument

TRANSACTION_NAME = u"ARV - Tạo ống thoát nước từ CAD"
COMMENT = u"ARV-CTN"
TOL = 3.0            # snap nút (mm)
GAP = 50.0           # nối khe hở cùng layer (mm)
DROP = 10.0          # đầu ống lớp trên trùng ống lớp dưới (mm)
NEAR_CIRCLE = 300.0  # đầu cụt gần tâm vòng tròn ống đứng (mm)
MIN_LEN_MM = 20.0    # ống còn lại sau khi đặt phụ kiện
BOP_LEADER = 1500.0  # chữ "BOP+…" cách đầu đuôi leader tối đa (mm)
BOP_TIP = 400.0      # mũi tên leader cách ống tối đa khi không kéo dài được (mm)
BOP_RAY = 1500.0     # kéo dài mũi tên leader theo hướng leader tối đa (mm) để gặp ống
CORE_TIMEOUT_S = 180
SIZES = [60, 75, 90, 110, 125, 140, 160, 200, 250, 315]     # OD uPVC (mm)
FAMILIES = {"bend": u"M_Bend - PVC - Sch 40 - DWV", "tee": u"M_Tee Sanitary - PVC - Sch 40 - DWV",
            "teeR": u"M_Tee Reducing Sanitary - PVC - Sch 40 - DWV", "red": u"M_Reducer - PVC - Sch 40 - DWV",
            "wye": u"M_Wye 45 Deg - PVC - Sch 40 - DWV", "wyeR": u"M_Wye 45 Deg Reducing - PVC - Sch 40 - DWV"}


def default_slope(dn):
    return 0.02 if dn <= 90 else 0.01


def wall_thk(d):
    return 2.2 if d <= 90 else (3.2 if d <= 160 else 4.9)


# =====================================================================================
# PHẦN XỬ LÝ MẠNG ỐNG – chỉ dùng tuple (x, y) theo mm, toạ độ DWG (chạy thử được ngoài Dynamo)
# =====================================================================================
def key(p):
    return (int(round(p[0] / TOL)), int(round(p[1] / TOL)))


def proj(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2
    tt = min(1.0, max(0.0, t))
    q = (a[0] + tt * dx, a[1] + tt * dy)
    return t, math.hypot(p[0] - q[0], p[1] - q[1]), q


def dist(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def unit(a, b):
    L = dist(a, b)
    return ((b[0] - a[0]) / L, (b[1] - a[1]) / L)


def build_network(ents, layer_sys, layer_group, pair, arrow_block, merge=False):
    """ents: dict lines/circles/inserts/dims/texts (toạ độ DWG, mm). Trả về dict mạng ống (như JSON thử nghiệm).
    merge=True: lớp có hậu tố (T5) cùng mặt bằng với lớp thường → nhánh T5 nối ngang vào ống thường (một mạng),
    không tạo ống rơi."""
    def canon(lay):
        return pair.get(lay, lay) if merge else lay
    log = collections.Counter()
    # ---- 1. line theo layer
    raw = collections.defaultdict(list)
    for lay, a, b in ents["lines"]:
        if lay in layer_sys and dist(a, b) > 1:
            raw[lay].append([a, b])
    # ---- 2. nối khe hở cùng layer
    for lay, S in raw.items():
        ends = collections.Counter(key(p) for s in S for p in s)
        for si, s in enumerate(S):
            for k in (0, 1):
                p = s[k]
                if ends[key(p)] > 1:
                    continue
                if any(proj(p, a, b)[1] < TOL for j, (a, b) in enumerate(S) if j != si):
                    continue
                best = None
                for j, (a, b) in enumerate(S):
                    if j == si:
                        continue
                    t, d, q = proj(p, a, b)
                    for cand in (a, b):
                        if dist(p, cand) < GAP and (best is None or dist(p, cand) - 5 < best[0]):
                            best = (dist(p, cand) - 5, cand)
                    if d < GAP and (best is None or d < best[0]):
                        best = (d, q)
                if best:
                    s[k] = best[1]
                    log[u"nối khe hở ≤ 50 mm"] += 1
    # ---- 2b. gộp mặt bằng: đầu ống lớp T5 nằm trên ống lớp thường (≤ DROP) → kéo đúng vào ống đó
    if merge:
        for l5, lb in pair.items():
            for s in raw.get(l5, []):
                for k in (0, 1):
                    p = s[k]
                    best = None
                    for a, b in raw.get(lb, []):
                        t, d, q = proj(p, a, b)
                        if d <= DROP and (best is None or d < best[0]):
                            best = (d, a if dist(q, a) <= DROP else (b if dist(q, b) <= DROP else q))
                    if best:
                        s[k] = best[1]
                        log[u"nhánh T5 nối ngang vào ống thường"] += 1
    # ---- 3. tách tại nút T (kể cả điểm rơi từ lớp có hậu tố)
    E = []
    for lay, S in raw.items():
        pts = [p for s in S for p in s]
        extra = [p for l5, lb in pair.items() if lb == lay for s in raw.get(l5, []) for p in s]
        seen = set()
        for a, b in S:
            L = dist(a, b)
            ts = {0.0, 1.0}
            for p in pts + extra:
                t, d, _ = proj(p, a, b)
                tol = TOL if p in pts else DROP
                if d < tol and TOL < t * L < L - TOL:
                    ts.add(round(t, 6))
            ts = sorted(ts)
            for t0, t1 in zip(ts, ts[1:]):
                p0 = (a[0] + t0 * (b[0] - a[0]), a[1] + t0 * (b[1] - a[1]))
                p1 = (a[0] + t1 * (b[0] - a[0]), a[1] + t1 * (b[1] - a[1]))
                k = tuple(sorted((key(p0), key(p1))))
                if dist(p0, p1) > TOL and k not in seen:
                    seen.add(k)
                    E.append({"layer": lay, "a": p0, "b": p1})
    nid, NP, NL = {}, [], {}

    def node(lay, p):
        k = (canon(lay), key(p))
        if k not in nid:
            nid[k] = len(NP)
            NP.append([p[0], p[1], 0.0])
        return nid[k]
    for e in E:
        e["u"] = node(e["layer"], e["a"])
        e["v"] = node(e["layer"], e["b"])
        e["len"] = dist(e["a"], e["b"])
        NL[e["u"]] = NL[e["v"]] = canon(e["layer"])
    adj = collections.defaultdict(list)
    for i, e in enumerate(E):
        adj[e["u"]].append(i)
        adj[e["v"]].append(i)

    def other(i, n):
        return E[i]["v"] if E[i]["u"] == n else E[i]["u"]
    comp_of, comps = {}, []
    for s in range(len(E)):
        if s in comp_of:
            continue
        c = len(comps)
        st, mem = [s], []
        comp_of[s] = c
        while st:
            i = st.pop()
            mem.append(i)
            for n in (E[i]["u"], E[i]["v"]):
                for j in adj[n]:
                    if j not in comp_of:
                        comp_of[j] = c
                        st.append(j)
        comps.append(mem)
    # ---- 4. mũi tên, vòng tròn, điểm rơi
    arrow = {}
    n_arrows = 0
    for lay, name, (x, y), rot in ents["inserts"]:
        if name != arrow_block:
            continue
        n_arrows += 1
        best = None
        for i, e in enumerate(E):
            t, d, _ = proj((x, y), e["a"], e["b"])
            if d < 200:
                ux, uy = unit(e["a"], e["b"])
                c = ux * math.cos(rot) + uy * math.sin(rot)
                if abs(c) > 0.9 and (best is None or d < best[0]):
                    best = (d, i, 1 if c > 0 else -1)
        if best:
            arrow[best[1]] = best[2]
    circles = [(lay, c) for lay, c, r in ents["circles"] if lay in layer_sys]
    drops = {}
    for n5, l5 in NL.items():
        if l5 not in pair:
            continue
        for nb, lb in NL.items():
            if lb == pair[l5] and dist(NP[n5], NP[nb]) <= DROP:
                drops[n5] = nb
    near_circle = set(n for n, l in NL.items() if len(adj[n]) == 1 and
                      any(l == canon(cl) and dist(NP[n], cp) < NEAR_CIRCLE for cl, cp in circles))
    drop_targets = set(drops.values())

    # ---- 5. hướng chảy
    def orient(sinks):
        dd = dict((s, 0.0) for s in sinks)
        h = [(0.0, s) for s in sinks]
        down = {}
        while h:
            d, n = heapq.heappop(h)
            if d > dd.get(n, 1e18):
                continue
            for i in adj[n]:
                m = other(i, n)
                nd = d + E[i]["len"]
                if nd < dd.get(m, 1e18):
                    dd[m] = nd
                    down[i] = n
                    heapq.heappush(h, (nd, m))
        return down

    def score(down, mem):
        g = b = 0
        for i in mem:
            if i in arrow:
                if down.get(i) == (E[i]["v"] if arrow[i] > 0 else E[i]["u"]):
                    g += 1
                else:
                    b += 1
        return g, b
    flow_to, report, sinks_all, bad_arrows = {}, [], set(), []
    for c, mem in enumerate(comps):
        nodes = set(n for i in mem for n in (E[i]["u"], E[i]["v"]))
        leaves = [n for n in nodes if len(adj[n]) == 1]
        arrow_in = set(n for n in leaves if adj[n][0] in arrow and
                       (E[adj[n][0]]["v"] if arrow[adj[n][0]] > 0 else E[adj[n][0]]["u"]) == n)
        cands = [n for n in leaves if (n in drops or n in near_circle or n in arrow_in) and n not in drop_targets]
        if 0 < len(cands) <= 12:
            subsets = [s for k in range(1, len(cands) + 1) for s in itertools.combinations(cands, k)]
        else:
            subsets = [tuple(cands)] if cands else []
        best = None
        for s in subsets:
            down = orient(s)
            g, b = score(down, mem)
            val = g - b - 0.01 * len(s)
            if best is None or val > best[0]:
                best = (val, s, down, g, b)
        if best is None or best[4] > 0:
            for s in leaves:
                if s in drop_targets:
                    continue
                down = orient((s,))
                g, b = score(down, mem)
                val = g - b - 0.5
                if best is None or val > best[0]:
                    best = (val, (s,), down, g, b)
        _, sk, down, g, b = best
        flow_to.update(down)
        sinks_all.update(sk)
        report.append({"comp": c, "layer": E[mem[0]]["layer"], "edges": len(mem), "sinks": list(sk),
                       "ok": g, "bad": b})
        for i in mem:
            if i in arrow and down.get(i) != (E[i]["v"] if arrow[i] > 0 else E[i]["u"]):
                bad_arrows.append((E[i]["layer"], ((E[i]["a"][0] + E[i]["b"][0]) / 2, (E[i]["a"][1] + E[i]["b"][1]) / 2)))
    # ---- 6. DN
    votes = collections.defaultdict(collections.Counter)
    slope_txt = {}
    dim_slope = {}

    def edges_at(p, lay=None, tol=5):
        return [i for i, e in enumerate(E) if (lay is None or e["layer"] == lay) and proj(p, e["a"], e["b"])[1] < tol]

    def path(e1, e2):
        if e1 == e2:
            return [e1]
        prev = {e1: None}
        q = collections.deque([e1])
        while q:
            i = q.popleft()
            for n in (E[i]["u"], E[i]["v"]):
                for j in adj[n]:
                    if j not in prev:
                        prev[j] = i
                        if j == e2:
                            out = [j]
                            while prev[out[-1]] is not None:
                                out.append(prev[out[-1]])
                            return out
                        q.append(j)
        return None
    for lay, style, p2, p3 in ents["dims"]:
        # "AV-Dim 1-75 (D160)" hoặc "0.T D110 (1-200)"
        m = re.search(r"(?<![A-Za-z])D(\d{2,3})(?!\d)", style or u"")
        if not m:
            continue
        if re.match(r"^\s*0\.C\b", style or u""):       # "0.C …" = dim ống cấp nước
            log[u"bỏ dim ống cấp nước (0.C)"] += 1
            continue
        D = int(m.group(1))
        best = None
        # điểm đo nằm trên ống (5 mm); không có thì nới tới 50 mm (dim vẽ không bắt điểm)
        for tol in (5, 50):
            for i in edges_at(p2, tol=tol):
                for j in edges_at(p3, E[i]["layer"], tol=tol):
                    pth = path(i, j)
                    if pth and (best is None or len(pth) < len(best)):
                        best = pth
            if best:
                break
        if not best:
            log[u"dim DN không khớp ống"] += 1
            continue
        ms = re.search(r"D\d+-(\d+(?:[.,]\d+)?)%", style or u"")      # độ dốc trong DIMPOST "D110-1%-<>M"
        for i in best:
            votes[i][D] += 1
            if ms:
                dim_slope.setdefault(i, float(ms.group(1).replace(",", ".")) / 100)
    for lay, p, text in ents["texts"]:
        m = re.match(r"\s*D(\d+)-(\d+(?:[.,]\d+)?)%", text)
        if not m or not E:
            continue
        d, i = min((proj(p, e["a"], e["b"])[1], i) for i, e in enumerate(E))
        if d < 300:
            votes[i][int(m.group(1))] += 3
            slope_txt[i] = float(m.group(2).replace(",", ".")) / 100
    for i, s in dim_slope.items():
        slope_txt.setdefault(i, s)
    log[u"độ dốc theo dim / chữ"] = len(slope_txt)
    dn = {}
    for i, v in votes.items():
        if len(v) > 1:
            log[u"DN xung đột (lấy số phiếu nhiều)"] += 1
        dn[i] = v.most_common(1)[0][0]
    log[u"DN có nhãn trực tiếp"] = len(dn)
    changed = True
    while changed:
        changed = False
        for i, e in enumerate(E):
            if i in dn:
                continue
            for n in (e["u"], e["v"]):
                if len(adj[n]) == 2:
                    j = [k for k in adj[n] if k != i][0]
                    if j in dn:
                        dn[i] = dn[j]
                        changed = True
                        log[u"DN lan dọc tuyến"] += 1
                        break
    changed = True
    while changed:
        changed = False
        for i, e in enumerate(E):
            if i in dn:
                continue
            n = flow_to.get(i)
            cand = [dn[k] for k in adj[n] if k != i and k in dn] if n is not None else []
            if cand:
                dn[i] = min(cand)
                changed = True
                log[u"DN theo ống hạ lưu"] += 1
    # DN mặc định / tối thiểu theo layer (IN[11]): "phân=110;*=75" – luật có tên layer là DN TỐI THIỂU
    # của layer đó (ống xí không nhỏ hơn D110), '*' chỉ dùng cho đoạn không xác định được DN.
    for i in range(len(E)):
        lay = E[i]["layer"]
        floor = first_match([r for r in dn_rules if r[0] != u"*"], lay)
        if i not in dn:
            dn[i] = int(float(floor or first_match(dn_rules, lay) or 75))
            log[u"DN không xác định → mặc định theo layer"] += 1
        elif floor and dn[i] < int(float(floor)):
            dn[i] = int(float(floor))
            slope_txt.pop(i, None)
            log[u"DN nâng lên tối thiểu theo layer"] += 1
    # DN không giảm về hạ lưu
    changed = True
    while changed:
        changed = False
        for i in range(len(E)):
            d = flow_to.get(i)
            if d is None:
                continue
            u = other(i, d)
            inc = [dn[j] for j in adj[u] if j != i and flow_to.get(j) == u]
            if inc and max(inc) > dn[i]:
                dn[i] = max(inc)
                slope_txt.pop(i, None)
                changed = True
                log[u"DN nâng cho không nhỏ hơn ống thượng lưu"] += 1
    slope = dict((i, slope_txt.get(i, default_slope(dn[i]))) for i in range(len(E)))
    # layer dựng phẳng (ống áp lực, VD ống đẩy bơm "Nước xả") – IN[12]
    for i in range(len(E)):
        if any(k.lower() in E[i]["layer"].lower() for k in flat_layers):
            slope[i] = 0.0
    # ---- 6b. cao độ đáy ống theo ghi chú "BOP+3.80M" có leader chỉ vào ống (thường là đầu tuyến)
    #      z neo = BOP + DN/2 (tâm ống), mm so với level của mặt bằng chứa link CAD.
    anchors = {}
    for lay, p, text in ents["texts"]:
        mb = re.match(r"\s*BOP\s*([+-]?\s*\d+(?:[.,]\d+)?)\s*M", text, re.I)
        if not mb:
            continue
        val = float(mb.group(1).replace(u" ", u"").replace(u",", u".")) * 1000
        best = None
        for llay, pts in ents.get("leaders", []):
            if len(pts) < 2:
                continue
            for end, tip, nxt in ((pts[-1], pts[0], pts[1]), (pts[0], pts[-1], pts[-2])):
                d = dist(end, p)
                if d < BOP_LEADER and (best is None or d < best[0]):
                    best = (d, tip, nxt)
        if best is None:
            log[u"BOP không có leader (bỏ qua)"] += 1
            continue
        tip, nxt = best[1], best[2]
        # Mũi tên thường dừng ở ký hiệu nút bịt cách đầu ống vài trăm mm → kéo dài theo hướng leader
        cand = None
        L = dist(nxt, tip)
        if L > 1e-6:
            ux, uy = (tip[0] - nxt[0]) / L, (tip[1] - nxt[1]) / L
            k = 0.0
            while k <= BOP_RAY and cand is None:
                q0 = (tip[0] + ux * k, tip[1] + uy * k)
                hits = [(proj(q0, e["a"], e["b"])[1], i) for i, e in enumerate(E)]
                hits = [h for h in hits if h[0] <= 30]
                if hits:
                    cand = (min(hits)[0], min(hits)[1], q0)
                k += 25.0
        if cand is None:
            near = min(((proj(tip, e["a"], e["b"])[1], i) for i, e in enumerate(E)), default=None)
            if near is not None and near[0] <= BOP_TIP:
                cand = (near[0], near[1], tip)
        if cand is None:
            log[u"BOP leader không tới ống (bỏ qua)"] += 1
            continue
        i = cand[1]
        e = E[i]
        down = flow_to.get(i, e["v"])
        up = other(i, down)
        q = proj(cand[2], e["a"], e["b"])[2]
        zq = val + dn[i] / 2.0
        if dist(q, NP[up]) <= 300:            # mũi tên ở đầu đoạn (đầu tuyến / nút) → neo tại nút đó
            n, z = up, zq
        elif dist(q, NP[down]) <= 300:
            n, z = down, zq
        else:                                 # giữa đoạn → quy về nút hạ lưu theo độ dốc
            n, z = down, zq - slope[i] * dist(q, NP[down])
        if n in anchors and abs(anchors[n] - z) > 5:
            log[u"BOP trùng nút, khác giá trị (lấy thấp hơn)"] += 1
            z = min(z, anchors[n])
        anchors[n] = z
        log[u"BOP gán vào ống"] += 1
    comp_abs = set()
    for c, mem in enumerate(comps):
        nodes = set(n for i in mem for n in (E[i]["u"], E[i]["v"]))
        an = dict((n, z) for n, z in anchors.items() if n in nodes)
        if not an:
            continue
        comp_abs.add(c)
        z = dict(an)
        # (A) xuôi dòng từ các điểm neo: nút hạ lưu thấp nhất trong các đường từ thượng lưu xuống
        changed = True
        while changed:
            changed = False
            for i in mem:
                d = flow_to.get(i)
                if d is None:
                    continue
                u = other(i, d)
                if u in z and d not in an:
                    nz = z[u] - E[i]["len"] * slope[i]
                    if nz < z.get(d, 1e18) - 1e-6:
                        z[d] = nz
                        changed = True
        # (B) nhánh không có BOP: tính ngược lên từ chỗ nhập vào
        changed = True
        while changed:
            changed = False
            for i in mem:
                d = flow_to.get(i)
                if d is None:
                    continue
                u = other(i, d)
                if d in z and u not in z:
                    z[u] = z[d] + E[i]["len"] * slope[i]
                    changed = True
        for i in mem:                         # kiểm tra ngược dốc tại điểm neo
            d = flow_to.get(i)
            if d is not None and d in an and other(i, d) in z and z[other(i, d)] < an[d] - 1:
                log[u"BOP làm ngược dốc (kiểm tra)"] += 1
        for n in nodes:
            NP[n][2] = z.get(n, 0.0)
        report[c]["abs"] = True
        report[c]["rise"] = max(z.values()) - min(z.values())
        report[c]["z_range"] = (min(z.values()), max(z.values()))
    log[u"cụm theo BOP"] = len(comp_abs)

    # ---- 7. cao độ tương đối (điểm cao nhất cụm = 0) – cụm không có BOP
    for c, mem in enumerate(comps):
        if c in comp_abs:
            continue
        sk = report[c]["sinks"]
        rise = dict((s, 0.0) for s in sk)
        h = [(0.0, s) for s in sk]
        while h:
            z, n = heapq.heappop(h)
            if z > rise.get(n, 1e18):
                continue
            for i in adj[n]:
                m = other(i, n)
                nz = z + E[i]["len"] * slope[i]
                if nz < rise.get(m, 1e18):
                    rise[m] = nz
                    heapq.heappush(h, (nz, m))
        top = max(rise.values())
        for n, z in rise.items():
            NP[n][2] = z - top
        report[c]["rise"] = top

    # ---- 8. gộp đoạn thẳng hàng, lập ống + ống đứng + phụ kiện
    def collinear(i, j, n):
        a = unit(NP[n], NP[other(i, n)])
        b = unit(NP[n], NP[other(j, n)])
        return a[0] * b[0] + a[1] * b[1] < -0.9995
    pipes, visited = [], set()
    special = set(drops) | drop_targets | sinks_all
    for i in range(len(E)):
        if i in visited:
            continue
        chain = [i]
        visited.add(i)
        for end in (E[i]["u"], E[i]["v"]):
            cur, n = i, end
            while len(adj[n]) == 2 and n not in special:
                j = [k for k in adj[n] if k != cur][0]
                if j in visited or dn[j] != dn[cur] or abs(slope[j] - slope[cur]) > 1e-9 or not collinear(cur, j, n) \
                        or E[j]["layer"] != E[cur]["layer"]:
                    break
                chain.append(j)
                visited.add(j)
                cur, n = j, other(j, n)
        ns = collections.Counter(n for k in chain for n in (E[k]["u"], E[k]["v"]))
        a, b = [n for n, c in ns.items() if c == 1]
        if NP[a][2] < NP[b][2]:
            a, b = b, a
        lay = E[chain[0]]["layer"]
        pipes.append({"id": len(pipes), "layer": lay, "system": layer_sys[lay], "group": layer_group[lay],
                      "dn": dn[chain[0]], "n1": a, "n2": b, "comp": comp_of[chain[0]],
                      "abs": comp_of[chain[0]] in comp_abs})
    pipe_at = collections.defaultdict(list)
    for p in pipes:
        pipe_at[p["n1"]].append(p["id"])
        pipe_at[p["n2"]].append(p["id"])
    risers = []

    def add_riser(**kw):
        kw["id"] = len(pipes) + len(risers)
        risers.append(kw)
    for n5, nb in drops.items():
        if n5 in sinks_all:
            p = pipes[pipe_at[n5][0]]
            add_riser(kind="drop", top=n5, bottom=nb, dn=p["dn"], system=p["system"], layer=p["layer"], group=p["group"])
            log[u"ống rơi xuống lớp dưới"] += 1
    for n in sinks_all:
        if n in drops:
            continue
        p = pipes[pipe_at[n][0]]
        add_riser(kind="down", node=n, dn=p["dn"], system=p["system"], layer=p["layer"], group=p["group"])
    for n in near_circle:
        if n in sinks_all or n not in pipe_at:
            continue
        p = pipes[pipe_at[n][0]]
        add_riser(kind="up", node=n, dn=p["dn"], system=p["system"], layer=p["layer"], group=p["group"])
    riser_at = collections.defaultdict(list)
    for r in risers:
        if r["kind"] == "drop":
            riser_at[r["top"]].append(r["id"])
            riser_at[r["bottom"]].append(r["id"])
        else:
            riser_at[r["node"]].append(r["id"])
    fittings = []
    for n in set(pipe_at) | set(riser_at):
        ps, rs = pipe_at.get(n, []), riser_at.get(n, [])
        if len(ps) + len(rs) < 2:
            continue

        def dir_from(k):
            p = pipes[k]
            return unit(NP[n], NP[p["n2"] if p["n1"] == n else p["n1"]])
        f = {"node": n}
        if rs:
            if len(ps) == 1:
                f.update(kind="elbow", pipes=ps + rs)
            elif len(ps) == 2:
                f.update(kind="tee", main=ps, branch=rs[0])
            else:
                f.update(kind=u"nút {} ống".format(len(ps) + len(rs)), pipes=ps + rs)
        elif len(ps) == 2:
            d0, d1 = dir_from(ps[0]), dir_from(ps[1])
            f.update(kind="transition" if d0[0] * d1[0] + d0[1] * d1[1] < -0.9995 else "elbow", pipes=ps)
        elif len(ps) == 3:
            dirs = [dir_from(k) for k in ps]
            pr = None
            for x, y in ((0, 1), (0, 2), (1, 2)):
                if dirs[x][0] * dirs[y][0] + dirs[x][1] * dirs[y][1] < -0.999:
                    pr = (x, y)
            if pr is None:
                f.update(kind=u"nút 3 ống không thẳng hàng", pipes=ps)
            else:
                br = 3 - pr[0] - pr[1]
                cb = [dirs[br][0] * dirs[k][0] + dirs[br][1] * dirs[k][1] for k in pr]
                if abs(cb[0]) < 0.05:
                    f.update(kind="tee", main=[ps[pr[0]], ps[pr[1]]], branch=ps[br])
                else:
                    l45 = pr[0] if cb[0] > 0 else pr[1]
                    l135 = pr[1] if l45 == pr[0] else pr[0]
                    f.update(kind="wye", leg45=ps[l45], leg135=ps[l135], branch=ps[br])
        else:
            f.update(kind=u"nút {} ống".format(len(ps)), pipes=ps)
        fittings.append(f)
    return {"nodes": NP, "pipes": pipes, "risers": risers, "fittings": fittings, "components": report,
            "bad_arrows": bad_arrows, "n_arrows": n_arrows, "log": log}


# =====================================================================================
# PHẦN REVIT
# =====================================================================================
def parse_map(s):
    out = []
    for part in (s or u"").split(u";"):
        if u"=" in part:
            k, v = part.split(u"=", 1)
            out.append((k.strip(), v.strip()))
    return out


def parse_points(s):
    pts = []
    for part in (s or u"").split(u";"):
        try:
            x, y = part.split(u",")
            pts.append((float(x), float(y)))
        except ValueError:
            continue
    return pts


cad_filter = ((IN[0] if DYNAMO else u"") or u"").strip()
layer_list = [s.strip() for s in ((IN[1] if DYNAMO else u"") or u"").split(u";") if s.strip()]
sys_map = parse_map(IN[2] if DYNAMO else u"phân=AV_P_Nước Thải Xí;rửa=AV_P_Nước Thải Rửa;bếp=AV_P_Nước Thải Bếp;"
                                          u"mưa=AV_P_Nước Mưa;Hơi=AV_P_Thông hơi Chung;*=AV_P_Nước Xả khác")
group_map = parse_map(IN[3] if DYNAMO else u"T5=TẦNG 5>TẦNG chuye;*=TẦNG chuye>TẦNG 4")
h_top_mm = float(IN[4]) if DYNAMO and IN[4] is not None else 400.0
arrow_block = ((IN[5] if DYNAMO else u"") or u"AV-P-Hướng nước chảy").strip()
family_dir = ((IN[6] if DYNAMO else u"") or u"").strip()
pipe_type_name = ((IN[7] if DYNAMO else u"") or u"uPVC thoát nước").strip()
dry_run = True if not DYNAMO or IN[8] is None else bool(IN[8])
only_points = parse_points(IN[9] if DYNAMO and len(IN) > 9 else u"")
color_map = parse_map(IN[10] if DYNAMO and len(IN) > 10 else u"")
dn_rules = parse_map(IN[11] if DYNAMO and len(IN) > 11 and IN[11] else u"phân=110;*=75")
flat_layers = [s.strip() for s in ((IN[12] if DYNAMO and len(IN) > 12 and IN[12] is not None else u"Nước xả") or u"").split(u";")
               if s.strip()]


def mm2ft(v):
    return v / 304.8


def ft2mm(v):
    return v * 304.8


def get_name(e):
    try:
        return e.Name
    except Exception:
        p = e.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
        return p.AsString() if p else u""


def is_central_file(document):
    if not document.IsWorkshared:
        return False
    try:
        central = ModelPathUtils.ConvertModelPathToUserVisiblePath(document.GetWorksharingCentralModelPath())
    except Exception:
        return False
    return os.path.normcase(central or "") == os.path.normcase(document.PathName or "")


def pick_cad():
    instances = list(FilteredElementCollector(doc).OfClass(ImportInstance).ToElements())
    if cad_filter:
        instances = [i for i in instances if cad_filter.lower() in get_name(doc.GetElement(i.GetTypeId())).lower()]
    if len(instances) != 1:
        names = [get_name(doc.GetElement(i.GetTypeId())) for i in
                 FilteredElementCollector(doc).OfClass(ImportInstance).ToElements()]
        raise Exception(u"Tìm thấy {} bản CAD khớp '{}'. Nhập tên bản CAD vào ô IN[0]. Các bản CAD: {}".format(
            len(instances), cad_filter, u", ".join(names) or u"không có"))
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


def find_accoreconsole():
    found = glob.glob(r"C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe")
    return sorted(found)[-1] if found else None


def core_env(core):
    """Môi trường sạch cho AutoCAD Core Console (xem README: Path của Revit làm Core Console nạp nhầm DLL)."""
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


# Xuất LINE / CIRCLE / INSERT / DIMENSION / TEXT / MTEXT ở model space (cấp ngoài cùng) ra file text.
DUMP_LISP = u"""(setq f (open "{out}" "w" "utf8"))
(defun _p (p) (if p (strcat (rtos (car p) 2 3) "," (rtos (cadr p) 2 3)) "x"))
(defun _s (v) (if v v ""))
(defun _pts (d / s) (setq s "") (foreach g d (if (= (car g) 10) (setq s (strcat s (if (= s "") "" ";") (_p (cdr g)))))) s)
(defun _post (n / r) (setq r (tblsearch "DIMSTYLE" n)) (if (and r (cdr (assoc 3 r))) (cdr (assoc 3 r)) ""))
(if (setq ss (ssget "_X" '((0 . "LINE,CIRCLE,INSERT,DIMENSION,TEXT,MTEXT,LEADER") (410 . "Model"))))
  (progn (setq i 0)
    (repeat (sslength ss)
      (setq d (entget (ssname ss i)) i (1+ i) ty (cdr (assoc 0 d)) la (cdr (assoc 8 d)))
      (cond
        ((= ty "LINE") (write-line (strcat "L|" la "|" (_p (cdr (assoc 10 d))) "|" (_p (cdr (assoc 11 d)))) f))
        ((= ty "CIRCLE") (write-line (strcat "C|" la "|" (_p (cdr (assoc 10 d))) "|" (rtos (cdr (assoc 40 d)) 2 3)) f))
        ((= ty "INSERT") (write-line (strcat "I|" la "|" (_p (cdr (assoc 10 d))) "|" (rtos (if (assoc 50 d) (cdr (assoc 50 d)) 0.0) 2 6) "|" (_s (cdr (assoc 2 d)))) f))
        ((= ty "DIMENSION") (write-line (strcat "D|" la "|" (_p (cdr (assoc 13 d))) "|" (_p (cdr (assoc 14 d))) "|" (_s (cdr (assoc 3 d))) "|" (_post (_s (cdr (assoc 3 d))))) f))
        ((= ty "LEADER") (write-line (strcat "R|" la "|" (_pts d)) f))
        (T (write-line (strcat "T|" la "|" (_p (cdr (assoc 10 d))) "|" (_s (cdr (assoc 1 d)))) f))))))
(close f)
"""


def clean_mtext(s):
    s = re.sub(r"\\[A-Za-z][^;\\{}]*;", "", s)
    s = re.sub(r"\\[Pp~]", " ", s)
    return s.replace("{", "").replace("}", "").strip()


def read_dwg(dwg_path, core):
    """Thực thể DWG (toạ độ DWG, mm). Chạy trên bản sao trong thư mục tạm – không mở file gốc."""
    work = tempfile.mkdtemp(prefix="ARV_CTN_")
    try:
        copy = os.path.join(work, "copy.dwg")
        shutil.copy2(dwg_path, copy)
        out = os.path.join(work, "ents.txt")
        scr = os.path.join(work, "dump.scr")
        with io.open(scr, "w", encoding="utf-8") as f:
            f.write(DUMP_LISP.replace("{out}", out.replace("\\", "/")))
        subprocess.run([core, "/i", copy, "/s", scr, "/l", "en-US"], stdin=subprocess.DEVNULL,
                       env=core_env(core), cwd=os.path.dirname(core),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=CORE_TIMEOUT_S, creationflags=0x08000000)
        if not os.path.isfile(out):
            raise Exception(u"Core Console không xuất được dữ liệu DWG")
        with io.open(out, "r", encoding="utf-8-sig", errors="replace") as f:
            return parse_dump(f.read())
    finally:
        shutil.rmtree(work, ignore_errors=True)


def parse_dump(text):
    ents = {"lines": [], "circles": [], "inserts": [], "dims": [], "texts": [], "leaders": []}

    def pt(s):
        x, y = s.split(",")
        return (float(x), float(y))
    for line in text.splitlines():
        parts = line.split("|")
        try:
            if parts[0] == "L":
                ents["lines"].append((parts[1], pt(parts[2]), pt(parts[3])))
            elif parts[0] == "C":
                ents["circles"].append((parts[1], pt(parts[2]), float(parts[3])))
            elif parts[0] == "I":
                ents["inserts"].append((parts[1], u"|".join(parts[4:]), pt(parts[2]), float(parts[3])))
            elif parts[0] == "D":
                # D|layer|p2|p3|dimstyle|DIMPOST (VD "D110-1%-<>M") – tiền / hậu tố mang DN và độ dốc
                ents["dims"].append((parts[1], parts[4] + (u" " + parts[5] if len(parts) > 5 else u""),
                                     pt(parts[2]), pt(parts[3])))
            elif parts[0] == "R":
                ents["leaders"].append((parts[1], [pt(s) for s in parts[2].split(";") if s]))
            elif parts[0] == "T":
                ents["texts"].append((parts[1], pt(parts[2]), clean_mtext(u"|".join(parts[3:]))))
        except (ValueError, IndexError):
            continue
    return ents


def first_match(rules, lay):
    for k, v in rules:
        if k == u"*" or k.lower() in lay.lower():
            return v
    return None


def layer_maps(layers):
    """layer → system, nhóm cao độ; cặp layer có hậu tố → layer thường cùng loại."""
    suffixes = [k for k, v in group_map if k != u"*"]
    lsys, lgrp, pair = {}, {}, {}
    for lay in layers:
        lsys[lay] = first_match(sys_map, lay) or u"Sanitary"
        grp = u"*"
        for sfx in suffixes:
            if lay.endswith(u" " + sfx):
                grp = sfx
                base = lay[:-len(sfx) - 1]
                if base in layers:
                    pair[lay] = base
        lgrp[lay] = grp
    return lsys, lgrp, pair


def parse_level(spec, lv, cad_level):
    """'TẦNG 5', 'Test+3000' hoặc 'CAD' / 'CAD+3000' (level của mặt bằng chứa link CAD) → (Level, cao độ ft)."""
    m = re.match(u"^(.*?)\\s*([+-]\\s*\\d+(?:\\.\\d+)?)?$", spec.strip())
    name, off = m.group(1).strip(), m.group(2)
    level = cad_level if name.upper() == u"CAD" else lv.get(name)
    if level is None:
        return None
    return level, level.Elevation + mm2ft(float(off.replace(u" ", u"")) if off else 0.0)


def cad_plan_level(cad):
    """Level của mặt bằng chứa link CAD (link theo view); link 3D → level của view đang mở."""
    for vid in (cad.OwnerViewId, doc.ActiveView.Id):
        v = doc.GetElement(vid) if vid is not None else None
        if v is not None and getattr(v, "GenLevel", None) is not None:
            return v.GenLevel, v.Name
    return None, None


def filter_network(net, points):
    """Mỗi điểm chọn cụm của ống GẦN NHẤT (≤ 300 mm). Ống rơi mất đầu dưới → ống đứng xuống."""
    NP = net["nodes"]
    comps = set()
    for q in points:
        best = min(((proj(q, NP[p["n1"]], NP[p["n2"]])[1], p["comp"]) for p in net["pipes"]), default=None)
        if best is not None and best[0] <= 300:
            comps.add(best[1])
    pipes = [p for p in net["pipes"] if p["comp"] in comps]
    nodes = set(n for p in pipes for n in (p["n1"], p["n2"]))
    risers = []
    for r in net["risers"]:
        if r["kind"] == "drop":
            if r["top"] in nodes and r["bottom"] in nodes:
                risers.append(r)
            elif r["top"] in nodes:
                risers.append(dict(r, kind="down", node=r["top"]))
        elif r["node"] in nodes:
            risers.append(r)
    keep = set(p["id"] for p in pipes) | set(r["id"] for r in risers)
    fittings = []
    for f in net["fittings"]:
        ids = [f.get("leg45"), f.get("leg135"), f.get("branch")] + list(f.get("main", [])) + list(f.get("pipes", []))
        ids = [i for i in ids if i is not None]
        if ids and all(i in keep for i in ids):
            fittings.append(f)
    out = dict(net)
    out.update(pipes=pipes, risers=risers, fittings=fittings,
               components=[c for c in net["components"] if c["comp"] in comps])
    return out


def write_log(rows, source):
    folder = os.path.join(os.path.expanduser("~"), "Documents", "ARV_Logs")
    if not os.path.isdir(folder):
        os.makedirs(folder)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(folder, "TaoOngThoatNuocTuCAD_{}_{}.csv".format("DRYRUN" if dry_run else "THUCHIEN", stamp))
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write(u"# Dự án: {}\n# Bản CAD: {}\n# Ngày xuất: {}\n# Chế độ: {}\n# Đơn vị: mm, toạ độ theo DWG\n".format(
            doc.Title, source, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            u"Chạy thử (dry-run)" if dry_run else u"Thực hiện"))
        w = csv.writer(f)
        w.writerow([u"Loại", u"Toạ độ DWG (mm)", u"DN", u"Kết quả / lý do", u"Layer"])
        w.writerows(rows)
    return path


class Builder(object):
    """Dựng ống + phụ kiện trong Transaction đang mở."""

    def __init__(self, net, tf, levels, pipe_type, systems, fits, cad_z):
        self.net, self.tf, self.levels, self.cad_z = net, tf, levels, cad_z
        self.pt, self.systems, self.fits = pipe_type, systems, fits
        self.by_id = dict((p["id"], p) for p in net["pipes"])
        self.by_id.update((r["id"], r) for r in net["risers"])
        self.made, self.dir0, self.xyz, self.layer_of = {}, {}, {}, {}
        self.fit_made = []      # (FamilyInstance, layer)
        self.min_len = mm2ft(MIN_LEN_MM)

    def node_xyz(self, n, grp, absz=False):
        """absz: cụm có BOP → z là cao độ tâm ống so với level mặt bằng CAD; không thì so với điểm cao nhất cụm."""
        if n not in self.xyz:
            p = self.net["nodes"][n]
            q = self.tf.OfPoint(XYZ(mm2ft(p[0]), mm2ft(p[1]), 0))
            base = self.cad_z if absz else self.levels[grp]["up_z"] - mm2ft(h_top_mm)
            self.xyz[n] = XYZ(q.X, q.Y, base + mm2ft(p[2]))
        return self.xyz[n]

    def new_pipe(self, pid, a, b, rec, grp):
        p = Pipe.Create(doc, self.systems[rec["system"]].Id, self.pt.Id, self.levels[grp]["host"].Id, a, b)
        p.get_Parameter(BuiltInParameter.RBS_PIPE_DIAMETER_PARAM).Set(mm2ft(rec["dn"]))
        short = rec["layer"].replace(u"AV-P-DR-", u"").replace(u"AV-P-VE-", u"")
        p.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).Set(u"{} | {}".format(COMMENT, short))
        self.made[pid] = p
        self.layer_of[pid] = rec["layer"]
        self.dir0[pid] = b.Subtract(a).Normalize()
        return p

    def pipes(self):
        for rec in self.net["pipes"]:
            a = self.node_xyz(rec["n1"], rec["group"], rec.get("abs", False))
            b = self.node_xyz(rec["n2"], rec["group"], rec.get("abs", False))
            self.new_pipe(rec["id"], a, b, rec, rec["group"])
        for r in self.net["risers"]:
            if r["kind"] == "drop":
                top = self.xyz[r["top"]]
                bot = XYZ(top.X, top.Y, self.xyz[r["bottom"]].Z)
                grp = u"*"
            else:
                q = self.xyz[r["node"]]
                grp = r["group"]
                if r["kind"] == "down":
                    top, bot = q, XYZ(q.X, q.Y, self.levels[grp]["host_z"])
                else:
                    bot, top = q, XYZ(q.X, q.Y, self.levels[grp]["up_z"])
            if top.Z - bot.Z > self.min_len:
                self.new_pipe(r["id"], top, bot, r, grp)
        doc.Regenerate()

    def con(self, pid, q):
        cs = list(self.made[pid].ConnectorManager.Connectors)
        return min(cs, key=lambda c: c.Origin.DistanceTo(q))

    def far(self, pid, q):
        cs = list(self.made[pid].ConnectorManager.Connectors)
        return max(cs, key=lambda c: c.Origin.DistanceTo(q)).Origin

    def pipes_ok(self, ids):
        for i in ids:
            p = self.made[i]
            if not p.IsValidObject:
                return False
            c = p.Location.Curve
            if c.Length < self.min_len:
                return False
            if c.GetEndPoint(1).Subtract(c.GetEndPoint(0)).Normalize().DotProduct(self.dir0[i]) < 0.99:
                return False
            # Phụ kiện đã nối ở đầu kia của ống phải còn thẳng hàng – nếu ống bị cắt lại làm xoay đi,
            # Revit báo "… can no longer keep the connectivity" lúc commit và hủy cả transaction (2026-10-21)
            for pc in p.ConnectorManager.Connectors:
                for r in pc.AllRefs:
                    if r.Owner.Id == p.Id or not isinstance(r.Owner, FamilyInstance):
                        continue
                    if pc.Origin.DistanceTo(r.Origin) > mm2ft(0.5) or \
                            pc.CoordinateSystem.BasisZ.DotProduct(r.CoordinateSystem.BasisZ) > -0.9995:
                        return False
        return True

    def place3(self, pair, N, legA, legB, br, level):
        """Đặt phụ kiện 3 cổng: legA → +X (C2), legB → −X (C1), nhánh → −Y (C3) của family.
        pair = (symbol cùng cỡ, symbol thu) – family có Nominal Radius 1/2/3 thì một symbol dùng cho cả hai."""
        uA = self.far(legA, N).Subtract(N)
        uB = self.far(legB, N).Subtract(N)
        ub = self.far(br, N).Subtract(N)
        if min(uA.GetLength(), uB.GetLength(), ub.GetLength()) < 1e-6:
            raise Exception(u"ống dài 0")
        uA, uB, ub = uA.Normalize(), uB.Normalize(), ub.Normalize()
        X = uA.Subtract(uB)
        if X.GetLength() < 1e-6:
            raise Exception(u"ống chính suy biến")
        X = X.Normalize()
        Yp = ub.Subtract(X.Multiply(ub.DotProduct(X)))
        if Yp.GetLength() < 0.05:
            raise Exception(u"nhánh thẳng hàng ống chính")
        Y = Yp.Normalize().Negate()
        Z = X.CrossProduct(Y)
        d1, d2, d3 = self.made[legB].Diameter, self.made[legA].Diameter, self.made[br].Diameter
        red = abs(d1 - d2) > 1e-6 or abs(d1 - d3) > 1e-6
        fi = doc.Create.NewFamilyInstance(N, pair[1] if red else pair[0], level, StructuralType.NonStructural)
        if fi.LookupParameter("Nominal Radius 1") is not None:
            fi.LookupParameter("Nominal Radius 1").Set(d1 / 2)
            fi.LookupParameter("Nominal Radius 2").Set(d2 / 2)
            fi.LookupParameter("Nominal Radius 3").Set(d3 / 2)
        else:
            fi.LookupParameter("Nominal Radius").Set(d1 / 2)
        # Ma trận quay R có cột X, Y, Z → trục + góc
        tr = X.X + Y.Y + Z.Z
        ang = math.acos(max(-1.0, min(1.0, (tr - 1) / 2)))
        if ang > 1e-9:
            if math.pi - ang < 1e-6:
                k = 0 if (X.X >= Y.Y and X.X >= Z.Z) else (1 if Y.Y >= Z.Z else 2)
                ax = [XYZ(X.X + 1, X.Y, X.Z), XYZ(Y.X, Y.Y + 1, Y.Z), XYZ(Z.X, Z.Y, Z.Z + 1)][k]
            else:
                ax = XYZ(Y.Z - Z.Y, Z.X - X.Z, X.Y - Y.X)
            if ax.GetLength() < 1e-9:
                raise Exception(u"trục xoay suy biến")
            ElementTransformUtils.RotateElement(doc, fi.Id, Line.CreateUnbound(N, ax.Normalize()), ang)
        doc.Regenerate()
        lp = fi.Location.Point
        if lp.DistanceTo(N) > 1e-6:
            ElementTransformUtils.MoveElement(doc, fi.Id, N.Subtract(lp))
            doc.Regenerate()
        cs = list(fi.MEPModel.ConnectorManager.Connectors)
        plan = []
        for pid, u in ((legA, uA), (legB, uB), (br, ub)):
            c = max(cs, key=lambda k: k.CoordinateSystem.BasisZ.DotProduct(u))
            far = self.far(pid, N)
            if far.Subtract(c.Origin).DotProduct(u) < self.min_len:
                raise Exception(u"ống quá ngắn cho phụ kiện")
            plan.append((pid, c, far))
        for pid, c, far in plan:
            cur = self.made[pid].Location.Curve
            end1 = cur.GetEndPoint(1).IsAlmostEqualTo(far)
            self.made[pid].Location.Curve = Line.CreateBound(c.Origin, far) if end1 else Line.CreateBound(far, c.Origin)
            self.con(pid, c.Origin).ConnectTo(c)
        return fi

    def fitting(self, f):
        kind = f["kind"]
        if kind == "wye":
            ids = [f["leg45"], f["leg135"], f["branch"]]
        elif kind == "tee":
            ids = list(f["main"]) + [f["branch"]]
        else:
            ids = list(f.get("pipes", []))
        if any(i not in self.made for i in ids):
            return u"thiếu ống"
        n = f["node"]
        N = self.xyz.get(n) or self.con(ids[0], XYZ.Zero).Origin
        level = self.levels[self.by_id[ids[0]].get("group", u"*")]["host"]
        st = SubTransaction(doc)
        st.Start()
        why, fi = None, None
        try:
            if kind == "elbow":
                fi = doc.Create.NewElbowFitting(self.con(ids[0], N), self.con(ids[1], N))
            elif kind == "transition":
                fi = doc.Create.NewTransitionFitting(self.con(ids[0], N), self.con(ids[1], N))
            elif kind == "tee":
                a0, a1 = ids[0], ids[1]
                if self.made[a0].Diameter > self.made[a1].Diameter:
                    a0, a1 = a1, a0
                fi = self.place3(self.fits["tee"], N, a0, a1, ids[2], level)
            elif kind == "wye":
                fi = self.place3(self.fits["wye"], N, ids[0], ids[1], ids[2], level)
            else:
                why = kind
            if why is None:
                doc.Regenerate()
                if not self.pipes_ok(ids):
                    why = u"ống quá ngắn / đổi chiều / làm lệch phụ kiện cạnh"
        except Exception as ex:
            why = u"{}".format(ex)
        if why is None:
            st.Commit()
            if fi is not None:
                self.fit_made.append((fi, self.layer_of[ids[0]]))
        else:
            st.RollBack()
        return why


def load_family(name):
    fams = dict((get_name(f), f) for f in FilteredElementCollector(doc).OfClass(Family).ToElements())
    if name not in fams:
        path = os.path.join(family_dir, name + u".rfa")
        if not os.path.isfile(path):
            raise Exception(u"Thiếu family '{}' (không có trong mô hình, không thấy file {}).".format(name, path))
        doc.LoadFamily(path)
        fams = dict((get_name(f), f) for f in FilteredElementCollector(doc).OfClass(Family).ToElements())
    s = doc.GetElement(list(fams[name].GetFamilySymbolIds())[0])
    if not s.IsActive:
        s.Activate()
    return s


def junction_symbols(pt):
    """Y / tê từ rule Junctions của pipe type (nhận theo tên family: WYE / Y → Y, còn lại → tê)."""
    rpm = pt.RoutingPreferenceManager
    wye = tee = None
    for i in range(rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Junctions)):
        s = doc.GetElement(rpm.GetRule(RoutingPreferenceRuleGroupType.Junctions, i).MEPPartId)
        if not isinstance(s, FamilySymbol):
            continue
        fam = s.FamilyName.upper()
        if (u"WYE" in fam or re.search(u"(^|[ _-])Y([ _-]|$)", fam)) and wye is None:
            wye = s
        elif tee is None:
            tee = s
    for s in (wye, tee):
        if s is not None and not s.IsActive:
            s.Activate()
    return wye, tee


def ensure_types():
    """Pipe type IN[7] (có sẵn thì dùng) + family Y / tê. Trả về (pipe_type, fits, danh sách việc đã làm)."""
    done = []
    pt = [p for p in FilteredElementCollector(doc).OfClass(PipeType).ToElements() if get_name(p) == pipe_type_name]
    if pt:
        pt = pt[0]
        wye, tee = junction_symbols(pt)
        fits = {}
        if wye is not None:
            fits["wye"] = (wye, wye)
            done.append(u"Y theo type: " + wye.FamilyName)
        if tee is not None:
            fits["tee"] = (tee, tee)
            done.append(u"tê theo type: " + tee.FamilyName)
        if "wye" not in fits:
            fits["wye"] = (load_family(FAMILIES["wye"]), load_family(FAMILIES["wyeR"]))
            done.append(u"Y theo thư viện " + FAMILIES["wye"])
        if "tee" not in fits:
            fits["tee"] = (load_family(FAMILIES["tee"]), load_family(FAMILIES["teeR"]))
            done.append(u"tê theo thư viện " + FAMILIES["tee"])
        return pt, fits, done
    syms = dict((k, load_family(name)) for k, name in FAMILIES.items())
    done.append(u"nạp family PVC DWV thư viện")
    mat = [m for m in FilteredElementCollector(doc).OfClass(Material).ToElements() if get_name(m) == u"uPVC"]
    mat = mat[0] if mat else doc.GetElement(Material.Create(doc, u"uPVC"))
    sch = [s for s in FilteredElementCollector(doc).OfClass(PipeScheduleType).ToElements() if get_name(s) == u"uPVC"]
    sch = sch[0] if sch else PipeScheduleType.Create(doc, u"uPVC")
    seg = [s for s in FilteredElementCollector(doc).OfClass(PipeSegment).ToElements()
           if s.MaterialId == mat.Id and s.ScheduleTypeId == sch.Id]
    if seg:
        seg = seg[0]
    else:
        sizes = List[MEPSize]()
        for d in SIZES:
            sizes.Add(MEPSize(mm2ft(d), mm2ft(d - 2 * wall_thk(d)), mm2ft(d), True, True))
        seg = PipeSegment.Create(doc, mat.Id, sch.Id, sizes)
        done.append(u"tạo segment uPVC (OD {})".format(u"/".join(str(d) for d in SIZES)))
    base = list(FilteredElementCollector(doc).OfClass(PipeType).ToElements())[0]
    pt = base.Duplicate(pipe_type_name)
    rpm = pt.RoutingPreferenceManager
    for g in (RoutingPreferenceRuleGroupType.Elbows, RoutingPreferenceRuleGroupType.Junctions,
              RoutingPreferenceRuleGroupType.Transitions, RoutingPreferenceRuleGroupType.Unions,
              RoutingPreferenceRuleGroupType.Crosses, RoutingPreferenceRuleGroupType.Caps):
        while rpm.GetNumberOfRules(g) > 0:
            rpm.RemoveRule(g, 0)
    rpm.AddRule(RoutingPreferenceRuleGroupType.Segments, RoutingPreferenceRule(seg.Id, u"uPVC"), 0)
    while rpm.GetNumberOfRules(RoutingPreferenceRuleGroupType.Segments) > 1:
        rpm.RemoveRule(RoutingPreferenceRuleGroupType.Segments, 1)
    rpm.AddRule(RoutingPreferenceRuleGroupType.Elbows, RoutingPreferenceRule(syms["bend"].Id, u"Co"))
    rpm.AddRule(RoutingPreferenceRuleGroupType.Junctions, RoutingPreferenceRule(syms["tee"].Id, u"Tê"))
    rpm.AddRule(RoutingPreferenceRuleGroupType.Transitions, RoutingPreferenceRule(syms["red"].Id, u"Côn"))
    done.append(u"tạo pipe type '{}'".format(pipe_type_name))
    return pt, {"wye": (syms["wye"], syms["wyeR"]), "tee": (syms["tee"], syms["teeR"])}, done


def apply_colors(builder):
    """Tô màu ống + phụ kiện trong view đang mở theo IN[10] (đè hiển thị theo phần tử, chỉ view này)."""
    if not color_map:
        return u"không tô màu"
    view = doc.ActiveView
    solid = [f for f in FilteredElementCollector(doc).OfClass(FillPatternElement).ToElements() if f.GetFillPattern().IsSolidFill]
    settings = {}
    for k, v in color_map:
        try:
            r, g, b = [int(x) for x in v.split(u",")]
        except ValueError:
            continue
        og = OverrideGraphicSettings()
        col = Color(r, g, b)
        og.SetProjectionLineColor(col)
        og.SetCutLineColor(col)
        if solid:
            og.SetSurfaceForegroundPatternId(solid[0].Id)
            og.SetSurfaceForegroundPatternColor(col)
        settings[k] = og
    n = 0
    items = [(p, builder.layer_of[i]) for i, p in builder.made.items()] + builder.fit_made
    for e, lay in items:
        if e is None or not e.IsValidObject:
            continue
        for k, og in settings.items():
            if k == u"*" or k.lower() in lay.lower():
                view.SetElementOverrides(e.Id, og)
                n += 1
                break
    return u"tô màu {} phần tử trong view '{}'".format(n, view.Name)


def fmt(p):
    return u"({:.0f}, {:.0f})".format(p[0], p[1])


def main():
    if is_central_file(doc):
        return [u"DỪNG: file đang mở là file CENTRAL. Hãy mở file local hoặc bản detached/copy."]
    cad = pick_cad()
    cad_name = get_name(doc.GetElement(cad.GetTypeId()))
    path = cad_file_path(cad)
    if path is None:
        return [u"DỪNG: bản CAD phải được LINK (không Import) và file DWG phải còn ở đường dẫn gốc."]
    core = find_accoreconsole()
    if core is None:
        return [u"DỪNG: không tìm thấy AutoCAD Core Console (C:\\Program Files\\Autodesk\\AutoCAD *\\accoreconsole.exe)."]
    ents = read_dwg(path, core)
    all_layers = sorted(set(l for l, a, b in ents["lines"]))
    layers = [l for l in layer_list if l in all_layers]
    if not layers:
        return [u"DỪNG: không có layer ống nào trong IN[1]. Các layer LINE trong DWG:"] + all_layers
    missing = [l for l in layer_list if l not in all_layers]

    lv = dict((l.Name, l) for l in FilteredElementCollector(doc).OfClass(Level).ToElements())
    cad_level, cad_view = cad_plan_level(cad)
    levels, level_notes = {}, []
    for k, v in group_map:
        up, _, host = v.partition(u">")
        u_, h_ = parse_level(up, lv, cad_level), parse_level(host, lv, cad_level)
        if u_ is None or h_ is None:
            # Level ghi ở IN[3] không có trong mô hình → vẽ trên mặt bằng chứa link CAD:
            # level dưới = level của mặt bằng đó, level trên = level kế trên (không có → +3000 mm)
            if cad_level is None:
                return [u"DỪNG: IN[3] có level không tồn tại ('{}') và không xác định được mặt bằng chứa link CAD. "
                        u"Các level: {}".format(v, u", ".join(sorted(lv)))]
            above = sorted((l for l in lv.values() if l.Elevation > cad_level.Elevation + 1e-6), key=lambda l: l.Elevation)
            h_ = (cad_level, cad_level.Elevation)
            u_ = (above[0], above[0].Elevation) if above else (cad_level, cad_level.Elevation + mm2ft(3000))
            level_notes.append(u"Nhóm '{}': không có level '{}' → vẽ trên mặt bằng chứa link CAD (view '{}', level {}), "
                               u"level trên = {}".format(k, v, cad_view, cad_level.Name,
                                                         above[0].Name if above else cad_level.Name + u" +3000"))
        levels[k] = {"up": u_[0], "up_z": u_[1], "host": h_[0], "host_z": h_[1]}
    if u"*" not in levels:
        return [u"DỪNG: IN[3] phải có nhóm '*' cho layer không hậu tố."]

    lsys, lgrp, pair = layer_maps(layers)
    systems = dict((get_name(s), s) for s in FilteredElementCollector(doc).OfClass(PipingSystemType).ToElements())
    bad_sys = sorted(set(v for v in lsys.values() if v not in systems))
    if bad_sys:
        return [u"DỪNG: không có piping system '{}'. Các system: {}".format(u", ".join(bad_sys), u", ".join(sorted(systems)))]
    # Các nhóm cùng level trên / dưới (VD mặt bằng chỉ 1 tầng) → nhánh T5 nối ngang vào ống thường
    merge = len(levels) > 1 and len(set((round(v["up_z"], 6), round(v["host_z"], 6)) for v in levels.values())) == 1
    net = build_network(ents, lsys, lgrp, pair, arrow_block, merge)
    if only_points:
        net = filter_network(net, only_points)
        if not net["pipes"]:
            return [u"DỪNG: không có tuyến ống nào cách điểm IN[9] ≤ 300 mm (toạ độ DWG)."]

    old = [p for p in FilteredElementCollector(doc).OfClass(Pipe).ToElements()
           if (p.get_Parameter(BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS).AsString() or u"").startswith(COMMENT)]

    kinds = collections.Counter(f["kind"] for f in net["fittings"])
    risers = collections.Counter(r["kind"] for r in net["risers"])
    groups_used = set(lgrp[c["layer"]] for c in net["components"])
    rises = dict((g, max([c["rise"] for c in net["components"] if lgrp[c["layer"]] == g and not c.get("abs")] or [0]))
                 for g in groups_used)
    abs_c = [c for c in net["components"] if c.get("abs")]
    good = sum(c["ok"] for c in net["components"])
    rows = [[u"Mũi tên ngược hướng tính", fmt(p), u"", u"Kiểm tra hướng chảy / điểm xả", lay] for lay, p in net["bad_arrows"]]

    mode = (u"CHẠY THỬ (không ghi vào mô hình)" if dry_run else
            u"KHÔNG GHI – đã có ống của lần chạy trước (xem dòng DỪNG GHI)" if old else u"ĐÃ THỰC HIỆN")
    lines = [u"{} – {}".format(TRANSACTION_NAME, mode),
             u"Bản CAD: {} | {} layer ống{}".format(cad_name, len(layers),
                                                     u" | KHÔNG có layer: " + u"; ".join(missing) if missing else u""),
             u"Phạm vi: " + (u"tuyến qua điểm " + u"; ".join(fmt(q) for q in only_points) if only_points else u"toàn bộ"),
             u"Ống ngang: {} | Ống đứng: {} (rơi {}, xuống {}, lên {}) | Cụm ống: {}".format(
                 len(net["pipes"]), len(net["risers"]), risers["drop"], risers["down"], risers["up"], len(net["components"])),
             u"Phụ kiện dự kiến: " + u", ".join(u"{} {}".format(k, v) for k, v in sorted(kinds.items())),
             u"DN: " + u", ".join(u"D{} × {}".format(d, c) for d, c in sorted(collections.Counter(p["dn"] for p in net["pipes"]).items())),
             u"System: " + u", ".join(sorted(set(u"{} → {}".format(p["layer"].replace(u"AV-P-DR-", u""), p["system"]) for p in net["pipes"]))),
             u"Mũi tên khớp hướng chảy: {} ({} ngược trên toàn bản vẽ – xem log)".format(good, len(net["bad_arrows"])),
             u"Xử lý: " + u", ".join(u"{} {}".format(k, v) for k, v in net["log"].items())] + level_notes
    if abs_c:
        lines.append(u"Theo BOP: {} cụm, tâm ống {:+.0f} … {:+.0f} so với level mặt bằng CAD ({})".format(
            len(abs_c), min(c["z_range"][0] for c in abs_c), max(c["z_range"][1] for c in abs_c),
            cad_level.Name if cad_level is not None else u"?"))
    for k in sorted(groups_used):
        L = levels[k]
        lines.append(u"Nhóm '{}' (cụm không có BOP): tâm ống điểm cao nhất {:+.0f}, thấp nhất ≈ {:+.0f}; ống đứng xuống tới {:+.0f} (level {})".format(
            k, ft2mm(L["up_z"]) - h_top_mm, ft2mm(L["up_z"]) - h_top_mm - rises[k], ft2mm(L["host_z"]), L["host"].Name))
    if old:
        lines.append(u"DỪNG GHI: mô hình đã có {} ống '{}' của lần chạy trước. Xoá chúng (lọc Comments) rồi chạy lại.".format(len(old), COMMENT))

    if not dry_run and not old:
        TransactionManager.Instance.ForceCloseTransaction()
        t = Transaction(doc, TRANSACTION_NAME)
        handler = CommitFailures()
        opts = t.GetFailureHandlingOptions()
        opts.SetFailuresPreprocessor(handler)
        opts.SetClearAfterRollback(True)
        t.SetFailureHandlingOptions(opts)
        t.Start()
        try:
            pt, fits, done = ensure_types()
            lines.append(u"Pipe type '{}': {}".format(get_name(pt), u"; ".join(done)))
            b = Builder(net, cad.GetTotalTransform(), levels, pt, systems, fits,
                        cad_level.Elevation if cad_level is not None else levels[u"*"]["host_z"])
            b.pipes()
            ok, fail = collections.Counter(), collections.Counter()
            order = {"wye": 0, "tee": 1, "transition": 2, "elbow": 3}      # Y / tê trước (cần nhiều chỗ)
            for f in sorted(net["fittings"], key=lambda f: order.get(f["kind"], 9)):
                why = b.fitting(f)
                if why is None:
                    ok[f["kind"]] += 1
                else:
                    fail[f["kind"]] += 1
                    ids = [f.get("leg45"), f.get("leg135"), f.get("branch")] + list(f.get("main", [])) + list(f.get("pipes", []))
                    dns = sorted(set(int(round(ft2mm(b.made[i].Diameter))) for i in ids if i is not None and i in b.made))
                    rows.append([u"Phụ kiện " + f["kind"], fmt(net["nodes"][f["node"]]), u"/".join(str(d) for d in dns), why, u""])
            lines.append(apply_colors(b))
            status = t.Commit()
            if status != TransactionStatus.Committed:
                lines.append(u"LỖI: Revit không commit được (trạng thái {}), mọi thay đổi đã bị hoàn tác. "
                             u"Bộ xử lý lỗi được gọi {} lần.".format(status, handler.calls))
                for (sev, text), n in handler.all.most_common():
                    ids = sorted(handler.ids.get(text, []))
                    lines.append(u"  [{}] {} ×{} | Id: {}".format(sev, text, n, u", ".join(str(i) for i in ids[:12])))
                    rows.append([u"Lỗi commit " + sev, u"", u"", text, u"Id " + u" ".join(str(i) for i in ids)])
                if not handler.all:
                    lines.append(u"  (không có thông báo lỗi nào qua bộ xử lý)")
                for text, n in handler.warnings.most_common(5):
                    lines.append(u"  [Warning] {} ×{}".format(text, n))
                try:
                    lines.append(u"Log: " + write_log(rows, cad_name))
                except Exception:
                    pass
                return lines
            lines.append(u"Đã tạo: {} ống; phụ kiện {}".format(len(b.made), u", ".join(u"{} {}".format(k, v) for k, v in sorted(ok.items()))))
            lines.append(u"Không đặt được (nối tay, xem log): " + (u", ".join(u"{} {}".format(k, v) for k, v in sorted(fail.items())) or u"0"))
            if handler.resolved:
                lines.append(u"Revit tự xử lý lúc commit (đã ngắt nối, kiểm tra lại): " +
                             u"; ".join(u"{} ×{}".format(k, v) for k, v in handler.resolved.items()))
            if handler.warnings:
                lines.append(u"Cảnh báo Revit (đã ẩn, không ảnh hưởng): " +
                             u"; ".join(u"{} ×{}".format(k, v) for k, v in handler.warnings.most_common(5)))
        except Exception as ex:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            import traceback
            return lines + [u"LỖI khi dựng ống, mọi thay đổi đã được hoàn tác: {}".format(ex), traceback.format_exc()]
    try:
        lines.append(u"Log: " + write_log(rows, cad_name))
    except Exception as ex:
        lines.append(u"Không ghi được file log: {}".format(ex))
    return lines + [u" | ".join(r[:4]) for r in rows[:200]]


if DYNAMO:
    try:
        OUT = main()
    except Exception as ex:
        import traceback
        OUT = [u"LỖI: {}".format(ex), traceback.format_exc()]
