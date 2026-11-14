# -*- coding: utf-8 -*-
"""Trích xuất bản vẽ chi tiết CAD (DXF) thành dữ liệu cho legend Revit.

Đầu vào : DXF gốc + DXF REGION / 3DSOLID đã nổ (acc\\regions2_no.dxf, tach_region.py) + regions.json
Đầu ra  : ct_cua.json gồm các ô chi tiết; mỗi ô có nét (đã gộp nét trùng), cung, đường tròn, vùng hatch,
          vùng che (wipeout), chữ, dim. Toạ độ mm, đã dời về bố cục legend (các ô cách nhau KHE mm).

Chạy: python trich_xuat.py <dxf gốc> <regions_no.dxf> <regions.json> <ra.json>
"""
import sys, json, math, re, collections
import ezdxf
from ezdxf.math import Matrix44, Vec3
from ezdxf import colors as ezcolors
from shapely.geometry import LineString
from shapely.ops import polygonize, unary_union

TOL_NOI = 0.5        # mm, coi 2 điểm trùng
NGAN_NHAT = 1.0      # mm, nét ngắn hơn thì bỏ (Revit không tạo được nét quá ngắn)
CONG_SAI = 0.5       # mm, độ võng khi chia spline / ellipse thành nét thẳng
KHE = 1000.0         # mm, khoảng hở giữa các ô trong legend (= 50 mm giấy ở 1:20)
TI_LE = 20

src_path, reg_path, regjs_path, out_path = sys.argv[1:5]
doc = ezdxf.readfile(src_path)
msp = doc.modelspace()

# ---------------------------------------------------------------- thuộc tính hiệu lực (ByLayer / ByBlock)
LAYERS = {l.dxf.name: l for l in doc.layers}


def lay_layer(e, cha):
    lay = e.dxf.get('layer', '0')
    if lay == '0' and cha is not None:
        return cha['layer']
    return lay


def thuoc_tinh(e, cha):
    """Trả về dict layer / aci / rgb / ltype / lw đã giải ByLayer / ByBlock."""
    lay = lay_layer(e, cha)
    L = LAYERS.get(lay)
    # màu
    aci = e.dxf.get('color', 256)
    rgb = e.rgb if e.dxf.hasattr('true_color') else None
    if aci == 0 and cha is not None:          # ByBlock
        aci, rgb = cha['aci'], cha['rgb']
    elif aci == 256:                          # ByLayer
        aci = L.color if L is not None else 7
        rgb = L.rgb if (L is not None and L.dxf.hasattr('true_color')) else None
    # kiểu nét
    lt = e.dxf.get('linetype', 'BYLAYER')
    if lt.upper() == 'BYBLOCK':
        lt = cha['ltype'] if cha is not None else 'CONTINUOUS'
    elif lt.upper() == 'BYLAYER':
        lt = L.dxf.get('linetype', 'CONTINUOUS') if L is not None else 'CONTINUOUS'
    # bề dày nét
    lw = e.dxf.get('lineweight', -1)
    if lw == -2:
        lw = cha['lw'] if cha is not None else -3
    elif lw == -1:
        lw = L.dxf.get('lineweight', -3) if L is not None else -3
    return {'layer': lay, 'aci': aci, 'rgb': tuple(rgb) if rgb else None, 'ltype': lt, 'lw': lw}


def kieu_net(tt):
    """Xếp nét vào 5 kiểu Revit dựng sẵn: thin / medium / wide / hidden / center."""
    n = (tt['ltype'] or '').upper()
    if any(k in n for k in ('CENTER', 'DASHDOT', 'PHANTOM', 'TRUC', 'CHAIN')):
        return 'center'
    if any(k in n for k in ('HIDDEN', 'DASH', 'KHUAT', 'DOT', 'DOTTED', 'DUT')):
        return 'hidden'
    lw = tt['lw']
    if lw is None or lw < 15:
        return 'thin'
    if lw < 35:
        return 'medium'
    return 'wide'


UU_TIEN = {'wide': 5, 'medium': 4, 'thin': 3, 'center': 2, 'hidden': 1}


def mau_rgb(tt):
    if tt['rgb']:
        return list(tt['rgb'])
    a = tt['aci']
    if a in (7, 0, 256, None):
        return [0, 0, 0]
    return list(ezcolors.aci2rgb(a))


XAM = {8, 9, 250, 251, 252, 253, 254}

# ---------------------------------------------------------------- tích luỹ hình học (toạ độ bản vẽ, mm)
seg_raw = []      # (x1,y1,x2,y2,kieu,z)
arc_raw = []      # (cx,cy,r,a0,a1,kieu,z)  a0<a1 độ, ngược chiều kim đồng hồ; đường tròn a0=0,a1=360
vung = []         # {'loops':[...], 'kieu':key, 'z':z}
che = []          # {'loops':[...], 'z':z}
chu = []          # {...}
dims = []         # {...}
mau_hatch = {}    # key -> định nghĩa mẫu
bao_cao = collections.Counter()
Z = [0]


def z_moi():
    Z[0] += 1
    return Z[0]


def la_dong_dang(m):
    """m là phép đồng dạng (tỉ lệ đều) trong mặt phẳng XY? Trả về (đúng/sai, tỉ lệ)."""
    if m is None:
        return True, 1.0
    ux = m.transform_direction(Vec3(1, 0, 0))
    uy = m.transform_direction(Vec3(0, 1, 0))
    sx, sy = ux.magnitude, uy.magnitude
    vuong = abs(ux.x * uy.x + ux.y * uy.y) < 1e-6 * max(sx * sy, 1e-9)
    return (abs(sx - sy) < 1e-6 * max(sx, 1e-9) and vuong), sx


def tf(m, p):
    p = Vec3(p)
    return m.transform(p) if m is not None else p


def them_seg(p, q, kieu, z):
    if math.hypot(q[0] - p[0], q[1] - p[1]) < 1e-6:
        return
    seg_raw.append((p[0], p[1], q[0], q[1], kieu, z))


def cung_3_diem(p0, pm, p1):
    """Tâm, bán kính, góc đầu, góc cuối (CCW) của cung qua 3 điểm; None nếu thẳng hàng."""
    ax, ay = p0[0], p0[1]; bx, by = pm[0], pm[1]; cx, cy = p1[0], p1[1]
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-9:
        return None
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    r = math.hypot(ax - ux, ay - uy)
    a0 = math.degrees(math.atan2(ay - uy, ax - ux))
    am = math.degrees(math.atan2(by - uy, bx - ux))
    a1 = math.degrees(math.atan2(cy - uy, cx - ux))
    # chiều: p0 -> pm -> p1 theo CCW?
    def ccw_tu(a, b):
        return (b - a) % 360.0
    if ccw_tu(a0, am) <= ccw_tu(a0, a1):
        s, e = a0, a0 + ccw_tu(a0, a1)
    else:
        s, e = a1, a1 + ccw_tu(a1, a0)
    return ux, uy, r, s, e


def them_cung_wcs(pts_wcs, m, kieu, z, day_du=False, tam=None, r=None):
    """pts_wcs: 3 điểm đầu / giữa / cuối của cung (toạ độ trước m). day_du: đường tròn."""
    dd, s = la_dong_dang(m)
    if day_du:
        c = tf(m, tam)
        arc_raw.append((c.x, c.y, r * s, 0.0, 360.0, kieu, z))
        return
    p0, pm, p1 = (tf(m, p) for p in pts_wcs)
    kq = cung_3_diem(p0, pm, p1)
    if kq is None:
        them_seg(p0, p1, kieu, z)
        return
    cx, cy, rr, a0, a1 = kq
    arc_raw.append((cx, cy, rr, a0, a1, kieu, z))


def them_duong_gay(pts, kieu, z, kin=False):
    """Chuỗi điểm (đã đổi toạ độ) -> nét thẳng, gộp điểm sát nhau để không có nét quá ngắn."""
    if len(pts) < 2:
        return
    gon = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - gon[-1][0], p[1] - gon[-1][1]) >= NGAN_NHAT * 1.2:
            gon.append(p)
    if len(gon) == 1 or math.hypot(pts[-1][0] - gon[-1][0], pts[-1][1] - gon[-1][1]) > 1e-6:
        if len(gon) > 1 and math.hypot(pts[-1][0] - gon[-1][0], pts[-1][1] - gon[-1][1]) < NGAN_NHAT * 1.2:
            gon[-1] = pts[-1]
        else:
            gon.append(pts[-1])
    for a, b in zip(gon, gon[1:]):
        them_seg(a, b, kieu, z)


def chia_duong(e, m):
    """Spline / ellipse / cung không đồng dạng -> danh sách điểm đã đổi toạ độ."""
    try:
        p = ezdxf.path.make_path(e)
        if m is not None:
            p = p.transform(m)
        return [(v.x, v.y) for v in p.flattening(CONG_SAI)]
    except Exception:
        bao_cao['khong_chia_duoc_' + e.dxftype()] += 1
        return []


# ---------------------------------------------------------------- hatch
def khoa_mau(h, tt):
    """Khoá kiểu filled region + lưu định nghĩa mẫu."""
    if h.dxf.solid_fill:
        rgb = mau_rgb(tt)
        if h.dxf.get('hatch_style', 0) is not None and getattr(h, 'gradient', None) is not None and h.gradient:
            try:
                rgb = list(h.gradient.color1) if h.gradient.color1 else rgb
            except Exception:
                pass
        k = 'SOLID_%d_%d_%d' % tuple(rgb)
        mau_hatch.setdefault(k, {'solid': True, 'rgb': rgb, 'ten': 'Đặc %d,%d,%d' % tuple(rgb)})
        return k
    lines = []
    for pl in h.pattern.lines if h.pattern else []:
        lines.append([round(pl.angle % 360.0, 4), round(pl.base_point[0], 4), round(pl.base_point[1], 4),
                      round(pl.offset[0], 4), round(pl.offset[1], 4), [round(d, 4) for d in pl.dash_length_items]])
    if not lines:
        k = 'SOLID_0_0_0'
        mau_hatch.setdefault(k, {'solid': True, 'rgb': [0, 0, 0], 'ten': 'Đặc 0,0,0'})
        return k
    rgb = mau_rgb(tt) if tt['aci'] in XAM else [0, 0, 0]
    # bỏ điểm gốc khỏi khoá (chỉ ảnh hưởng vị trí, không ảnh hưởng hình mẫu)
    ky = json.dumps([[l[0], l[3], l[4], l[5]] for l in lines]) + str(rgb)
    k = 'P%05d' % (abs(hash(ky)) % 100000)
    while k in mau_hatch and mau_hatch[k]['ky'] != ky:
        k += 'b'
    if k not in mau_hatch:
        ten = '%s %s %g°' % (h.dxf.pattern_name, ('%g' % round(h.dxf.pattern_scale, 3)), round(h.dxf.pattern_angle % 360, 1))
        mau_hatch[k] = {'solid': False, 'rgb': rgb, 'ky': ky, 'lines': lines, 'ten': ten}
    return k


def vong_hatch(h):
    """Các vòng biên của hatch (toạ độ WCS của hatch, trước khi nhân m) dưới dạng primitive."""
    ocs = h.ocs()
    elev = h.dxf.elevation.z if h.dxf.hasattr('elevation') else 0.0
    vongs = []
    for path in h.paths:
        prims = []
        t = type(path).__name__
        if t == 'PolylinePath':
            v = list(path.vertices)
            n = len(v)
            for i in range(n if path.is_closed or True else n - 1):
                x0, y0, b = v[i][0], v[i][1], (v[i][2] if len(v[i]) > 2 else 0.0)
                x1, y1 = v[(i + 1) % n][0], v[(i + 1) % n][1]
                p0 = ocs.to_wcs(Vec3(x0, y0, elev)); p1 = ocs.to_wcs(Vec3(x1, y1, elev))
                if abs(b) > 1e-9:
                    # điểm giữa cung theo bulge
                    dx, dy = x1 - x0, y1 - y0
                    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
                    s = b * math.hypot(dx, dy) / 2
                    nx, ny = dy, -dx
                    ln = math.hypot(nx, ny) or 1
                    pm = ocs.to_wcs(Vec3(mx + nx / ln * s, my + ny / ln * s, elev))
                    prims.append(('A', p0, pm, p1))
                else:
                    prims.append(('L', p0, p1))
        else:
            for ed in path.edges:
                et = type(ed).__name__
                if et == 'LineEdge':
                    prims.append(('L', ocs.to_wcs(Vec3(ed.start[0], ed.start[1], elev)),
                                  ocs.to_wcs(Vec3(ed.end[0], ed.end[1], elev))))
                elif et == 'ArcEdge':
                    a0, a1 = ed.start_angle, ed.end_angle
                    c, r = ed.center, ed.radius
                    if ed.ccw:
                        if a1 < a0: a1 += 360
                        angs = (a0, (a0 + a1) / 2, a1)
                    else:
                        # góc lưu theo chiều kim đồng hồ: đảo dấu
                        a0, a1 = -a0, -a1
                        if a0 < a1: a0 += 360
                        angs = (a0, (a0 + a1) / 2, a1)
                    pts = [ocs.to_wcs(Vec3(c[0] + r * math.cos(math.radians(a)), c[1] + r * math.sin(math.radians(a)), elev)) for a in angs]
                    if abs(angs[2] - angs[0]) >= 359.999:
                        pm2 = ocs.to_wcs(Vec3(c[0] - r, c[1], elev)); p0 = ocs.to_wcs(Vec3(c[0] + r, c[1], elev))
                        prims.append(('A', p0, ocs.to_wcs(Vec3(c[0], c[1] + r, elev)), pm2))
                        prims.append(('A', pm2, ocs.to_wcs(Vec3(c[0], c[1] - r, elev)), p0))
                    else:
                        prims.append(('A', pts[0], pts[1], pts[2]))
                elif et in ('EllipseEdge', 'SplineEdge'):
                    try:
                        if et == 'EllipseEdge':
                            from ezdxf.math import ConstructionEllipse
                            a0, a1 = math.radians(ed.start_angle), math.radians(ed.end_angle)
                            if not ed.ccw:
                                a0, a1 = -a0, -a1
                            ce = ConstructionEllipse(center=Vec3(ed.center[0], ed.center[1], 0), major_axis=Vec3(ed.major_axis[0], ed.major_axis[1], 0),
                                                     ratio=ed.ratio, start_param=a0, end_param=a1, ccw=ed.ccw)
                            pts = list(ce.flattening(CONG_SAI))
                        else:
                            from ezdxf.math import BSpline
                            if ed.control_points:
                                bs = BSpline([Vec3(p[0], p[1], 0) for p in ed.control_points], order=ed.degree + 1,
                                             knots=ed.knot_values or None, weights=ed.weights or None)
                            else:
                                from ezdxf.math import fit_points_to_cad_cv
                                bs = fit_points_to_cad_cv([Vec3(p[0], p[1], 0) for p in ed.fit_points])
                            pts = list(bs.flattening(CONG_SAI))
                        pts = [ocs.to_wcs(Vec3(p.x, p.y, elev)) for p in pts]
                        for a, b in zip(pts, pts[1:]):
                            prims.append(('L', a, b))
                    except Exception:
                        bao_cao['hatch_canh_loi_' + et] += 1
        if prims:
            vongs.append(prims)
    return vongs


def vong_sang_toa_do(prims, m):
    """Primitive (trước m) -> danh sách đoạn {'L':[x0,y0,x1,y1]} / {'A':[x0,y0,xm,ym,x1,y1]} sau m, đã nối kín."""
    dd, s = la_dong_dang(m)
    out = []
    for pr in prims:
        if pr[0] == 'L':
            a, b = tf(m, pr[1]), tf(m, pr[2])
            out.append(['L', a.x, a.y, b.x, b.y])
        else:
            if dd:
                a, c, b = tf(m, pr[1]), tf(m, pr[2]), tf(m, pr[3])
                out.append(['A', a.x, a.y, c.x, c.y, b.x, b.y])
            else:
                # cung qua phép biến dạng: chia thẳng
                kq = cung_3_diem(pr[1], pr[2], pr[3])
                if kq is None:
                    a, b = tf(m, pr[1]), tf(m, pr[3]); out.append(['L', a.x, a.y, b.x, b.y]); continue
                cx, cy, r, a0, a1 = kq
                # giữ đúng chiều p1 -> p3
                st = math.degrees(math.atan2(pr[1][1] - cy, pr[1][0] - cx))
                n = max(4, int(abs(a1 - a0) / 5))
                d = (a1 - a0) / n
                if abs(((st - a0 + 180) % 360) - 180) > 1e-3:
                    angs = [a1 - i * d for i in range(n + 1)]
                else:
                    angs = [a0 + i * d for i in range(n + 1)]
                pts = [tf(m, (cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t)), 0)) for t in angs]
                for p, q in zip(pts, pts[1:]):
                    out.append(['L', p.x, p.y, q.x, q.y])
    return lam_kin(out)


def dau(sg):
    return (sg[1], sg[2])


def cuoi(sg):
    return (sg[-2], sg[-1])


def lam_kin(sgs):
    """Bỏ đoạn quá ngắn, nối đầu - cuối các đoạn liên tiếp, đóng vòng."""
    sgs = [s for s in sgs if math.hypot(cuoi(s)[0] - dau(s)[0], cuoi(s)[1] - dau(s)[1]) >= NGAN_NHAT * 1.0 or s[0] == 'A']
    if not sgs:
        return []
    # cung quá nhỏ -> bỏ
    ok = []
    for s in sgs:
        if s[0] == 'A' and math.hypot(s[5] - s[1], s[6] - s[2]) < NGAN_NHAT * 1.0:
            kq = cung_3_diem((s[1], s[2]), (s[3], s[4]), (s[5], s[6]))
            if kq is None or kq[2] * math.radians(kq[4] - kq[3]) < NGAN_NHAT * 2:
                continue
        ok.append(s)
    sgs = ok
    kq = []
    for i, s in enumerate(sgs):
        s = list(s)
        if kq:
            p = cuoi(kq[-1]); q = dau(s)
            g = math.hypot(p[0] - q[0], p[1] - q[1])
            if g > TOL_NOI:
                kq.append(['L', p[0], p[1], q[0], q[1]])
            else:
                s[1], s[2] = p
        kq.append(s)
    if len(kq) >= 1:
        p = cuoi(kq[-1]); q = dau(kq[0])
        g = math.hypot(p[0] - q[0], p[1] - q[1])
        if g > TOL_NOI:
            kq.append(['L', p[0], p[1], q[0], q[1]])
        else:
            kq[-1][-2], kq[-1][-1] = q
    # đoạn thẳng sau khi nối có thể quá ngắn: gộp vào đoạn trước
    gon = []
    for s in kq:
        if s[0] == 'L' and math.hypot(s[3] - s[1], s[4] - s[2]) < NGAN_NHAT * 1.0:
            if gon:
                gon[-1][-2], gon[-1][-1] = s[3], s[4]
            continue
        gon.append(s)
    if len(gon) >= 2:
        q = dau(gon[0]); gon[-1][-2], gon[-1][-1] = q
    tong = sum(math.hypot(cuoi(s)[0] - dau(s)[0], cuoi(s)[1] - dau(s)[1]) for s in gon)
    if len(gon) < 2 or tong < NGAN_NHAT * 4:
        return []
    return [[round(v, 3) if isinstance(v, float) else v for v in s] for s in gon]


# ---------------------------------------------------------------- chữ
def font_cua(style_name):
    try:
        st = doc.styles.get(style_name)
        f = (st.dxf.font or '').lower()
        wf = st.dxf.get('width', 1.0) or 1.0
    except Exception:
        f, wf = '', 1.0
    if 'tahoma' in f:
        return 'Tahoma', wf
    if 'times' in f:
        return 'Times New Roman', wf
    return 'Arial', wf


def them_chu(noi_dung, p, h, rot, ngang, doc_, font, wf, z):
    noi_dung = noi_dung.replace('\r', '').replace('\t', ' ').strip('\n')
    if not noi_dung.strip() or h <= 0:
        return
    chu.append({'t': noi_dung, 'x': round(p[0], 2), 'y': round(p[1], 2), 'h': round(h, 2), 'rot': round(rot % 360, 3),
                'ngang': ngang, 'doc': doc_, 'font': font, 'wf': round(wf, 2), 'z': z})


def xu_ly_text(e, m, tt, z):
    c = e.copy()
    try:
        if m is not None:
            c.transform(m)
    except Exception:
        bao_cao['text_khong_bien_doi'] += 1
        return
    try:
        align, p1, p2 = c.get_placement()
    except Exception:
        align, p1, p2 = None, c.dxf.insert, None
    h = c.dxf.height
    rot = c.dxf.rotation
    font, wf = font_cua(c.dxf.get('style', 'Standard'))
    wf = c.dxf.get('width', wf) or wf
    an = align.name if align is not None else 'LEFT'
    ngang = 'L'
    if 'CENTER' in an or an in ('MIDDLE', 'ALIGNED', 'FIT'):
        ngang = 'C'
    if 'RIGHT' in an:
        ngang = 'R'
    if an in ('ALIGNED', 'FIT') and p2 is not None:
        p = Vec3((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, 0)
        dichz = h / 2
    else:
        p = Vec3(p1)
        if an.startswith('TOP'):
            dichz = -h / 2
        elif an.startswith('MIDDLE') or an == 'MIDDLE':
            dichz = 0.0
        elif an.startswith('BOTTOM'):
            dichz = h / 2 + h * 0.2
        else:  # baseline
            dichz = h / 2
    # dịch vuông góc theo hướng chữ để neo vào giữa chiều cao chữ
    r = math.radians(rot)
    p = (p[0] - math.sin(r) * dichz, p[1] + math.cos(r) * dichz)
    t = c.plain_text()
    them_chu(t, p, h, rot, ngang, 'M', font, wf, z)


def xu_ly_mtext(e, m, tt, z):
    c = e.copy()
    try:
        if m is not None:
            c.transform(m)
    except Exception:
        bao_cao['mtext_khong_bien_doi'] += 1
        return
    ap = c.dxf.get('attachment_point', 1)
    ngang = {1: 'L', 2: 'C', 3: 'R'}[(ap - 1) % 3 + 1]
    doc_ = {0: 'T', 1: 'M', 2: 'B'}[(ap - 1) // 3]
    font, wf = font_cua(c.dxf.get('style', 'Standard'))
    try:
        t = c.plain_text(split=False)
    except Exception:
        t = c.text
    them_chu(t, c.dxf.insert, c.dxf.char_height, c.get_rotation(), ngang, doc_, font, wf, z)


# ---------------------------------------------------------------- dim
def xu_ly_dim(e, m, tt, cha, z):
    c = e.copy()
    try:
        if m is not None:
            c.transform(m)
    except Exception:
        bao_cao['dim_khong_bien_doi_no'] += 1
        no_ra(e, m, tt, cha)
        return
    dt = c.dimtype
    if dt not in (0, 1):
        no_ra(c, None, tt, cha)
        bao_cao['dim_khac_no'] += 1
        return
    try:
        p1 = Vec3(c.dxf.defpoint); p2 = Vec3(c.dxf.defpoint2); p3 = Vec3(c.dxf.defpoint3)
    except Exception:
        no_ra(c, None, tt, cha); return
    if dt == 0:
        ang = c.dxf.get('angle', 0.0)
    else:
        ang = math.degrees(math.atan2(p3.y - p2.y, p3.x - p2.x))
    try:
        from ezdxf.entities.dimstyleoverride import DimStyleOverride
        ov = DimStyleOverride(c)
        txt_h = (ov.get('dimtxt', 2.5) or 2.5) * (ov.get('dimscale', 1.0) or 1.0)
        lfac = ov.get('dimlfac', 1.0) or 1.0
        dec = ov.get('dimdec', 0)
        rnd = ov.get('dimrnd', 0) or 0
    except Exception:
        txt_h, lfac, dec, rnd = 50.0, 1.0, 0, 0
    dirv = Vec3(math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0)
    do_hinh = abs((p3 - p2).dot(dirv))
    gia_tri = do_hinh * lfac
    if rnd:
        gia_tri = round(gia_tri / rnd) * rnd
    so = ('%.' + str(int(dec)) + 'f') % gia_tri if dec else '%d' % round(gia_tri)
    text = c.dxf.get('text', '') or ''
    if text in ('', '<>'):
        hien = so
        tien_to = hau_to = ''
    elif '<>' in text:
        tien_to, hau_to = text.split('<>', 1)
        hien = so
    else:
        hien = text
        tien_to = hau_to = ''
    def sach(s):
        s = re.sub(r'\\[A-Za-z][^;]*;', '', s).replace('\\P', ' ').replace('{', '').replace('}', '')
        return s.replace('%%c', 'Ø').replace('%%C', 'Ø').replace('%%d', '°').replace('%%p', '±')
    if do_hinh < NGAN_NHAT:
        bao_cao['dim_qua_ngan'] += 1
        return
    dims.append({'p1': [round(p1.x, 3), round(p1.y, 3)], 'p2': [round(p2.x, 3), round(p2.y, 3)], 'p3': [round(p3.x, 3), round(p3.y, 3)],
                 'ang': round(ang, 5), 'h': round(txt_h, 2), 'gia_tri': round(do_hinh, 3),
                 'hien': sach(hien), 'tien_to': sach(tien_to), 'hau_to': sach(hau_to), 'z': z})


# ---------------------------------------------------------------- REGION / 3DSOLID đã nổ bằng AutoCAD
reg_doc = ezdxf.readfile(reg_path)
REG = collections.defaultdict(list)
for e in reg_doc.modelspace():
    REG[e.dxf.layer].append(e)
REG_I = [0]


def xu_ly_region(e, m, tt, z):
    i = REG_I[0]; REG_I[0] += 1
    kieu = kieu_net(tt)
    for r in REG.get('R%d' % i, []):
        t = r.dxftype()
        if t == 'LINE':
            a, b = tf(m, r.dxf.start), tf(m, r.dxf.end)
            them_seg(a, b, kieu, z)
        elif t in ('ARC', 'CIRCLE') and abs(abs(r.dxf.extrusion[2]) - 1) < 1e-6:
            if t == 'CIRCLE':
                them_cung_wcs(None, m, kieu, z, day_du=True, tam=r.ocs().to_wcs(r.dxf.center), r=r.dxf.radius)
            else:
                a0, a1 = r.dxf.start_angle, r.dxf.end_angle
                if a1 < a0: a1 += 360
                pts = list(r.vertices([a0, (a0 + a1) / 2, a1]))
                them_cung_wcs(pts, m, kieu, z)
        else:
            pts = chia_duong(r, m)
            them_duong_gay(pts, kieu, z)


# ---------------------------------------------------------------- duyệt bản vẽ
def no_ra(e, m, tt, cha):
    """Nổ đối tượng phức (dim, leader, multileader) bằng virtual_entities rồi duyệt tiếp."""
    try:
        ve = list(e.virtual_entities())
    except Exception:
        bao_cao['khong_no_duoc_' + e.dxftype()] += 1
        return
    duyet(ve, m, tt)


def duyet(ents, m, cha):
    for e in ents:
        t = e.dxftype()
        if t in ('ATTDEF', 'POINT', 'VIEWPORT'):
            continue
        if e.dxf.get('invisible', 0):
            continue
        tt = thuoc_tinh(e, cha)
        L = LAYERS.get(tt['layer'])
        if L is not None and (L.is_off() or L.is_frozen()):
            continue
        if t == 'INSERT':
            blk = doc.blocks.get(e.dxf.name)
            if blk is None:
                continue
            ins_list = list(e.multi_insert()) if e.mcount > 1 else [e]
            for ins in ins_list:
                mi = ins.matrix44() if m is None else ins.matrix44() @ m
                duyet(blk.entities_in_redraw_order(), mi, tt)
            for a in e.attribs:
                if not a.dxf.get('invisible', 0) and not a.is_invisible:
                    tta = thuoc_tinh(a, cha)
                    xu_ly_text(a, m, tta, z_moi())
            continue
        z = z_moi()
        kieu = kieu_net(tt)
        if t == 'LINE':
            them_seg(tf(m, e.dxf.start), tf(m, e.dxf.end), kieu, z)
        elif t in ('LWPOLYLINE', 'POLYLINE'):
            if t == 'POLYLINE' and (e.is_poly_face_mesh or e.is_polygon_mesh):
                bao_cao['bo_mesh'] += 1
                continue
            dd, s = la_dong_dang(m)
            try:
                for ve in e.virtual_entities():
                    if ve.dxftype() == 'LINE':
                        them_seg(tf(m, ve.dxf.start), tf(m, ve.dxf.end), kieu, z)
                    elif ve.dxftype() == 'ARC':
                        if dd:
                            a0, a1 = ve.dxf.start_angle, ve.dxf.end_angle
                            if a1 < a0: a1 += 360
                            them_cung_wcs(list(ve.vertices([a0, (a0 + a1) / 2, a1])), m, kieu, z)
                        else:
                            them_duong_gay(chia_duong(ve, m), kieu, z)
            except Exception:
                bao_cao['pline_loi'] += 1
        elif t == 'ARC':
            dd, s = la_dong_dang(m)
            if dd:
                a0, a1 = e.dxf.start_angle, e.dxf.end_angle
                if a1 < a0: a1 += 360
                them_cung_wcs(list(e.vertices([a0, (a0 + a1) / 2, a1])), m, kieu, z)
            else:
                them_duong_gay(chia_duong(e, m), kieu, z)
        elif t == 'CIRCLE':
            dd, s = la_dong_dang(m)
            if dd:
                them_cung_wcs(None, m, kieu, z, day_du=True, tam=e.ocs().to_wcs(e.dxf.center), r=e.dxf.radius)
            else:
                them_duong_gay(chia_duong(e, m), kieu, z)
        elif t in ('SPLINE', 'ELLIPSE'):
            them_duong_gay(chia_duong(e, m), kieu, z)
        elif t == 'HATCH':
            k = khoa_mau(e, tt)
            loops = [vong_sang_toa_do(v, m) for v in vong_hatch(e)]
            loops = [l for l in loops if l]
            if loops:
                vung.append({'loops': loops, 'kieu': k, 'z': z})
            else:
                bao_cao['hatch_khong_bien'] += 1
        elif t in ('SOLID', 'TRACE'):
            ps = [e.dxf.vtx0, e.dxf.vtx1, e.dxf.vtx3, e.dxf.vtx2]
            ocs = e.ocs()
            ps = [tf(m, ocs.to_wcs(Vec3(p))) for p in ps]
            sg = [['L', ps[i].x, ps[i].y, ps[(i + 1) % 4].x, ps[(i + 1) % 4].y] for i in range(4)]
            lp = lam_kin(sg)
            if lp:
                rgb = mau_rgb(tt)
                k = 'SOLID_%d_%d_%d' % tuple(rgb)
                mau_hatch.setdefault(k, {'solid': True, 'rgb': rgb, 'ten': 'Đặc %d,%d,%d' % tuple(rgb)})
                vung.append({'loops': [lp], 'kieu': k, 'z': z})
        elif t == 'WIPEOUT':
            try:
                ps = [tf(m, p) for p in e.boundary_path_wcs()]
                sg = [['L', ps[i].x, ps[i].y, ps[(i + 1) % len(ps)].x, ps[(i + 1) % len(ps)].y] for i in range(len(ps))]
                lp = lam_kin(sg)
                if lp:
                    che.append({'loops': [lp], 'z': z})
            except Exception:
                bao_cao['wipeout_loi'] += 1
        elif t == 'TEXT' or t == 'ATTRIB':
            xu_ly_text(e, m, tt, z)
        elif t == 'MTEXT':
            xu_ly_mtext(e, m, tt, z)
        elif t == 'DIMENSION':
            xu_ly_dim(e, m, tt, cha, z)
        elif t in ('LEADER', 'MULTILEADER', 'ARC_DIMENSION'):
            no_ra(e, m, tt, cha)
        elif t in ('REGION', '3DSOLID', 'SURFACE', 'BODY'):
            xu_ly_region(e, m, tt, z)
        else:
            bao_cao['bo_qua_' + t] += 1


duyet(msp.entities_in_redraw_order(), None, None)
reg_info = json.load(open(regjs_path))
assert REG_I[0] == len(reg_info), 'Thứ tự REGION không khớp file đã nổ: %d / %d' % (REG_I[0], len(reg_info))
print('raw: nét', len(seg_raw), 'cung', len(arc_raw), 'hatch', len(vung), 'che', len(che), 'chữ', len(chu), 'dim', len(dims))

# ---------------------------------------------------------------- gộp nét trùng (thẳng hàng, chồng nhau)
nhom = {}
khoa_nhom = collections.defaultdict(list)


def tim_nhom(ang, rho):
    ka, kr = int(round(ang / 0.02)), int(round(rho / 0.3))
    for da in (-1, 0, 1):
        for dr in (-1, 0, 1):
            for g in khoa_nhom.get(((ka + da) % 9000, kr + dr), []):
                a2, r2 = nhom[g]['ang'], nhom[g]['rho']
                dang = min(abs(ang - a2), 180 - abs(ang - a2))
                if dang < 0.02 and abs(rho - r2) < 0.3:
                    return g
    g = len(nhom)
    nhom[g] = {'ang': ang, 'rho': rho, 'ds': []}
    khoa_nhom[(ka % 9000, kr)].append(g)
    return g


for (x1, y1, x2, y2, kieu, z) in seg_raw:
    ang = math.degrees(math.atan2(y2 - y1, x2 - x1)) % 180.0
    if ang >= 179.99:
        ang = 0.0
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    rho = -x1 * uy + y1 * ux
    g = tim_nhom(ang, rho)
    t1, t2 = x1 * ux + y1 * uy, x2 * ux + y2 * uy
    if t1 > t2:
        t1, t2 = t2, t1
    nhom[g]['ds'].append((t1, t2, kieu, z))

net = []   # (x1,y1,x2,y2,kieu,z)
for g, d in nhom.items():
    a = math.radians(d['ang'])
    ux, uy = math.cos(a), math.sin(a)
    rho = d['rho']
    ds = d['ds']
    moc = sorted(set([t for s in ds for t in (s[0], s[1])]))
    # gom mốc sát nhau
    gon = []
    for t in moc:
        if not gon or t - gon[-1] > 0.05:
            gon.append(t)
    manh = []
    for ta, tb in zip(gon, gon[1:]):
        tm = (ta + tb) / 2
        tot = None
        for (s1, s2, k, z) in ds:
            if s1 - 0.05 <= tm <= s2 + 0.05:
                if tot is None or UU_TIEN[k] > UU_TIEN[tot[0]] or (k == tot[0] and z > tot[1]):
                    tot = (k, z)
        if tot is not None:
            if manh and manh[-1][2] == tot[0] and abs(manh[-1][1] - ta) < 0.06:
                manh[-1][1] = tb
                manh[-1][3] = max(manh[-1][3], tot[1])
            else:
                manh.append([ta, tb, tot[0], tot[1]])
    for ta, tb, k, z in manh:
        if tb - ta < NGAN_NHAT:
            bao_cao['net_ngan_bo'] += 1
            continue
        # điểm trên đường: t*u + rho*n, n = (-uy, ux)
        p = (ta * ux - rho * uy, ta * uy + rho * ux)
        q = (tb * ux - rho * uy, tb * uy + rho * ux)
        net.append((p[0], p[1], q[0], q[1], k, z))
print('nét sau gộp:', len(net), '(trước', len(seg_raw), ')')

# cung: gộp cùng tâm + bán kính
nhom_c = collections.defaultdict(list)
for (cx, cy, r, a0, a1, k, z) in arc_raw:
    nhom_c[(round(cx / 0.3), round(cy / 0.3), round(r / 0.3))].append((cx, cy, r, a0, a1, k, z))
cung = []   # (cx,cy,r,a0,a1,k,z)
for key, ds in nhom_c.items():
    cx = sum(d[0] for d in ds) / len(ds); cy = sum(d[1] for d in ds) / len(ds); r = sum(d[2] for d in ds) / len(ds)
    iv = []
    for (_, _, _, a0, a1, k, z) in ds:
        if a1 - a0 >= 359.99:
            iv.append((0.0, 360.0, k, z)); continue
        a0n = a0 % 360.0; a1n = a0n + (a1 - a0)
        if a1n > 360.0:
            iv.append((a0n, 360.0, k, z)); iv.append((0.0, a1n - 360.0, k, z))
        else:
            iv.append((a0n, a1n, k, z))
    moc = sorted(set([0.0, 360.0] + [t for s in iv for t in (s[0], s[1])]))
    manh = []
    for ta, tb in zip(moc, moc[1:]):
        if tb - ta < 1e-6:
            continue
        tm = (ta + tb) / 2
        tot = None
        for (s1, s2, k, z) in iv:
            if s1 - 1e-4 <= tm <= s2 + 1e-4:
                if tot is None or UU_TIEN[k] > UU_TIEN[tot[0]] or (k == tot[0] and z > tot[1]):
                    tot = (k, z)
        if tot is not None:
            if manh and manh[-1][2] == tot[0] and abs(manh[-1][1] - ta) < 1e-4:
                manh[-1][1] = tb; manh[-1][3] = max(manh[-1][3], tot[1])
            else:
                manh.append([ta, tb, tot[0], tot[1]])
    # nối qua mốc 0/360
    if len(manh) >= 2 and manh[0][0] == 0.0 and manh[-1][1] == 360.0 and manh[0][2] == manh[-1][2]:
        manh[-1][1] = 360.0 + manh[0][1]; manh[-1][3] = max(manh[-1][3], manh[0][3]); manh.pop(0)
    for ta, tb, k, z in manh:
        if r * math.radians(tb - ta) < NGAN_NHAT:
            continue
        cung.append((cx, cy, r, ta, tb, k, z))
print('cung sau gộp:', len(cung), '(trước', len(arc_raw), ')')

# ---------------------------------------------------------------- ô chi tiết
khung = []
for e in msp.query('LINE LWPOLYLINE'):
    if e.dxf.layer not in ('A_Symbol', 'A-Symbol', 'CDC-KT-net thay'):
        continue
    pts = [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)] if e.dxftype() == 'LINE' else [tuple(p[:2]) for p in e.get_points()]
    segs = list(zip(pts, pts[1:])) + ([(pts[-1], pts[0])] if e.dxftype() == 'LWPOLYLINE' and e.closed else [])
    for a, b in segs:
        if math.hypot(a[0] - b[0], a[1] - b[1]) < 2500:
            continue
        if abs(a[1] - b[1]) < 1:
            if abs(a[1] + 65085) < 2 or abs(a[1] + 58075) < 2:   # dải tiêu đề ô: không chia ô
                continue
            khung.append(LineString([a, b]))
        elif abs(a[0] - b[0]) < 1:
            khung.append(LineString([a, b]))
mat = [p for p in polygonize(unary_union(khung)) if p.area > 4e6]
# tờ: ô rộng đủ 1 tờ (17388) thì gộp mọi mặt trong tờ đó
to = sorted(set(round(p.bounds[0]) for p in mat if round(p.bounds[2] - p.bounds[0]) >= 17000))
cells = []
dung = set()
for x0 in to:
    trong = [p for p in mat if p.bounds[0] >= x0 - 1 and p.bounds[2] <= x0 + 17388 + 1]
    for p in trong:
        dung.add(id(p))
    b = [min(p.bounds[0] for p in trong), min(p.bounds[1] for p in trong), max(p.bounds[2] for p in trong), max(p.bounds[3] for p in trong)]
    cells.append(b)
for p in mat:
    if id(p) not in dung:
        cells.append(list(p.bounds))
cells.sort(key=lambda b: (-round(b[3] / 1000), b[0]))
print('số ô:', len(cells))

# vị trí trong legend: cột / hàng theo mép trái / mép trên, cách nhau KHE
xs = sorted(set(round(b[0]) for b in cells))
ys = sorted(set(round(b[3]) for b in cells), reverse=True)
X0 = min(b[0] for b in cells); Y1 = max(b[3] for b in cells)
o_ds = []
for i, b in enumerate(cells):
    col = xs.index(round(b[0])); row = ys.index(round(b[3]))
    dx = -X0 + col * KHE
    dy = -Y1 - row * KHE
    o_ds.append({'i': i, 'bounds': b, 'dx': dx, 'dy': dy, 'net': [], 'cung': [], 'vung': [], 'che': [], 'chu': [], 'dim': []})


def o_chua(x, y):
    for o in o_ds:
        b = o['bounds']
        if b[0] - 0.5 <= x <= b[2] + 0.5 and b[1] - 0.5 <= y <= b[3] + 0.5:
            return o
    return None


def cat_doan(x1, y1, x2, y2, b):
    """Cắt đoạn theo hình chữ nhật (Liang–Barsky)."""
    xmin, ymin, xmax, ymax = b[0] - 0.5, b[1] - 0.5, b[2] + 0.5, b[3] + 0.5
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - xmin), (dx, xmax - x1), (-dy, y1 - ymin), (dy, ymax - y1)):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            r = q / p
            if p < 0:
                t0 = max(t0, r)
            else:
                t1 = min(t1, r)
            if t0 > t1:
                return None
    return (x1 + t0 * dx, y1 + t0 * dy, x1 + t1 * dx, y1 + t1 * dy)


def dich(o, x, y):
    return round(x + o['dx'], 3), round(y + o['dy'], 3)


ngoai = collections.Counter()
for (x1, y1, x2, y2, k, z) in net:
    co = False
    for o in o_ds:
        c = cat_doan(x1, y1, x2, y2, o['bounds'])
        if c and math.hypot(c[2] - c[0], c[3] - c[1]) >= NGAN_NHAT:
            a = dich(o, c[0], c[1]); b = dich(o, c[2], c[3])
            o['net'].append([a[0], a[1], b[0], b[1], k, z]); co = True
    if not co:
        ngoai['net'] += 1
for (cx, cy, r, a0, a1, k, z) in cung:
    am = math.radians((a0 + a1) / 2)
    o = o_chua(cx + r * math.cos(am), cy + r * math.sin(am))
    if o is None:
        ngoai['cung'] += 1; continue
    c = dich(o, cx, cy)
    o['cung'].append([c[0], c[1], round(r, 3), round(a0, 4), round(a1, 4), k, z])


def tam_vong(loops):
    xs_ = [s[1] for l in loops for s in l]; ys_ = [s[2] for l in loops for s in l]
    return (min(xs_) + max(xs_)) / 2, (min(ys_) + max(ys_)) / 2


def dich_vong(o, loops):
    kq = []
    for l in loops:
        kl = []
        for s in l:
            s2 = [s[0]]
            for j in range(1, len(s), 2):
                x, y = dich(o, s[j], s[j + 1]); s2 += [x, y]
            kl.append(s2)
        kq.append(kl)
    return kq


def diem_vong(l):
    """Vòng (đoạn L / cung A 3 điểm) -> chuỗi điểm (cung chia nhỏ)."""
    pts = []
    for s in l:
        if s[0] == 'L':
            pts.append((s[1], s[2]))
        else:
            kq = cung_3_diem((s[1], s[2]), (s[3], s[4]), (s[5], s[6]))
            if kq is None:
                pts.append((s[1], s[2])); continue
            cx, cy, r, a0, a1 = kq
            st = math.degrees(math.atan2(s[2] - cy, s[1] - cx))
            n = max(4, int((a1 - a0) / 6))
            nguoc = abs(((st - a0 + 180) % 360) - 180) > 1e-3
            for i in range(n):
                t = (a1 - i * (a1 - a0) / n) if nguoc else (a0 + i * (a1 - a0) / n)
                pts.append((cx + r * math.cos(math.radians(t)), cy + r * math.sin(math.radians(t))))
    return pts


def vong_sua(loops):
    """Biên dự phòng khi Revit không nhận biên gốc (tự cắt / các vòng chồng nhau): tô chẵn lẻ như CAD rồi nắn lại."""
    from shapely.geometry import Polygon
    from shapely.validation import make_valid
    try:
        polys = [make_valid(Polygon(diem_vong(l))) for l in loops if len(diem_vong(l)) >= 3]
    except Exception:
        return None
    if not polys:
        return None
    hop = polys[0]
    for p in polys[1:]:
        hop = hop.symmetric_difference(p)
    hop = make_valid(hop.buffer(0)).simplify(0.2)
    # mỗi mảnh đa giác 1 Filled Region riêng (Revit không nhận các vòng chạm nhau tại 1 điểm)
    manh = []
    geoms = getattr(hop, 'geoms', [hop])
    for g in geoms:
        if g.geom_type != 'Polygon' or g.area < 1.0:
            continue
        vongs = []
        for ring in [g.exterior] + list(g.interiors):
            cs = list(ring.coords)[:-1]
            sg = [['L', cs[i][0], cs[i][1], cs[(i + 1) % len(cs)][0], cs[(i + 1) % len(cs)][1]] for i in range(len(cs))]
            lp = lam_kin(sg)
            if lp:
                vongs.append(lp)
        if vongs:
            manh.append(vongs)
    return manh or None


so_sua = 0
for v in vung:
    o = o_chua(*tam_vong(v['loops']))
    if o is None:
        ngoai['vung'] += 1; continue
    it = {'loops': dich_vong(o, v['loops']), 'kieu': v['kieu'], 'z': v['z']}
    sua = vong_sua(v['loops'])
    if sua:
        it['sua'] = [dich_vong(o, m) for m in sua]; so_sua += 1
    o['vung'].append(it)
print('vùng có biên dự phòng:', so_sua)
for v in che:
    o = o_chua(*tam_vong(v['loops']))
    if o is None:
        ngoai['che'] += 1; continue
    o['che'].append({'loops': dich_vong(o, v['loops']), 'z': v['z']})
for t in chu:
    o = o_chua(t['x'], t['y'])
    if o is None:
        ngoai['chu'] += 1; continue
    t2 = dict(t); t2['x'], t2['y'] = dich(o, t['x'], t['y'])
    o['chu'].append(t2)
for d in dims:
    mx = (d['p2'][0] + d['p3'][0]) / 2; my = (d['p2'][1] + d['p3'][1]) / 2
    o = o_chua(mx, my) or o_chua(*d['p1'])
    if o is None:
        ngoai['dim'] += 1; continue
    d2 = dict(d)
    for kk in ('p1', 'p2', 'p3'):
        d2[kk] = list(dich(o, *d[kk]))
    o['dim'].append(d2)

# tên ô: mã cửa trong dải tiêu đề (1300 mm trên cùng)
MA = re.compile(r'^[A-Z]{1,5}[A-Z0-9]*(\.[A-Z0-9]+)?$')
KT = re.compile(r'(\d+|[A-Z])\s*[xX*×]\s*\d+')
for o in o_ds:
    b = o['bounds']
    tieu_de = [t for t in chu if b[0] <= t['x'] <= b[2] and b[3] - 1300 <= t['y'] <= b[3]]
    tieu_de.sort(key=lambda t: (-t['h'], t['x']))
    ma = [t['t'].strip() for t in tieu_de if MA.match(t['t'].strip()) and t['t'].strip() not in ('EI', 'TT')
          and not t['t'].strip().startswith('EI')]
    kt = [t['t'].strip().replace(' ', '') for t in tieu_de if KT.search(t['t'])]
    if not ma:
        mo_ta = [t['t'].strip().strip('()').strip() for t in tieu_de if t['t'].strip().startswith('(')]
        if not mo_ta:
            trong = sorted([t for t in chu if b[0] <= t['x'] <= b[2] and b[1] <= t['y'] <= b[3]], key=lambda t: (-t['h'], not re.search(r'EI\d', t['t']), -len(t['t'])))
            mo_ta = [trong[0]['t'].splitlines()[0].strip()] if trong else []
        ma = mo_ta[:1]
    ten = ' '.join(x for x in ((ma[0] if ma else ''), (kt[0] if kt else '')) if x) or ('O%02d' % (o['i'] + 1))
    o['ten'] = ten
    o['so'] = {k: len(o[k]) for k in ('net', 'cung', 'vung', 'che', 'chu', 'dim')}
# bỏ ô rỗng (chỉ có khung)
rong = [o for o in o_ds if o['so']['cung'] + o['so']['vung'] + o['so']['chu'] + o['so']['dim'] == 0 and o['so']['net'] <= 8]
o_ds = [o for o in o_ds if o not in rong]
# tên trùng: thêm số thứ tự
dem = collections.Counter(o['ten'] for o in o_ds)
thu = collections.Counter()
for o in o_ds:
    if dem[o['ten']] > 1:
        thu[o['ten']] += 1
        o['ten'] = '%s (%d)' % (o['ten'], thu[o['ten']])
for o in o_ds:
    print('%-22s' % o['ten'], o['so'])
print('ô rỗng bỏ qua:', [[round(v) for v in o['bounds']] for o in rong])
print('ngoài ô:', dict(ngoai))
print('báo cáo:', dict(bao_cao))
print('mẫu hatch:', len(mau_hatch))

json.dump({'ti_le': TI_LE, 'nguon': src_path, 'mau_hatch': mau_hatch, 'o': o_ds,
           'bao_cao': dict(bao_cao), 'ngoai': dict(ngoai)}, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)
print('XONG', out_path)
