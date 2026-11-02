# -*- coding: utf-8 -*-
"""Vách kính Revit theo quy tắc lệnh VK / MDVK (Archivina) – phần lõi, không giao diện.

Chạy được cả IronPython 2.7 (nút pyRevit, updater) lẫn CPython 3 (Dynamo PythonNet3, để thử tự động).

Quy tắc (người dùng chốt 2026-11-01, chép từ VK / MDVK):
  - Đố 65 x 150 (kiểu "ARV_Đố 65x150", đặt giữa mặt kính). L = mép ngoài - mép ngoài; đố biên Revit nằm TRONG
    đầu vách nên tâm đố biên cách mép ngoài 32,5 (đã thử: đố biên chiếm 0..65 của vách).
  - Khoảng chia S = L - đầu - 32,5 (đầu = 32,5; cánh vách góc = 75, tâm đố góc 150 x 150). Cửa sổ / cửa đi chiếm
    đúng bề rộng tâm - tâm nhập trong bảng; phần còn lại chia đều N ô kính, N nhỏ nhất để mỗi ô < 1200.
    Cửa không ghi ô thì rải đều vào ô trống (cửa đi trước, cửa sổ sau) – y hệt vk:chia / Vk.Chia.
  - Cao độ tính từ chân vách (sàn): cửa đi cao hd -> đố ngang suốt vách, mặt dưới = hd; cửa + 65 + khung trên 65
    vượt vách thì bỏ đố ngang, cửa lên sát khung trên. Cửa sổ: mép dưới cánh = sàn hoàn thiện + bậu (50 + 1400),
    đố dưới cửa sổ chỉ trong ô cửa sổ; có thanh ngang -> đố ngang suốt vách ngay trên cửa sổ (cao cửa sổ nhập tay),
    không -> cửa sổ lên sát khung trên. Ô cửa đi không có khung dưới. Đố ngang không cắt qua cửa (bỏ đoạn đó).
  - Vách góc vuông (như mẫu file vach kinh.rvt, T1-VK.11 / 12): cánh 1 bắt đầu bằng đố góc 150 x 150 (Border 1),
    cánh 2 không có đố biên ở góc, ô đầu là panel kính góc "Kinh_goc_6_trai". Điểm góc pick = góc NGOÀI.
  - Thông số vách lưu trong Extensible Storage của vách -> đổi chiều dài / chiều cao vách thì updater chia lại.
Không xoá gì ngoài lưới / đố / panel của chính vách do công cụ tạo.
"""
from __future__ import division, unicode_literals

import io
import json
import math
import os

import clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB.ExtensibleStorage import Schema, SchemaBuilder, Entity, AccessLevel
from System import Guid, String
from System.Collections.Generic import List as NetList

DO = 65.0           # bề rộng đố
NUA = 32.5
TOI_DA = 1200.0     # mỗi ô kính < 1200 tâm - tâm
GOC = 150.0         # đố góc 150 x 150
NUA_GOC = 75.0
SAU_DO = 150.0      # chiều sâu đố

TEN_DO = "ARV_Đố 65x150"
TEN_DO_GOC = "ARV_Đố góc 150x150"
TEN_VACH = "ARV_Vách kính 65"
TEN_VACH_GOC_DO = "ARV_Vách kính 65 - cánh đố góc"
TEN_VACH_GOC_KINH = "ARV_Vách kính 65 - cánh kính góc"
FAM_CUA_DI = "Door-Curtain-Wall-Double-Glass"
FAM_CUA_SO = "CuaSoVK_A_loai2"
FAM_KINH_GOC = "Kinh_goc_6_trai"

SCHEMA_GUID = Guid("6f1c2d9a-3b4e-4f5a-9c7d-8e2a1b0c4d53")
THU_MUC_FAMILY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vach_kinh")


# ---------------------------------------------------------------- số / đơn vị
def ft(v):
    return DB.UnitUtils.ConvertToInternalUnits(v, DB.UnitTypeId.Millimeters)


def mm(v):
    return DB.UnitUtils.ConvertFromInternalUnits(v, DB.UnitTypeId.Millimeters)


def so(x):
    """Số -> chuỗi gọn, dấu phẩy, tối đa 2 chữ số lẻ (như vk:so)."""
    if x is None:
        return "-"
    s = "%.2f" % (math.floor(x * 100.0 + 0.5) / 100.0)
    s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def doc_so(s):
    """Chuỗi -> số (nhận dấu phẩy); rỗng / sai -> None."""
    if s is None:
        return None
    s = ("%s" % s).strip().replace(",", ".", 1)
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ---------------------------------------------------------------- chia đố (y hệt Vk.Chia, thêm "dau")
def chia(L, ns, ws, nd, wd, vs, vd, dau=NUA):
    """Trả (kq, lỗi). kq = {"tam": [tâm đố từ đầu vách], "o": [(loại "S"/"D"/"K", rộng)], "b": rộng ô kính, "n": số ô kính}.
    vs / vd: danh sách ô (đếm từ 1) đặt cửa sổ / cửa đi; cửa không ghi ô thì tự rải."""
    vs = list(vs or [])
    vd = list(vd or [])
    if L is None or L <= dau + NUA:
        return None, "Nhập chiều dài vách lớn hơn %s mm" % so(dau + NUA)
    if ns < 0 or nd < 0:
        return None, "Số lượng cửa không được âm"
    if ns > 0 and (ws is None or ws <= 0):
        return None, "Nhập bề rộng cửa sổ"
    if nd > 0 and (wd is None or wd <= 0):
        return None, "Nhập bề rộng cửa đi"
    if len(vs) > ns:
        return None, "Ô cửa sổ: ghi %d ô nhưng chỉ có %d cửa sổ" % (len(vs), ns)
    if len(vd) > nd:
        return None, "Ô cửa đi: ghi %d ô nhưng chỉ có %d cửa đi" % (len(vd), nd)
    S = L - dau - NUA
    R = S - ns * (ws or 0) - nd * (wd or 0)
    if R < -1e-6:
        return None, "Vách quá ngắn: cửa chiếm %s > khoảng chia %s" % (so(S - R), so(S))
    n = 0 if R < 1e-6 else 1 + int(R / TOI_DA)
    tong = n + ns + nd
    b = R / n if n > 0 else 0.0
    co_dinh = {}
    for k, l in [(k, "S") for k in vs] + [(k, "D") for k in vd]:
        if k < 1 or k > tong:
            return None, "Ô đặt cửa phải từ 1 đến %d" % tong
        if k in co_dinh:
            return None, "Hai cửa trùng một ô"
        co_dinh[k] = l
    tu_do = [i for i in range(1, tong + 1) if i not in co_dinh]
    tu_dong = ["D"] * (nd - len(vd)) + ["S"] * (ns - len(vs))
    for i, l in enumerate(tu_dong):
        co_dinh[tu_do[int((i + 0.5) * len(tu_do) / len(tu_dong))]] = l
    x = dau
    tam = [x]
    o = []
    for i in range(1, tong + 1):
        t = co_dinh.get(i)
        r = ws if t == "S" else (wd if t == "D" else b)
        o.append((t or "K", r))
        x += r
        tam.append(x)
    return {"tam": tam, "o": o, "b": b, "n": n}, None


def vi_tri(kq, loai):
    return [i + 1 for i, x in enumerate(kq["o"]) if x[0] == loai]


# ---------------------------------------------------------------- cao độ (theo vkmd:tinh, mở rộng cho vách có cả 2 loại cửa)
def tinh_cao(H, co_di, hd, co_so, hs, co_ngang, san, bau):
    """Trả (kq, lỗi). Cao độ tính từ chân vách. kq = {"ngang": [(tâm đố ngang suốt vách, "D"/"S")],
    "di_tren": đỉnh cửa đi, "so": (mép dưới cánh, đỉnh cửa sổ) hoặc None, "duoi": tâm đố dưới cửa sổ, "ghi_chu": []}"""
    if H is None or H <= 3 * DO:
        return None, "Nhập chiều cao vách"
    kq = {"ngang": [], "di_tren": None, "so": None, "duoi": None, "ghi_chu": []}
    if co_di:
        if hd is None or hd <= 0:
            return None, "Nhập chiều cao cửa đi"
        if hd > H + 1e-6:
            return None, "Cửa đi cao %s > vách %s" % (so(hd), so(H))
        if hd + 2 * DO > H + 1e-6:
            # không đủ chỗ đố ngang (cửa + 65 + khung trên 65 > vách): bỏ đố ngang, cửa lên sát khung trên
            kq["di_tren"] = H - DO
            kq["ghi_chu"].append("không đủ chỗ đố ngang trên cửa đi: bỏ, cửa cao %s" % so(H - DO))
        else:
            kq["di_tren"] = hd
            kq["ngang"].append((hd + NUA, "D"))
    if co_so or (co_ngang and not co_di):
        if san is None or san < 0:
            return None, "Nhập chiều dày sàn hoàn thiện (0 nếu không có)"
        if bau is None or bau <= 0:
            return None, "Nhập cao bậu cửa sổ"
        y1 = san + bau
        if co_ngang:
            if hs is None or hs <= 0:
                return None, "Nhập chiều cao cửa sổ (hoặc bỏ chọn thanh ngang)"
            yt = y1 + hs
            if yt + DO > H - DO + 1e-6:
                if co_so:
                    return None, ("Thanh ngang chạm khung trên: sàn + bậu + cửa sổ + 65 = %s > %s "
                                  "(bỏ thanh ngang hoặc giảm số đo)" % (so(yt + DO), so(H - DO)))
                kq["ghi_chu"].append("vách thấp: không đặt thanh ngang cửa sổ")
            else:
                kq["ngang"].append((yt + NUA, "S"))
        else:
            yt = H - DO
        if co_so:
            if yt - y1 <= 0:
                return None, "Vách thấp quá: sàn + bậu = %s >= mép dưới khung trên %s" % (so(y1), so(H - DO))
            if y1 - DO < DO - 1e-6:
                return None, "Đố dưới cửa sổ chạm khung dưới: sàn + bậu phải >= %s" % so(2 * DO)
            kq["so"] = (y1, yt)
            kq["duoi"] = y1 - NUA
    # 2 đố ngang suốt chồng nhau
    z = sorted(kq["ngang"])
    for i in range(1, len(z)):
        if z[i][0] - z[i - 1][0] < DO - 1e-6:
            return None, "Đố ngang cửa đi (%s) và thanh ngang cửa sổ (%s) chồng nhau" % (
                so(z[i - 1][0] - NUA), so(z[i][0] - NUA))
    kq["ngang"] = z
    return kq, None


# ---------------------------------------------------------------- dữ liệu lưu trong vách
def _schema():
    s = Schema.Lookup(SCHEMA_GUID)
    if s is not None:
        return s
    sb = SchemaBuilder(SCHEMA_GUID)
    sb.SetSchemaName("ARV_VachKinh")
    sb.SetReadAccessLevel(AccessLevel.Public)
    sb.SetWriteAccessLevel(AccessLevel.Public)
    sb.SetDocumentation("Thông số vách kính ARV (chia đố theo quy tắc VK)")
    sb.AddSimpleField("DuLieu", String)
    return sb.Finish()


def doc_du_lieu(wall):
    s = Schema.Lookup(SCHEMA_GUID)
    if s is None:
        return None
    try:
        ent = wall.GetEntity(s)
        if ent is None or not ent.IsValid():
            return None
        return json.loads(ent.Get[String]("DuLieu"))
    except Exception:
        return None


def ghi_du_lieu(wall, d):
    s = _schema()
    ent = Entity(s)
    ent.Set[String]("DuLieu", json.dumps(d, ensure_ascii=False))
    wall.SetEntity(ent)


# ---------------------------------------------------------------- kiểu đố / vách / family
def _ten(e):
    # IronPython (pyRevit): .Name của ElementType (FamilySymbol, PanelType, ...) báo lỗi -> đọc qua Element.Name.
    # Không lồng try trong except: IronPython 2.7 trên .NET 10 lỗi biên dịch (InvalidCastException, Revit thoát).
    try:
        return e.Name
    except Exception:
        pass
    try:
        return DB.Element.Name.GetValue(e)
    except Exception:
        return ""


def _tim(doc, cls, ten):
    for x in DB.FilteredElementCollector(doc).OfClass(cls):
        if _ten(x) == ten:
            return x
    return None


def _dat(e, bip_ten, v):
    """Đặt tham số theo tên BuiltInParameter (bỏ qua nếu không có)."""
    bip = getattr(DB.BuiltInParameter, bip_ten, None)
    if bip is None:
        return False
    prm = e.get_Parameter(bip)
    if prm is None or prm.IsReadOnly:
        return False
    prm.Set(v)
    return True


def _so_nguyen(e, bip_ten):
    prm = e.get_Parameter(getattr(DB.BuiltInParameter, bip_ten))
    return prm.AsInteger() if prm is not None else None


def _id(e, bip_ten):
    prm = e.get_Parameter(getattr(DB.BuiltInParameter, bip_ten))
    return prm.AsElementId() if prm is not None else DB.ElementId.InvalidElementId


def _kieu_do(doc, ten, w1, w2, bao):
    """Kiểu đố chữ nhật profile hệ thống, đặt giữa mặt kính. Có rồi thì dùng nguyên (không sửa phần người dùng chỉnh)."""
    t = _tim(doc, DB.MullionType, ten)
    if t is not None:
        return t
    goc = None
    for m in DB.FilteredElementCollector(doc).OfClass(DB.MullionType):
        if m.get_Parameter(DB.BuiltInParameter.RECT_MULLION_THICK) is not None:
            goc = m
            if _ten(m) == "65 x 150mm":
                break
    if goc is None:
        raise Exception("Mô hình không có kiểu đố chữ nhật (Rectangular Mullion) để nhân bản")
    t = goc.Duplicate(ten)
    _dat(t, "RECT_MULLION_WIDTH1", ft(w1))
    _dat(t, "RECT_MULLION_WIDTH2", ft(w2))
    _dat(t, "RECT_MULLION_THICK", ft(SAU_DO))
    _dat(t, "MULLION_OFFSET", 0.0)
    nhom = _tim(doc, DB.MullionType, "Đố nổi-65x150mm")
    if nhom is not None:
        _dat(t, "MATERIAL_ID_PARAM", _id(nhom, "MATERIAL_ID_PARAM"))
    bao.append("tạo kiểu đố \"%s\"" % ten)
    return t


def _panel_kinh(doc, goc):
    pid = _id(goc, "AUTO_PANEL_WALL")
    if pid.Value > 0:
        return pid
    ds = list(DB.FilteredElementCollector(doc).OfClass(DB.PanelType))
    for k in ("12mm", "Glazed", "kính"):
        for t in ds:
            if k.lower() in _ten(t).lower():
                return t.Id
    raise Exception("Mô hình không có kiểu panel kính (System Panel)")


def _kieu_vach(doc, ten, do_id, b1_id, bao):
    t = _tim(doc, DB.WallType, ten)
    if t is None:
        goc = _tim(doc, DB.WallType, "Vách kính đố nổi")
        if goc is None:
            for x in DB.FilteredElementCollector(doc).OfClass(DB.WallType):
                if x.Kind == DB.WallKind.Curtain:
                    goc = x
                    break
        if goc is None:
            raise Exception("Mô hình không có kiểu tường Curtain Wall để nhân bản")
        pk = _panel_kinh(doc, goc)
        t = goc.Duplicate(ten)
        for k in ("AUTO_MULLION_INTERIOR_VERT", "AUTO_MULLION_BORDER2_VERT", "AUTO_MULLION_INTERIOR_HORIZ",
                  "AUTO_MULLION_BORDER1_HORIZ", "AUTO_MULLION_BORDER2_HORIZ"):
            _dat(t, k, do_id)
        _dat(t, "AUTO_MULLION_BORDER1_VERT", b1_id)
        _dat(t, "AUTO_PANEL_WALL", pk)
        _dat(t, "AUTO_JOIN_CONDITION_WALL", 1)       # Vertical Grid Continuous: đố đứng chạy suốt
        _dat(t, "CURTAINGRID_ADJUST_BORDER_VERT", 0)
        _dat(t, "CURTAINGRID_ADJUST_BORDER_HORIZ", 0)
        bao.append("tạo kiểu vách \"%s\"" % ten)
    # lưới phải do công cụ đặt (Layout = None), không thì Revit tự chèn lưới
    for k in ("SPACING_LAYOUT_VERT", "SPACING_LAYOUT_HORIZ"):
        if _so_nguyen(t, k) != 0:
            _dat(t, k, 0)
    return t


def _symbol(doc, fam, bao, bat_buoc=True):
    for s in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol):
        if s.FamilyName == fam:
            if not s.IsActive:
                s.Activate()
            return s
    p = os.path.join(THU_MUC_FAMILY, fam + ".rfa")
    if os.path.isfile(p):
        doc.LoadFamily(p)
        for s in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol):
            if s.FamilyName == fam:
                if not s.IsActive:
                    s.Activate()
                bao.append("nạp family \"%s\"" % fam)
                return s
    if bat_buoc:
        raise Exception("Không có family \"%s\" (mô hình chưa nạp, không thấy %s)" % (fam, p))
    return None


def dam_bao_kieu(doc, bao=None):
    """Tạo / tìm mọi kiểu cần dùng. Gọi TRONG transaction. Trả dict id."""
    bao = bao if bao is not None else []
    do = _kieu_do(doc, TEN_DO, NUA, NUA, bao)
    dg = _kieu_do(doc, TEN_DO_GOC, NUA_GOC, NUA_GOC, bao)
    k = {
        "do": do.Id, "do_goc": dg.Id,
        "thuong": _kieu_vach(doc, TEN_VACH, do.Id, do.Id, bao).Id,
        "A": _kieu_vach(doc, TEN_VACH_GOC_DO, do.Id, dg.Id, bao).Id,
        "B": _kieu_vach(doc, TEN_VACH_GOC_KINH, do.Id, DB.ElementId.InvalidElementId, bao).Id,
        "cua_di": _symbol(doc, FAM_CUA_DI, bao).Id,
        "cua_so": _symbol(doc, FAM_CUA_SO, bao).Id,
    }
    kg = _symbol(doc, FAM_KINH_GOC, bao, bat_buoc=False)
    k["kinh_goc"] = kg.Id if kg is not None else None
    if kg is None:
        bao.append("thiếu family kính góc \"%s\": ô góc dùng kính thường" % FAM_KINH_GOC)
    k["kinh"] = _id(doc.GetElement(k["thuong"]), "AUTO_PANEL_WALL")
    return k


def tim_kieu(doc):
    """Như dam_bao_kieu nhưng chỉ tìm (dùng trong updater: không tạo gì)."""
    def i(cls, ten):
        e = _tim(doc, cls, ten)
        return e.Id if e is not None else None

    def s(fam):
        for x in DB.FilteredElementCollector(doc).OfClass(DB.FamilySymbol):
            if x.FamilyName == fam:
                return x.Id
        return None
    k = {"do": i(DB.MullionType, TEN_DO), "do_goc": i(DB.MullionType, TEN_DO_GOC), "thuong": i(DB.WallType, TEN_VACH),
         "cua_di": s(FAM_CUA_DI), "cua_so": s(FAM_CUA_SO), "kinh_goc": s(FAM_KINH_GOC)}
    k["kinh"] = _id(doc.GetElement(k["thuong"]), "AUTO_PANEL_WALL") if k["thuong"] else None
    return k


# ---------------------------------------------------------------- tên vách (Mark)
def ten_dang_dung(doc):
    kq = set()
    for w in DB.FilteredElementCollector(doc).OfClass(DB.Wall):
        prm = w.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
        if prm is not None and prm.AsString():
            kq.add(prm.AsString())
    return kq


def tien_to_tang(level):
    """"Tầng 2" -> "T2-"; tên tầng không có số -> ""."""
    so_tang = "".join(c for c in (_ten(level) or "") if c.isdigit())
    return ("T%s-" % so_tang) if so_tang else ""


def ten_tu_dat(dang_dung, tien_to, so_luong=1):
    """Tên kế tiếp số lớn nhất đang có: <T1->VK.<nn>."""
    goc = tien_to + "VK."
    lon = 0
    for t in dang_dung:
        if t.startswith(goc) and t[len(goc):].isdigit():
            lon = max(lon, int(t[len(goc):]))
    return [goc + "%02d" % (lon + i + 1) for i in range(so_luong)]


def ten_khong_trung(ten, dang_dung):
    if ten not in dang_dung:
        return ten
    i = 2
    while "%s (%d)" % (ten, i) in dang_dung:
        i += 1
    return "%s (%d)" % (ten, i)


# ---------------------------------------------------------------- dựng lưới / panel cho 1 vách
def _chieu_cao(wall):
    prm = wall.get_Parameter(DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM)
    return mm(prm.AsDouble())


def _truc(wall):
    c = wall.Location.Curve
    a = c.GetEndPoint(0)
    d = (c.GetEndPoint(1) - a).Normalize()
    off = wall.get_Parameter(DB.BuiltInParameter.WALL_BASE_OFFSET)
    z0 = a.Z + (off.AsDouble() if off is not None else 0.0)
    return a, d, mm(c.Length), z0


def _xoa(doc, ids):
    lst = NetList[DB.ElementId]()
    for i in ids:
        e = doc.GetElement(i)
        if e is None:
            continue
        if e.Pinned:
            e.Pinned = False
        lst.Add(i)
    if lst.Count:
        doc.Delete(lst)


def _o_cua(x, tam):
    """Chỉ số ô (0..) chứa vị trí x (mm từ đầu vách)."""
    for i in range(len(tam) - 1):
        if x < tam[i + 1]:
            return i
    return len(tam) - 2


def dung_luoi(doc, wall, d, k, bao=None):
    """(Dựng lại) lưới, đố, panel của vách theo dữ liệu d. KHÔNG mở transaction (gọi trong transaction / updater).
    d: {"vai_tro": "thuong"/"A"/"B", "dau", "o": [(loại, rộng)], "cao": kq tinh_cao, "lat": bool}"""
    bao = bao if bao is not None else []
    g = wall.CurtainGrid
    # 1) bỏ toàn bộ lưới cũ (vách kiểu Layout None: mọi lưới đều do công cụ đặt)
    cu = list(g.GetUGridLineIds()) + list(g.GetVGridLineIds())
    if cu:
        _xoa(doc, cu)
        doc.Regenerate()
    a, dvec, L, z0 = _truc(wall)
    H = _chieu_cao(wall)
    o = d["o"]
    tam = [d["dau"]]
    for loai, r in o:
        tam.append(tam[-1] + r)
    cao = d["cao"]
    zg = ft(H / 2.0)

    def diem(x, z):
        return a + dvec * ft(x) + DB.XYZ(0, 0, z0 - a.Z + ft(z))

    # 2) đố đứng
    for x in tam[1:-1]:
        g.AddGridLine(False, diem(x, H / 2.0), False)
    doc.Regenerate()
    # 3) đố ngang suốt vách; bỏ đoạn cắt qua cửa (đố ngang không cắt cửa đi / cửa sổ)
    for zc, nguon in cao["ngang"]:
        gl = g.AddGridLine(True, diem(tam[0] + 1.0, zc), False)
        doc.Regenerate()
        bo = []
        for c in gl.AllSegmentCurves:
            m = (c.GetEndPoint(0) + c.GetEndPoint(1)) * 0.5
            i = _o_cua(mm((m - a).DotProduct(dvec)), tam)
            loai = o[i][0]
            if loai == "D" and cao["di_tren"] is not None and zc - NUA < cao["di_tren"] - 1e-6:
                bo.append(c)
            elif loai == "S" and cao["so"] is not None and cao["so"][0] - 1e-6 < zc < cao["so"][1] + DO - 1e-6 \
                    and nguon != "S":
                bo.append(c)
        for c in bo:
            gl.RemoveSegment(c)
        if bo:
            doc.Regenerate()
    # 4) đố dưới cửa sổ: 1 đoạn trong từng ô cửa sổ
    if cao["so"] is not None:
        for i, (loai, r) in enumerate(o):
            if loai == "S":
                g.AddGridLine(True, diem((tam[i] + tam[i + 1]) / 2.0, cao["duoi"]), True)
        doc.Regenerate()
    # 5) panel: cửa đi / cửa sổ / kính góc / kính
    dem = {"D": 0, "S": 0, "G": 0}
    for pid in list(g.GetPanelIds()):
        e = doc.GetElement(pid)
        bb = e.get_BoundingBox(None) if e is not None else None
        if bb is None:
            continue
        m = (bb.Min + bb.Max) * 0.5
        x = mm((m - a).DotProduct(dvec))
        z = mm(m.Z - z0)
        i = _o_cua(x, tam)
        loai = o[i][0]
        moi = k["kinh"]
        if loai == "D" and cao["di_tren"] is not None and z < cao["di_tren"]:
            moi, dem["D"] = k["cua_di"], dem["D"] + 1
        elif loai == "S" and cao["so"] is not None and cao["so"][0] < z < cao["so"][1]:
            moi, dem["S"] = k["cua_so"], dem["S"] + 1
        elif loai == "K" and i == 0 and d["vai_tro"] == "B" and k.get("kinh_goc"):
            moi, dem["G"] = k["kinh_goc"], dem["G"] + 1
        if moi is not None and e.GetTypeId() != moi:
            if e.Pinned:
                e.Pinned = False
            e.ChangeTypeId(moi)
    doc.Regenerate()
    # 6) ô cửa đi không có khung dưới; lật cửa
    bo = []
    for mid in g.GetMullionIds():
        mu = doc.GetElement(mid)
        bb = mu.get_BoundingBox(None)
        if bb is None or mm(bb.Max.Z - z0) > DO + 5:
            continue
        x = mm(((bb.Min + bb.Max) * 0.5 - a).DotProduct(dvec))
        if o[_o_cua(x, tam)][0] == "D" and mm(bb.Max.Z - bb.Min.Z) < DO + 5:
            bo.append(mid)
    if bo:
        _xoa(doc, bo)
    if d.get("lat"):
        for pid in g.GetPanelIds():
            e = doc.GetElement(pid)
            if e is not None and e.GetTypeId() in (k["cua_di"], k["cua_so"]):
                try:
                    if e.CanFlipFacing:
                        e.flipFacing()
                except Exception:
                    pass
    doc.Regenerate()
    return dem


# ---------------------------------------------------------------- dựng vách mới
def _du_lieu(cfg, canh, vai_tro, dau, kq, cao, L, H):
    return {"v": 1, "vai_tro": vai_tro, "dau": dau, "L": L, "H": H,
            "o": [[l, r] for l, r in kq["o"]], "vs": vi_tri(kq, "S"), "vd": vi_tri(kq, "D"),
            "ns": len(vi_tri(kq, "S")), "nd": len(vi_tri(kq, "D")),
            "ws": cfg["ws"], "wd": cfg["wd"], "hd": cfg["hd"], "hs": cfg["hs"], "co_ngang": cfg["co_ngang"],
            "san": cfg["san"], "bau": cfg["bau"], "lat": cfg.get("lat", False), "cao": cao,
            "ten": canh["ten"], "doi_tac": None}


def tao_vach(doc, level, cfg, diem, bao=None):
    """Dựng vách theo cfg (bảng nhập) và điểm pick. GỌI TRONG transaction.
    cfg: {"H", "ws", "wd", "hd", "hs", "co_ngang", "san", "bau", "lat", "goc": bool,
          "canh": [{"ten", "L", "ns", "nd", "vs", "vd"}, ...]}  (1 cánh, hoặc 2 cánh khi vách góc)
    diem: thẳng [P1, P2]; góc [P1 (đầu cánh 1), C (góc ngoài), P2 (đầu cánh 2)] – XYZ (feet).
    Trả danh sách vách đã dựng."""
    bao = bao if bao is not None else []
    k = dam_bao_kieu(doc, bao)
    z = level.Elevation
    pts = [DB.XYZ(p.X, p.Y, z) for p in diem]
    H = cfg["H"]
    if not cfg.get("goc"):
        d = (pts[1] - pts[0]).Normalize()
        ds = [(pts[0], d, "thuong", NUA, cfg["canh"][0])]
    else:
        C = pts[1]
        dA = (pts[0] - C).Normalize()
        dB = (pts[2] - C).Normalize()
        if abs(dA.DotProduct(dB)) > 1e-3:
            raise Exception("Hai cánh vách không vuông góc (lệch %.2f°)" %
                            abs(90.0 - math.degrees(math.acos(max(-1.0, min(1.0, dA.DotProduct(dB)))))))
        # mặt kính lùi vào trong góc nửa đố góc (75) so với mép ngoài
        ds = [(C + dB * ft(NUA_GOC), dA, "A", NUA_GOC, cfg["canh"][0]),
              (C + dA * ft(NUA_GOC), dB, "B", NUA_GOC, cfg["canh"][1])]
    co_di = any(c["nd"] > 0 for c in cfg["canh"])
    co_so = any(c["ns"] > 0 for c in cfg["canh"])
    cao, loi = tinh_cao(H, co_di, cfg["hd"], co_so, cfg["hs"], cfg["co_ngang"], cfg["san"], cfg["bau"])
    if loi:
        raise Exception(loi)
    vach = []
    dang_dung = ten_dang_dung(doc)
    trong = [c for _, _, _, _, c in ds if not (c.get("ten") or "").strip()]
    for c, t in zip(trong, ten_tu_dat(dang_dung, tien_to_tang(level), len(trong))):
        c["ten"] = t
    for goc0, d, vai_tro, dau, canh in ds:
        kq, loi = chia(canh["L"], canh["ns"], cfg["ws"], canh["nd"], cfg["wd"], canh["vs"], canh["vd"], dau)
        if loi:
            raise Exception(loi)
        if vai_tro == "B" and kq["o"][0][0] != "K":
            raise Exception("Cánh 2: ô sát góc là kính góc, không đặt cửa vào ô 1 (Cần xác nhận lại cách làm)")
        # 2 cánh vách góc dùng chung đố ngang (thẳng hàng quanh góc); đố dưới cửa sổ chỉ nằm trong ô cửa sổ
        kieu = k["thuong"] if vai_tro == "thuong" else k[vai_tro]
        w = DB.Wall.Create(doc, DB.Line.CreateBound(goc0, goc0 + d * ft(canh["L"])), kieu, level.Id, ft(H), 0.0,
                           False, False)
        DB.WallUtils.DisallowWallJoinAtEnd(w, 0)
        DB.WallUtils.DisallowWallJoinAtEnd(w, 1)
        doc.Regenerate()
        if vai_tro == "B" and (dA.CrossProduct(dB)).Z < 0:
            w.Flip()            # kính góc dời kính ngược hướng mặt vách: giữ kính góc ra phía ngoài góc
            doc.Regenerate()
        ten = ten_khong_trung(canh["ten"], dang_dung)
        dang_dung.add(ten)
        w.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).Set(ten)
        du = _du_lieu(cfg, dict(canh, ten=ten), vai_tro, dau, kq, cao, canh["L"], H)
        du["co_di"], du["co_so"] = co_di, co_so
        dem = dung_luoi(doc, w, du, k, bao)
        ghi_du_lieu(w, du)
        bao.append("%s: dài %s, cao %s | %s | cửa đi %d, cửa sổ %d%s" % (
            ten, so(canh["L"]), so(H), chuoi_o(kq), dem["D"], dem["S"], ", kính góc" if dem["G"] else ""))
        vach.append(w)
    if len(vach) == 2:
        for w, w2 in ((vach[0], vach[1]), (vach[1], vach[0])):
            du = doc_du_lieu(w)
            du["doi_tac"] = int(w2.Id.Value)     # IronPython: Int64 -> long, json không ghi được
            ghi_du_lieu(w, du)
    for x in cao["ghi_chu"]:
        bao.append("Ghi chú: " + x)
    return vach


def chuoi_o(kq):
    t = {"S": "SO ", "D": "DI ", "K": ""}
    return " | ".join(t[l] + so(r) for l, r in kq["o"])


# ---------------------------------------------------------------- chia lại khi vách đổi chiều dài / chiều cao
def cap_nhat_vach(doc, wall, k=None, bao=None):
    """Vách có dữ liệu ARV đổi chiều dài / chiều cao -> chia lại (giữ ô cửa nếu còn hợp, không thì tự đặt);
    cửa không vừa -> trả vách về chiều dài cũ. Không mở transaction. Trả True nếu đã dựng lại."""
    bao = bao if bao is not None else []
    d = doc_du_lieu(wall)
    if not d:
        return False
    try:
        a, dvec, L, z0 = _truc(wall)
        H = _chieu_cao(wall)
    except Exception:
        return False
    if abs(L - d["L"]) < 0.5 and abs(H - d["H"]) < 0.5:
        return False
    k = k or tim_kieu(doc)
    if not k.get("kinh") or not k.get("cua_di"):
        return False
    ns, nd = d["ns"], d["nd"]
    kq, loi = chia(L, ns, d["ws"], nd, d["wd"], d["vs"], d["vd"], d["dau"])
    if loi:
        kq, loi = chia(L, ns, d["ws"], nd, d["wd"], [], [], d["dau"])
    cao, loi2 = tinh_cao(H, d.get("co_di", nd > 0), d["hd"], d.get("co_so", ns > 0), d["hs"], d["co_ngang"],
                         d["san"], d["bau"])
    if loi or loi2 or (d["vai_tro"] == "B" and kq["o"][0][0] != "K"):
        # không chia được: trả chiều dài / chiều cao cũ
        wall.Location.Curve = DB.Line.CreateBound(a, a + dvec * ft(d["L"]))
        wall.get_Parameter(DB.BuiltInParameter.WALL_USER_HEIGHT_PARAM).Set(ft(d["H"]))
        bao.append("%s: %s -> giữ kích thước cũ" % (d.get("ten"), loi or loi2 or "ô góc thành cửa"))
        return False
    d.update({"L": L, "H": H, "o": [[l, r] for l, r in kq["o"]], "vs": vi_tri(kq, "S"), "vd": vi_tri(kq, "D"),
              "cao": cao})
    dung_luoi(doc, wall, d, k, bao)
    ghi_du_lieu(wall, d)
    bao.append("%s: chia lại dài %s cao %s | %s" % (d.get("ten"), so(L), so(H), chuoi_o(kq)))
    return True
