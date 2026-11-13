# Vẽ lại 1 ô từ ct_cua.json (kiểm tra trích xuất) + vẽ CAD gốc cùng vùng để so
import json, sys, math, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Arc
d = json.load(open('ct_cua.json', encoding='utf-8'))
ten = sys.argv[1]
o = [o for o in d['o'] if o['ten'] == ten][0]
W = {'thin': 0.3, 'medium': 0.7, 'wide': 1.2, 'hidden': 0.3, 'center': 0.3}
LS = {'hidden': (0, (4, 2)), 'center': (0, (8, 2, 1, 2))}
b = o['bounds']; w = b[2]-b[0]; h = b[3]-b[1]
fig = plt.figure(figsize=(w/500, h/500), dpi=150); ax = fig.add_axes([0,0,1,1]); ax.set_aspect('equal'); ax.axis('off')
def pts(loop):
    p = []
    for s in loop:
        if s[0] == 'L': p += [(s[1], s[2])]
        else:
            # cung 3 điểm: chia
            (x0,y0),(xm,ym),(x1,y1) = (s[1],s[2]),(s[3],s[4]),(s[5],s[6])
            p += [(x0,y0),(xm,ym)]
    return p
for v in sorted(o['vung'], key=lambda v: v['z']):
    m = d['mau_hatch'][v['kieu']]
    col = [c/255 for c in m['rgb']]
    for l in v['loops']:
        ax.add_patch(Polygon(pts(l), closed=True, fc=col if m['solid'] else 'none', ec='none' if m['solid'] else (0.6,0.6,1.0), lw=0.2, hatch=None if m['solid'] else '////', alpha=1 if m['solid'] else 0.5))
for v in o['che']:
    for l in v['loops']: ax.add_patch(Polygon(pts(l), closed=True, fc='white', ec='none'))
for x1,y1,x2,y2,k,z in o['net']:
    ax.plot([x1,x2],[y1,y2], color='k', lw=W[k], ls=LS.get(k,'-'))
for cx,cy,r,a0,a1,k,z in o['cung']:
    ax.add_patch(Arc((cx,cy),2*r,2*r,theta1=a0,theta2=a1,color='k',lw=W[k]))
for t in o['chu']:
    ax.text(t['x'], t['y'], t['t'], fontsize=t['h']/500*72*0.9, rotation=t['rot'], ha={'L':'left','C':'center','R':'right'}[t['ngang']],
            va={'M':'center','T':'top','B':'bottom'}[t['doc']], color='b', rotation_mode='anchor')
for dm in o['dim']:
    a = math.radians(dm['ang']); ux,uy = math.cos(a), math.sin(a)
    def proj(p):
        t = (p[0]-dm['p1'][0])*ux + (p[1]-dm['p1'][1])*uy
        return (dm['p1'][0]+t*ux, dm['p1'][1]+t*uy)
    q2, q3 = proj(dm['p2']), proj(dm['p3'])
    ax.plot([q2[0],q3[0]],[q2[1],q3[1]], color='r', lw=0.4)
    ax.plot([dm['p2'][0],q2[0]],[dm['p2'][1],q2[1]], color='r', lw=0.3); ax.plot([dm['p3'][0],q3[0]],[dm['p3'][1],q3[1]], color='r', lw=0.3)
    ax.text((q2[0]+q3[0])/2,(q2[1]+q3[1])/2, dm['tien_to']+dm['hien']+dm['hau_to'], color='r', fontsize=dm['h']/20*1.6, rotation=dm['ang'] if -90<dm['ang']<=90 else dm['ang']-180, ha='center', va='bottom', rotation_mode='anchor')
x0 = b[0]+o['dx']; y0 = b[1]+o['dy']
ax.set_xlim(x0-50, x0+w+50); ax.set_ylim(y0-50, y0+h+50)
fig.savefig(sys.argv[2])
