# -*- coding: utf-8 -*-
"""Ghép 2 ảnh (trên / dưới) kèm chú thích để so trước - sau. Chạy: python ghep_anh.py <ra.png> <rộng px> <ảnh 1> <chú thích 1> <ảnh 2> <chú thích 2>"""
import sys
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
ra, W = sys.argv[1], int(sys.argv[2])
cap = [(sys.argv[i], sys.argv[i + 1]) for i in range(3, len(sys.argv) - 1, 2)]
font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", max(18, W // 70))
ds = []
for p, t in cap:
    im = Image.open(p).convert("RGB")
    k = W / im.size[0]
    im = im.resize((W, int(im.size[1] * k)), Image.LANCZOS)
    ds.append((im, t))
H = sum(im.size[1] for im, _ in ds) + len(ds) * (font.size + 24)
kq = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(kq)
y = 0
for im, t in ds:
    d.rectangle([0, y, W, y + font.size + 24], fill=(40, 40, 40))
    d.text((14, y + 10), t, fill="white", font=font)
    y += font.size + 24
    kq.paste(im, (0, y)); y += im.size[1]
kq.save(ra)
print(kq.size, ra)