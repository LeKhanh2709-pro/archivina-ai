# -*- coding: utf-8 -*-
"""Ghép ảnh soi DXF TRƯỚC / SAU của cùng 1 vòng (tâm cách nhau < 600 mm) thành 1 ảnh đôi.
python ghep_truoc_sau.py <thư mục ảnh trước> <tên trước> <thư mục ảnh sau> <tên sau> <thư mục ra> <tiền tố ra>"""
import glob
import os
import re
import sys

from PIL import Image, ImageDraw

d_tr, t_tr, d_s, t_s, ra, tien_to = sys.argv[1:7]
os.makedirs(ra, exist_ok=True)


def doc(d, t):
    kq = []
    for f in glob.glob(os.path.join(d, t + "_*.png")):
        m = re.search(r"_(\d+)_(-?\d+)_(-?\d+)\.png$", f)
        if m:
            kq.append((int(m.group(2)), int(m.group(3)), f))
    return kq


tr, sau = doc(d_tr, t_tr), doc(d_s, t_s)
n = 0
for x, y, f in sorted(tr, key=lambda a: (a[1], a[0])):
    g = [s for s in sau if abs(s[0] - x) < 600 and abs(s[1] - y) < 600]
    if not g:
        continue
    a, b = Image.open(f).convert("RGB"), Image.open(g[0][2]).convert("RGB")
    h = max(a.height, b.height)
    o = Image.new("RGB", (a.width + b.width + 30, h + 40), "white")
    o.paste(a, (0, 40))
    o.paste(b, (a.width + 30, 40))
    dr = ImageDraw.Draw(o)
    dr.text((10, 10), "TRUOC (file 47, link kien truc hien tai)", fill=(200, 0, 0))
    dr.text((a.width + 40, 10), "SAU (ve lai voi link hien tai)", fill=(0, 120, 0))
    n += 1
    o.save(os.path.join(ra, "%s_%02d_%d_%d.png" % (tien_to, n, x, y)))
print("ghép", n, "ảnh →", ra)
