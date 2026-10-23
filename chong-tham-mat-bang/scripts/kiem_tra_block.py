#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kiem tra ban sao DWG da ve chong tham: doc bang ODA File Converter (ezdxf.addons.odafc), dem doi tuong trong
block CHONG THAM*, kiem layer / mau / width / hatch, va so doi tuong AEC (proxy) so voi file goc (khong mat tuong ACA).

    python kiem_tra_block.py <ban_sao.dwg> [--goc <file_goc.dwg>] [--anh <png> --khung x0,y0,x1,y1]
"""
import argparse
import collections
import math
import os
import shutil
import sys
import tempfile

from ezdxf.addons import odafc


def thu_muc_tam():
    """<goc>\\_tmp (goc = thu muc cha cua .claude chua skill, vd. D:\\AI), khong co thi %LOCALAPPDATA%\\ARCHIVINA\\_tmp."""
    goc = os.environ.get("ARCHIVINA_AI", "")
    if not goc:
        d = os.path.dirname(os.path.abspath(__file__))
        while os.path.dirname(d) != d:
            if os.path.basename(d).lower() == ".claude":
                g = os.path.dirname(d)
                if os.path.normcase(g) != os.path.normcase(os.path.expanduser("~")):
                    goc = g
                break
            d = os.path.dirname(d)
    t = os.path.join(goc, "_tmp") if goc else os.path.join(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()), "ARCHIVINA", "_tmp")
    os.makedirs(t, exist_ok=True)
    return t


def doc(path):
    # ODA doc file tren ban sao trong thu muc tam (khong dong file goc)
    tmp = tempfile.mkdtemp(prefix="kt_chongtham_", dir=thu_muc_tam())
    cp = os.path.join(tmp, "x.dwg")
    shutil.copy2(path, cp)
    return odafc.readfile(cp)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dwg")
    ap.add_argument("--goc", default="")
    ap.add_argument("--anh", default="")
    ap.add_argument("--khung", default="")
    a = ap.parse_args()
    d = doc(a.dwg)
    msp = d.modelspace()
    loi = []
    ins = [e for e in msp.query("INSERT") if e.dxf.name.upper().startswith("CHONG THAM")]
    print("INSERT CHONG THAM*:", [(e.dxf.name, e.dxf.layer, tuple(round(c, 3) for c in e.dxf.insert)) for e in ins])
    if not ins:
        sys.exit("Khong co block CHONG THAM")
    for e in ins:
        if e.dxf.layer != "A-Material" or any(abs(c) > 1e-6 for c in e.dxf.insert):
            loi.append(f"INSERT {e.dxf.name}: layer {e.dxf.layer}, diem chen {e.dxf.insert}")
        blk = d.blocks.get(e.dxf.name)
        dem = collections.Counter()
        for x in blk:
            t = x.dxftype()
            if t == "LWPOLYLINE":
                # net ven: co global width (co the kin khi phong khong co cua); bo / dao: width 0
                k = "ven" if (not x.closed or x.dxf.get("const_width", 0) > 0) else "bo/dao"
                dem[k] += 1
                mau = x.dxf.get("color")
                w = x.dxf.get("const_width", 0)
                if x.dxf.layer != "A-Material":
                    loi.append(f"{k} {x.dxf.handle} layer {x.dxf.layer}")
                if k == "ven" and (mau != 1 or abs(w - 40) > 0.01):
                    loi.append(f"ven {x.dxf.handle} mau {mau} width {w}")
                if k == "bo/dao" and mau != 3:
                    loi.append(f"bo {x.dxf.handle} mau {mau}")
            elif t == "HATCH":
                dem["hatch"] += 1
                sp = [math.hypot(l.offset.x, l.offset.y) for l in x.pattern.lines] if x.pattern else []
                # -HATCH _U luu ten "_U", hop thoai HATCH luu "_USER": cung kieu user-defined
                ok = (x.dxf.layer == "A-Material" and x.dxf.get("color") == 3 and x.dxf.pattern_name.upper() in ("_USER", "_U")
                      and x.dxf.pattern_double == 1 and sp and all(abs(s - 400) < 0.5 for s in sp))
                if not ok:
                    loi.append(f"hatch {x.dxf.handle}: layer {x.dxf.layer} mau {x.dxf.get('color')} {x.dxf.pattern_name} "
                               f"double {x.dxf.pattern_double} khoang {sp}")
                if not x.dxf.get("associative", 0):
                    dem["hatch_khong_lien_ket"] += 1
            else:
                dem[t] += 1
        print(e.dxf.name, dict(dem))
    if a.goc:
        g = doc(a.goc)
        def proxy(doc_):
            n = 0
            for b in doc_.blocks:
                n += sum(1 for x in b if x.dxftype() == "ACAD_PROXY_ENTITY")
            return n + sum(1 for x in doc_.modelspace() if x.dxftype() == "ACAD_PROXY_ENTITY")
        pg, ps = proxy(g), proxy(d)
        print(f"Doi tuong AEC (proxy) - goc: {pg}, ban sao: {ps}")
        if pg != ps:
            loi.append(f"So doi tuong AEC khac goc: {pg} -> {ps}")
    if a.anh and a.khung:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import Frontend, RenderContext
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        x0, y0, x1, y1 = (float(v) for v in a.khung.split(","))
        fig = plt.figure(figsize=(14, 14 * (y1 - y0) / (x1 - x0)))
        ax = fig.add_axes([0, 0, 1, 1])
        Frontend(RenderContext(d), MatplotlibBackend(ax)).draw_entities(ins)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        fig.savefig(a.anh, dpi=110, facecolor="#1e1e1e")
        print(a.anh)
    print("LOI:", len(loi))
    for s in loi[:30]:
        print("  ", s)


if __name__ == "__main__":
    main()
