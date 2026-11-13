# Tách mọi REGION / 3DSOLID / SURFACE / BODY (kể cả trong block) ra DXF riêng, mỗi đối tượng 1 layer R<n>,
# kèm ma trận biến đổi về toạ độ bản vẽ -> regions.json. AutoCAD Core Console nổ chúng thành line / arc.
import ezdxf, sys, json
src = ezdxf.readfile(sys.argv[1]); msp = src.modelspace()
out = ezdxf.new('R2018'); om = out.modelspace()
ds = []
LOAI = ('REGION', '3DSOLID', 'SURFACE', 'BODY')
def walk(ents, m):
    for e in ents:
        t = e.dxftype()
        if t == 'INSERT':
            blk = src.blocks.get(e.dxf.name)
            if blk is None: continue
            mi = e.matrix44() if m is None else e.matrix44() @ m
            walk(blk.entities_in_redraw_order() if hasattr(blk,'entities_in_redraw_order') else blk, mi)
        elif t in LOAI:
            i = len(ds); lay = 'R%d' % i
            out.layers.add(lay)
            r = om.new_entity('3DSOLID' if t == 'SURFACE' else t, {'layer': lay})
            if e.has_binary_data: r.sab = e.sab
            else: r.sat = e.sat
            ds.append({'i': i, 'loai': t, 'handle': e.dxf.handle, 'm': list(m) if m is not None else None})
walk(msp.entities_in_redraw_order(), None)
out.saveas(sys.argv[2])
json.dump(ds, open(sys.argv[3], 'w'), indent=0)
print(len(ds))
