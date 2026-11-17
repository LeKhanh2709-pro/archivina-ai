# -*- coding: utf-8 -*-
"""So 2 ảnh bản vẽ (PNG xuất từ Revit) → khoanh các vùng khác nhau, đánh số (ý tưởng "so ảnh trước / sau" của BIMgent).

Dùng khi:
  - bấm lại / chạy lại → ảnh phải GIỐNG lần trước (không vẽ trùng);
  - sửa phương án / sửa công cụ → chỉ xem vùng thay đổi so với bản người dùng đã duyệt.

Cách dùng (Python có Pillow + numpy, vd. <gốc>\\_tools\\venv):
  python so_anh.py <ảnh A (cũ)> <ảnh B (mới)> [--ra <ảnh kết quả.png>]
  python so_anh.py --thu-muc <thư mục lần A> <thư mục lần B> --ra <thư mục kết quả MỚI>
     (ghép ảnh theo số hiệu bản vẽ trong tên file '<số> - Sheet - …png'; ghi so_anh.json + ảnh so từng tờ)
Ảnh kết quả: nền là ảnh B nhạt, nét CHỈ CÓ ở A (mất đi) màu đỏ, nét chỉ có ở B (thêm vào) màu xanh, khung cam đánh số
từng vùng. Lệch ≤ 2 px (khử răng cưa) không tính là khác.
Chỉ đọc ảnh, không sửa gì; không ghi đè file đã có.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soat_chung as sc  # noqa: E402

NGUONG_TOI = 160      # điểm ảnh < ngưỡng = nét
LECH_PX = 2           # chấp nhận lệch
O_LUOI = 24           # cỡ ô gom vùng (px)
DIEM_O = 4            # ô có ≥ số điểm khác này mới tính
RONG_RA = 2400        # ảnh kết quả thu về bề rộng này


def _nap(p):
    a = np.asarray(Image.open(p).convert("L"))
    m = a < 245
    r, c = np.where(m.any(axis=1))[0], np.where(m.any(axis=0))[0]
    if len(r) == 0:
        return a, (0, 0, a.shape[1], a.shape[0])
    y0, y1, x0, x1 = r[0], r[-1] + 1, c[0], c[-1] + 1
    return a[y0:y1, x0:x1], (x0, y0, x1, y1)


def _no(b, r):
    """Nở vùng True r px (lấy max trên ô vuông 2r+1)."""
    h, w = b.shape
    p = np.pad(b, r)
    kq = np.zeros_like(b)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            kq |= p[dy:dy + h, dx:dx + w]
    return kq


def _vung(doi, o=O_LUOI, nguong=DIEM_O):
    """Gom điểm khác thành các khung (px) theo lưới ô, ô kề nhau (kể cả chéo, cách 1 ô) là 1 vùng."""
    h, w = doi.shape
    H, W = -(-h // o), -(-w // o)
    p = np.zeros((H * o, W * o), bool)
    p[:h, :w] = doi
    dem = p.reshape(H, o, W, o).sum(axis=(1, 3))
    bat = dem >= nguong
    gan = _no(bat, 1)
    nhan = np.zeros((H, W), int)
    ds = []
    for y in range(H):
        for x in range(W):
            if not bat[y, x] or nhan[y, x]:
                continue
            ky = len(ds) + 1
            ngan = [(y, x)]
            nhan[y, x] = ky
            y0, y1, x0, x1 = y, y, x, x
            while ngan:
                cy, cx = ngan.pop()
                y0, y1, x0, x1 = min(y0, cy), max(y1, cy), min(x0, cx), max(x1, cx)
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and gan[ny, nx] and not nhan[ny, nx]:
                            nhan[ny, nx] = ky
                            ngan.append((ny, nx))
            ds.append((x0 * o, y0 * o, min(w, (x1 + 1) * o), min(h, (y1 + 1) * o)))
    return ds


def so_sanh(a_p, b_p, ra=None):
    """Trả về dict kết quả; ra = đường dẫn ảnh so (file mới, không ghi đè)."""
    a, _ = _nap(a_p)
    b, _ = _nap(b_p)
    canh_bao = []
    if a.shape != b.shape:
        ty_a, ty_b = a.shape[1] / float(a.shape[0]), b.shape[1] / float(b.shape[0])
        if abs(ty_a - ty_b) / ty_a > 0.01:
            canh_bao.append(u"Khung nội dung 2 ảnh khác tỉ lệ (%dx%d / %dx%d px): có thể có phần tràn ra ngoài khung tên "
                            u"khác nhau – vùng khác có thể lệch chỗ." % (a.shape[1], a.shape[0], b.shape[1], b.shape[0]))
        b = np.asarray(Image.fromarray(b).resize((a.shape[1], a.shape[0]), Image.LANCZOS))
    ad, bd = a < NGUONG_TOI, b < NGUONG_TOI
    mat = ad & ~_no(bd, LECH_PX)
    them = bd & ~_no(ad, LECH_PX)
    doi = mat | them
    net = int((ad | bd).sum()) or 1
    vung = _vung(doi)
    h, w = a.shape
    kq = {"a": os.path.abspath(a_p), "b": os.path.abspath(b_p),
          "ty_le_khac_phan_tram": round(100.0 * doi.sum() / net, 3), "so_vung": len(vung),
          "giong": len(vung) == 0,
          "vung": [{"so": i + 1, "px": [int(v) for v in vb],
                    "vi_tri": u"%s, %s" % (_doc(vb[0] + vb[2], 2 * w, (u"trái", u"giữa", u"phải")),
                                          _doc(vb[1] + vb[3], 2 * h, (u"trên", u"giữa", u"dưới")))}
                   for i, vb in enumerate(vung)],
          "canh_bao": canh_bao}
    if ra:
        ra = sc.file_moi(ra)
        nen = (255 - (255 - b.astype(np.int16)) * 0.35).clip(0, 255).astype(np.uint8)
        rgb = np.stack([nen, nen, nen], axis=-1)
        rgb[mat] = (220, 30, 30)
        rgb[them] = (20, 90, 230)
        im = Image.fromarray(rgb)
        tl = min(1.0, RONG_RA / float(w))
        if tl < 1.0:
            im = im.resize((int(w * tl), int(h * tl)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        try:
            ft = ImageFont.load_default(size=max(14, int(28 * tl / 0.6)))
        except Exception:
            ft = ImageFont.load_default()
        for v in kq["vung"]:
            x0, y0, x1, y1 = [int(t * tl) for t in v["px"]]
            d.rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], outline=(255, 140, 0), width=3)
            d.text((x0 - 4, max(0, y0 - 34)), str(v["so"]), fill=(255, 100, 0), font=ft)
        im.save(ra)
        kq["anh_so"] = os.path.abspath(ra)
    return kq


def _doc(tong, toan, ten):
    t = tong / float(toan)
    return ten[0] if t < 1 / 3.0 else (ten[1] if t < 2 / 3.0 else ten[2])


def so_thu_muc(a_dir, b_dir, ra_dir):
    if os.path.exists(ra_dir) and os.listdir(ra_dir):
        raise IOError(u"Thư mục kết quả đã có file (không ghi đè): %s" % ra_dir)
    os.makedirs(ra_dir, exist_ok=True)
    A, B = sc.anh_cua_lan(a_dir), sc.anh_cua_lan(b_dir)
    tong = {"a": os.path.abspath(a_dir), "b": os.path.abspath(b_dir), "to": [],
            "chi_co_o_a": sorted(set(A) - set(B)), "chi_co_o_b": sorted(set(B) - set(A))}
    for so in sorted(set(A) & set(B)):
        r = so_sanh(A[so], B[so], os.path.join(ra_dir, u"%s_so.png" % so))
        r["so_hieu"] = so
        tong["to"].append(r)
    sc.ghi_json(os.path.join(ra_dir, "so_anh.json"), tong)
    return tong


def main():
    sc.utf8_ra()
    ap = argparse.ArgumentParser(description=u"So 2 ảnh / 2 lần chạy, khoanh vùng khác nhau.")
    ap.add_argument("a", nargs="?")
    ap.add_argument("b", nargs="?")
    ap.add_argument("--thu-muc", nargs=2, metavar=("A", "B"))
    ap.add_argument("--ra")
    g = ap.parse_args()
    if g.thu_muc:
        if not g.ra:
            ap.error(u"--thu-muc cần --ra <thư mục mới>")
        t = so_thu_muc(g.thu_muc[0], g.thu_muc[1], g.ra)
        for r in t["to"]:
            print(u"%-16s %s  khác %.3f%%  %d vùng%s" % (r["so_hieu"], u"GIỐNG" if r["giong"] else u"KHÁC ",
                                                     r["ty_le_khac_phan_tram"], r["so_vung"],
                                                     (u"  ⚠ " + r["canh_bao"][0]) if r["canh_bao"] else u""))
        if t["chi_co_o_a"]:
            print(u"Chỉ có ở A:", u", ".join(t["chi_co_o_a"]))
        if t["chi_co_o_b"]:
            print(u"Chỉ có ở B:", u", ".join(t["chi_co_o_b"]))
        print(u"Kết quả:", os.path.join(g.ra, "so_anh.json"))
        return 0 if all(r["giong"] for r in t["to"]) and not t["chi_co_o_a"] and not t["chi_co_o_b"] else 1
    if not (g.a and g.b):
        ap.error(u"cần 2 ảnh hoặc --thu-muc")
    r = so_sanh(g.a, g.b, g.ra)
    print(u"%s – khác %.3f%% nét, %d vùng" % (u"GIỐNG" if r["giong"] else u"KHÁC", r["ty_le_khac_phan_tram"], r["so_vung"]))
    for v in r["vung"]:
        print(u"  %d. %s (px %s)" % (v["so"], v["vi_tri"], v["px"]))
    for c in r["canh_bao"]:
        print(u"  ⚠", c)
    if r.get("anh_so"):
        print(u"Ảnh so:", r["anh_so"])
    return 0 if r["giong"] else 1


if __name__ == "__main__":
    sys.exit(main())
