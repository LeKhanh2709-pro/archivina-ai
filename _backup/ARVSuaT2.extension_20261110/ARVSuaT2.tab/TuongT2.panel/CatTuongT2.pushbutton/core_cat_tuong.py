# -*- coding: utf-8 -*-
# Tầng 2: cắt tường thường trùng vách kính, CHỈ các tường người dùng đã duyệt (ke_hoach_duyet.json, 2026-11-10).
# Tường đã đổi so với lúc duyệt, đang do người khác mượn, hoặc chưa đồng bộ thì bỏ qua và báo. Một lần Ctrl+Z là hoàn tác.
from __future__ import unicode_literals
import io, os, json, clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB

THU_MUC = THU_MUC_NUT
TEN_FILE = "2.HQV_A_ThapB_L1-L3"
TEN_TANG = "Tầng 2"
DOAN_NHO = 300.0
PHU_NHO = 30.0
LECH = 2.0

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
def i_(e):
    return int(e.Id.Value)

class BoQuaCanhBao(DB.IFailuresPreprocessor):
    def PreprocessFailures(self, a):
        for f in a.GetFailureMessages():
            if f.GetSeverity() == DB.FailureSeverity.Warning:
                ghi("  canh bao trong luc sua: %s" % f.GetDescriptionText())
                a.DeleteWarning(f)
        return DB.FailureProcessingResult.Continue

def doan_phu(w, CW):
    c = w.Location.Curve
    a, b = c.GetEndPoint(0), c.GetEndPoint(1)
    u = (b - a).Normalize()
    L = mm(c.Length)
    hw = mm(w.Width) / 2
    iv = []
    for g in CW:
        gc = g.Location.Curve
        ga, gb = gc.GetEndPoint(0), gc.GetEndPoint(1)
        gu = (gb - ga).Normalize()
        if abs(u.X * gu.X + u.Y * gu.Y) < 0.995:
            continue
        n = DB.XYZ(-gu.Y, gu.X, 0)
        kc = (mm((a - ga).DotProduct(n)) + mm((b - ga).DotProduct(n))) / 2
        if abs(kc) > hw + 80:
            continue
        t = sorted([mm((ga - a).DotProduct(u)), mm((gb - a).DotProduct(u))])
        x, y = max(t[0], 0.0), min(t[1], L)
        if y - x >= PHU_NHO:
            iv.append((x, y))
    iv.sort()
    gop = []
    for x, y in iv:
        if gop and x <= gop[-1][1] + 1.0:
            gop[-1][1] = max(gop[-1][1], y)
        else:
            gop.append([x, y])
    return gop, a, u, L

def con_lai(gop, L):
    kq = []
    p = 0.0
    for x, y in gop:
        if x - p >= DOAN_NHO:
            kq.append((p, x))
        p = max(p, y)
    if L - p >= DOAN_NHO:
        kq.append((p, L))
    return kq

def khop(con, duyet):
    if len(con) != len(duyet):
        return False
    for p, q in zip(con, duyet):
        if abs(p[0] - q[0]) > LECH or abs(p[1] - q[1]) > LECH:
            return False
    return True

def trang_thai_chung(w):
    """Trả về lý do không sửa được do worksharing, hoặc None."""
    if not doc.IsWorkshared:
        return None
    st = DB.WorksharingUtils.GetCheckoutStatus(doc, w.Id)
    if st == DB.CheckoutStatus.OwnedByOtherUser:
        return "đang do người khác mượn"
    if doc.IsWorkshared and not doc.IsModelInCloud:
        mu = None
        try:
            mu = DB.WorksharingUtils.GetModelUpdatesStatus(doc, w.Id)
        except Exception:
            mu = None
        if mu is not None and mu != DB.ModelUpdatesStatus.CurrentWithCentral:
            return "chưa đồng bộ với file trung tâm (%s)" % mu
    return None

def chay():
    if KIEM_TEN and not doc.Title.startswith(TEN_FILE):
        return "Dừng: file đang mở là \"%s\", không phải %s. Chưa sửa gì." % (doc.Title, TEN_FILE)
    duyet = dict((m["id"], m) for m in json.load(io.open(os.path.join(THU_MUC, "ke_hoach_duyet.json"), encoding="utf-8"))["lam"])
    ghi("Danh sach da duyet: %d tuong" % len(duyet))
    lv = [l for l in DB.FilteredElementCollector(doc).OfClass(DB.Level) if l.Name == TEN_TANG]
    if not lv:
        return "Dừng: không thấy level %s. Chưa sửa gì." % TEN_TANG
    level = lv[0]
    ds = [w for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall) if w.LevelId == level.Id]
    CW = [w for w in ds if w.WallType.Kind == DB.WallKind.Curtain]
    BW = [w for w in ds if w.WallType.Kind == DB.WallKind.Basic]
    co = dict((i_(w), w) for w in BW)
    truoc_cw = dict((i_(c), (round(mm(c.Location.Curve.Length), 1), c.CurtainGrid.GetPanelIds().Count, c.CurtainGrid.GetMullionIds().Count)) for c in CW)
    ghi("Truoc: %d vach kinh, %d tuong thuong" % (len(CW), len(BW)))
    lam = []; bo = []
    for ma in sorted(duyet):
        m = duyet[ma]
        w = co.get(ma)
        if w is None:
            bo.append((ma, "không còn trong Tầng 2"))
            continue
        gop, a, u, L = doan_phu(w, CW)
        con = con_lai(gop, L)
        if abs(L - m["L"]) > LECH or not khop(con, m["con"]):
            bo.append((ma, "đã đổi so với lúc duyệt"))
            continue
        ly_do = None
        if w.GroupId != DB.ElementId.InvalidElementId:
            ly_do = "nằm trong group"
        elif w.Pinned:
            ly_do = "đang pin"
        elif w.FindInserts(True, True, True, True).Count > 0:
            ly_do = "có đối tượng gắn trên tường"
        else:
            ly_do = trang_thai_chung(w)
        if ly_do:
            bo.append((ma, ly_do))
            continue
        lam.append((w, a, u, L, con))
    ghi("Se sua %d, bo qua %d %s" % (len(lam), len(bo), bo))
    if not lam:
        return "Không có tường nào để sửa.\nBỏ qua %d tường: %s" % (len(bo), "; ".join("%s (%s)" % x for x in bo[:20]))

    tx = DB.Transaction(doc, "ARV cắt tường trùng vách kính Tầng 2")
    fo = tx.GetFailureHandlingOptions()
    fo.SetFailuresPreprocessor(BoQuaCanhBao())
    tx.SetFailureHandlingOptions(fo)
    tx.Start()
    xoa = 0; cat = 0; doan = 0
    for w, a, u, L, con in lam:
        if not con:
            doc.Delete(w.Id)
            xoa += 1
            continue
        z = a.Z
        moi = []
        for x, y in con[1:]:
            cp = DB.ElementTransformUtils.CopyElement(doc, w.Id, u.Multiply(ft(x - con[0][0])))
            moi.append((doc.GetElement(list(cp)[0]), x, y))
        moi.insert(0, (w, con[0][0], con[0][1]))
        for t, x, y in moi:
            if x > 1.0:
                DB.WallUtils.DisallowWallJoinAtEnd(t, 0)
            if y < L - 1.0:
                DB.WallUtils.DisallowWallJoinAtEnd(t, 1)
            p = a + u.Multiply(ft(x))
            q = a + u.Multiply(ft(y))
            t.Location.Curve = DB.Line.CreateBound(DB.XYZ(p.X, p.Y, z), DB.XYZ(q.X, q.Y, z))
        cat += 1
        doan += len(moi)
    doc.Regenerate()
    kq = tx.Commit()
    ghi("Commit: %s; xoa %d, cat %d thanh %d doan" % (kq, xoa, cat, doan))
    if kq != DB.TransactionStatus.Committed:
        return "Revit không cho lưu thay đổi (%s). Chưa sửa gì." % kq

    ds2 = [w for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall) if w.LevelId == level.Id]
    CW2 = [w for w in ds2 if w.WallType.Kind == DB.WallKind.Curtain]
    BW2 = [w for w in ds2 if w.WallType.Kind == DB.WallKind.Basic]
    sau_cw = dict((i_(c), (round(mm(c.Location.Curve.Length), 1), c.CurtainGrid.GetPanelIds().Count, c.CurtainGrid.GetMullionIds().Count)) for c in CW2)
    khac = [k for k in truoc_cw if truoc_cw[k] != sau_cw.get(k)]
    con_trung = [i_(w) for w in BW2 if doan_phu(w, CW2)[0]]
    ghi("Sau: %d vach kinh, %d tuong thuong; vach kinh doi: %s; tuong con trung: %s" % (len(CW2), len(BW2), khac, con_trung))
    s = "Đã sửa %d tường Tầng 2: xoá %d, cắt %d thành %d đoạn.\nVách kính thay đổi: %d.\nTường còn trùng kính: %d (2 tường có kính gắn sẵn là đúng).\n" % (len(lam), xoa, cat, doan, len(khac), len(con_trung))
    if bo:
        s += "\nBỏ qua %d tường:\n%s\n" % (len(bo), "\n".join("%s: %s" % x for x in bo[:20]))
    s += "\nCtrl+Z để hoàn tác. Thấy đúng thì bấm Synchronize để lưu vào file gốc."
    return s

bao_cao = chay()
ghi("BAO CAO: " + bao_cao)
