# -*- coding: utf-8 -*-
"""Phần dùng chung của các script soát kết quả agent HS TKBVTC (chạy NGOÀI Revit, Python thường có Pillow + numpy).

Áp dụng ý tưởng của BIMgent (2026-11-17):
- mỗi lỗi / dòng "CẦN XEM LẠI" được phân loại rồi tra đúng mục trong mau\\goi_y_sua.json (nguyên nhân, cách sửa, ai quyết,
  được chạy lại mấy lần) – không phải đọc lại cả lịch sử bẫy;
- rút số liệu chính của từng mục (số ô, diện tích, số tag…) để so với chuẩn đã duyệt.

Không gắn cứng đường dẫn: mọi thứ tìm theo __file__ (quy tắc 8).
"""
import io
import json
import os
import re
import sys

THU_MUC = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(THU_MUC)
GOI_Y_FILE = os.path.join(SKILL, "mau", "goi_y_sua.json")


def utf8_ra():
    """Cho print tiếng Việt không lỗi trên console cp1252."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def doc_json(p):
    with io.open(p, encoding="utf-8-sig") as f:
        return json.load(f)


def ghi_json(p, d):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=1))


def ghi_chu(p, s):
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(s)


def file_moi(p):
    """Không ghi đè (quy tắc 1): đã có thì thêm _2, _3…"""
    if not os.path.exists(p):
        return p
    goc, duoi = os.path.splitext(p)
    i = 2
    while os.path.exists("%s_%d%s" % (goc, i, duoi)):
        i += 1
    return "%s_%d%s" % (goc, i, duoi)


def goi_y():
    return doc_json(GOI_Y_FILE)


def doc_ket_qua(lan):
    """lan = thư mục kết quả 1 lần chạy (có ket_qua.json) hoặc chính file ket_qua.json."""
    p = lan if lan.lower().endswith(".json") else os.path.join(lan, "ket_qua.json")
    if not os.path.isfile(p):
        raise IOError(u"Không thấy %s" % p)
    return doc_json(p), os.path.dirname(os.path.abspath(p))


# ----------------------------------------------------------------------------------------------- phân loại
# (mẫu regex, loại) – xét theo thứ tự, mẫu đầu tiên khớp là loại. Thêm câu báo mới của lõi: thêm dòng ở đây +
# khoá cùng tên trong goi_y_sua.json.
MAU = [
    (r"Số hiệu .* khác số yêu cầu", "so_hieu"),
    (r"không có khung tên", "khung_ten"),
    (r"không nằm trên bản vẽ nào", "khong_len_ban_ve"),
    (r"cặp tag đè nhau", "tag_de"),
    (r"tràn ra ngoài vùng vẽ", "tran"),               # tách tiếp thành tran_nho / tran_vua / tran_rat_lon
    (r"^(view|bảng) '.*' đè (view|bảng) '", "de"),     # tách tiếp thành de_bang / de_view
    (r"lớn hơn vùng (vẽ|trống)", "lon_hon_vung_ve"),
    (r"chạm bảng", "cham_bang"),
    (r"trong link chưa ẩn", "link_chua_an"),
    (r"KHÔNG theo tiền tố", "mark_sai_tien_to"),
    (r"chưa có Mark|Mark trống", "thieu_mark"),
    (r"không tìm được chỗ trống|tag còn đè|cần dời tay", "tag_can_doi_tay"),
    (r"CÓ EI NHƯNG TAG KHÔNG HIỆN EI", "ei_khong_hien"),
    (r"Không thấy trên tầng|chọn 0 đối tượng", "thieu_doi_tuong"),
    (r"phòng hở|> 15 m2|tràn qua lỗ mở", "phong_uot_nghi_ngo"),
    (r"Link KHÔNG nạp được", "link_khong_nap"),
    (r"^Lõi hỏi:", "loi_hoi"),
    (r"view đích, cần chọn 1|khoá view_dich", "nhieu_view_dich"),
    (r"không phải file cần mở|nút Mo không mở được|CArchiveException", "mo_file_that_bai"),
    (r"DesktopConnectorInterop|AcDbMgd", "acdbmgd"),
    (r"KHÔNG LƯU: đã có file", "trung_file_luu"),
    (r"Traceback", "loi_lop"),
]

_RE_TRAN = re.compile(r"\((\d+) x (\d+) mm\) tràn ra ngoài vùng vẽ (\d+) x (\d+) mm: trái (\d+) / dưới (\d+) / phải (\d+) / trên (\d+)")


def phan_loai(dong):
    s = (dong or u"").strip()
    for mau, loai in MAU:
        if re.search(mau, s):
            if loai == "tran":
                return _loai_tran(s)
            if loai == "de":
                return _loai_de(s)
            return loai
    return "khac"


_RE_DE = re.compile(r"^(view|bảng) '(.*)' đè (view|bảng) '(.*)' \(")
_CHU_BANG = (u"BẢNG", u"THỐNG KÊ", u"GHI CHÚ", u"CHÚ THÍCH")


def _la_bang(kieu, ten):
    t = (ten or u"").upper()
    return kieu == u"bảng" or any(c in t for c in _CHU_BANG)


def _loai_de(s):
    """Mặt bằng đè bảng (thống kê / ghi chú) = de_bang; 2 bảng hoặc 2 view thường đè nhau = de_view."""
    m = _RE_DE.match(s)
    if not m:
        return "de_view"
    a, b = _la_bang(m.group(1), m.group(2)), _la_bang(m.group(3), m.group(4))
    return "de_bang" if a != b else "de_view"


def _loai_tran(s):
    m = _RE_TRAN.search(s)
    if not m:
        return "tran_vua"
    w, h, vw, vh = [int(x) for x in m.groups()[:4]]
    lan = max(int(x) for x in m.groups()[4:])
    if w > 1.5 * vw or h > 1.5 * vh:
        return "tran_rat_lon"
    if lan <= 15:
        return "tran_nho"
    return "tran_vua"


# ----------------------------------------------------------------------------------------------- số liệu từng mục
def _so(m, i=1, kieu=int):
    try:
        return kieu(m.group(i))
    except Exception:
        return None


SO_LIEU = [
    # (nút hoặc None = mọi nút, regex, [tên số liệu theo nhóm], kiểu)
    ("NganChay", r"Filled Region ngăn cháy lan \((\d+) ô\)", ["o_hatch"], int),
    ("NganChay", r"Trục / hộp kỹ thuật cần hatch: (\d+)", ["truc_can_hatch"], int),
    ("NganChay", r"loại vì thang: (\d+)", ["loai_vi_thang"], int),
    ("ChongTham", r"Hatch Filled Region sẽ vẽ: (\d+) phòng", ["phong_uot"], int),
    ("ChongTham", r"ĐÃ VẼ (\d+) nét vén", ["net_ven"], int),
    (None, r"^Diện tích [^:]*: ([\d.]+) m", ["dien_tich_m2"], float),
    ("TagCua", r"Đã tag: (\d+) cửa đi, (\d+) cửa sổ, (\d+) lam / louver; đặt lại (\d+) tag cũ; (\d+) tag có leader",
     ["tag_cua_di", "tag_cua_so", "tag_louver", "tag_dat_lai", "tag_leader"], int),
    ("TagCua", r"đã tag (\d+) vách kính", ["tag_vach_kinh"], int),
    ("TagCua", r"Không tag (\d+) cửa đi / cửa sổ nằm trong vách kính", ["cua_trong_vach_kinh"], int),
    ("TagCua", r"chưa có Mark \(không tag\): (\d+)", ["vach_kinh_chua_mark"], int),
    ("LanCanLouver", r"Nhận (\d+) lan can, (\d+) louver", ["nhan_lan_can", "nhan_louver"], int),
    ("LanCanLouver", r"Đã tag: (\d+) lan can, (\d+) louver; đặt lại (\d+) tag cũ; (\d+) tag có leader; bỏ qua (\d+)",
     ["tag_lan_can", "tag_louver", "tag_dat_lai", "tag_leader", "bo_qua_da_co_tag"], int),
    ("ChiTietCua", r"Số cửa / vách kính đã chọn: (\d+)", ["cua_da_chon"], int),
]


def so_lieu_muc(m):
    """Rút số liệu chính từ các dòng báo của lõi (m['dong']). Thiếu dòng thì không có khoá đó."""
    kq = {}
    nut = m.get("nut")
    for ln in m.get("dong") or []:
        s = ln.strip()
        for n, mau, ten, kieu in SO_LIEU:
            if n and n != nut:
                continue
            r = re.search(mau, s)
            if r:
                for i, t in enumerate(ten):
                    kq[t] = _so(r, i + 1, kieu)
        if nut == "ChiTietCua" and s.startswith(u"Xong: sheet"):
            kq["cua_xong"] = kq.get("cua_xong", 0) + 1
    kq["can_xem_lai"] = len(m.get("can_xem") or [])
    return kq


def khoa_muc(m):
    return u"%s|%s" % (m.get("view"), m.get("nut"))


def anh_cua_lan(thu_muc):
    """{số hiệu: đường dẫn PNG} – ảnh Revit xuất tên '<số-hiệu> - Sheet - <số-hiệu> - <tên>.png' (bỏ ảnh xem nhanh _xem_)."""
    ds = {}
    for f in sorted(os.listdir(thu_muc)):
        if f.lower().endswith(".png") and not f.startswith("_") and u" - Sheet - " in f:
            ds[f.split(u" - Sheet - ")[0]] = os.path.join(thu_muc, f)
    return ds


def so_anh_file(so):
    return (so or u"").replace(u".", u"-").replace(u"/", u"-")
