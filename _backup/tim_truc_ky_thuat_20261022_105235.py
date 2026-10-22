# -*- coding: utf-8 -*-
"""Tìm trục kỹ thuật / hộp kỹ thuật (HKT) cần hatch ngăn cháy lan trên mặt bằng tầng (DXF).

Nhận diện: mỗi trục/hộp có DẤU X (2 nét chéo nối 4 góc ô chữ nhật) trên các layer
A-Wall-Open, A-Material, A-Truc ME, A-Hidden (đổi bằng --layer-x). Ô X chạm nhau được gộp
thành một vùng (vd. hộp chữ L). Loại trừ: dấu X trong block cabin thang máy (tên block
khớp --block-thang-may) và đồ nội thất (layer khác danh sách trên, vd. máy rửa bát).
Vùng đã có hatch NET (layer A-Material, hoặc A-HATCH- Color của bản vẽ cũ) được đánh dấu "da_co" để không vẽ trùng.

Đầu ra (trong --out-dir): <tên>_vung.json (cho ve_hatch_vao_ban_sao.ps1), <tên>_vung.xlsx,
<tên>_vung.png (ảnh xem lại: xanh = sẽ hatch, xám = đã có, đỏ = loại).

Ví dụ:
  python tim_truc_ky_thuat.py "D:\\AI\\_tmp\\x\\MB tang 4.dxf" --out-dir "D:\\AI\\<du an>\\05_NganChay"
"""
import argparse
import fnmatch
import json
import math
import os
import re
import sys
import unicodedata

import ezdxf
from ezdxf import bbox as ezbbox
from ezdxf import path as ezpath
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

LAYER_X = ["A-Wall-Open", "A-Material", "A-Truc*", "A-Hidden", "A-Mep"]
# Khi dò mọi layer (--layer-x "*"): bỏ các layer chắc chắn không phải trục
LAYER_BO = ["A-Interior*", "A-Noi that*", "*Furn*", "A-Door*", "A-Cua*", "A-Window*", "A-Glaz*", "A-Dim*", "A-Text*",
            "A-Symbol*", "A-Ki hieu*", "A-axis", "Defpoints", "*Xref*|*"]
BLOCK_THANG_MAY = ["*cabin*", "*thang may*", "*thangmay*", "*elevator*", "*lift*"]
# Đồ nội thất / thiết bị hay vẽ dấu X (máy giặt, máy rửa bát…)
BLOCK_NOI_THAT = ["*may giat*", "*maygiat*", "*may rua*", "*tu lanh*", "*tulanh*", "*mb-bep*", "*sink*",
                  "*lavabo*", "*bon tam*", "*bontam*", "*giuong*", "*sofa*", "*tivi*", "*louver*",
                  # nét khuất của tầng khác lồng trong block lõi (vd. "CT1 - T3 - Loi Thang/…/Tang ham")
                  "*tang ham*", "*tangham*", "*basement*"]
# Ký hiệu ống đứng trên mặt bằng (ống tròn + cùm chữ U), thư viện MEP: piped125-xi, PIPE150
BLOCK_ONG = ["*pipe*"]
# Block lỗ mở sàn kiến trúc: chỉ là trục khi bên trong có ống đứng (không thì là lỗ mở / phễu thu, không hatch)
BLOCK_LO_MO = ["*lo mo*", "*lomo*"]
# Khung lỗ mở của MEP (vd. "AV-P-LO MO"): có ống đứng bên trong là hộp kỹ thuật dù không vẽ dấu X
LAYER_KHUNG_ONG = ["*lo mo*"]
# Người dùng chốt 22/10/2026: bo + hatch ngăn cháy lan luôn trên A-Material. "A-HATCH- Color" chỉ để nhận
# hatch có sẵn trong bản vẽ cũ (bản mẫu Tháp B), không vẽ mới lên layer này.
LAYER_HATCH = "A-Material"
LAYER_HATCH_CU = ["A-Material", "A-HATCH- Color"]
PATTERN = "NET"
CANH_MIN = 150      # mm, cạnh ô X nhỏ nhất
CANH_MAX = 4000     # mm, cạnh ô X lớn nhất (lớn hơn thì là thông tầng / sảnh, không phải trục)
DUNG_SAI = 40       # mm, sai số khi so 2 nét chéo cùng một ô
GOC_MIN = 3         # độ, nét chéo của trục dẹt (vd. 3000 × 350 ≈ 6.6°) vẫn phải nhận; ghép cặp 2 nét cùng khung
                    # nên nét gần ngang lẻ loi (bậc thang, mũi tên) không thành ô X


def lam_phang(entities, depth=0, eff=None, path=""):
    """Duyệt đệ quy block; layer "0" trong block lấy theo layer của INSERT (layer hiệu lực)."""
    for e in entities:
        lay = e.dxf.get("layer", "0")
        el = eff if (lay == "0" and eff) else lay
        if e.dxftype() == "INSERT" and depth < 8:
            try:
                yield from lam_phang(e.virtual_entities(), depth + 1, el, path + "/" + e.dxf.name)
            except Exception:
                pass
        else:
            yield e, el, path


def chuan(ten):
    """Tên layer chuẩn hoá để so: bỏ tiền tố xref đã bind ("CH19$0$A_MEP" → "A_MEP"), bỏ dấu tiếng Việt,
    coi "_" như "-", bỏ dấu cách, chữ thường ("A- Truc ME" = "A-Truc ME", "A-Nội thất" = "A-Noi that")."""
    ten = re.sub(r"^.*\$\d+\$", "", ten).replace("đ", "d").replace("Đ", "D")
    ten = "".join(c for c in unicodedata.normalize("NFD", ten) if unicodedata.category(c) != "Mn")
    return ten.replace("_", "-").replace(" ", "").lower()


def khop(ten, mau):
    t = ten.lower()
    return any(fnmatch.fnmatch(t, m.lower()) for m in mau)


def khop_layer(ten, mau):
    t = chuan(ten)
    return any(fnmatch.fnmatch(t, chuan(m)) for m in mau)


def cac_doan(e):
    """Đoạn thẳng trong hệ WCS (LWPOLYLINE phải đổi từ OCS, block lật gương có extrusion -Z)."""
    t = e.dxftype()
    if t == "LINE":
        s, d = e.dxf.start, e.dxf.end
        return [((s.x, s.y), (d.x, d.y))]
    if t == "LWPOLYLINE":
        pts = [(v.x, v.y) for v in e.vertices_in_wcs()]
        if e.closed and pts:
            pts.append(pts[0])
        return list(zip(pts, pts[1:]))
    if t == "POLYLINE" and not e.is_3d_polyline:
        pts = [(v.x, v.y) for v in e.points_in_wcs()] if hasattr(e, "points_in_wcs") else []
        return list(zip(pts, pts[1:]))
    return []


def doc_ban_ve(dxf_path, layer_x, block_tm, layer_bo=(), block_bo=(), block_ong=(), layer_khung=()):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()
    cheo, cabin, chu, hatch_co, nen, ong, khung = [], [], [], [], [], [], []
    for e, el, path in lam_phang(msp):
        t = e.dxftype()
        # xref lồng đã bind giữ tên gốc trong tiền tố layer ("…$0$Tang ham$0$A-Hidden") nên so cả layer
        if block_bo and (khop(path, block_bo) or khop(el, block_bo)):
            continue
        cuoi = path.rsplit("/", 1)[-1]
        if block_ong and khop(cuoi, block_ong):
            if t == "CIRCLE" and 25 <= e.dxf.radius <= 160:
                c = e.ocs().to_wcs(e.dxf.center)
                ong.append((c.x, c.y))
            continue  # nét bên trong ký hiệu ống không phải dấu X / khung
        if layer_khung and t == "LWPOLYLINE" and e.closed and len(e) >= 4 and khop_layer(el, layer_khung):
            pts = [(v.x, v.y) for v in e.vertices_in_wcs()]
            khung.append(dict(hinh=Polygon(pts).buffer(0), layer=el, path=path))
        if block_tm and khop(path, block_tm):
            try:
                b = ezbbox.extents([e])
                if b.has_data:
                    cabin.append(box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
            except Exception:
                pass
            continue
        if t in ("TEXT", "MTEXT"):
            try:
                txt = e.plain_text() if t == "MTEXT" else e.dxf.text
                p = e.dxf.insert
                chu.append((p.x, p.y, txt.strip()))
            except Exception:
                pass
            continue
        if t == "HATCH":
            if chuan(el) in {chuan(l) for l in LAYER_HATCH_CU} and e.dxf.pattern_name.upper() == PATTERN:
                for p in ezpath.from_hatch(e):
                    try:
                        pts = [(v.x, v.y) for v in p.flattening(10)]
                        if len(pts) >= 3:
                            hatch_co.append(Polygon(pts).buffer(0))
                    except Exception:
                        pass
            continue
        if t in ("LINE", "LWPOLYLINE", "POLYLINE"):
            doan = cac_doan(e)
            if chuan(el).startswith("a-wall") or chuan(el) in ("a-trucme", "a-column"):
                nen.extend(doan)
            if not khop_layer(el, layer_x) or khop_layer(el, layer_bo):
                continue
            if path == "" and chuan(el) == "a-material":
                continue  # polyline biên do skill (hoặc người vẽ) tạo, không phải dấu X
            for a, b in doan:
                dx, dy = b[0] - a[0], b[1] - a[1]
                if math.hypot(dx, dy) < CANH_MIN:
                    continue
                goc = math.degrees(math.atan2(abs(dy), abs(dx)))
                if GOC_MIN < goc < 90 - GOC_MIN:
                    cheo.append((a, b, el, path))
    return cheo, cabin, chu, hatch_co, nen, gom_ong(ong), khung


def gom_ong(tam):
    """Mỗi ký hiệu ống có 2 – 3 vòng tròn gần đồng tâm: gom thành một điểm tâm ống."""
    kq = []
    for x, y in tam:
        if not any(math.hypot(x - a, y - b) < 60 for a, b in kq):
            kq.append((x, y))
    return [Point(p) for p in kq]


def ghep_dau_x(cheo):
    """Ghép 2 nét chéo ngược hướng có cùng khung chữ nhật thành một ô X."""
    def khung(s):
        (x1, y1), (x2, y2) = s[0], s[1]
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    luoi = {}
    for i, s in enumerate(cheo):
        k = khung(s)
        luoi.setdefault((round(k[0] / 50), round(k[1] / 50)), []).append(i)
    o_x = []
    for i, s in enumerate(cheo):
        k = khung(s)
        w, h = k[2] - k[0], k[3] - k[1]
        if not (CANH_MIN <= w <= CANH_MAX and CANH_MIN <= h <= CANH_MAX):
            continue
        huong = (s[1][1] - s[0][1]) * (s[1][0] - s[0][0])
        gx, gy = round(k[0] / 50), round(k[1] / 50)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                for j in luoi.get((gx + ox, gy + oy), []):
                    if j <= i:
                        continue
                    t = cheo[j]
                    k2 = khung(t)
                    if all(abs(a - b) < DUNG_SAI for a, b in zip(k, k2)):
                        if huong * (t[1][1] - t[0][1]) * (t[1][0] - t[0][0]) < 0:
                            o_x.append(dict(khung=k, layer=s[2], path=s[3]))
    # bỏ ô trùng (cùng một dấu X vẽ chồng nhiều nét)
    kq = []
    for o in o_x:
        if not any(all(abs(a - b) < 60 for a, b in zip(o["khung"], q["khung"])) for q in kq):
            kq.append(o)
    return kq


def gop_vung(o_x):
    """Ô X chạm nhau (chung cạnh) gộp thành một vùng; ô cách nhau bởi tường thì giữ riêng."""
    hinh = [box(*o["khung"]) for o in o_x]
    hop = unary_union([h.buffer(5, join_style=2) for h in hinh])
    gs = list(hop.geoms) if hasattr(hop, "geoms") else [hop]
    vung = []
    for g in gs:
        g = g.buffer(-5, join_style=2).simplify(1)
        if g.is_empty:
            continue
        if g.geom_type != "Polygon":
            g = max(g.geoms, key=lambda x: x.area)
        thanh_phan = [o for o, h in zip(o_x, hinh) if h.intersects(g)]
        vung.append((Polygon(g.exterior.coords), thanh_phan))
    return vung


def dung_vung(o_x, ong, khung, block_lo_mo):
    """Dựng vùng hatch từ 3 nguồn, trả list dict(g, tp, kieu, tt, ghi):
    1. Ô X của trục / hộp (không phải block lỗ mở): gộp các ô chạm nhau (hộp chữ L).
    2. Ô X của block lỗ mở sàn: bỏ nếu chồng lên vùng (1) (X lệch của cùng hộp làm méo đường bo);
       còn lại chỉ nhận khi bên trong có ống đứng, không có thì đánh "loai".
    3. Khung kín layer lỗ mở MEP có ống đứng bên trong, chưa thuộc vùng nào: hộp kỹ thuật không vẽ X."""
    def so_ong(g):
        v = g.buffer(20)
        return sum(1 for p in ong if v.contains(p))

    def chong(g, ds, ti_le=0.05):
        return any(g.intersection(v["g"]).area > ti_le * min(g.area, v["g"].area) for v in ds)

    truc = [o for o in o_x if not khop(o["path"], block_lo_mo)]
    lo_mo = [o for o in o_x if khop(o["path"], block_lo_mo)]
    vung = [dict(g=g, tp=tp, kieu="Dấu X trục / hộp", tt=None, ghi="") for g, tp in gop_vung(truc)]
    loai = []
    for o in lo_mo:
        g = box(*o["khung"])
        if chong(g, vung):
            continue
        if so_ong(g):
            vung.append(dict(g=g, tp=[o], kieu="Lỗ mở có ống đứng", tt=None, ghi=""))
        elif not chong(g, loai, 0.5):
            loai.append(dict(g=g, tp=[o], kieu="Lỗ mở sàn", tt="loai",
                             ghi="Lỗ mở sàn không có ống đứng (block lỗ mở, không phải trục)"))
    for k in sorted(khung, key=lambda k: k["hinh"].area):
        g = k["hinh"]
        if g.is_empty or g.area < 1e4 or chong(g, vung, 0.2) or not so_ong(g):
            continue
        g = Polygon(g.exterior.coords) if g.geom_type == "Polygon" else max(g.geoms, key=lambda x: x.area)
        vung.append(dict(g=g, tp=[k], kieu="Khung lỗ mở MEP có ống (không có X)", tt=None, ghi=""))
    for v in vung + loai:
        v["so_ong"] = so_ong(v["g"])
    return vung + loai


def nguon(path):
    p = [x for x in path.split("/") if x]
    return p[0] if p else "(model)"


def main():
    ap = argparse.ArgumentParser(description="Tìm trục/hộp kỹ thuật cần hatch ngăn cháy lan (dấu X).")
    ap.add_argument("dxf")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--layer-x", default=",".join(LAYER_X),
                    help='Layer chứa dấu X (wildcard, phân cách dấu phẩy; so không phân biệt dấu cách/hoa thường). '
                         'Bản vẽ đặt layer không chuẩn thì dùng "*" để dò mọi layer')
    ap.add_argument("--layer-bo", default=",".join(LAYER_BO), help="Layer không bao giờ coi là dấu X trục")
    ap.add_argument("--block-thang-may", default=",".join(BLOCK_THANG_MAY),
                    help="Mẫu tên block cabin/giếng thang máy cần loại (wildcard, phân cách dấu phẩy)")
    ap.add_argument("--block-bo", default=",".join(BLOCK_NOI_THAT),
                    help="Mẫu tên block đồ nội thất / thiết bị có dấu X cần bỏ qua")
    ap.add_argument("--block-ong", default=",".join(BLOCK_ONG),
                    help="Mẫu tên block ký hiệu ống đứng (ống tròn + cùm U)")
    ap.add_argument("--block-lo-mo", default=",".join(BLOCK_LO_MO),
                    help="Mẫu tên block lỗ mở sàn kiến trúc (chỉ nhận khi có ống đứng bên trong)")
    ap.add_argument("--layer-khung-ong", default=",".join(LAYER_KHUNG_ONG),
                    help="Layer khung lỗ mở MEP: khung kín có ống đứng bên trong là hộp kỹ thuật dù không có X")
    ap.add_argument("--khong-anh", action="store_true", help="Không vẽ ảnh PNG xem lại")
    a = ap.parse_args()

    tach = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    layer_x, layer_bo = tach(a.layer_x), tach(a.layer_bo)
    block_tm, block_bo = tach(a.block_thang_may), tach(a.block_bo)
    block_ong, block_lo_mo, layer_khung = tach(a.block_ong), tach(a.block_lo_mo), tach(a.layer_khung_ong)
    os.makedirs(a.out_dir, exist_ok=True)
    ten = os.path.splitext(os.path.basename(a.dxf))[0]
    f_json = os.path.join(a.out_dir, ten + "_vung.json")
    f_xlsx = os.path.join(a.out_dir, ten + "_vung.xlsx")
    f_png = os.path.join(a.out_dir, ten + "_vung.png")
    for f in (f_json, f_xlsx):
        if os.path.exists(f):
            sys.exit(f"Đã tồn tại, không ghi đè: {f} (chuyển bản cũ vào D:\\AI\\_backup trước)")

    print("Đang đọc DXF...", flush=True)
    cheo, cabin, chu, hatch_co, nen, ong, khung = doc_ban_ve(a.dxf, layer_x, block_tm, layer_bo, block_bo,
                                                            block_ong, layer_khung)
    o_x = ghep_dau_x(cheo)
    vung = dung_vung(o_x, ong, khung, block_lo_mo)
    cabin_u = unary_union(cabin) if cabin else None
    hatch_u = unary_union(hatch_co) if hatch_co else None

    ds = []
    for i, v in enumerate(sorted(vung, key=lambda v: (-round(v["g"].centroid.y / 500), v["g"].centroid.x)), 1):
        g, tp = v["g"], v["tp"]
        c = g.centroid
        x0, y0, x1, y1 = g.bounds
        vien = g.buffer(30)
        nhan = sorted({t for (x, y, t) in chu if t and vien.contains(Point(x, y))})
        trang_thai, ghi_chu = v["tt"] or "se_hatch", v["ghi"]
        if trang_thai == "loai":
            pass
        elif cabin_u is not None and g.intersection(cabin_u).area > 0.2 * g.area:
            trang_thai, ghi_chu = "loai", "Trùng cabin thang máy"
        elif hatch_u is not None and g.intersection(hatch_u).area > 0.5 * g.area:
            # phủ quá nửa: coi là đã có (người vẽ bo hẹp hơn ô X một chút), không vẽ dải thừa còn lại
            trang_thai, ghi_chu = "da_co", "Đã có hatch NET"
        elif hatch_u is not None and g.intersection(hatch_u).area > 1:
            # vùng gộp chạm ô đã hatch (vd. hộp chữ L có 1 nhánh đã hatch): chỉ vẽ phần còn thiếu, không chồng hatch
            con = g.difference(hatch_u).buffer(-1, join_style=2).buffer(1, join_style=2)
            if con.geom_type != "Polygon":
                con = max(getattr(con, "geoms", [con]), key=lambda x: x.area)
            if not con.is_empty:
                g = Polygon(con.exterior.coords).simplify(1)
                c, (x0, y0, x1, y1) = g.centroid, g.bounds
                ghi_chu = "Chỉ vẽ phần chưa có hatch (vùng chạm ô đã hatch)"
        if trang_thai == "se_hatch" and min(x1 - x0, y1 - y0) > 1400 and max(x1 - x0, y1 - y0) > 1400:
            ghi_chu = "Ô lớn, kiểm tra lại có phải giếng thang / lỗ mở sàn không (Cần xác nhận lại)"
        ds.append(dict(
            id=i, trang_thai=trang_thai, ghi_chu=ghi_chu,
            cx=round(c.x), cy=round(c.y), rong=round(x1 - x0), dai=round(y1 - y0),
            dien_tich_m2=round(g.area / 1e6, 3), kieu=v["kieu"], so_ong=v["so_ong"],
            nguon=sorted({nguon(o["path"]) for o in tp}),
            layer_x=sorted({o["layer"] for o in tp}),
            nhan=nhan,
            dinh=[[round(x, 1), round(y, 1)] for x, y in list(g.exterior.coords)[:-1]],
        ))

    # Ống đứng không nằm trong vùng nào (kể cả hatch có sẵn): trục chưa có khung bo, báo người dùng xem
    phu = unary_union([Polygon(v["dinh"]).buffer(20) for v in ds if v["trang_thai"] != "loai"]
                      + ([hatch_u] if hatch_u is not None else []))
    ong_le = [(round(p.x), round(p.y)) for p in ong if phu.is_empty or not phu.contains(p)]

    json.dump(dict(dxf=os.path.abspath(a.dxf), layer_hatch=LAYER_HATCH, pattern=PATTERN, vung=ds,
                   ong_chua_bo=ong_le),
              open(f_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Truc - HKT"
    ws.append(["STT", "Trạng thái", "Tâm X", "Tâm Y", "Rộng (mm)", "Dài (mm)", "Diện tích (m²)", "Kiểu nhận diện",
               "Số ống đứng", "Nguồn (xref/block)", "Layer dấu X / khung", "Chữ trong ô", "Ghi chú"])
    nhan_tt = {"se_hatch": "Sẽ hatch", "da_co": "Đã có hatch", "loai": "Loại"}
    for v in ds:
        ws.append([v["id"], nhan_tt[v["trang_thai"]], v["cx"], v["cy"], v["rong"], v["dai"], v["dien_tich_m2"],
                   v["kieu"], v["so_ong"], ", ".join(v["nguon"]), ", ".join(v["layer_x"]), ", ".join(v["nhan"]),
                   v["ghi_chu"]])
    for col, w in zip("ABCDEFGHIJKLM", (6, 12, 9, 9, 10, 10, 13, 30, 10, 34, 26, 16, 50)):
        ws.column_dimensions[col].width = w
    ws2 = wb.create_sheet("Ong chua co khung")
    ws2.append(["STT", "Tâm X", "Tâm Y", "Ghi chú"])
    for i, (x, y) in enumerate(ong_le, 1):
        ws2.append([i, x, y, "Ống đứng chưa nằm trong khung nào – kiểm tra trục / hộp (Cần xác nhận lại)"])
    wb.save(f_xlsx)

    if not a.khong_anh and ds:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection
        xs = [p[0] for v in ds for p in v["dinh"]]
        ys = [p[1] for v in ds for p in v["dinh"]]
        pad = 3000
        X0, X1, Y0, Y1 = min(xs) - pad, max(xs) + pad, min(ys) - pad, max(ys) + pad
        fig, ax = plt.subplots(figsize=(16, 16 * (Y1 - Y0) / max(X1 - X0, 1)))
        seg = [s for s in nen if X0 < s[0][0] < X1 and Y0 < s[0][1] < Y1]
        ax.add_collection(LineCollection(seg, colors="#999999", linewidths=0.3))
        mau = {"se_hatch": "#1a9e3a", "da_co": "#7f7f7f", "loai": "#d62728"}
        for v in ds:
            p = plt.Polygon(v["dinh"], closed=True, fc=mau[v["trang_thai"]], ec="k", lw=0.5, alpha=0.7)
            ax.add_patch(p)
            ax.text(v["cx"], v["cy"], str(v["id"]), fontsize=6, ha="center", va="center", color="k")
        if ong_le:
            ax.scatter([p[0] for p in ong_le], [p[1] for p in ong_le], s=12, c="#d400d4", marker="o", zorder=5)
        ax.set_xlim(X0, X1)
        ax.set_ylim(Y0, Y1)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title("Xanh = sẽ hatch, xám = đã có, đỏ = loại (thang máy / lỗ mở không ống), chấm tím = ống chưa có khung")
        fig.savefig(f_png, dpi=150, bbox_inches="tight")

    dem = {k: sum(1 for v in ds if v["trang_thai"] == k) for k in ("se_hatch", "da_co", "loai")}
    print(f"Ô X: {len(o_x)} | ống đứng: {len(ong)} | vùng: {len(ds)} | sẽ hatch: {dem['se_hatch']} | "
          f"đã có: {dem['da_co']} | loại: {dem['loai']} | ống chưa có khung: {len(ong_le)}")
    print(f_json)
    print(f_xlsx)
    if not a.khong_anh:
        print(f_png)


if __name__ == "__main__":
    main()
