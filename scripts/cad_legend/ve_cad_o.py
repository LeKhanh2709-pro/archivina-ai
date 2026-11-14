# -*- coding: utf-8 -*-
"""Vẽ lại 1 ô của CAD GỐC (ezdxf drawing) để so với ảnh legend Revit. Chạy: python ve_cad_o.py <tên ô có chứa> <ra.png> [px rộng]"""
import sys, io, json
import ezdxf
from ezdxf import bbox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
from ezdxf.addons.drawing.config import Configuration, BackgroundPolicy, ColorPolicy

G = r"D:\AI\_tmp\ct_cua_legend"
ten, ra = sys.argv[1], sys.argv[2]
px = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
d = json.load(io.open(G + r"\ct_cua.json", encoding="utf-8"))
o = [o for o in d["o"] if ten in o["ten"]][0]
B = o["bounds"]
doc = ezdxf.readfile(G + r"\CT_Cua_khanh.dxf")
msp = doc.modelspace()
chon = []
cache = bbox.Cache()
for e in msp:
    try:
        bb = bbox.extents([e], fast=True, cache=cache)
        if not bb.has_data:
            continue
        c = bb.center
        if B[0] - 1 <= c.x <= B[2] + 1 and B[1] - 1 <= c.y <= B[3] + 1:
            chon.append(e)
    except Exception:
        pass
w, h = B[2] - B[0], B[3] - B[1]
fig = plt.figure(figsize=(px / 200.0, px / 200.0 * h / w), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ctx = RenderContext(doc)
ctx.set_current_layout(msp)
out = MatplotlibBackend(ax, adjust_figure=False)
cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
Frontend(ctx, out, config=cfg).draw_entities(chon)
out.finalize()
ax.set_xlim(B[0], B[2]); ax.set_ylim(B[1], B[3])
fig.savefig(ra, dpi=200)
print(o["ten"], len(chon), "đối tượng ->", ra)