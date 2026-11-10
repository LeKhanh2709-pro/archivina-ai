# -*- coding: utf-8 -*-
# Tầng 2: 2 hàng ô trên cùng của vách kính ARV đổi sang kiểu A-ALU (người dùng duyệt bản mẫu 2026-11-10).
# Cửa sổ và các hàng dưới không đụng tới. Vách / ô đang do người khác mượn hoặc chưa đồng bộ thì bỏ qua và báo.
from __future__ import unicode_literals
import io, os, clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB

TEN_FILE = "2.HQV_A_ThapB_L1-L3"
TEN_TANG = "Tầng 2"
TEN_KIEU = "A-ALU"
TIEN_TO_VACH = "ARV_Vách kính"
Z_CHIA = 2800.0   # đáy ô từ mức này trở lên (mm từ chân vách) = 2 hàng trên cùng

log = []
def ghi(s):
    log.append("%s" % s)
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    f = io.open(os.path.join(OUT_DIR, "log.txt"), "w", encoding="utf-8")
    f.write("\n".join(log))
    f.close()

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

def trang_thai_chung(e):
    """Trả về lý do không sửa được do worksharing, hoặc None."""
    if not doc.IsWorkshared:
        return None
    if DB.WorksharingUtils.GetCheckoutStatus(doc, e.Id) == DB.CheckoutStatus.OwnedByOtherUser:
        return "đang do người khác mượn"
    mu = None
    try:
        mu = DB.WorksharingUtils.GetModelUpdatesStatus(doc, e.Id)
    except Exception:
        mu = None
    if mu is not None and mu != DB.ModelUpdatesStatus.CurrentWithCentral:
        return "chưa đồng bộ với file trung tâm (%s)" % mu
    return None

def o_tren(w, ma_cat):
    """Ô kính thuộc 2 hàng trên cùng của vách."""
    z0 = w.get_BoundingBox(None).Min.Z
    kq = []
    for pid in w.CurtainGrid.GetPanelIds():
        e = doc.GetElement(pid)
        if e is None or e.Category is None or int(e.Category.Id.Value) != ma_cat:
            continue
        bb = e.get_BoundingBox(None)
        if bb is None or mm(bb.Min.Z - z0) < Z_CHIA:
            continue
        kq.append(e)
    return kq

def chay():
    if KIEM_TEN and not doc.Title.startswith(TEN_FILE):
        return "Dừng: file đang mở là \"%s\", không phải %s. Chưa sửa gì." % (doc.Title, TEN_FILE)
    kieu = [t for t in DB.FilteredElementCollector(doc).OfClass(DB.PanelType) if ten(t) == TEN_KIEU]
    if not kieu:
        return "Dừng: file chưa có kiểu %s. Chưa sửa gì." % TEN_KIEU
    lv = [l for l in DB.FilteredElementCollector(doc).OfClass(DB.Level) if l.Name == TEN_TANG]
    if not lv:
        return "Dừng: không thấy level %s. Chưa sửa gì." % TEN_TANG
    ma_cat = int(DB.BuiltInCategory.OST_CurtainWallPanels)
    W = [w for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall)
         if w.LevelId == lv[0].Id and w.WallType.Kind == DB.WallKind.Curtain and ten(w.WallType).startswith(TIEN_TO_VACH)]
    ghi("Vach kinh ARV Tang 2: %d" % len(W))
    lam = []; da_co = 0; bo = []
    for w in W:
        ly_do = trang_thai_chung(w)
        if ly_do:
            bo.append((int(w.Id.Value), "vách " + ly_do))
            continue
        for e in o_tren(w, ma_cat):
            if e.GetTypeId() == kieu[0].Id:
                da_co += 1
                continue
            ly_do = trang_thai_chung(e)
            if ly_do:
                bo.append((int(e.Id.Value), "ô " + ly_do))
                continue
            lam.append(e)
    ghi("Se doi %d o, da la %s %d, bo qua %d %s" % (len(lam), TEN_KIEU, da_co, len(bo), bo[:30]))
    if not lam:
        s = "Không có ô nào cần đổi (đã là %s: %d ô)." % (TEN_KIEU, da_co)
        if bo:
            s += "\nBỏ qua %d mục: %s" % (len(bo), "; ".join("%s (%s)" % x for x in bo[:20]))
        return s

    tx = DB.Transaction(doc, "ARV đổi 2 hàng ô trên cùng Tầng 2 sang A-ALU")
    fo = tx.GetFailureHandlingOptions()
    fo.SetFailuresPreprocessor(BoQuaCanhBao())
    tx.SetFailureHandlingOptions(fo)
    tx.Start()
    doi = 0; loi = []
    for e in lam:
        try:
            e.ChangeTypeId(kieu[0].Id)
            doi += 1
        except Exception as ex:
            loi.append((int(e.Id.Value), "%s" % ex))
    doc.Regenerate()
    kq = tx.Commit()
    ghi("Commit: %s; doi %d, loi %d %s" % (kq, doi, len(loi), loi[:10]))
    if kq != DB.TransactionStatus.Committed:
        return "Revit không cho lưu thay đổi (%s). Chưa sửa gì." % kq

    con = 0; alu = 0
    for w in W:
        for e in o_tren(w, ma_cat):
            if e.GetTypeId() == kieu[0].Id:
                alu += 1
            else:
                con += 1
    ghi("Sau: 2 hang tren cung co %d o %s, %d o chua doi" % (alu, TEN_KIEU, con))
    s = "Đã đổi %d ô sang %s trên %d vách kính Tầng 2.\n2 hàng trên cùng: %d ô %s, còn %d ô chưa đổi.\n" % (doi, TEN_KIEU, len(W), alu, TEN_KIEU, con)
    if loi:
        s += "\nLỗi %d ô: %s\n" % (len(loi), "; ".join("%s" % x[0] for x in loi[:20]))
    if bo:
        s += "\nBỏ qua %d mục:\n%s\n" % (len(bo), "\n".join("%s: %s" % x for x in bo[:20]))
    s += "\nCtrl+Z để hoàn tác. Thấy đúng thì bấm Synchronize để lưu vào file gốc."
    return s

bao_cao = chay()
ghi("BAO CAO: " + bao_cao)
