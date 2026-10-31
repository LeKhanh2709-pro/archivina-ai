#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Do phong uot can chong tham (WC, lo gia, ban cong, phong ky thuat nuoc, phong rac) tren mat bang tang (Archivina).

Dau vao: DXF da NO AEC (dwg_to_dxf_aec.ps1). Cach lam:
  1. Dung luoi net tuong / cot / lan can + khung cua (ham cua dien-tich-ch\\scripts\\tao_polyline_phong.py), polygonize ra
     cac o kin.
  2. Hat giong phong uot: thiet bi ve sinh (block tren layer A-Interior WC, xi, sen, lavabo), may giat / cuc nong dieu hoa,
     text ten phong (WC, lo gia, ban cong, phong rac, phong ky thuat nuoc; bo text "Truc ...").
  3. Moi hat -> o kin nho nhat chua no = phong. Day canh ra MAT LOI tuong (bo lop trat 8-22 mm neu co net song song).
  4. Dao: truc / hop ky thuat, cot, vach S-Wall nam trong phong -> lo trong hatch (net ven khong di vong).
  5. Net ven chan tuong: offset bien phong vao trong --cach-ven (50), ngat tai cua di (cua co cung quay, cua truot)
     va o mo khong co tuong.
Xuat: <ten>_chongtham.json (dung cho ve_chong_tham_vao_ban_sao.ps1), .png; .xlsx chi khi co --excel (nguoi dung chot 23/10/2026: mac dinh khong tao Excel). Khong sua file dau vao.

    python tim_phong_uot.py <file_aec.dxf> --out-dir <thu muc> [--vung x0,y0,x1,y1] [--khong-anh] [--excel]
"""
import argparse
import importlib.util
import json
import math
import os
import re
import sys
from collections import defaultdict

import ezdxf
import shapely
from ezdxf import bbox as ezbbox
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from shapely.ops import linemerge, polygonize, unary_union

# Dung lai ham dung luoi net / khung cua / polygonize cua skill dien-tich-ch. Tim o: bien ARCHIVINA_DTCH,
# canh skill nay (.claude\skills\dien-tich-ch), <goc>\.claude\skills (goc = ARCHIVINA_AI hoac cha cua thu muc
# repo), %USERPROFILE%\.claude\skills -> chay duoc o may khac / repo GitHub dat skill o goc repo.
def _tim_dtch():
    ten = os.path.join("dien-tich-ch", "scripts", "tao_polyline_phong.py")
    skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ung = [os.environ.get("ARCHIVINA_DTCH", ""),
           os.path.join(os.path.dirname(skill), ten),
           os.path.join(os.path.dirname(skill), ".claude", "skills", ten),
           os.path.join(os.environ.get("ARCHIVINA_AI", ""), ".claude", "skills", ten) if os.environ.get("ARCHIVINA_AI") else "",
           os.path.join(os.path.expanduser("~"), ".claude", "skills", ten)]
    for c in ung:
        if c and os.path.isfile(c):
            return c
    sys.exit("Khong thay skill dien-tich-ch (tao_polyline_phong.py) - can skill nay de dung luoi net tuong. "
             "Chep thu muc dien-tich-ch canh thu muc chong-tham-mat-bang, hoac dat bien ARCHIVINA_DTCH. Da tim: "
             + "; ".join(c for c in ung if c))


_DTCH = _tim_dtch()
_spec = importlib.util.spec_from_file_location("tao_polyline_phong", _DTCH)
tpp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tpp)
bo_dau, layer_goc = tpp.bo_dau, tpp.layer_goc

LAYER_VE = "A-Material"
# Layer lam ranh phong. A-Material: thanh phan tuong ACA sau khi no (loi + trat) nam tren layer nay o du an 254HQV.
LAYER_RANH = ["A-Wall", "A-Material", "A-Column", "A-Line", "S-Wall", "A-Lancan", "A_Wall BT", "A-Vua trat"]
LAYER_CUA = tpp.LAYER_CUA
LAYER_WC = "A-Interior WC"
# Ten block (khong dau, chu thuong) thiet bi ve sinh / lo gia
RE_TB_WC = r"马桶|台盆|toilet|\bbet\b|bon cau|sen\b|voi sen|lavabo|chau rua mat|tieu nam|urinal|bon tam"
RE_TB_LG = r"may giat|washing|vrf|cuc nong|dan nong|dieu hoa|outdoor|may say|giat say"
# ong dung (vd. 'piped125-xi'), block truc tang ap 'TA1' (CT1 tang 5A-10, nam tren layer A-Interior WC) khong phai thiet bi
RE_TB_BO = r"^pipe|^ong\b|ong dung|piped|^ta\d*$"
RE_LAN_CAN = r"lan ?can|railing|balustrade|louver"  # block lan can / lam: phong sat lan can la lo gia / ban cong
NOI_DAI = 40.0       # mm: noi dai dau net ho toi net gan nhat (net tuong lung ngan hut 15 mm so voi tuong vuong goc)
LG_DT = (1.0, 12.0)  # m2: lo gia nhan theo cua truot / lan can
# Text ten phong (khong dau, chu thuong)
RE_TEN = [("phong_rac", r"phong rac|p\.? ?rac\b|kho rac"),
          ("phong_kt_nuoc", r"(phong|p\.)? ?(ky thuat|k\.?t\.?) ?(cap |thoat )?nuoc|bom nuoc|phong bom"),
          ("wc", r"\bwc\b|ve sinh|\bvs\b|phong tam"),
          ("lo_gia", r"lo ?gia|logia|loggia|ban cong")]
RE_TEN_BO = r"^\s*(truc|hop|ong|o thoang|gieng)"     # "Truc ky thuat nuoc", "Truc hut mui rac" la truc, khong phai phong
# Ky hieu phong 1 chu (so khop nguyen van, chu hoa): tang 4 Thap B ghi "R" = phong rac, "N" = phong ky thuat nuoc,
# tren layer Defpoints (nguoi dung chot 22/10/2026). Ky hieu nam trong o KHONG co cua (hop ky thuat) thi bo qua.
# CT1 tang 5A-10 ghi phong ky thuat nuoc la "KTN" (nguoi dung bo sung 23/10/2026)
KY_HIEU = "R=phong_rac,N=phong_kt_nuoc,KTN=phong_kt_nuoc"
DT_BUONG_DEM = 10.0  # m2: buong dem phong rac lon nhat
# Layer net mat ngoai (lan can, mep san) dung de khep lo gia khi thiet bi khong nam trong o kin nao
LAYER_MAT_NGOAI = r"^(0|a-line\d*)$"
# Layer net dao trong phong: truc / hop ky thuat, cot, vach
RE_LAYER_DAO = r"truc|hkt|hop ky thuat|a-mep|a_mep|a-column|s-wall|shaft|wall-open|lo mo"
# Layer khung lo mo: polyline kin la TOAN BO lo mo, chi can de len phong la phai khoet (Thap B 'A-Wall-Open', CT1 'A_MEP',
# 'AV-P-Lo mo', 'A-Truc nuoc'). Hatch tung chay de len hop vi cac layer nay khong duoc doc hoac chi tinh hop nam trong phong
# >= 80% (nguoi dung bao 31/10/2026, lo gia CH05A)
RE_LAYER_LO_MO = r"a[-_]mep|wall-open|lo mo|truc nuoc"
LO_MO_DE_MIN = 0.005e6   # mm2: lo mo de len phong tu muc nay moi khoet, nho hon la sai so net ve
# Nhung bo net ong / cum ong (vd. CT2 'AV-ME-Ống trục đứng', 'AV-ME-Cùm ống'): vong tron ong cat hop thanh manh vun
# -> mat ca hop (nguoi dung bao loi 23/10/2026)
RE_LAYER_DAO_BO = r"\bong\b|cum ong|pipe"
DAO_KIN_DT = (0.02e6, 6e6)   # mm2: polyline kin tren layer truc / A-MEP lay nguyen lam dao neu polygonize bo sot
TEN_LOAI = {"wc": "WC", "lo_gia": "Lô gia / ban công", "phong_rac": "Phòng rác", "phong_kt_nuoc": "Phòng KT nước",
            "buong_dem_rac": "Buồng đệm phòng rác"}
UU_TIEN = {"phong_rac": 0, "buong_dem_rac": 1, "phong_kt_nuoc": 2, "wc": 3, "lo_gia": 4}
CAN_CUA = {"phong_rac", "phong_kt_nuoc"}   # nhan theo ky hieu / ten: o phai co cua di moi la phong


def r1(v):
    return round(float(v), 1)


def diem_wcs(e):
    """Dinh LWPOLYLINE theo toa do Model. get_points() la toa do OCS: block chen lat guong co extrusion -Z, x bi doi dau
    -> doi tuong roi sang vi tri khac (hop ky thuat trong block lat guong khong duoc khoet, CT1 31/10/2026)."""
    return [(v.x, v.y) for v in e.vertices_in_wcs()]


# ---------------------------------------------------------------- doc ban ve
def loc_msp(msp):
    """Bo chong tham da ve (hatch / polyline A-Material o Model, block CHONG THAM*) khoi net nen."""
    out = []
    for e in msp:
        t = e.dxftype()
        if t == "INSERT" and bo_dau(e.dxf.name).startswith("chong tham"):
            continue
        if t in ("HATCH", "LWPOLYLINE") and layer_goc(e.dxf.layer) == layer_goc(LAYER_VE):
            continue
        out.append(e)
    return out


_XREF = {}   # duong dan DXF xref -> (doc, doi tuong da gom xref con)


def ma_can_xref(name):
    """'CT2 - CH.05A' -> 'CH05A' (ma can tu ten xref can ho)."""
    m = re.search(r"\bCH[\s.\-]*(\d+[A-Z]?)\b", name or "", re.I)
    return ("CH" + m.group(1)).upper() if m else ""


def doc_xref(ents, dxf_path, depth=0):
    """Noi dung xref ngoai, KHONG bind (nguoi dung chot 23/10/2026, ke ca ban tam): dwg_to_dxf_aec.ps1 chuyen rieng moi
    xref thanh DXF (no AEC tren ban sao) va ghi <ten>_xref.txt "ten|duong dan|dxf". Lay doi tuong Model cua DXF xref,
    sao ao + bien doi theo INSERT xref trong ban ve chu, chi trong bo nho, khong ghi file nao.
    Tra ve (doi tuong toa do Model, [(khung bao, ma can)])."""
    f = os.path.splitext(dxf_path)[0] + "_xref.txt"
    if depth > 2 or not os.path.exists(f):
        return [], []
    bang = {}
    with open(f, encoding="utf-8-sig") as fi:
        for dong in fi:
            p = dong.rstrip("\r\n").split("|")
            if len(p) >= 3 and p[2] and os.path.exists(p[2]):
                bang[p[0].lower()] = p[2]
    out, khung = [], []
    for e in ents:
        if e.dxftype() != "INSERT" or e.dxf.name.lower() not in bang:
            continue
        x = bang[e.dxf.name.lower()]
        if x not in _XREF:
            xd = ezdxf.readfile(x)
            xe = loc_msp(xd.modelspace())
            con, _ = doc_xref(xe, x, depth + 1)           # xref long nhau: da o toa do cua xref nay
            _XREF[x] = (xd, xe + con)
        m = e.matrix44()
        moi = []
        for v in _XREF[x][1]:
            try:
                c = v.copy()
                c.transform(m)
                moi.append(c)
            except Exception:
                pass
        out += moi
        can = ma_can_xref(e.dxf.name)
        if can and moi:
            try:
                b = ezbbox.extents(moi, fast=True)
                if b.has_data:
                    khung.append((box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y), can))
            except Exception:
                pass
    return out, khung


def duyet_insert(entities, depth=0, max_depth=4, par_layer=None):
    """Sinh (insert ao, ten block, layer hieu dung) cho moi INSERT, ke ca long nhau (toa do Model)."""
    for e in entities:
        if e.dxftype() != "INSERT":
            continue
        lay = par_layer if (par_layer and layer_goc(e.dxf.layer) == "0") else e.dxf.layer
        yield e, e.dxf.name, lay
        if depth < max_depth:
            try:
                subs = list(e.virtual_entities())
            except Exception:
                continue
            yield from duyet_insert(subs, depth + 1, max_depth, lay)


def duyet_text(entities, depth=0, max_depth=4):
    for e in entities:
        t = e.dxftype()
        if t in ("TEXT", "MTEXT"):
            yield e
        elif t == "INSERT" and depth < max_depth:
            try:
                yield from duyet_text(list(e.virtual_entities()), depth + 1, max_depth)
            except Exception:
                pass


def tam_bbox(e):
    try:
        b = ezbbox.extents([e], fast=True)
        if b.has_data:
            return ((b.extmin.x + b.extmax.x) / 2, (b.extmin.y + b.extmax.y) / 2), (b.size.x, b.size.y)
    except Exception:
        pass
    return (e.dxf.insert.x, e.dxf.insert.y), (0, 0)


def ma_can(name):
    m = re.match(r"\s*(CH\s?\d+[A-Z]?)", name or "", re.I)
    return m.group(1).upper().replace(" ", "") if m else ""


def doc_hat_giong(ents, a):
    """Hat giong: (loai, diem, nguon, can)."""
    re_wc, re_lg, re_bo = re.compile(a.tb_wc, re.I), re.compile(a.tb_lg, re.I), re.compile(RE_TB_BO)
    seeds = []
    for e, name, lay in duyet_insert(ents):
        n = bo_dau(name)
        ten_ngan = n.split("$")[-1]
        if re_bo.search(ten_ngan):
            continue
        loai = None
        if re_wc.search(ten_ngan) or layer_goc(lay) == layer_goc(LAYER_WC):
            loai = "wc"
        elif re_lg.search(ten_ngan):
            loai = "lo_gia"
        if not loai:
            continue
        p, sz = tam_bbox(e)
        if max(sz) > 3000:            # block lon (ca cum noi that / ca can) khong lam hat giong
            continue
        seeds.append((loai, p, name.split("$")[-1], ma_can(name)))
    re_bo = re.compile(RE_TEN_BO)
    ky = dict(kv.split("=") for kv in a.ky_hieu.split(",") if "=" in kv)
    for e in duyet_text(ents):
        goc = (e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text).strip()
        if goc in ky:                                  # ky hieu 1 chu "R", "N" (so nguyen van, phan biet hoa thuong)
            p, _ = tam_bbox(e)
            seeds.append((ky[goc], p, "ký hiệu: " + goc, ""))
            continue
        s = bo_dau(goc)
        if not s or len(s) > 40 or re_bo.search(s):
            continue
        for loai, rx in RE_TEN:
            if re.search(rx, s):
                p = e.dxf.insert
                seeds.append((loai, (p.x, p.y), "text: " + s, ""))
                break
    return seeds


def doc_dao(ents):
    """Net tren layer truc / hop ky thuat / cot / vach (ke ca trong block) -> (polygon dao, cac dao la khung lo mo)."""
    rx, rx_bo, rx_mo = re.compile(RE_LAYER_DAO), re.compile(RE_LAYER_DAO_BO), re.compile(RE_LAYER_LO_MO)
    segs, kin, kin_mo = [], [], []
    for e in tpp.walk(ents, max_depth=4):
        if e.dxftype() not in ("LINE", "LWPOLYLINE"):
            continue
        lay = bo_dau(layer_goc(e.dxf.layer))
        if not rx.search(lay) or rx_bo.search(lay):
            continue
        if e.dxftype() == "LINE":
            segs.append(LineString([(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]))
        else:
            pts = diem_wcs(e)
            if e.closed and len(pts) > 2:
                if len(pts) >= 3:
                    q = Polygon(pts)
                    if q.is_valid and DAO_KIN_DT[0] <= q.area <= DAO_KIN_DT[1]:
                        (kin_mo if rx_mo.search(lay) else kin).append(q)
                pts.append(pts[0])
            if len(pts) >= 2:
                segs.append(LineString(pts))
    if not segs:
        return [], []
    polys = list(polygonize(shapely.union_all(segs, grid_size=0.01)))
    long, tamgiac = [], []
    for p in polys:
        lo = sum(Polygon(r).area for r in p.interiors)
        if p.interiors and lo >= 0.5 * Polygon(p.exterior).area:
            continue        # vo hop (vach mong bao quanh long hop): bo, long hop la o rieng (mau CH15: vo hop van hatch)
        q = Polygon(p.exterior)                       # lo nho ben trong (ong tron) khong tinh
        if len(shapely.simplify(q, 1).exterior.coords) == 4:
            tamgiac.append(q)                         # tam giac cua dau X: gop lai thanh o hop
        else:
            long.append(q)
    if tamgiac:
        gop = unary_union([t.buffer(0.5, join_style="mitre") for t in tamgiac])
        long += [Polygon(g.exterior).buffer(-0.5, join_style="mitre") for g in (gop.geoms if hasattr(gop, "geoms") else [gop])]
    # o hep < 100 mm la vach vo hop / bau, khong phai long hop (mau CH15: vo hop 80 mm van hatch)
    long = [g.simplify(5) for g in long if g.area >= 0.02e6 and not g.buffer(-50).is_empty]
    long.sort(key=lambda g: -g.area)
    out = []
    for g in long:                                    # o nam trong o da giu (o chia boi ong, net trong hop) -> bo
        if not any(o.buffer(2).contains(g) for o in out):
            out.append(g)
    # Du phong: hop ve bang polyline kin (vd. 'A-Mep' CT2) ma polygonize bo sot (bi net trong hop cat vun) -> lay nguyen
    for k in sorted(kin, key=lambda g: g.area):
        if not any(o.intersection(k).area >= 0.3 * k.area for o in out):
            out.append(k.simplify(5))
    # Khung lo mo lay ngoai cung: dau X, dai vach 80 trong khung chia khung thanh o vun, khoet theo o vun se sot 1 phan hop
    mo = []
    for k in sorted(kin_mo, key=lambda g: -g.area):
        if not any(o.buffer(2).contains(k) for o in mo):
            mo.append(k.simplify(5))
    out = [o for o in out if not any(k.buffer(2).contains(o) for k in mo)]
    # buffer / simplify co the tach thanh MultiPolygon o cho that hep: tach ra tung o
    out = [p for o in out for p in getattr(o, "geoms", [o])]
    mo = [p for o in mo for p in getattr(o, "geoms", [o])]
    return out + mo, mo


def tim_can(ents):
    """Tam cac INSERT ten 'CHxx (T4)$0$...' (thiet bi, noi that cua can) -> (cay, ma can) de gan ma can cho phong."""
    pts, ma = [], []
    for e, name, lay in duyet_insert(ents):
        m = ma_can(name)
        if m and "$" in name:
            p, sz = tam_bbox(e)
            if max(sz) < 5000:
                pts.append(Point(p))
                ma.append(m)
    return (shapely.STRtree(pts), pts, ma) if pts else None


def cua_net_roi(ents, want, gan=30.0):
    """Cua / cua so ve bang NET ROI tren layer cua (khong phai block): CT2 xref can ho sau khi no AEC_DOOR chi con
    LINE / LWPOLYLINE / ARC tren A-Door (nguoi dung bao loi net ven chay qua cua 23/10/2026). Gom cac net cach nhau
    <= gan (mm) thanh mot cua."""
    items = []

    def di(es, d):
        for e in es:
            t = e.dxftype()
            if t == "INSERT":           # INSERT tren layer cua da tinh o tpp._nhom_cua
                if layer_goc(e.dxf.layer) in want or d >= 3 or (
                        tpp._BO_QUA[0] is not None and tpp._BO_QUA[0].search(e.dxf.name or "")):
                    continue
                try:
                    di(list(e.virtual_entities()), d + 1)
                except Exception:
                    pass
            elif t in ("LINE", "LWPOLYLINE", "ARC") and layer_goc(e.dxf.layer) in want:
                try:
                    b = ezbbox.extents([e], fast=True)
                except Exception:
                    continue
                if b.has_data:
                    items.append((e, box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y).buffer(gan / 2)))

    di(ents, 0)
    if not items:
        return []
    cay = shapely.STRtree([g for _, g in items])
    cha = list(range(len(items)))

    def goc(i):
        while cha[i] != i:
            cha[i] = cha[cha[i]]
            i = cha[i]
        return i
    for i, (_, g) in enumerate(items):
        for j in cay.query(g, predicate="intersects"):
            a, b = goc(i), goc(int(j))
            if a != b:
                cha[a] = b
    nhom = defaultdict(list)
    for i, (e, _) in enumerate(items):
        nhom[goc(i)].append(e)
    return list(nhom.values())


def doc_cua(ents, chains):
    """Moi cua (INSERT tren layer cua) -> dict(doan, co_cung, loai). loai: 'cua_di' (co cung quay, hoac chi gom polyline
    nhu cua truot) / 'cua_so' (co >= 3 LINE kinh, khong cung quay)."""
    want = {layer_goc(x) for x in LAYER_CUA}
    out = []
    for flat in list(tpp._nhom_cua(ents, want)) + cua_net_roi(ents, want):
        doan, n_arc = tpp._doan_cua(flat)
        if not doan:
            continue
        n_line = sum(1 for s in flat if s.dxftype() == "LINE")
        loai = "cua_di" if (n_arc > 0 or n_line < 3) else "cua_so"
        c = dict(doan=doan, loai=loai, truot=(loai == "cua_di" and n_arc == 0))
        mo = duong_mo_cua(flat, doan)
        if mo:
            c["mo"] = mo
        out.append(c)
    return out


def duong_mo_cua(flat, doan):
    """Duong mo cua (nam trong tuong): ban le -> mep canh khi dong, tu cung quay lon nhat. Ban kinh nao co canh cua
    (doan song song, sat ban kinh) la canh dang mo; ban kinh con lai la duong mo. Dung de chi cat net ven o phong co
    canh song song duong mo: canh cua phong ben canh ve o tu the mo nam sat tuong WC khong cat nham (CT2, 23/10/2026)."""
    arcs = [s for s in flat if s.dxftype() == "ARC" and 300 <= s.dxf.radius <= 1500]
    if not arcs:
        return None
    a = max(arcs, key=lambda s: s.dxf.radius)
    try:
        c = a.ocs().to_wcs(a.dxf.center)
        p1, p2 = a.start_point, a.end_point
    except Exception:
        return None
    c, r = (c.x, c.y), a.dxf.radius

    def do_canh(p):                 # tong chieu dai doan cua song song va sat ban kinh c -> p
        ux, uy = (p[0] - c[0]) / r, (p[1] - c[1]) / r
        tong = 0.0
        for s, e in doan:
            L = math.dist(s, e)
            if L < 1:
                continue
            if abs(((e[0] - s[0]) * ux + (e[1] - s[1]) * uy) / L) < 0.95:
                continue
            ngang = max(abs((q[0] - c[0]) * -uy + (q[1] - c[1]) * ux) for q in (s, e))
            if ngang <= 120:
                tong += L
        return tong
    p1, p2 = (p1.x, p1.y), (p2.x, p2.y)
    mo = p2 if do_canh(p1) >= do_canh(p2) else p1
    return (c, mo)


def doc_tuong_no(ents, max_depth=4):
    """Net cua tuong ACA da no nhung nam tren layer 0 (block an danh '*U..' chi gom LINE/LWPOLYLINE + HATCH, canh ngan
    <= 450 mm). Tang 4 Thap B: nhieu can co tuong kieu nay, khong co net A-Wall nao."""
    chains = []

    def di(entities, depth):
        for e in entities:
            if e.dxftype() != "INSERT":
                continue
            try:
                subs = list(e.virtual_entities())
            except Exception:
                continue
            kieu = {s.dxftype() for s in subs}
            if e.dxf.name.startswith("*") and "HATCH" in kieu and kieu <= {"LINE", "LWPOLYLINE", "HATCH"}:
                try:
                    b = ezbbox.extents([e], fast=True)
                except Exception:
                    continue
                if b.has_data and min(b.size.x, b.size.y) <= 450:
                    for s in subs:
                        if s.dxftype() == "LINE":
                            chains.append((False, [(s.dxf.start.x, s.dxf.start.y), (s.dxf.end.x, s.dxf.end.y)]))
                        elif s.dxftype() == "LWPOLYLINE":
                            pts = diem_wcs(s)
                            if len(pts) >= 2:
                                chains.append((bool(s.closed), pts))
                    continue
            if depth < max_depth:
                di(subs, depth + 1)

    di(ents, 0)
    return chains


def doc_mat_ngoai(ents, dmin=300.0):
    """Net LINE / LWPOLYLINE o cap Model tren layer 0 / A-line* (mep san, mat ngoai lan can) dai >= dmin. Chi dung de
    khep lai lo gia ma thiet bi khong nam trong o kin nao (vd. lo gia CH27 tang 4 Thap B: mat ngoai chi co lan can
    dai 1039 va 2 LINE layer 0)."""
    rx = re.compile(LAYER_MAT_NGOAI)
    out = []
    for e in ents:
        t = e.dxftype()
        if t not in ("LINE", "LWPOLYLINE") or not rx.match(layer_goc(e.dxf.layer)):
            continue
        if t == "LINE":
            pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
            closed = False
        else:
            pts = diem_wcs(e)
            closed = bool(e.closed)
        if len(pts) >= 2 and LineString(pts).length >= dmin:
            out.append((closed, pts))
    return out


def khep_lai(diem, chains, khung, mat_ngoai, gap_max, r=6000.0):
    """Dung lai luoi net quanh cac diem (them net mat ngoai), tra ve (o kin nho nhat 1-20 m2 chua mot diem, cac doan
    dong o mo) hoac (None, [])."""
    vung = unary_union([Point(p).buffer(r) for p in diem])

    def gan(c):
        return LineString(c[1] if len(c[1]) > 1 else c[1] * 2).intersects(vung)

    ch = [c for c in chains if gan(c)] + [c for c in mat_ngoai if gan(c)]
    kh = [k for k in khung if k.intersects(vung)]
    fs, _, br = tpp.build_faces(ch, gap_max, kh + noi_dai_dau_ho(ch))
    best = None
    for f in fs:
        if not (1.0e6 <= f.area <= 20.0e6):
            continue
        if any(f.contains(Point(p)) for p in diem) and (best is None or f.area < best.area):
            best = f
    return best, br


def doc_cua_thang(ents):
    """O cua thang may: polyline kin o cap Model tren layer tuong (A-Wall), canh ngan <= 300, khong hatch, nam canh
    text tai trong thang '300KG' (<= 2,5 m). Tang 4 Thap B: cua thang may rac giua phong rac va thang may la
    polyline 150 x 1000 tren A-Wall (nguoi dung xac nhan 23/10/2026 la cua -> ngat net ven)."""
    rx_kg = re.compile(r"^\s*\d+\s*kg\s*$")
    kg = []
    for e in duyet_text(ents):
        s = bo_dau(e.plain_text() if e.dxftype() == "MTEXT" else e.dxf.text)
        if rx_kg.match(s):
            p, _ = tam_bbox(e)
            kg.append(Point(p))
    if not kg:
        return []
    out = []
    for e in ents:
        if e.dxftype() != "LWPOLYLINE" or not e.closed or layer_goc(e.dxf.layer) != "a-wall":
            continue
        pts = diem_wcs(e)
        if len(pts) < 3:
            continue
        g = Polygon(pts)
        x0, y0, x1, y1 = g.bounds
        if min(x1 - x0, y1 - y0) > 300 or max(x1 - x0, y1 - y0) < 600:
            continue
        if any(g.distance(k) <= 2500 for k in kg):
            out.append(g)
    return out


def doc_gieng_thang(ents):
    """Gieng thang may: polyline kin 4 dinh (0,8-12 m2), ben trong co 2 duong cheo noi cac goc doi dien (dau X), moi
    layer ke ca net khuat. CT1 tang 5A-10: gieng thang may rac chi co vien + dau X tren '...Loi TDH$0$A-Hidden',
    khong co net tuong ngan voi phong rac."""
    hcn, cheo = [], []
    for e in tpp.walk(ents, max_depth=4):
        t = e.dxftype()
        if t == "LINE":
            cheo.append(((e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)))
        elif t == "LWPOLYLINE":
            pts = diem_wcs(e)
            if len(pts) == 2:
                cheo.append((pts[0], pts[1]))
            elif e.closed and len(pts) in (4, 5):
                g = Polygon(pts[:4])
                if g.is_valid and 0.8e6 <= g.area <= 12e6 and abs(g.area - g.minimum_rotated_rectangle.area) < 0.02 * g.area:
                    hcn.append(g)
    if not hcn or not cheo:
        return []
    cay = shapely.STRtree([LineString(s) for s in cheo])
    out = []
    for g in hcn:
        goc = list(g.exterior.coords)[:4]
        cap = [(goc[0], goc[2]), (goc[1], goc[3])]
        n = 0
        for a, b in cap:
            for k in cay.query(LineString([a, b]).buffer(100)):
                p, q = cheo[int(k)]
                if (math.dist(p, a) < 150 and math.dist(q, b) < 150) or (math.dist(p, b) < 150 and math.dist(q, a) < 150):
                    n += 1
                    break
        if n == 2 and not any(o.buffer(5).contains(g) for o in out):
            out.append(g)
    return out


def cua_quanh(face, cuas, d=250.0):
    """Chi so cac cua di nam sat bien o (khung cua cach bien <= d)."""
    ext = Polygon(face.exterior).exterior
    out = []
    for i, c in enumerate(cuas):
        if c["loai"] != "cua_di":
            continue
        pts = list(c["mo"]) if c.get("mo") else [p for s in c["doan"] for p in s]
        g = LineString(pts) if len(pts) > 1 else Point(pts[0])
        if g.distance(ext) <= d:
            out.append(i)
    return out


def doc_noi_that(ents):
    """Tam cac block noi that (giuong, tu, sofa, ban ...) - o kin co noi that khong phai lo gia."""
    rx_bo = re.compile("|".join([RE_TB_WC, RE_TB_LG, RE_TB_BO, RE_LAN_CAN]))
    pts = []
    for e, name, lay in duyet_insert(ents, max_depth=2):
        L = bo_dau(layer_goc(lay))
        if not (L.startswith("a-interior") or L.startswith("a-noi that") or "furn" in L) or "wc" in L:
            continue
        if rx_bo.search(bo_dau(name).split("$")[-1]):
            continue
        p, sz = tam_bbox(e)
        if 400 <= max(sz) <= 4000:
            pts.append(Point(p))
    return pts


def doc_lan_can(ents):
    """Khung bao cac block lan can / lam (Model): ten khop RE_LAN_CAN, hoac block an danh mong (canh ngan <= 200,
    dai >= 800) chua >= 5 doi tuong va co block con (song lan can) - vd. '*U1095' tang 4 Thap B."""
    rx = re.compile(RE_LAN_CAN)
    cua = {layer_goc(x) for x in LAYER_CUA} | {layer_goc(LAYER_WC)}
    out = []
    for e, name, lay in duyet_insert(ents, max_depth=3):
        ten = bo_dau(name).split("$")[-1]
        theo_ten = rx.search(ten) or rx.search(bo_dau(layer_goc(lay)))
        if not theo_ten and (not name.startswith("*") or layer_goc(lay) in cua):
            continue
        try:
            b = ezbbox.extents([e], fast=True)
        except Exception:
            continue
        if not b.has_data or max(b.size.x, b.size.y) >= 20000:
            continue
        # chi lay block mong (canh ngan <= 200): lam goc chu L co khung bao trum vao long lo gia, lam chia doi phong
        if min(b.size.x, b.size.y) > 200 or max(b.size.x, b.size.y) < 800:
            continue
        if not theo_ten:
            try:
                subs = list(e.virtual_entities())
            except Exception:
                continue
            if len(subs) < 5 or not any(s.dxftype() == "INSERT" for s in subs):
                continue
        out.append(box(b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
    return out


def noi_dai_dau_ho(chains, dmax=NOI_DAI):
    """Doan noi dai dau mut net ho theo huong cua no toi net gan nhat (<= dmax). Tra ve list LineString."""
    segs = []
    for closed, pts in chains:
        q = pts + ([pts[0]] if closed else [])
        segs += [LineString([q[i], q[i + 1]]) for i in range(len(q) - 1) if math.dist(q[i], q[i + 1]) > 0.5]
    if not segs:
        return []
    cay = shapely.STRtree(segs)
    out = []
    for closed, pts in chains:
        if closed or len(pts) < 2:
            continue
        for p, q in ((pts[0], pts[1]), (pts[-1], pts[-2])):
            L = math.dist(p, q)
            if L < 1:
                continue
            ux, uy = (p[0] - q[0]) / L, (p[1] - q[1]) / L
            tia = LineString([(p[0] + ux * 0.5, p[1] + uy * 0.5), (p[0] + ux * dmax, p[1] + uy * dmax)])
            best = None
            for k in cay.query(tia, predicate="intersects"):
                x = tia.intersection(segs[int(k)])
                if x.is_empty:
                    continue
                d = Point(p).distance(x)
                if 1.0 < d <= dmax and (best is None or d < best):
                    best = d
            if best:
                out.append(LineString([p, (p[0] + ux * best, p[1] + uy * best)]))
    return out


def giap_ngoai_nha(poly, faces_tree, faces, dmin=800.0):
    """Co canh dai >= dmin ma phia ngoai (300 va 600 mm) khong thuoc o kin nao -> giap ngoai nha."""
    pts = list(shapely.geometry.polygon.orient(poly, 1.0).exterior.coords)
    for a, b in zip(pts, pts[1:]):
        L = math.dist(a, b)
        if L < dmin:
            continue
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = uy, -ux
        ngoai = True
        for t in (0.25, 0.5, 0.75):
            for d in (300.0, 600.0):
                P = Point(a[0] + ux * L * t + nx * d, a[1] + uy * L * t + ny * d)
                if any(faces[int(k)].contains(P) for k in faces_tree.query(P)):
                    ngoai = False
                    break
            if not ngoai:
                break
        if ngoai:
            return True
    return False


def hatch_da_co(msp):
    """Polygon cac hatch chong tham da co: HATCH _USER tren A-Material o Model hoac trong block CHONG THAM*."""
    polys = []

    def tu_hatch(h):
        for p in h.paths:
            try:
                if hasattr(p, "vertices"):
                    pts = [(v[0], v[1]) for v in p.vertices]
                else:
                    pts = [(ed.start[0], ed.start[1]) for ed in p.edges if hasattr(ed, "start")]
                if len(pts) >= 3:
                    polys.append(Polygon(pts).buffer(0))
            except Exception:
                pass

    for e in msp:
        if e.dxftype() == "HATCH" and layer_goc(e.dxf.layer) == layer_goc(LAYER_VE) and e.dxf.pattern_name.upper() in ("_USER", "_U"):
            tu_hatch(e)
        elif e.dxftype() == "INSERT" and bo_dau(e.dxf.name).startswith("chong tham"):
            for v in e.virtual_entities():
                if v.dxftype() == "HATCH":
                    tu_hatch(v)
    return unary_union(polys) if polys else None


# ---------------------------------------------------------------- hinh hoc
def don_gian(poly):
    """Bo dinh thang hang / trung nhau, huong CCW."""
    poly = shapely.geometry.polygon.orient(poly.buffer(0), 1.0)
    pts = list(poly.exterior.coords)[:-1]
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(len(pts)):
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % len(pts)]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if math.dist(a, b) < 0.5 or abs(cross) / max(math.dist(a, c), 1e-9) < 0.5:
                pts.pop(i)
                changed = True
                break
    return Polygon(pts, [list(r.coords) for r in poly.interiors])


def ve_mat_loi(poly, cay_net, net, tmin=8.0, tmax=22.0):
    """Day tung canh ra ngoai toi net song song cach tmin-tmax mm (mat loi tuong phia sau lop trat).
    Tra ve (polygon moi, so canh da day)."""
    pts = list(poly.exterior.coords)[:-1]          # CCW: phia ngoai la ben phai huong canh
    n = len(pts)
    dich = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = uy, -ux                            # phap tuyen ra ngoai
        vung = LineString([a, b]).buffer(tmax + 1, cap_style="flat")
        best = 0.0
        tot = defaultdict(float)
        for k in cay_net.query(vung):
            s = net[k]
            (x1, y1), (x2, y2) = s.coords[0], s.coords[-1]
            ls = math.dist((x1, y1), (x2, y2))
            if ls < 1 or abs((x2 - x1) * uy - (y2 - y1) * ux) / ls > 0.02:   # khong song song
                continue
            d = (x1 - a[0]) * nx + (y1 - a[1]) * ny
            if not (tmin <= d <= tmax):
                continue
            t1 = (x1 - a[0]) * ux + (y1 - a[1]) * uy
            t2 = (x2 - a[0]) * ux + (y2 - a[1]) * uy
            ov = max(0.0, min(max(t1, t2), L) - max(min(t1, t2), 0.0))
            tot[round(d, 1)] += ov
        if tot:
            d, ov = max(tot.items(), key=lambda kv: kv[1])
            if ov >= 0.4 * L:
                best = d
        dich.append(best)
    if not any(dich):
        return poly, 0

    def giao(p1, d1, p2, d2):
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-9:
            return None
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / den
        return (p1[0] + t * d1[0], p1[1] + t * d1[1])

    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        L = math.dist(a, b)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = uy, -ux
        lines.append(((a[0] + nx * dich[i], a[1] + ny * dich[i]), (ux, uy), (b[0] + nx * dich[i], b[1] + ny * dich[i])))
    moi = []
    for i in range(n):
        p0, d0, e0 = lines[i - 1]
        p1, d1, _ = lines[i]
        q = giao(p0, d0, p1, d1)
        if q is None:                               # hai canh thang hang, do day khac nhau -> bac
            moi += [e0, p1]
        else:
            moi.append(q)
    g = Polygon(moi, [list(r.coords) for r in poly.interiors]).buffer(0)
    if g.geom_type != "Polygon" or abs(g.area - poly.area) > 0.2 * poly.area:
        return poly, 0
    return g, sum(1 for d in dich if d)


def dai_cat_cua(ring_poly, cua):
    """Vung cat net ven tai mot cua di: dai doc theo canh phong gan cua nhat, rong bang be rong o cua.
    Cua co duong mo (cung quay): chi cat canh song song duong mo (lech <= 20 do), rong bang duong mo."""
    mo = cua.get("mo")
    pts = list(mo) if mo else [p for s in cua["doan"] for p in s]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    ext = ring_poly.exterior
    best = None
    coords = list(ext.coords)
    for a, b in zip(coords, coords[1:]):
        if mo:
            La, Lm = math.dist(a, b), math.dist(*mo)
            if La < 1 or Lm < 1 or abs(((b[0] - a[0]) * (mo[1][0] - mo[0][0]) + (b[1] - a[1]) * (mo[1][1] - mo[0][1]))
                                       / (La * Lm)) < math.cos(math.radians(20)):
                continue
        seg = LineString([a, b])
        d = seg.distance(LineString(pts) if len(pts) > 1 else Point(pts[0]))
        if best is None or d < best[0]:
            best = (d, a, b)
    if best is None:
        return None
    d, a, b = best
    if d > 400:
        return None
    L = math.dist(a, b)
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    ts = [(p[0] - a[0]) * ux + (p[1] - a[1]) * uy for p in pts]
    t0, t1 = min(ts), max(ts)
    nx, ny = -uy, ux
    # be ngang vung cat tinh tu canh phong: du phu net ven (cach bo 50) chu khong lan sang net ven canh vuong goc khi
    # ban le cua sat goc phong (truoc la 400, cat mat ~360 mm net ven canh ben, CT2 23/10/2026)
    w = 120.0
    q = [(a[0] + ux * t0 + nx * w, a[1] + uy * t0 + ny * w), (a[0] + ux * t1 + nx * w, a[1] + uy * t1 + ny * w),
         (a[0] + ux * t1 - nx * w, a[1] + uy * t1 - ny * w), (a[0] + ux * t0 - nx * w, a[1] + uy * t0 - ny * w)]
    return Polygon(q)


def net_ven(poly, cut, cach):
    """Offset bien ngoai vao trong 'cach', bo phan nam trong vung cat (cua). Tra ve list (dong?, [diem])."""
    inner = poly.buffer(-cach, join_style="mitre")
    if inner.is_empty:
        return []
    if inner.geom_type == "MultiPolygon":
        inner = max(inner.geoms, key=lambda g: g.area)
    inner = shapely.geometry.polygon.orient(Polygon(inner.exterior), 1.0)
    ring = LineString(inner.exterior.coords)
    if cut is None or cut.is_empty:
        return [(True, [(r1(x), r1(y)) for x, y in list(ring.coords)[:-1]])]
    rest = ring.difference(cut)
    if rest.is_empty:
        return []
    parts = list(rest.geoms) if hasattr(rest, "geoms") else [rest]
    # vong bi cat tai diem dau (goc dau tien) -> noi lai hai doan cham nhau
    merged = linemerge(MultiLineString(parts)) if len(parts) > 1 else parts[0]
    parts = list(merged.geoms) if hasattr(merged, "geoms") else [merged]
    out = []
    for p in parts:
        cs = list(shapely.simplify(p, 0.5).coords)
        if p.length >= 20:
            out.append((False, [(r1(x), r1(y)) for x, y in cs]))
    return out


# ---------------------------------------------------------------- chinh
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dxf")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--vung", default="", help="chi xet vung x0,y0,x1,y1 (toa do Model)")
    ap.add_argument("--cach-ven", type=float, default=50.0, help="net ven cach duong bo vao trong (mm)")
    ap.add_argument("--gap-max", type=float, default=1200.0, help="dong o mo tuong <= gap (mm)")
    ap.add_argument("--dien-tich-max", type=float, default=15.0, help="phong lon hon (m2) -> can_xem")
    ap.add_argument("--layer-ranh", default=",".join(LAYER_RANH))
    ap.add_argument("--tb-wc", default=RE_TB_WC, help="regex ten block thiet bi ve sinh (khong dau)")
    ap.add_argument("--tb-lg", default=RE_TB_LG, help="regex ten block may giat / cuc nong (khong dau)")
    ap.add_argument("--them", default="",
                    help="them phong chi dinh tay 'loai:x,y;loai:x,y' (loai: wc, lo_gia, phong_rac, phong_kt_nuoc, "
                         "buong_dem_rac), vd. phong rac khong co text ten")
    ap.add_argument("--ky-hieu", default=KY_HIEU,
                    help="text ky hieu phong so khop nguyen van: 'R=phong_rac,N=phong_kt_nuoc'")
    ap.add_argument("--khong-anh", action="store_true")
    ap.add_argument("--excel", action="store_true", help="xuat them file Excel (mac dinh khong xuat)")
    ap.add_argument("--xuat-lsp", default="",
                    help="ghi them file du lieu cho lenh LISP CHONGTHAM (ASCII, moi dong 1 bieu thuc LISP)")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    ten = os.path.splitext(os.path.basename(a.dxf))[0]
    print("Doc DXF...", flush=True)
    doc = ezdxf.readfile(a.dxf)
    msp = doc.modelspace()
    ents = loc_msp(msp)
    xents, xkhung = doc_xref(ents, a.dxf)
    if xents:
        print(f"  them {len(xents)} doi tuong tu {len(_XREF)} xref (doc rieng, khong bind)", flush=True)
        ents = ents + xents
    if a.vung:
        x0, y0, x1, y1 = (float(v) for v in a.vung.split(","))
        khung_xet = box(x0, y0, x1, y1)
    else:
        khung_xet = None

    print("Dung luoi net...", flush=True)
    chains = tpp.doc_chains(ents, [x.strip() for x in a.layer_ranh.split(",") if x.strip()])
    them = doc_tuong_no(ents)
    chains += them
    # khung bao block lan can lam ranh: lo gia / ban cong dung o MAT TRONG lan can (chot 22/10/2026)
    lan_can = doc_lan_can(ents)
    chains += [(True, list(b.exterior.coords)[:-1]) for b in lan_can]
    if khung_xet is not None:
        kx = khung_xet.buffer(3000)
        chains = [c for c in chains if LineString(c[1] if len(c[1]) > 1 else c[1] * 2).intersects(kx)]
    khung, tk = tpp.doc_khung_cua(ents, chains, LAYER_CUA)
    noi = noi_dai_dau_ho(chains)
    faces, pairs, bridges = tpp.build_faces(chains, a.gap_max, list(khung) + noi)
    faces = [f for f in faces if f.area > 0.3e6]
    cay_face = shapely.STRtree(faces)
    net = []
    for closed, pts in chains:
        q = pts + ([pts[0]] if closed else [])
        net += [LineString([q[i], q[i + 1]]) for i in range(len(q) - 1) if math.dist(q[i], q[i + 1]) > 0.5]
    cay_net = shapely.STRtree(net)
    cuas = doc_cua(ents, chains)
    cua_thang = doc_cua_thang(ents)
    gieng = doc_gieng_thang(ents)
    dao_all, lo_mo = doc_dao(ents)
    la_lo_mo = {id(q) for q in lo_mo}
    cay_dao = shapely.STRtree(dao_all) if dao_all else None
    da_co = hatch_da_co(msp)
    print(f"  {len(chains)} chuoi net (them {len(them)} net tuong da no o layer 0), {len(faces)} o kin, {len(cuas)} cua, "
          f"{len(dao_all)} o dao", flush=True)

    seeds = doc_hat_giong(ents, a)
    for s in [x for x in a.them.split(";") if x.strip()]:
        loai, xy = s.split(":")
        if loai.strip() not in TEN_LOAI:
            sys.exit(f"--them: loai '{loai}' khong hop le, chon trong {list(TEN_LOAI)}")
        x, y = (float(v) for v in xy.split(","))
        seeds.append((loai.strip(), (x, y), "chỉ định tay", ""))
    if xkhung:   # hat trong xref can ho: ma can lay tu ten xref (khung bao nho nhat chua hat)
        def can_xref(p):
            c = [(k.area, ma) for k, ma in xkhung if k.contains(Point(p))]
            return min(c)[1] if c else ""
        seeds = [(l, p, n, c or can_xref(p)) for l, p, n, c in seeds]
    if khung_xet is not None:
        seeds = [s for s in seeds if khung_xet.contains(Point(s[1]))]
    # gom hat theo o kin
    phong = {}
    khong_vao = []
    for loai, p, nguon, can in seeds:
        P = Point(p)
        cands = [faces[int(k)] for k in cay_face.query(P, predicate="intersects")]
        cands = [f for f in cands if f.contains(P) or f.distance(P) < 1]
        # o hep < 500 mm / < 0,5 m2 (khe tuong, dai mep san) khong phai phong: CT2 cuc nong roi vao dai 1400 x 150
        # thanh "lo gia" 0,21 m2 (23/10/2026)
        cands = [f for f in cands if f.area >= 0.5e6 and not Polygon(f.exterior).buffer(-250, join_style="mitre").is_empty]
        if not cands:
            khong_vao.append((loai, p, nguon))
            continue
        f = min(cands, key=lambda g: g.area)
        k = id(f)
        z = phong.setdefault(k, dict(face=f, loai=set(), nguon=[], can=set()))
        z["loai"].add(loai)
        z["nguon"].append(nguon)
        if can:
            z["can"].add(can)
    # Lo gia / ban cong khong co thiet bi, khong co ten: o kin 1-12 m2, giap ngoai nha, co cua truot hoac lan can sat bien
    noi_that = doc_noi_that(ents)
    cay_nt = shapely.STRtree(noi_that) if noi_that else None
    truot = [LineString([p for s in c["doan"] for p in s]) for c in cuas if c.get("truot")]
    for f in faces:
        if id(f) in phong or not (LG_DT[0] <= f.area / 1e6 <= LG_DT[1]):
            continue
        if khung_xet is not None and not khung_xet.contains(f.representative_point()):
            continue
        if cay_nt is not None and len(cay_nt.query(f, predicate="contains")) > 0:
            continue                                    # co giuong / tu / sofa... -> phong o, khong phai lo gia
        if Polygon(f.exterior).buffer(-400, join_style="mitre").is_empty:
            continue                                    # rong < 800 mm: dai bau / khe tuong, khong phai lo gia
        vien = Polygon(f.exterior).buffer(250)
        ly_do = []
        if any(vien.intersects(t) and Polygon(f.exterior).buffer(-50).disjoint(t) for t in truot):
            ly_do.append("cửa trượt")
        if any(vien.intersects(l) for l in lan_can):
            ly_do.append("lan can")
        if ly_do and giap_ngoai_nha(Polygon(f.exterior), cay_face, faces):
            phong[id(f)] = dict(face=f, loai={"lo_gia"}, nguon=["giáp ngoài nhà + " + " + ".join(ly_do)], can=set())

    # Thiet bi / ten phong khong nam trong o kin nao: dung lai luoi net quanh do, them net mat ngoai (layer 0, A-line*)
    nhom = []
    for l, p, n in khong_vao:
        g = next((g for g in nhom if math.dist(g["diem"][0], p) <= 2000), None)
        if g is None:
            nhom.append(dict(loai=[l], diem=[p], nguon=[n]))
        else:
            g["loai"].append(l)
            g["diem"].append(p)
            g["nguon"].append(n)
    mat_ngoai = doc_mat_ngoai(ents) if nhom else []
    khong_vao = []
    for g in nhom:
        f, br = khep_lai(g["diem"], chains, khung, mat_ngoai, a.gap_max)
        if f is not None and (f.area < 0.5e6 or Polygon(f.exterior).buffer(-250, join_style="mitre").is_empty):
            f = None                                    # o hep (khe tuong / dai mep san) khong phai phong
        if f is None:
            khong_vao += list(zip(g["loai"], g["diem"], g["nguon"]))
            continue
        trung = next((z for z in phong.values() if z["face"].intersection(f).area > 0.5 * f.area), None)
        z = trung or phong.setdefault(id(f), dict(face=f, loai=set(), nguon=[], can=set()))
        z["loai"].update(g["loai"])
        z["nguon"] += g["nguon"] + ["khép bằng nét mặt ngoài (layer 0 / A-line)"]
        bridges = list(bridges) + list(br)

    # Phong rac / phong KT nuoc nhan theo ky hieu, ten: o phai co cua di, khong thi la hop ky thuat -> bo
    for k in list(phong):
        z = phong[k]
        if z["loai"] <= CAN_CUA and "chỉ định tay" not in z["nguon"] and not cua_quanh(z["face"], cuas):
            del phong[k]
            khong_vao.append((min(z["loai"]), (z["face"].centroid.x, z["face"].centroid.y),
                              "ký hiệu / tên phòng trong ô không có cửa đi (hộp kỹ thuật?)"))

    # Buong dem phong rac: o 1-10 m2 noi voi phong rac bang cua di NAM TRONG TUONG GIUA HAI O (khung cua cham bien ca
    # hai o <= 150) va co them it nhat 1 cua di khac (ra hanh lang); nhieu o dat thi lay o nho nhat. Thang may rac noi
    # voi phong rac bang tuong / o mo (khong cua) nen khong bi nhan; phong dem thang bo "Đ" o sat phong rac nhung cua
    # phong rac khong nam trong tuong chung nen cung bi loai (tang 4 Thap B).
    for z in [z for z in list(phong.values()) if "phong_rac" in z["loai"]]:
        cua_r = cua_quanh(z["face"], cuas)
        ung = []
        for f in faces:
            if id(f) in phong or f is z["face"] or not (1.0e6 <= f.area <= DT_BUONG_DEM * 1e6):
                continue
            if f.distance(z["face"]) > 400:
                continue
            cua_f = cua_quanh(f, cuas)
            chung = [i for i in cua_r if i in cua_f and
                     LineString([p for s in cuas[i]["doan"] for p in s]).distance(Polygon(f.exterior).exterior) <= 150 and
                     LineString([p for s in cuas[i]["doan"] for p in s]).distance(Polygon(z["face"].exterior).exterior) <= 150]
            if chung and len(cua_f) >= 2:
                ung.append(f)
        if ung:
            f = min(ung, key=lambda g: g.area)
            phong[id(f)] = dict(face=f, loai={"buong_dem_rac"}, nguon=["cửa đi sang phòng rác + cửa ra hành lang"],
                                can=set())

    can_idx = tim_can(ents)
    vung = []
    for z in sorted(phong.values(), key=lambda z: (-z["face"].centroid.y, z["face"].centroid.x)):
        f = z["face"]
        loai = min(z["loai"], key=lambda l: UU_TIEN[l])
        ghi = []
        g = don_gian(f)
        g, n_day = ve_mat_loi(g, cay_net, net)
        g = don_gian(g)
        if g.area < 0.5e6 or Polygon(g.exterior).buffer(-250, join_style="mitre").is_empty:
            # o hep (khe tuong / dai mep san) khong phai phong -> cho can xem (CT2: dai 1400 x 150, 23/10/2026)
            khong_vao.append((loai, (f.centroid.x, f.centroid.y), "ô hẹp < 500 mm, không phải phòng"))
            continue
        # dao: truc / hop ky thuat nam trong phong (>= 80% dien tich dao); khung lo mo thi chi can de len phong
        # (lo mo nam mot phan trong tuong van phai khoet phan de len phong)
        dao = []
        if cay_dao is not None:
            for k in cay_dao.query(g):
                q = dao_all[int(k)]
                de = q.intersection(g).area
                if (de >= 0.8 * q.area or (id(q) in la_lo_mo and de >= LO_MO_DE_MIN)) and q.area < 0.6 * g.area:
                    dao.append(q)
        lo = [Polygon(r) for r in g.interiors if Polygon(r).area >= 0.02e6]
        bo = Polygon(g.exterior)
        # dao cham bien phong (cot, hop sat tuong) -> khac vao duong bo, net ven di theo
        # khe giua dao va bien < khoang lui net ven (50) thi net ven se cat qua dao -> coi la cham (CT2: hop truc cach
        # bo 25 mm, nguoi dung bao loi 23/10/2026)
        cham = [q for q in dao if q.distance(bo.exterior) < a.cach_ven]
        if cham:
            g2 = bo.difference(unary_union(cham))
            # bo dai vun < 60 mm con lai giua dao va tuong (mau CH15: cot cach tuong 50 -> khac lien toi tuong)
            g2 = g2.buffer(-30, join_style="mitre").buffer(30, join_style="mitre")
            if g2.geom_type == "MultiPolygon":
                g2 = max(g2.geoms, key=lambda x: x.area)
            if g2.geom_type == "Polygon" and not g2.is_empty:
                bo = don_gian(Polygon(g2.exterior))
            dao = [q for q in dao if not any(q is c for c in cham)]
        # gieng thang may lan vao phong (khong co net tuong ngan): khoet gieng + dai o cua <= 300 trong chieu day tuong,
        # canh con lai giap o cua la cua thang may -> ngat net ven
        cua_tm = []
        for sh in gieng:
            if sh.intersection(bo).area < 0.05e6:
                continue
            # do khoet d: tang 10 mm/buoc; trong dai o cua dien tich khoet tang deu (= be rong o cua x 10), cham mat tuong
            # phong chinh thi tang dot bien -> dung o buoc truoc do
            ngoai = bo.difference(sh)
            dt = [ngoai.intersection(sh.buffer(d, join_style="mitre")).area for d in range(0, 410, 10)]
            buoc = [dt[i + 1] - dt[i] for i in range(len(dt) - 1)]
            d_ok = 0
            if buoc and buoc[0] > 0:
                for i, b_ in enumerate(buoc):
                    if b_ > 1.3 * buoc[0] + 1000:
                        break
                    d_ok = (i + 1) * 10
            bo2 = ngoai.difference(sh.buffer(d_ok, join_style="mitre")) if d_ok else ngoai
            bo2 = bo2.buffer(-30, join_style="mitre").buffer(30, join_style="mitre")
            if bo2.geom_type == "MultiPolygon":
                bo2 = max(bo2.geoms, key=lambda x: x.area)
            if bo2.is_empty or bo2.geom_type != "Polygon" or bo2.area < 0.5 * bo.area:
                continue
            bo_moi = don_gian(Polygon(bo2.exterior))
            # chi dai o cua (phan khoet ngoai gieng); khong dung bo - bo_moi vi phep tru de lai mep vun doc moi canh
            # dung truoc mat tuong 5 mm: o d_ok dai khoet cham mat phong chinh doc ca canh (dien tich 0)
            dai = ngoai.intersection(sh.buffer(max(d_ok - 5, 1), join_style="mitre")) if d_ok else sh
            chung = bo_moi.exterior.intersection(dai.buffer(10))
            bo = bo_moi
            if not chung.is_empty and chung.length >= 300:
                cua_tm.append(chung.buffer(300, cap_style="flat"))
            dao = [q for q in dao if q.intersection(bo).area > 0.5 * q.area]
            lo = [q for q in lo if q.intersection(bo).area > 0.5 * q.area]
            ghi.append("khoét giếng thang máy, ngắt nét vén ở cửa thang")
        vung_hatch = bo.difference(unary_union(dao + lo)) if (dao or lo) else bo
        # cat net ven tai cua di
        cut = list(cua_tm)
        n_cua = len(cua_tm)
        for c in cuas:
            if c["loai"] != "cua_di":
                continue
            pts = [p for s in c["doan"] for p in s]
            if Polygon(bo.exterior).buffer(300).intersects(LineString(pts) if len(pts) > 1 else Point(pts[0])):
                d = dai_cat_cua(bo, c)
                if d is not None:
                    cut.append(d)
                    n_cua += 1
        # cua thang may (o tuong khong hatch canh thang may co text tai trong) sat bien phong
        for g_ct in cua_thang:
            if g_ct.distance(bo.exterior) <= 50 and not bo.buffer(-20).contains(g_ct.centroid):
                d = dai_cat_cua(bo, dict(doan=[(p, q) for p, q in zip(g_ct.exterior.coords, list(g_ct.exterior.coords)[1:])]))
                if d is not None:
                    cut.append(d)
                    n_cua += 1
                    if "cửa thang máy" not in ghi:
                        ghi.append("cửa thang máy")
        # o kin khac cham thang vao bien phong (chi cach 1 net, khong co be day tuong) = o mo, vd. thang may rac thong
        # thang vao phong rac (CT1 tang 5A-10). Cua co khung / tuong co be day thi hai o cach nhau >= 100 nen khong bi cat.
        # Chi ap cho phong rac / buong dem: o WC, lo gia tang 4 Thap B quy tac nay cat nham 4 cho (day phong chi la 1 net).
        for k in (cay_face.query(f.buffer(30)) if loai in ("phong_rac", "buong_dem_rac") else []):
            nb = faces[int(k)]
            if nb is f or nb.area > 0.6 * f.area and nb.area > 20e6:
                continue
            if nb.buffer(-250, join_style="mitre").is_empty:
                continue                                # dai hep < 500 mm: long tuong / bau, khong phai o mo
            chung = f.exterior.intersection(nb.buffer(30))
            if chung.is_empty or chung.length < 300:
                continue
            cut.append(chung.buffer(300, cap_style="flat"))
            s = f"ô mở giáp ô kín bên cạnh {chung.length:.0f} mm"
            if s not in ghi:
                ghi.append(s)
        # o mo khong co cua (doan dong o mo nam tren bien phong, khong trung khung cua so)
        for br in bridges:
            if br.length < 300:
                continue
            if bo.exterior.buffer(5).contains(br) and not any(
                    LineString([p for s in c["doan"] for p in s][:2]).buffer(300).intersects(br) for c in cuas):
                cut.append(br.buffer(300, cap_style="flat"))
                s = f"ô mở không vẽ cửa {br.length:.0f} mm"
                if s not in ghi:
                    ghi.append(s)
        if os.environ.get("CT_DEBUG"):
            print("  [debug]", loai, [r1(v) for v in bo.bounds], "cat:", [[r1(v) for v in c.bounds] for c in cut])
        if bo.area < 0.5e6 or Polygon(bo.exterior).buffer(-250, join_style="mitre").is_empty:
            khong_vao.append((loai, (bo.centroid.x, bo.centroid.y), "ô hẹp < 500 mm sau khi khoét, không phải phòng"))
            continue
        ven = net_ven(bo, unary_union(cut) if cut else None, a.cach_ven)
        dt = bo.area / 1e6
        trang = "se_ve"
        if da_co is not None and vung_hatch.intersection(da_co).area >= 0.9 * vung_hatch.area:
            trang = "da_co"
        elif dt > a.dien_tich_max:
            trang = "can_xem"
            ghi.append(f"phòng lớn {dt:.1f} m² (có thể gộp nhầm với phòng khác)")
        elif n_cua == 0 and not any("ô mở" in s for s in ghi):
            ghi.append("không tìm thấy cửa đi - nét vén chạy kín")
        cx, cy = bo.centroid.x, bo.centroid.y
        if loai in CAN_CUA | {"buong_dem_rac"}:
            z["can"] = {"Khu chung"}                    # phong rac, buong dem, phong KT nuoc thuoc loi chung
        elif not z["can"] and can_idx is not None:
            cay_c, pts_c, ma_c = can_idx
            k = cay_c.nearest(Point(cx, cy))
            if k is not None and pts_c[int(k)].distance(bo) <= 3000:
                z["can"].add(ma_c[int(k)])
        vung.append(dict(
            id=len(vung) + 1, loai=loai, ten_loai=TEN_LOAI[loai], can=",".join(sorted(z["can"])),
            nguon=sorted(set(z["nguon"]))[:8], dien_tich=round(dt, 2), tam=[r1(cx), r1(cy)],
            bo=[[r1(x), r1(y)] for x, y in list(bo.exterior.coords)[:-1]],
            dao=[[[r1(x), r1(y)] for x, y in list(Polygon(q.exterior).exterior.coords)[:-1]] for q in dao + lo],
            ven=[dict(dong=dg, dinh=[[x, y] for x, y in pts]) for dg, pts in ven],
            so_cua=n_cua, canh_day_ra_mat_loi=n_day, trang_thai=trang, ghi_chu="; ".join(ghi)))

    # hat giong khong roi vao o kin nao: gom theo vi tri (<= 2 m) -> "cho can xem" (phong ho, tuong ve net manh)
    lot = []
    for l, p, n in khong_vao:
        g = next((g for g in lot if math.dist(g["diem"], p) <= 2000), None)
        if g is None:
            lot.append(dict(loai=l, diem=[r1(p[0]), r1(p[1])], nguon=[n]))
        else:
            g["nguon"].append(n)
    kq = dict(file=a.dxf, cach_ven=a.cach_ven, layer=LAYER_VE, vung=vung, cho_can_xem=lot)
    jp = os.path.join(a.out_dir, ten + "_chongtham.json")
    with open(jp, "w", encoding="utf-8") as fo:
        json.dump(kq, fo, ensure_ascii=False, indent=1)
    if a.excel:
        xuat_excel(vung, lot, os.path.join(a.out_dir, ten + "_chongtham.xlsx"))
    if a.xuat_lsp:
        xuat_lsp(vung, lot, a.xuat_lsp)
    if not a.khong_anh:
        xuat_anh(vung, net, cuas, lot, os.path.join(a.out_dir, ten + "_chongtham.png"), khung_xet)
    dem = defaultdict(int)
    for v in vung:
        dem[(v["trang_thai"], v["loai"])] += 1
    print("Ket qua:", dict(dem))
    print("Cho can xem (thiet bi / ten phong khong nam trong o kin nao):", len(lot))
    for g in lot:
        print("  ", g["loai"], g["diem"], ", ".join(sorted(set(g["nguon"])))[:80])
    print(jp)


def xuat_lsp(vung, lot, path):
    """Du lieu cho lenh LISP CHONGTHAM, chi ky tu ASCII (doc bang read-line + read, khong phu thuoc ma hoa):
       (VUNG id "loai" "trang_thai" "can" ((x y) ...) (((x y) ...) ...) ((dong ((x y) ...)) ...))
       (XEM "loai" x y "nguon")"""
    def s(v):
        return '"' + bo_dau(str(v)).encode("ascii", "replace").decode().replace("\\", "/").replace('"', "'") + '"'

    def ds(pts):
        return "(" + " ".join(f"({x:.1f} {y:.1f})" for x, y in pts) + ")"

    with open(path, "w", encoding="ascii", newline="\r\n") as fo:
        for v in vung:
            dao = "(" + " ".join(ds(d) for d in v["dao"]) + ")"
            ven = "(" + " ".join(f"({1 if l['dong'] else 0} {ds(l['dinh'])})" for l in v["ven"]) + ")"
            fo.write(f"(VUNG {v['id']} {s(v['loai'])} {s(v['trang_thai'])} {s(v['can'])} {ds(v['bo'])} {dao} {ven})\n")
        for g in lot:
            fo.write(f"(XEM {s(g['loai'])} {g['diem'][0]:.1f} {g['diem'][1]:.1f} {s(', '.join(sorted(set(g['nguon']))))})\n")


def xuat_excel(vung, lot, path):
    try:
        from openpyxl import Workbook
    except ImportError:
        return
    wb = Workbook()
    ws = wb.active
    ws.title = "Chống thấm"
    ws.append(["STT", "Loại", "Căn", "Trạng thái", "Diện tích (m²)", "Tâm X", "Tâm Y", "Số cửa đi", "Số đảo",
               "Số đoạn nét vén", "Nhận theo", "Ghi chú"])
    for v in vung:
        ws.append([v["id"], v["ten_loai"], v["can"], v["trang_thai"], v["dien_tich"], v["tam"][0], v["tam"][1],
                   v["so_cua"], len(v["dao"]), len(v["ven"]), ", ".join(v["nguon"]), v["ghi_chu"]])
    for col, w in zip("ABCDEFGHIJKL", (6, 18, 8, 10, 12, 10, 10, 9, 8, 12, 50, 50)):
        ws.column_dimensions[col].width = w
    ws2 = wb.create_sheet("Chỗ cần xem")
    ws2.append(["STT", "Loại", "X", "Y", "Nhận theo", "Ghi chú"])
    for i, g in enumerate(lot, 1):
        ws2.append([i, TEN_LOAI.get(g["loai"], g["loai"]), g["diem"][0], g["diem"][1], ", ".join(sorted(set(g["nguon"]))),
                    "Không khép được phòng (tường vẽ nét mảnh / hở một phía) - vẽ tay hoặc chạy lại với --them"])
    for col, w in zip("ABCDEF", (6, 18, 10, 10, 50, 70)):
        ws2.column_dimensions[col].width = w
    try:
        wb.save(path)
    except PermissionError:
        print("Khong ghi duoc Excel (dang mo?):", path)


def xuat_anh(vung, net, cuas, lot, path, khung_xet):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if khung_xet is not None:
        x0, y0, x1, y1 = khung_xet.bounds
    elif vung:
        xs = [p[0] for v in vung for p in v["bo"]]
        ys = [p[1] for v in vung for p in v["bo"]]
        x0, x1, y0, y1 = min(xs) - 3000, max(xs) + 3000, min(ys) - 3000, max(ys) + 3000
    else:
        return
    W = 24
    fig = plt.figure(figsize=(W, max(4, W * (y1 - y0) / max(x1 - x0, 1))))
    ax = fig.add_axes([0, 0, 1, 1])
    kx = box(x0, y0, x1, y1)
    for s in net:
        if s.intersects(kx):
            xs, ys = s.xy
            ax.plot(xs, ys, color="#9a9a9a", lw=0.3)
    for c in cuas:
        for p, q in c["doan"]:
            ax.plot([p[0], q[0]], [p[1], q[1]], color="#c8a060" if c["loai"] == "cua_di" else "#60a0c8", lw=0.4)
    mau = {"se_ve": "#22aa22", "da_co": "#888888", "can_xem": "#ff8800"}
    for v in vung:
        b = v["bo"] + [v["bo"][0]]
        ax.fill([p[0] for p in b], [p[1] for p in b], color=mau[v["trang_thai"]], alpha=0.25, lw=0)
        ax.plot([p[0] for p in b], [p[1] for p in b], color=mau[v["trang_thai"]], lw=0.8)
        for d in v["dao"]:
            d2 = d + [d[0]]
            ax.fill([p[0] for p in d2], [p[1] for p in d2], color="white", lw=0.5, ec="#2255ff")
        for l in v["ven"]:
            pts = l["dinh"] + ([l["dinh"][0]] if l["dong"] else [])
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color="red", lw=1.2)
        ax.text(v["tam"][0], v["tam"][1], f'{v["id"]}\n{v["ten_loai"].split(" /")[0]}', ha="center", va="center",
                fontsize=6, color="black")
    for i, g in enumerate(lot, 1):
        ax.plot([g["diem"][0]], [g["diem"][1]], marker="X", ms=12, color="#ff8800")
        ax.text(g["diem"][0] + 400, g["diem"][1], f"Xem {i}", fontsize=7, color="#ff5500")
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
