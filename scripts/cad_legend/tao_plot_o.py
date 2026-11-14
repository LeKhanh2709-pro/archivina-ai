# Ghi script Core Console in TỪNG Ô ra PNG (ảnh thật của AutoCAD, monochrome) để đối chiếu với legend Revit
import json, io, os
G = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(io.open(os.path.join(G, 'o_cfg.json'), encoding='utf-8'))
ra = os.path.join(G, 'acc', 'cad_o')
os.makedirs(ra, exist_ok=True)
d = ['TILEMODE', '1']
ds = []
for i, o in enumerate(cfg['o']):
    b = o['bounds']
    f = os.path.join(ra, '%02d_%s.png' % (i + 1, o['to']))
    ds.append((i + 1, o['to'], o['ten'], f))
    d += ['-PLOT', 'Y', '', 'PublishToWeb PNG.pc3', 'Sun Hi-Res (1600.00 x 1280.00 Pixels)', 'L', 'N', 'W',
          '%.1f,%.1f' % (b[0], b[1]), '%.1f,%.1f' % (b[2], b[3]), 'F', 'C', 'Y', 'monochrome.ctb', 'Y', 'A', f, 'N', 'Y']
d += ['QUIT', 'Y', '']
open(os.path.join(G, 'acc', 'plot_o.scr'), 'w', encoding='ascii', newline='').write('\r\n'.join(d))
io.open(os.path.join(ra, 'danh_sach.txt'), 'w', encoding='utf-8').write(u'\n'.join(u'%02d\t%s\t%s' % (a, b, c) for a, b, c, _ in ds))
print(len(ds), 'ô')