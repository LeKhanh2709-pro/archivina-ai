# -*- coding: utf-8 -*-
"""Bảng ảnh nhiều ô để soát nhanh. Chạy: python bang_anh.py <ra.png> <số cột> <rộng mỗi ảnh px> <số ô 1> <số ô 2> ..."""
import sys, glob, os, io, json
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
G = r"D:\AI\_tmp\ct_cua_legend"
ra, cot, W = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
ds = [int(v) for v in sys.argv[4:]]
ten = [o["ten"] for o in json.load(io.open(os.path.join(G, "ct_cua.json"), encoding="utf-8"))["o"]]
font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", 22)
ims = []
for i in ds:
    f = glob.glob(os.path.join(G, "kq", "anh_o", "%02d" % i, "*.png"))[0]
    im = Image.open(f).convert("RGB")
    im = im.resize((W, int(im.size[1] * W / im.size[0])), Image.LANCZOS)
    ims.append((i, im))
hang = [ims[k:k + cot] for k in range(0, len(ims), cot)]
H = sum(max(im.size[1] for _, im in h) + 34 for h in hang)
kq = Image.new("RGB", (W * cot, H), "white")
d = ImageDraw.Draw(kq)
y = 0
for h in hang:
    for j, (i, im) in enumerate(h):
        d.rectangle([j * W, y, (j + 1) * W, y + 34], fill=(40, 40, 40))
        d.text((j * W + 8, y + 5), "%02d %s" % (i, ten[i - 1]), fill="white", font=font)
        kq.paste(im, (j * W, y + 34))
    y += max(im.size[1] for _, im in h) + 34
kq.save(ra)
print(kq.size, ra)