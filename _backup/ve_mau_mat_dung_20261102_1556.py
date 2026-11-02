# Ảnh mẫu (mockup) mặt đứng cửa kính cường lực bản lề sàn + vách kính cường lực kẹp, để người dùng duyệt bố cục
# trước khi viết LISP. Mọi kích thước là giá trị mặc định tạm (Cần xác nhận lại), sẽ là ô nhập trong bảng.
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

plt.rcParams['font.family'] = 'Arial'
OUT = Path(__file__).resolve().parent / '01_mau_mat_dung_cua_kinh.png'

# ---- thông số mặc định (mm) ----
W_TRAI, W_CUA, W_PHAI = 800, 900, 800    # module ô fix trái / cửa / ô fix phải
H_CUA, H_TONG = 2400, 3000               # cao cửa (từ sàn HT), cao vách (tới trần)
KHE = 3                                  # khe kính - kính
KHE_DUOI = 10                            # khe đáy cửa - sàn HT
KEP_W, KEP_H = 180, 60                   # kẹp trên / dưới / khoá sàn (mặt đứng)
KEP_FIX = 60                             # kẹp kính - kính ô fix
TN_DAI, TN_TAM, TN_CACH = 600, 1050, 80  # tay nắm: dài, cao tâm, cách mép cửa
BLS_DAI, BLS_SAU = 300, 60               # hộp bản lề sàn (khuất)
TUONG = 200

C_KINH = '#1f6fb5'    # A-Window
C_KEP = '#222222'
C_DIM = '#7a3db8'     # A-Dimension
C_TXT = '#b8860b'     # A-Text
C_KHUAT = '#888888'   # A-Hidden

x0, x1 = 0, W_TRAI
x2 = x1 + W_CUA
x3 = x2 + W_PHAI

fig, ax = plt.subplots(figsize=(16, 11), dpi=110)
ax.set_aspect('equal'); ax.axis('off')


def rect(x, y, w, h, **kw):
    ax.add_patch(Rectangle((x, y), w, h, **kw))


def kinh(xa, ya, xb, yb):
    rect(xa, ya, xb - xa, yb - ya, fill=False, ec=C_KINH, lw=1.4)
    # ký hiệu kính "///"
    cx, cy = (xa + xb) / 2, (ya + yb) / 2
    for d in (-60, 0, 60):
        ax.plot([cx + d - 70, cx + d + 70], [cy - 110, cy + 110], color=C_KINH, lw=0.9)


def dim_ngang(xa, xb, y, txt=None, yref=None):
    ax.plot([xa, xb], [y, y], color=C_DIM, lw=0.8)
    for x in (xa, xb):
        ax.plot([x - 25, x + 25], [y - 25, y + 25], color=C_DIM, lw=1.2)
        if yref is not None:
            ax.plot([x, x], [yref - 80 if yref > y else yref - 80, y - 60], color=C_DIM, lw=0.5)
    ax.text((xa + xb) / 2, y + 30, txt or f'{xb - xa:g}', ha='center', va='bottom', color=C_DIM, fontsize=9)


def dim_dung(ya, yb, x, txt=None, xref=None):
    ax.plot([x, x], [ya, yb], color=C_DIM, lw=0.8)
    for y in (ya, yb):
        ax.plot([x - 25, x + 25], [y - 25, y + 25], color=C_DIM, lw=1.2)
        if xref is not None:
            ax.plot([xref + 80, x + 60], [y, y], color=C_DIM, lw=0.5)
    ax.text(x + 40, (ya + yb) / 2, txt or f'{yb - ya:g}', ha='left', va='center', rotation=90, color=C_DIM, fontsize=9)


def ghi_chu(px, py, tx, ty, s, trai=False):
    # trai=True: chữ nằm bên trái, căn phải tại tx
    d = -1 if trai else 1
    ax.plot([px, tx], [py, ty], color=C_TXT, lw=0.7)
    ax.plot([tx, tx + 60 * d], [ty, ty], color=C_TXT, lw=0.7)
    ax.plot(px, py, 'o', ms=3, color=C_TXT)
    ax.text(tx + 80 * d, ty, s, ha='right' if trai else 'left', va='center', color=C_TXT, fontsize=9)


# ---- tường, sàn HT, trần ----
for xa in (-TUONG, x3):
    rect(xa, -150, TUONG, H_TONG + 300, fill=True, fc='#eeeeee', ec='#555555', lw=1.2, hatch='///')
ax.plot([-TUONG - 150, x3 + TUONG + 150], [0, 0], color='#333333', lw=1.4)
ax.text(x0 + 40, 30, 'SÀN HT ±0.000', fontsize=8, color='#333333')
ax.plot([-TUONG - 150, x3 + TUONG + 150], [H_TONG, H_TONG], color='#333333', lw=1.0)
ax.text(x0 + 40, H_TONG - 90, 'TRẦN / DẦM', fontsize=8, color='#333333')

# ---- kính ----
kinh(x0 + 5, 0, x1 - KHE / 2, H_TONG)                                  # ô fix trái (chân trong rãnh U)
kinh(x2 + KHE / 2, 0, x3 - 5, H_TONG)                                  # ô fix phải
kinh(x1 + KHE / 2, H_CUA + KHE, x2 - KHE / 2, H_TONG)                  # ô fix trên cửa
kinh(x1 + KHE / 2, KHE_DUOI, x2 - KHE / 2, H_CUA)                      # cánh cửa

# rãnh U chân / đỉnh ô fix (khuất)
for xa, xb in ((x0, x1), (x2, x3)):
    rect(xa, -40, xb - xa, 40, fill=False, ec=C_KHUAT, lw=0.8, ls='--')
    rect(xa, H_TONG, xb - xa, 40, fill=False, ec=C_KHUAT, lw=0.8, ls='--')
rect(x1, H_TONG, W_CUA, 40, fill=False, ec=C_KHUAT, lw=0.8, ls='--')

# ---- phụ kiện ----
rect(x1, H_CUA - KEP_H, KEP_W, KEP_H * 2 + KHE, fc=C_KEP, ec=C_KEP)    # kẹp trên (nối ô fix trên, top pivot)
rect(x1, KHE_DUOI, KEP_W, KEP_H, fc=C_KEP, ec=C_KEP)                   # kẹp dưới (bản lề sàn)
rect(x2 - KEP_W, KHE_DUOI, KEP_W, KEP_H, fc=C_KEP, ec=C_KEP)           # khoá sàn
for xk in (x1, x2):                                                     # kẹp ô fix trên - ô fix bên
    rect(xk - KEP_FIX / 2, H_TONG - 400, KEP_FIX, KEP_FIX, fc=C_KEP, ec=C_KEP)
rect(x2 - KEP_FIX / 2, H_CUA - KEP_H, KEP_FIX, KEP_H * 2 + KHE, fc=C_KEP, ec=C_KEP)  # kẹp góc phía khoá

# hộp bản lề sàn (khuất, dưới sàn)
rect(x1 - 20, -BLS_SAU - 10, BLS_DAI, BLS_SAU, fill=False, ec=C_KHUAT, lw=1.0, ls='--')

# tay nắm
xt = x2 - TN_CACH
ya, yb = TN_TAM - TN_DAI / 2, TN_TAM + TN_DAI / 2
rect(xt - 13, ya, 26, TN_DAI, fill=False, ec=C_KEP, lw=1.3)
for y in (ya + 60, yb - 60):
    ax.plot([xt - 25, xt + 25], [y, y], color=C_KEP, lw=2)

# hướng mở (đỉnh tam giác về phía bản lề)
ax.plot([x2 - KHE / 2, x1 + KHE / 2, x2 - KHE / 2], [H_CUA, (H_CUA + KHE_DUOI) / 2, KHE_DUOI],
        color=C_KINH, lw=0.8, ls=(0, (8, 6)))

# ---- kích thước ----
dim_ngang(x0, x1, -350, yref=0); dim_ngang(x1, x2, -350, yref=0); dim_ngang(x2, x3, -350, yref=0)
dim_ngang(x0, x3, -550, yref=0)
dim_dung(0, H_CUA, x3 + TUONG + 250, xref=x3); dim_dung(H_CUA, H_TONG, x3 + TUONG + 250, xref=x3)
dim_dung(0, H_TONG, x3 + TUONG + 450, xref=x3)
dim_dung(0, TN_TAM, x2 - 330, txt=f'{TN_TAM:g}')
ax.plot([x2 - 330, xt - 13], [TN_TAM, TN_TAM], color=C_DIM, lw=0.5)

# ---- ghi chú ----
gx = x3 + TUONG + 750
tx = -TUONG - 350
ghi_chu(x1 + KEP_W / 2, H_CUA, tx, 2550, 'KẸP TRÊN (TOP PIVOT + NỐI Ô FIX)', True)
ghi_chu(x0 + 300, 1900, tx, 1900, 'KÍNH CƯỜNG LỰC 12mm - Ô FIX BÊN', True)
ghi_chu(x1 + KEP_W / 2, KHE_DUOI + KEP_H / 2, tx, 800, 'KẸP DƯỚI', True)
ghi_chu(x1 + 150, -40, tx, 450, 'BẢN LỀ SÀN (ÂM SÀN, NÉT KHUẤT)', True)
ghi_chu(x0 + 400, -20, tx, 150, 'RÃNH U CHÂN / ĐỈNH KÍNH FIX', True)
ghi_chu(x2 - 250, H_TONG - 150, gx, 2850, 'KÍNH CƯỜNG LỰC 12mm - Ô FIX TRÊN')
ghi_chu(x2, H_TONG - 370, gx, 2600, 'KẸP KÍNH - KÍNH Ô FIX')
ghi_chu(x1 + 450, 1800, gx, 1800, 'CÁNH CỬA KÍNH CƯỜNG LỰC 12mm')
ghi_chu(xt, TN_TAM + 150, gx, 1300, 'TAY NẮM INOX D25 L=600')
ghi_chu(x2 - KEP_W / 2, KHE_DUOI + KEP_H / 2, gx, 700, 'KHOÁ SÀN (KẸP KHOÁ)')

ax.text((x0 + x3) / 2, -900, 'MẶT ĐỨNG CỬA KÍNH CƯỜNG LỰC BẢN LỀ SÀN  -  TL 1/50',
        ha='center', fontsize=13, fontweight='bold')
ax.text((x0 + x3) / 2, -1060, 'Ảnh mẫu bố cục - mọi kích thước là giá trị mặc định tạm (Cần xác nhận lại), '
        'sẽ là ô nhập trong bảng', ha='center', fontsize=9, color='#c0392b')

ax.set_xlim(-TUONG - 2900, gx + 2700)
ax.set_ylim(-1150, H_TONG + 250)
fig.tight_layout()
fig.savefig(OUT, facecolor='white')
print(OUT)
