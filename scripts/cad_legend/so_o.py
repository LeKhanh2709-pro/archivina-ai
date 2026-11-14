# -*- coding: utf-8 -*-
"""Ghép ảnh đối chiếu TỪNG Ô: trái = ảnh in thật từ AutoCAD (acc\\cad_o\\NN_<tờ>.png, in bằng Core Console theo đúng khung
ô), phải = cùng vùng đó cắt từ ảnh legend Revit (kq\\<KQ>\\<tờ>\\*.png, vị trí tính theo dòng "Khung view" trong log).
Chạy: python so_o.py <KQ> [số ô, số ô...]   -> kq\\<KQ>\\so\\NN_<tờ>.png"""
import sys, os, io, json, re, glob
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None
G = os.path.dirname(os.path.abspath(__file__))
KQ = os.path.join(G, 'kq', sys.argv[1])
chon = [int(x) for x in sys.argv[2:]]
cfg = json.load(io.open(os.path.join(G, 'o_cfg.json'), encoding='utf-8'))
ra = os.path.join(KQ, 'so')
os.makedirs(ra, exist_ok=True)
anh = {}; khung = {}; goc = {}
for t in cfg['to']:
    ma = t['ma']
    fs = glob.glob(os.path.join(KQ, ma, '*.png'))
    lg = os.path.join(KQ, 'log_%s.txt' % ma)
    if not fs or not os.path.isfile(lg):
        continue
    m = re.search(r'Khung view \(mm mô hình\): (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+)', io.open(lg, encoding='utf-8').read())
    anh[ma] = Image.open(fs[0]).convert('RGB')
    if m:
        khung[ma] = [float(v) for v in m.groups()]
    else:
        # log không có khung view: ước lượng bằng khung bao hình học của tờ trong json (chữ nhô ra ngoài thì lệch chút)
        if 'JS' not in globals():
            JS = json.load(io.open(os.path.join(G, 'ct_chung.json'), encoding='utf-8'))
        xs = []; ys = []
        for o in JS['o']:
            if o['to'] != ma:
                continue
            for n in o['net']:
                xs += [n[0], n[2]]; ys += [n[1], n[3]]
            for c in o['cung']:
                xs += [c[0] - c[2], c[0] + c[2]]; ys += [c[1] - c[2], c[1] + c[2]]
            for v in o['vung']:
                for l in (v['loops'] or [x for mm in (v['du_phong'][0] if v.get('du_phong') else []) for x in mm]):
                    for s in l:
                        xs.append(s[1]); ys.append(s[2])
        khung[ma] = [min(xs), min(ys), max(xs), max(ys)]
    os_ = [o for o in cfg['o'] if o['to'] == ma]
    goc[ma] = (min(o['bounds'][0] for o in os_), max(o['bounds'][3] for o in os_))     # dx = -X0, dy = -Y1
W0, H0 = 1600, 1280
for i, o in enumerate(cfg['o']):
    so = i + 1
    ma = o['to']
    if (chon and so not in chon) or ma not in anh:
        continue
    cad = os.path.join(G, 'acc', 'cad_o', '%02d_%s.png' % (so, ma))
    if not os.path.isfile(cad):
        continue
    b = o['bounds']
    # ảnh CAD: khung ô đặt vừa khổ 1600 x 1280, canh giữa
    bw, bh = b[2] - b[0], b[3] - b[1]
    tl = min(W0 / bw, H0 / bh)
    cw, ch = bw * tl, bh * tl
    ic = Image.open(cad).convert('RGB').crop((int((W0 - cw) / 2), int((H0 - ch) / 2), int((W0 + cw) / 2), int((H0 + ch) / 2)))
    # ảnh Revit: toạ độ legend = toạ độ CAD - góc trái trên của tờ
    im = anh[ma]; k = khung[ma]; X0, Y1 = goc[ma]
    px = im.size[0] / (k[2] - k[0]); py = im.size[1] / (k[3] - k[1])
    x0 = (b[0] - X0 - k[0]) * px; x1 = (b[2] - X0 - k[0]) * px
    y0 = (k[3] - (b[3] - Y1)) * py; y1 = (k[3] - (b[1] - Y1)) * py
    ir = Image.new('RGB', (int(round(x1 - x0)), int(round(y1 - y0))), 'white')
    ir.paste(im.crop((int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))), (0, 0))
    cao = 1100
    ic = ic.resize((int(ic.size[0] * cao / ic.size[1]), cao), Image.LANCZOS)
    ir = ir.resize((int(ir.size[0] * cao / ir.size[1]), cao), Image.LANCZOS)
    kq = Image.new('RGB', (ic.size[0] + ir.size[0] + 30, cao + 40), 'white')
    kq.paste(ic, (0, 40)); kq.paste(ir, (ic.size[0] + 30, 40))
    d = ImageDraw.Draw(kq)
    d.text((10, 10), 'AutoCAD (in that) - o %02d to %s 1:%s' % (so, ma, [t['ti_le'] for t in cfg['to'] if t['ma'] == ma][0]), fill=(200, 0, 0))
    d.text((ic.size[0] + 40, 10), 'Revit (legend)', fill=(0, 0, 200))
    d.line([(ic.size[0] + 15, 0), (ic.size[0] + 15, cao + 40)], fill=(180, 180, 180), width=2)
    f = os.path.join(ra, '%02d_%s.png' % (so, ma))
    kq.save(f)
    print(f, kq.size)
