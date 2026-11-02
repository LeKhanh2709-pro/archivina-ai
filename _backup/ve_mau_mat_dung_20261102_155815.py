# Ảnh mẫu (mockup) mặt đứng cửa kính cường lực bản lề sàn (1 cánh / 2 cánh) + vách kính cường lực kẹp, để người
# dùng duyệt bố cục trước khi viết LISP. Mọi kích thước là giá trị mặc định tạm (Cần xác nhận lại), sẽ là ô nhập
# trong bảng.
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams['font.family'] = 'Arial'
THU_MUC = Path(__file__).resolve().parent

# ---- thông số mặc định (mm) ----
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


def ve(so_canh, w_trai, w_cua, w_phai, out):
    x0, x1 = 0, w_trai
    x2 = x1 + w_cua
    x3 = x2 + w_phai
    # cánh: (trái, phải, bản lề bên trái?)
    if so_canh == 1:
        canh = [(x1, x2, True)]
    else:
        xm = x1 + w_cua / 2
        canh = [(x1, xm, True), (xm, x2, False)]

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

    def dim_ngang(xa, xb, y, yref):
        ax.plot([xa, xb], [y, y], color=C_DIM, lw=0.8)
        for x in (xa, xb):
            ax.plot([x - 25, x + 25], [y - 25, y + 25], color=C_DIM, lw=1.2)
            ax.plot([x, x], [yref - 80, y - 60], color=C_DIM, lw=0.5)
        ax.text((xa + xb) / 2, y + 30, f'{xb - xa:g}', ha='center', va='bottom', color=C_DIM, fontsize=9)

    def dim_dung(ya, yb, x, xref=None):
        ax.plot([x, x], [ya, yb], color=C_DIM, lw=0.8)
        for y in (ya, yb):
            ax.plot([x - 25, x + 25], [y - 25, y + 25], color=C_DIM, lw=1.2)
            if xref is not None:
                ax.plot([xref + 80, x + 60], [y, y], color=C_DIM, lw=0.5)
        ax.text(x + 40, (ya + yb) / 2, f'{yb - ya:g}', ha='left', va='center', rotation=90, color=C_DIM,
                fontsize=9)

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

    # ---- kính fix ----
    kinh(x0 + 5, 0, x1 - KHE / 2, H_TONG)                                  # ô fix trái (chân trong rãnh U)
    kinh(x2 + KHE / 2, 0, x3 - 5, H_TONG)                                  # ô fix phải
    kinh(x1 + KHE / 2, H_CUA + KHE, x2 - KHE / 2, H_TONG)                  # ô fix trên cửa

    # rãnh U chân / đỉnh ô fix (khuất)
    for xa, xb in ((x0, x1), (x2, x3)):
        rect(xa, -40, xb - xa, 40, fill=False, ec=C_KHUAT, lw=0.8, ls='--')
        rect(xa, H_TONG, xb - xa, 40, fill=False, ec=C_KHUAT, lw=0.8, ls='--')
    rect(x1, H_TONG, w_cua, 40, fill=False, ec=C_KHUAT, lw=0.8, ls='--')

    # kẹp ô fix trên - ô fix bên
    for xk in (x1, x2):
        rect(xk - KEP_FIX / 2, H_TONG - 400, KEP_FIX, KEP_FIX, fc=C_KEP, ec=C_KEP)

    # ---- từng cánh ----
    tay_nam = []
    for xa, xb, bl_trai in canh:
        kinh(xa + KHE / 2, KHE_DUOI, xb - KHE / 2, H_CUA)
        h, l = (xa, xb) if bl_trai else (xb, xa)       # mép bản lề, mép khoá
        s = 1 if bl_trai else -1                       # hướng từ mép bản lề vào trong cánh
        xk_bl = h if bl_trai else h - KEP_W            # góc trái của kẹp phía bản lề
        xk_kh = l - KEP_W if bl_trai else l            # góc trái của kẹp phía khoá
        rect(xk_bl, H_CUA - KEP_H, KEP_W, KEP_H * 2 + KHE, fc=C_KEP, ec=C_KEP)   # kẹp trên (top pivot + nối ô fix)
        rect(xk_bl, KHE_DUOI, KEP_W, KEP_H, fc=C_KEP, ec=C_KEP)                  # kẹp dưới (bản lề sàn)
        rect(xk_kh, KHE_DUOI, KEP_W, KEP_H, fc=C_KEP, ec=C_KEP)                  # khoá sàn
        # hộp bản lề sàn (khuất, dưới sàn)
        rect(h - 20 if bl_trai else h + 20 - BLS_DAI, -BLS_SAU - 10, BLS_DAI, BLS_SAU,
             fill=False, ec=C_KHUAT, lw=1.0, ls='--')
        # tay nắm
        xt = l - s * TN_CACH
        ya, yb = TN_TAM - TN_DAI / 2, TN_TAM + TN_DAI / 2
        rect(xt - 13, ya, 26, TN_DAI, fill=False, ec=C_KEP, lw=1.3)
        for y in (ya + 60, yb - 60):
            ax.plot([xt - 25, xt + 25], [y, y], color=C_KEP, lw=2)
        tay_nam.append((xt, l, s))
        # hướng mở (đỉnh tam giác về phía bản lề)
        ax.plot([l - s * KHE / 2, h + s * KHE / 2, l - s * KHE / 2], [H_CUA, (H_CUA + KHE_DUOI) / 2, KHE_DUOI],
                color=C_KINH, lw=0.8, ls=(0, (8, 6)))
    if so_canh == 1:
        rect(x2 - KEP_FIX / 2, H_CUA - KEP_H, KEP_FIX, KEP_H * 2 + KHE, fc=C_KEP, ec=C_KEP)  # kẹp góc phía khoá

    # ---- kích thước ----
    moc = [x0, x1] + [c[1] for c in canh] + [x3]
    for xa, xb in zip(moc, moc[1:]):
        dim_ngang(xa, xb, -350, 0)
    dim_ngang(x0, x3, -550, 0)
    dim_dung(0, H_CUA, x3 + TUONG + 250, xref=x3); dim_dung(H_CUA, H_TONG, x3 + TUONG + 250, xref=x3)
    dim_dung(0, H_TONG, x3 + TUONG + 450, xref=x3)
    xt, l, s = tay_nam[-1]                             # dim cao tâm tay nắm ở cánh cuối
    xd = l - s * 330
    dim_dung(0, TN_TAM, xd)
    ax.plot([xd, xt + s * 13], [TN_TAM, TN_TAM], color=C_DIM, lw=0.5)

    # ---- ghi chú ----
    gx = x3 + TUONG + 750
    tx = -TUONG - 350
    hl = canh[0][0]                                    # mép bản lề cánh trái
    kh_phai = canh[-1]                                 # cánh có khoá sàn ghi chú bên phải
    xk_ghi = kh_phai[1] - KEP_W / 2 if kh_phai[2] else kh_phai[0] + KEP_W / 2
    ghi_chu(hl + KEP_W / 2, H_CUA, tx, 2550, 'KẸP TRÊN (TOP PIVOT + NỐI Ô FIX)', True)
    ghi_chu(x0 + 300, 1900, tx, 1900, 'KÍNH CƯỜNG LỰC 12mm - Ô FIX BÊN', True)
    ghi_chu(hl + KEP_W / 2, KHE_DUOI + KEP_H / 2, tx, 800, 'KẸP DƯỚI', True)
    ghi_chu(hl + 150, -40, tx, 450, 'BẢN LỀ SÀN (ÂM SÀN, NÉT KHUẤT)', True)
    ghi_chu(x0 + 400, -20, tx, 150, 'RÃNH U CHÂN / ĐỈNH KÍNH FIX', True)
    ghi_chu(x2 - 250, H_TONG - 150, gx, 2850, 'KÍNH CƯỜNG LỰC 12mm - Ô FIX TRÊN')
    ghi_chu(x2, H_TONG - 370, gx, 2600, 'KẸP KÍNH - KÍNH Ô FIX')
    ghi_chu(kh_phai[1] - 250, 1800, gx, 1800, 'CÁNH CỬA KÍNH CƯỜNG LỰC 12mm')
    ghi_chu(xt, TN_TAM + 150, gx, 1300, 'TAY NẮM INOX D25 L=600' + (' (2 BỘ)' if so_canh == 2 else ''))
    ghi_chu(xk_ghi, KHE_DUOI + KEP_H / 2, gx, 700, 'KHOÁ SÀN (KẸP KHOÁ)')

    ten = 'MẶT ĐỨNG CỬA KÍNH CƯỜNG LỰC ' + ('2 CÁNH ' if so_canh == 2 else '1 CÁNH ') + 'BẢN LỀ SÀN  -  TL 1/50'
    ax.text((x0 + x3) / 2, -900, ten, ha='center', fontsize=13, fontweight='bold')
    ax.text((x0 + x3) / 2, -1060, 'Ảnh mẫu bố cục - mọi kích thước là giá trị mặc định tạm (Cần xác nhận lại), '
            'sẽ là ô nhập trong bảng', ha='center', fontsize=9, color='#c0392b')

    ax.set_xlim(-TUONG - 2900, gx + 2700)
    ax.set_ylim(-1150, H_TONG + 250)
    fig.tight_layout()
    fig.savefig(out, facecolor='white')
    plt.close(fig)
    print(out)


ve(1, 800, 900, 800, THU_MUC / '01_mau_mat_dung_cua_kinh.png')
ve(2, 800, 1600, 800, THU_MUC / '02_mau_mat_dung_cua_kinh_2canh.png')
