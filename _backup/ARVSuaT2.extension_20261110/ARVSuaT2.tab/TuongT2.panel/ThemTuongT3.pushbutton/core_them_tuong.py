# -*- coding: utf-8 -*-
# Tầng 3BA: thêm tường lấp khoảng hở phía trên vách kính, từ đỉnh vách tới đáy dầm / sàn trong link kết cấu.
# Tường đặt theo tuyến vách kính, mặt ngoài tường bằng mặt ngoài đố. Không sửa vách kính, không xoá gì.
from __future__ import unicode_literals
import io, os, json, math, clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB

TEN_TANG = "Tầng 3BA"
TEN_TANG_TREN = "Tầng chuyển"
TEN_KIEU_TUONG = "XMCL 15-200-15"
TIEN_TO_VACH = "ARV_Vách kính"
LUI_VAO = 40.0     # tim tường lùi vào trong so với tim vách: (230 - 150) / 2, mặt ngoài tường bằng mặt ngoài đố
DOAN_NHO = 100.0   # đoạn ngắn hơn thì bỏ
HO_NHO = 30.0      # hở ít hơn thì không lấp
GAN_GOC = 400.0
BUOC = 50.0        # mm giữa 2 tia đo dọc vách

log = []
def ghi(s):
    log.append("%s" % s)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    f = io.open(os.path.join(OUT_DIR, "log.txt"), "w", encoding="utf-8")
    f.write("\n".join(log))
    f.close()
def ft(x):
    return DB.UnitUtils.ConvertToInternalUnits(x, DB.UnitTypeId.Millimeters)
def mm(x):
    return DB.UnitUtils.ConvertFromInternalUnits(x, DB.UnitTypeId.Millimeters)
def ten(e):
    return DB.Element.Name.GetValue(e)

class BoQuaCanhBao(DB.IFailuresPreprocessor):
    def PreprocessFailures(self, a):
        for f in a.GetFailureMessages():
            if f.GetSeverity() == DB.FailureSeverity.Warning:
                ghi("  canh bao trong luc sua: %s" % f.GetDescriptionText())
                a.DeleteWarning(f)
        return DB.FailureProcessingResult.Continue

def lay_ket_cau():
    """Khối đặc của dầm, sàn, cột, vách trong link kết cấu, trong dải cao độ cần xét."""
    kq = []
    op = DB.Options()
    op.DetailLevel = DB.ViewDetailLevel.Fine
    def khoi(g, ra):
        for o in g:
            if isinstance(o, DB.GeometryInstance):
                khoi(o.GetInstanceGeometry(), ra)
            elif isinstance(o, DB.Solid) and o.Volume > 1e-6:
                ra.append(o)
    cat = [DB.BuiltInCategory.OST_StructuralFraming, DB.BuiltInCategory.OST_Floors,
           DB.BuiltInCategory.OST_StructuralColumns, DB.BuiltInCategory.OST_Walls]
    for li in DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkInstance):
        ld = li.GetLinkDocument()
        if ld is None:
            ghi("Link chua nap: %s" % li.Name)
            continue
        T = li.GetTotalTransform()
        Ti = T.Inverse
        for c in cat:
            for e in DB.FilteredElementCollector(ld).OfCategory(c).WhereElementIsNotElementType():
                bb = e.get_BoundingBox(None)
                if bb is None or bb.Max.Z < ft(14000) or bb.Min.Z > ft(17300):
                    continue
                g = e.get_Geometry(op)
                if g is None:
                    continue
                ds = []
                khoi(g, ds)
                if ds:
                    kq.append({"bb": bb, "khoi": ds, "T": T, "Ti": Ti})
    return kq

TUY_CHON_TIA = DB.SolidCurveIntersectionOptions()
def tia(kc, x, y, z0, z1):
    """Cao độ thấp nhất chạm khối kết cấu trên tia đứng z0 -> z1 (mm, toạ độ model); không chạm thì None."""
    tot = None
    for k in kc:
        p = k["Ti"].OfPoint(DB.XYZ(ft(x), ft(y), ft(z0)))
        bb = k["bb"]
        if p.X < bb.Min.X or p.X > bb.Max.X or p.Y < bb.Min.Y or p.Y > bb.Max.Y:
            continue
        q = k["Ti"].OfPoint(DB.XYZ(ft(x), ft(y), ft(z1)))
        ln = DB.Line.CreateBound(p, q)
        for s in k["khoi"]:
            r = s.IntersectWithCurve(ln, TUY_CHON_TIA)
            for i in range(r.SegmentCount):
                c = r.GetCurveSegment(i)
                z = mm(min(c.GetEndPoint(0).Z, c.GetEndPoint(1).Z) + k["T"].Origin.Z)
                if tot is None or z < tot:
                    tot = z
    return tot

def huong_ngoai(w, u, spec):
    """Hướng ra ngoài nhà: ưu tiên hướng cửa sổ của vách, không có thì tra bảng hướng lúc dựng."""
    n = (-u[1], u[0])
    for pid in w.CurtainGrid.GetPanelIds():
        e = doc.GetElement(pid)
        if e is not None and e.Category is not None and int(e.Category.Id.Value) == int(DB.BuiltInCategory.OST_Windows):
            f = e.FacingOrientation
            d = f.X * n[0] + f.Y * n[1]
            if abs(d) > 0.5:
                return (n[0] * (1 if d > 0 else -1), n[1] * (1 if d > 0 else -1)), "cua so"
    c = w.Location.Curve
    a, b = c.GetEndPoint(0), c.GetEndPoint(1)
    mx, my = mm((a.X + b.X) / 2), mm((a.Y + b.Y) / 2)
    L = mm(c.Length)
    for it in spec:
        du = (it["q"][0] - it["p"][0], it["q"][1] - it["p"][1])
        dl = math.hypot(du[0], du[1])
        v = (du[0] / dl, du[1] / dl)
        if abs(v[0] * u[0] + v[1] * u[1]) < 0.99:
            continue
        s = (mx - it["p"][0]) * (-v[1]) + (my - it["p"][1]) * v[0]
        t = (mx - it["p"][0]) * v[0] + (my - it["p"][1]) * v[1]
        if abs(s) < 160 and -100 < t < dl + 100:
            d = it["ra"][0] * n[0] + it["ra"][1] * n[1]
            return (n[0] * (1 if d > 0 else -1), n[1] * (1 if d > 0 else -1)), "bang huong"
    return None, "khong ro"

def bang_huong():
    t = [x for x in json.load(io.open(FILE_SPEC, encoding="utf-8")) if x["ten"] == "T3"][0]
    kq = []
    for x in t["thang"]:
        kq.append({"p": x["p1"], "q": x["p2"], "ra": x["ra"]})
    for x in t["goc"]:
        kq.append({"p": x["P1"], "q": x["C"], "ra": x["ra1"]})
        kq.append({"p": x["C"], "q": x["P2"], "ra": x["ra2"]})
    for x in t["lom"]:
        kq.append({"p": x["p"], "q": [x["p"][0] + x["d"][0] * x["L"], x["p"][1] + x["d"][1] * x["L"]], "ra": x["ra"]})
    return kq

def ke_hoach():
    """Danh sách đoạn tường: {x0,y0,x1,y1,day,dinh,cw}. Toạ độ mm, tim tường."""
    tang = [l for l in DB.FilteredElementCollector(doc).OfClass(DB.Level) if l.Name == TEN_TANG][0]
    tren = [l for l in DB.FilteredElementCollector(doc).OfClass(DB.Level) if l.Name == TEN_TANG_TREN][0]
    cao_tren = mm(tren.Elevation)
    ds = [w for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall) if w.LevelId == tang.Id]
    # gồm cả vách đặt ở level khác nhưng cao lên tới Tầng 3 (vách thông tầng)
    CW = [w for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall)
          if w.WallType.Kind == DB.WallKind.Curtain and ten(w.WallType).startswith(TIEN_TO_VACH)
          and (w.LevelId == tang.Id or w.get_BoundingBox(None).Max.Z > tang.Elevation + ft(100))]
    BW = [w for w in ds if w.WallType.Kind == DB.WallKind.Basic]
    kc = lay_ket_cau()
    import collections
    ghi("Phan tu ket cau xet: %d" % len(kc))
    spec = bang_huong()
    doan = []; khong_ho = 0; khong_huong = []
    # hướng ra ngoài của từng vách; vách không có cửa sổ và không có trong bảng thì lấy theo vách cùng phương gần nhất
    bang_ra = {}
    for w in CW:
        c = w.Location.Curve
        a, b = c.GetEndPoint(0), c.GetEndPoint(1)
        u = ((b.X - a.X) / c.Length, (b.Y - a.Y) / c.Length)
        ra, nguon = huong_ngoai(w, u, spec)
        bang_ra[int(w.Id.Value)] = (ra, nguon, (mm((a.X + b.X) / 2), mm((a.Y + b.Y) / 2)), u)
    for k in list(bang_ra):
        ra, nguon, m, u = bang_ra[k]
        if ra is not None:
            continue
        ung = [(math.hypot(v[2][0] - m[0], v[2][1] - m[1]), v[0]) for k2, v in bang_ra.items()
               if v[0] is not None and abs(v[3][0] * u[0] + v[3][1] * u[1]) > 0.99]
        if ung:
            ung.sort(key=lambda x: x[0])
            bang_ra[k] = (ung[0][1], "vach gan nhat %.0f mm" % ung[0][0], m, u)
            ghi("Vach %s lay huong theo vach cung phuong cach %.0f mm: %s" % (k, ung[0][0], ung[0][1]))
    for w in CW:
        c = w.Location.Curve
        a, b = c.GetEndPoint(0), c.GetEndPoint(1)
        ax, ay = mm(a.X), mm(a.Y)
        L = mm(c.Length)
        u = ((b.X - a.X) / c.Length, (b.Y - a.Y) / c.Length)
        n = (-u[1], u[0])
        day = mm(w.get_BoundingBox(None).Max.Z)
        if cao_tren - day < HO_NHO:
            khong_ho += 1
            continue
        ra, nguon = bang_ra[int(w.Id.Value)][:2]
        if ra is None:
            khong_huong.append(int(w.Id.Value))
            s0 = 0.0
        else:
            s0 = -LUI_VAO * (ra[0] * n[0] + ra[1] * n[1])
        def chieu(x, y):
            return (x - ax) * u[0] + (y - ay) * u[1], (x - ax) * n[0] + (y - ay) * n[1]
        # tường thường song song đã có trên tuyến thì không dựng trùng
        co_san = []
        for t2 in BW:
            c2 = t2.Location.Curve
            if not isinstance(c2, DB.Line):
                continue
            p, q = c2.GetEndPoint(0), c2.GetEndPoint(1)
            d2 = (q - p).Normalize()
            if abs(d2.X * u[0] + d2.Y * u[1]) < 0.995:
                continue
            bb2 = t2.get_BoundingBox(None)
            if mm(bb2.Max.Z) <= day + 50 or mm(bb2.Min.Z) > day + 1:
                continue
            t1, s1 = chieu(mm(p.X), mm(p.Y))
            t3, s3 = chieu(mm(q.X), mm(q.Y))
            if abs((s1 + s3) / 2 - s0) < mm(t2.Width) / 2 + 115 - 30:
                co_san.append((min(t1, t3), max(t1, t3)))
        so_buoc = max(1, int(L / BUOC))
        ket = []
        for i in range(so_buoc):
            x = L * i / so_buoc
            y = L * (i + 1) / so_buoc
            giua = (x + y) / 2
            if [q for q in co_san if q[0] <= giua <= q[1]]:
                ket.append((x, y, None))
                continue
            z = tia(kc, ax + u[0] * giua + n[0] * s0, ay + u[1] * giua + n[1] * s0, day + 2, cao_tren + 100)
            if z is None:
                dinh = cao_tren
            elif z <= day + 20:
                dinh = None
            else:
                dinh = min(z, cao_tren)
            ket.append((x, y, dinh if dinh is not None and dinh - day >= HO_NHO else None))
        gop = []
        for x, y, d in ket:
            if d is None:
                continue
            if gop and abs(gop[-1][1] - x) < 1 and abs(gop[-1][2] - d) < 3:
                gop[-1][1] = y
            else:
                gop.append([x, y, d])
        ghi("  vach %s L=%.0f dinh=%.0f: lap %s; khong lap %s" % (int(w.Id.Value), L, day, [(round(x), round(y), round(d)) for x, y, d in gop],
            "%.0f mm" % sum(y - x for x, y, d in ket if d is None)))
        for x, y, d in gop:
            if y - x < DOAN_NHO:
                continue
            doan.append({"x0": ax + u[0] * x + n[0] * s0, "y0": ay + u[1] * x + n[1] * s0, "x1": ax + u[0] * y + n[0] * s0, "y1": ay + u[1] * y + n[1] * s0,
                         "day": day, "dinh": d, "cw": int(w.Id.Value), "nguon": nguon})
    ghi("Vach ARV %d: %d khong ho; %d doan tuong truoc khi gop; khong ro huong: %s" % (len(CW), khong_ho, len(doan), khong_huong))
    # gộp đoạn thẳng hàng trùng nhau hoặc nối tiếp (vách chồng 1 đố)
    nhom = {}
    for p in doan:
        doc_y = abs(p["x0"] - p["x1"]) < abs(p["y0"] - p["y1"])
        k = (doc_y, round((p["x0"] + p["x1"]) / 2 / 40.0) if doc_y else round((p["y0"] + p["y1"]) / 2 / 40.0), round(p["day"]), round(p["dinh"]))
        nhom.setdefault(k, []).append(p)
    ra_lai = []
    for k, l in nhom.items():
        doc_y = k[0]
        c0 = "y0" if doc_y else "x0"; c1 = "y1" if doc_y else "x1"
        l2 = sorted(l, key=lambda p: min(p[c0], p[c1]))
        hien = None
        for p in l2:
            a_, b_ = min(p[c0], p[c1]), max(p[c0], p[c1])
            if hien is not None and a_ <= hien["b"] + 5:
                hien["b"] = max(hien["b"], b_)
                hien["cw"].append(p["cw"])
            else:
                hien = {"doc_y": doc_y, "c": (p["x0"] + p["x1"]) / 2 if doc_y else (p["y0"] + p["y1"]) / 2, "a": a_, "b": b_, "day": p["day"], "dinh": p["dinh"], "cw": [p["cw"]]}
                ra_lai.append(hien)
    # góc vuông: kéo 2 tường tới giao tuyến để Revit nối góc
    for i in range(len(ra_lai)):
        for j in range(len(ra_lai)):
            p, q = ra_lai[i], ra_lai[j]
            if not (p["doc_y"] and not q["doc_y"]):
                continue
            X, Y = p["c"], q["c"]
            ten_p = "a" if abs(p["a"] - Y) <= abs(p["b"] - Y) else "b"
            ten_q = "a" if abs(q["a"] - X) <= abs(q["b"] - X) else "b"
            if abs(p[ten_p] - Y) < GAN_GOC and abs(q[ten_q] - X) < GAN_GOC:
                # trên cùng tuyến chỉ đoạn sát góc nhất mới được kéo tới góc
                gan_hon = [r for r in ra_lai if r is not p and r["doc_y"] == p["doc_y"] and abs(r["c"] - p["c"]) < 5
                           and min(abs(r["a"] - Y), abs(r["b"] - Y)) < abs(p[ten_p] - Y) - 1]
                gan_hon += [r for r in ra_lai if r is not q and r["doc_y"] == q["doc_y"] and abs(r["c"] - q["c"]) < 5
                            and min(abs(r["a"] - X), abs(r["b"] - X)) < abs(q[ten_q] - X) - 1]
                if gan_hon:
                    continue
                p[ten_p] = Y
                q[ten_q] = X
    ra_lai = [p for p in ra_lai if p["b"] - p["a"] >= DOAN_NHO]
    return tang, tren, ra_lai

def dung(tang, tren, ds):
    kieu = [t for t in DB.FilteredElementCollector(doc).OfClass(DB.WallType) if ten(t) == TEN_KIEU_TUONG]
    if not kieu:
        raise Exception("Khong co kieu tuong %s" % TEN_KIEU_TUONG)
    cao_tang, cao_tren = mm(tang.Elevation), mm(tren.Elevation)
    tx = DB.Transaction(doc, "ARV thêm tường lấp phía trên vách kính Tầng 3")
    fo = tx.GetFailureHandlingOptions()
    fo.SetFailuresPreprocessor(BoQuaCanhBao())
    tx.SetFailureHandlingOptions(fo)
    tx.Start()
    tao = []
    for p in ds:
        if p["doc_y"]:
            A = DB.XYZ(ft(p["c"]), ft(p["a"]), tang.Elevation)
            B = DB.XYZ(ft(p["c"]), ft(p["b"]), tang.Elevation)
        else:
            A = DB.XYZ(ft(p["a"]), ft(p["c"]), tang.Elevation)
            B = DB.XYZ(ft(p["b"]), ft(p["c"]), tang.Elevation)
        w = DB.Wall.Create(doc, DB.Line.CreateBound(A, B), kieu[0].Id, tang.Id, ft(p["dinh"] - p["day"]), ft(p["day"] - cao_tang), False, False)
        w.get_Parameter(DB.BuiltInParameter.WALL_HEIGHT_TYPE).Set(tren.Id)
        w.get_Parameter(DB.BuiltInParameter.WALL_TOP_OFFSET).Set(ft(p["dinh"] - cao_tren))
        p["id"] = int(w.Id.Value)
        tao.append(w)
    doc.Regenerate()
    kq = tx.Commit()
    ghi("Commit: %s; tao %d tuong" % (kq, len(tao)))
    return kq, tao


# ===== Phần riêng của nút: chỉ dựng các đoạn người dùng đã duyệt trong bản mẫu v5 (2026-11-10) =====
TEN_FILE = "2.HQV_A_ThapB_L1-L3"

def khop_duyet(p, duyet):
    for q in duyet:
        if q["doc_y"] == p["doc_y"] and abs(q["c"] - p["c"]) < 5 and abs(q["a"] - p["a"]) < 5 and abs(q["b"] - p["b"]) < 5 \
                and abs(q["day"] - p["day"]) < 2 and abs(q["dinh"] - p["dinh"]) < 5:
            return True
    return False

def chay():
    if KIEM_TEN and not doc.Title.startswith(TEN_FILE):
        return "Dừng: file đang mở là \"%s\", không phải %s. Chưa sửa gì." % (doc.Title, TEN_FILE)
    if len(lay_ket_cau()) < 100:
        return "Dừng: link kết cấu chưa nạp nên không đo được đáy dầm. Chưa sửa gì."
    tang, tren, ds = ke_hoach()
    duyet = json.load(io.open(os.path.join(THU_MUC_NUT, "doan_duyet.json"), encoding="utf-8"))
    hop = [p for p in ds if khop_duyet(p, duyet)]
    la = [p for p in ds if not khop_duyet(p, duyet)]
    ghi("Tinh ra %d doan; khop danh sach duyet %d; khac %d %s" % (len(ds), len(hop), len(la), [(round(p["c"]), round(p["a"]), round(p["b"]), round(p["day"]), round(p["dinh"])) for p in la][:20]))
    if not hop:
        return "Không có đoạn tường nào cần thêm (danh sách duyệt: %d đoạn, tính ra %d đoạn, khác danh sách %d)." % (len(duyet), len(ds), len(la))
    kq, tao = dung(tang, tren, hop)
    if kq != DB.TransactionStatus.Committed:
        return "Revit không cho lưu thay đổi (%s). Chưa sửa gì." % kq
    s = "Đã thêm %d đoạn tường, tổng %.1f m, phía trên vách kính Tầng 3.\n" % (len(tao), sum(p["b"] - p["a"] for p in hop) / 1000.0)
    if la:
        s += "\nBỏ qua %d đoạn khác với bản mẫu đã duyệt (model đã đổi), xem nhật ký.\n" % len(la)
    s += "\nCtrl+Z để hoàn tác. Thấy đúng thì bấm Synchronize để lưu vào file gốc."
    return s

bao_cao = chay()
ghi("BAO CAO: " + bao_cao)
