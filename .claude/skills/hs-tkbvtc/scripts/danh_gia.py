# -*- coding: utf-8 -*-
"""Đánh giá 1 lần chạy của agent HS TKBVTC (chạy NGOÀI Revit) – áp dụng vòng giám sát của BIMgent:

  1. Mỗi bản vẽ được xếp 1 trong 4 trạng thái (tách bước tự động / cần nhìn / cần người quyết):
       ĐẠT                  – kiểm tra sạch, lõi không báo gì: agent chỉ cần xem ảnh 1 lần;
       CẦN XEM ẢNH          – lõi có dòng CẦN XEM LẠI loại agent tự soát được bằng ảnh;
       CẦN NGƯỜI DÙNG QUYẾT – lỗi trình bày / câu hỏi của lõi (quy tắc 10, 11 của agent: chỉ báo, không tự sửa);
       LỖI CHẠY             – phiên / lõi lỗi: theo luật chạy lại bên dưới.
  2. Mỗi vấn đề kèm NGUYÊN NHÂN THƯỜNG GẶP + CÁCH XỬ LÝ + AI QUYẾT, tra theo loại trong mau\\goi_y_sua.json.
  3. Luật chạy lại có giới hạn: đếm các lần chạy trước trong cùng thư mục 'lan' có cùng 'chi' và cùng loại lỗi; vượt
     'chay_lai_toi_da' thì ghi KHÔNG CHẠY LẠI NỮA – dừng hỏi người dùng.
  4. --truoc <thư mục lần trước>: so ảnh từng tờ với lần trước (scripts\\so_anh.py), khoanh vùng khác.
  5. Gom câu hỏi gợi ý cho mục '## CẦN NGƯỜI DÙNG TRẢ LỜI'.

Cách dùng (Python có Pillow + numpy):
  python danh_gia.py <thư mục lần chạy> [--truoc <thư mục lần trước>] [--ra <thư mục ghi kết quả>]
Ghi <ra>\\danh_gia.md + danh_gia.json (mặc định ra = thư mục lần chạy; đã có thì thêm _2, không ghi đè).
Mã thoát: 0 = mọi bản vẽ ĐẠT; 1 = còn việc phải xem / hỏi; 2 = có LỖI CHẠY.
"""
import argparse
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soat_chung as sc  # noqa: E402

DAT, XEM, HOI, LOI = u"ĐẠT", u"CẦN XEM ẢNH", u"CẦN NGƯỜI DÙNG QUYẾT", u"LỖI CHẠY"
THU_TU = {DAT: 0, XEM: 1, HOI: 2, LOI: 3}
AI = {"nguoi_dung": u"người dùng", "agent": u"agent", "phien_chinh": u"phiên chính (sửa công cụ)"}


def dong_can_xem(m):
    """Các dòng CẦN XEM LẠI của mục, kèm các dòng thụt lề ngay sau tiêu đề 'CẦN XEM LẠI (n):' / 'CỬA CÓ EI …'."""
    ds, dang = [], None
    for ln in m.get("dong") or []:
        s = ln.rstrip()
        tho = s.strip()
        thut = ln[:1] in (u" ", u"\t") and dang is not None
        if thut and s.startswith(u"   "):
            ds[dang]["chi_tiet"].append(tho)
            continue
        dang = None
        if tho.startswith(u"CẦN XEM LẠI") or tho.startswith(u"CỬA CÓ EI") or tho.startswith(u"KHÔNG "):
            ds.append({"dong": tho, "chi_tiet": []})
            if tho.endswith(u":"):
                dang = len(ds) - 1
    kq = []
    for d in ds:
        if d["chi_tiet"] and re.match(u"^CẦN XEM LẠI( \\(\\d+\\))?:$", d["dong"]):
            kq += [{"dong": c, "chi_tiet": []} for c in d["chi_tiet"]]      # tiêu đề rỗng: tách từng dòng con
        else:
            kq.append(d)
    return kq


def van_de(dong, gy, nguon):
    loai = sc.phan_loai(dong)
    g = gy.get(loai) or gy["khac"]
    return {"loai": loai, "nguon": nguon, "dong": dong, "ten": g["ten"], "nguyen_nhan": g["nguyen_nhan"],
            "cach_sua": g["cach_sua"], "ai_quyet": g["ai_quyet"], "chay_lai_toi_da": g["chay_lai_toi_da"]}


def trang_thai_tu(vd):
    if not vd:
        return DAT
    if any(v["ai_quyet"] in ("nguoi_dung", "phien_chinh") for v in vd):
        return HOI
    return XEM


def chu_ky_lan(K):
    return tuple(sorted((K.get("viec") or {}).get("chi") or []))


def loi_muc(m):
    """Dòng lỗi cụ thể nhất trong các dòng báo của 1 mục lõi lỗi (dòng có tên lỗi .NET / Python)."""
    ds = [ln.strip().lstrip(u"| ").strip() for ln in m.get("dong") or []]
    for d in ds:
        if re.search(r"(Exception|Error)\b.*:", d) and u"Traceback" not in d:
            return d
    for d in ds:
        if d.startswith(u"LỖI") or u"Traceback" in d:
            return d
    return None


def loi_chay(K, thu_muc):
    """Lỗi cấp phiên: Traceback, phiên không kết thúc, mục lõi lỗi (kèm dòng lỗi cụ thể của mục)."""
    muc = {sc.khoa_muc(m).replace(u"|", u" – "): m for m in K.get("muc") or []}
    ds = []
    for x in K.get("loi") or []:
        dong = x.strip().splitlines()[-1] if u"Traceback" in x else x
        if dong in muc:
            chi_tiet = loi_muc(muc[dong])
            if chi_tiet:
                dong = u"%s: %s" % (dong, chi_tiet)
        ds.append(dong)
    if "ket_thuc" not in K:
        ds.append(u"Phiên dừng giữa chừng (ket_qua.json không có 'ket_thuc') – xem <lan>_chay_nen.log / journal.")
    return ds


def loai_phien(dong):
    l = sc.phan_loai(dong)
    if l == "khac" and u"dừng giữa chừng" in dong:
        return "phien_dung"
    if l == "khac" and re.match(u".* – \\w+(:|$)", dong):      # 'view – nút' = mục lõi báo LỖI
        return "loi_lop"
    return l


def dem_lan_truoc(thu_muc, chu_ky, loai):
    """Số lần chạy TỚI lần này (thư mục cùng cha, tên xếp ≤ tên lần này – thư mục đánh số NN_) có cùng 'chi' và cùng
    loại lỗi phiên."""
    cha, ten = os.path.split(os.path.abspath(thu_muc))
    n = 0
    for f in sorted(os.listdir(cha)):
        if f > ten:
            continue
        p = os.path.join(cha, f, "ket_qua.json")
        if not os.path.isfile(p):
            continue
        try:
            K = sc.doc_json(p)
        except Exception:
            continue
        if chu_ky_lan(K) != chu_ky:
            continue
        if loai in [loai_phien(d) for d in loi_chay(K, os.path.join(cha, f))]:
            n += 1
    return n


def muon_central(thu_muc):
    """Đọc dòng 'mượn phần tử từ central: N' trong <lan>_chay_nen.log (nếu có)."""
    cha, ten = os.path.split(os.path.abspath(thu_muc))
    so = ten.split("_")[0]
    for f in os.listdir(cha):
        if f.endswith("chay_nen.log") and (f.startswith(ten) or f.startswith(so + "_")):
            try:
                s = io.open(os.path.join(cha, f), encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            m = re.findall(r"central: (\d+)", s)
            if m:
                return int(m[-1])
    return None


def danh_gia(thu_muc, truoc=None, ra=None):
    gy = sc.goi_y()
    K, thu_muc = sc.doc_ket_qua(thu_muc)
    muc = {sc.khoa_muc(m).replace(u"|", u" – "): m for m in K.get("muc") or []}
    to = []
    for r in K.get("kiem_tra") or []:
        m = muc.get(r.get("muc")) or {}
        vd = [van_de(x, gy, u"kiểm tra") for x in r.get("loi") or []]
        for d in dong_can_xem(m):
            v = van_de(d["dong"], gy, u"lõi")
            if d["chi_tiet"]:
                v["chi_tiet"] = d["chi_tiet"][:20] + ([u"… (%d dòng)" % len(d["chi_tiet"])] if len(d["chi_tiet"]) > 20 else [])
            vd.append(v)
        # lõi báo trước + kiểm tra báo sau cùng 1 chuyện: giữ 1 (kiểm tra là số chắc)
        loai_kt = set(v["loai"] for v in vd if v["nguon"] == u"kiểm tra")
        trung = {"lon_hon_vung_ve": ("tran_vua", "tran_nho", "tran_rat_lon"), "cham_bang": ("de_bang",)}
        vd = [v for v in vd if not (v["nguon"] == u"lõi" and any(t in loai_kt for t in trung.get(v["loai"], ())))]
        to.append({"so": r.get("so"), "ten": r.get("ten"), "muc": r.get("muc"), "trang_thai": trang_thai_tu(vd),
                   "so_lieu": sc.so_lieu_muc(m) if m else {}, "van_de": vd, "luu_y": r.get("luu_y") or []})
    # mục không ra bản vẽ / mục lõi lỗi
    co_to = set(t["muc"] for t in to)
    for k, m in muc.items():
        if k not in co_to and (m.get("loi") or not m.get("sheet")):
            to.append({"so": None, "ten": None, "muc": k, "trang_thai": LOI, "so_lieu": sc.so_lieu_muc(m),
                       "van_de": [van_de(u"Mục %s không ra bản vẽ%s" % (k, u" (lõi báo LỖI)" if m.get("loi") else u""),
                                         gy, u"lõi")], "luu_y": []})
    hoi = [van_de(x, gy, u"câu hỏi của lõi / công cụ") for x in K.get("can_hoi") or []]
    phien = []
    for d in loi_chay(K, thu_muc):
        v = van_de(d, gy, u"phiên")
        v["loai"] = loai_phien(d)
        g = gy.get(v["loai"]) or gy["khac"]
        v.update({"ten": g["ten"], "nguyen_nhan": g["nguyen_nhan"], "cach_sua": g["cach_sua"],
                  "ai_quyet": g["ai_quyet"], "chay_lai_toi_da": g["chay_lai_toi_da"]})
        n = dem_lan_truoc(thu_muc, chu_ky_lan(K), v["loai"])
        v["so_lan_da_chay"] = n
        v["duoc_chay_lai"] = n < 1 + v["chay_lai_toi_da"]
        phien.append(v)
    so_anh = None
    if truoc:
        import so_anh as sa
        so_anh = sa.so_thu_muc(truoc, thu_muc, sc.file_moi(os.path.join(ra or thu_muc, "so_anh")))
        for t in to:
            for r in so_anh["to"]:
                if t["so"] and r["so_hieu"] == sc.so_anh_file(t["so"]):
                    t["so_anh"] = {"giong": r["giong"], "ty_le_khac_phan_tram": r["ty_le_khac_phan_tram"],
                                   "so_vung": r["so_vung"], "anh_so": r.get("anh_so")}
    tong = LOI if phien else max([t["trang_thai"] for t in to] or [DAT], key=lambda s: THU_TU[s])
    if hoi and THU_TU[tong] < THU_TU[HOI]:
        tong = HOI
    return {"lan": thu_muc, "chi": list(chu_ky_lan(K)), "file": K.get("file"), "da_luu": K.get("da_luu"),
            "muon_central": muon_central(thu_muc), "trang_thai": tong, "ban_ve": to, "can_hoi": hoi, "loi_phien": phien,
            "so_anh": so_anh}


def _vd_md(i, v):
    s = [u"%d. **[%s]** %s  \n   _%s_ – ai quyết: **%s**" % (i, v["loai"], v["dong"], v["ten"], AI.get(v["ai_quyet"], v["ai_quyet"]))]
    for c in v.get("chi_tiet") or []:
        s.append(u"   - %s" % c)
    s.append(u"   - Nguyên nhân thường gặp: " + u" / ".join(v["nguyen_nhan"]))
    s.append(u"   - Xử lý: " + u" / ".join(v["cach_sua"]))
    return u"\n".join(s)


def _nhom_md(ds):
    """Vấn đề cùng loại: liệt kê từng dòng, nguyên nhân / cách xử lý in 1 lần cho cả nhóm."""
    L, thu_tu = [], []
    for v in ds:
        if v["loai"] not in thu_tu:
            thu_tu.append(v["loai"])
    i = 0
    for loai in thu_tu:
        nh = [v for v in ds if v["loai"] == loai]
        v0 = nh[0]
        L.append(u"- **[%s] %s** – ai quyết: **%s**" % (loai, v0["ten"], AI.get(v0["ai_quyet"], v0["ai_quyet"])))
        for v in nh:
            i += 1
            L.append(u"  %d. %s" % (i, v["dong"]))
            for c in v.get("chi_tiet") or []:
                L.append(u"     - %s" % c)
        L.append(u"  - Nguyên nhân thường gặp: " + u" / ".join(v0["nguyen_nhan"]))
        L.append(u"  - Xử lý: " + u" / ".join(v0["cach_sua"]))
    return L


def ra_md(D):
    L = [u"# Đánh giá lần chạy `%s`" % os.path.basename(D["lan"]), u"",
         u"- Trạng thái chung: **%s**" % D["trang_thai"],
         u"- Mục chạy: %s" % (u", ".join(D["chi"]) or u"(tất cả trong phương án)"),
         u"- File mở: %s%s" % ((D["file"] or {}).get("mo"), u" (đã tách central)" if (D["file"] or {}).get("tach") else u""),
         u"- Đã lưu: %s" % (D["da_luu"] or u"KHÔNG"),
         u"- Dòng mượn phần tử từ central: %s%s" % (D["muon_central"] if D["muon_central"] is not None else u"(không thấy log)",
                                                  u"  ⚠ DỪNG, báo người dùng ngay" if D["muon_central"] else u""),
         u"", u"| Số hiệu | Mục | Trạng thái | Số liệu | So ảnh lần trước |", u"|---|---|---|---|---|"]
    for t in D["ban_ve"]:
        sl = u", ".join(u"%s %s" % (k, v) for k, v in t["so_lieu"].items() if v is not None)
        sa = t.get("so_anh")
        sa = (u"giống" if sa["giong"] else u"khác %.2f%% / %d vùng" % (sa["ty_le_khac_phan_tram"], sa["so_vung"])) if sa else u""
        L.append(u"| %s | %s | %s | %s | %s |" % (t["so"] or u"–", t["muc"], t["trang_thai"], sl, sa))
    for t in D["ban_ve"]:
        L += [u"", u"## %s – %s (%s)" % (t["so"] or u"(không có tờ)", t["muc"], t["trang_thai"])]
        if t.get("so_anh") and t["so_anh"].get("anh_so"):
            L.append(u"Ảnh so với lần trước: `%s`" % t["so_anh"]["anh_so"])
        if not t["van_de"]:
            L.append(u"Không có vấn đề nào. Vẫn phải xem ảnh 1 lần.")
        L += _nhom_md(t["van_de"])
        for x in t["luu_y"]:
            L.append(u"- Lưu ý: %s" % x)
    if D["loi_phien"]:
        L += [u"", u"## LỖI CHẠY"]
        for i, v in enumerate(D["loi_phien"], 1):
            L.append(_vd_md(i, v))
            L.append(u"   - Đã chạy %d lần với lỗi này → %s" % (
                v["so_lan_da_chay"], u"được chạy lại (từ bản .rvt TRƯỚC lần hỏng, thư mục kết quả mới)" if v["duoc_chay_lai"]
                else u"**KHÔNG CHẠY LẠI NỮA – dừng, báo người dùng**"))
    if D["can_hoi"]:
        L += [u"", u"## Câu hỏi / báo của lõi"]
        for i, v in enumerate(D["can_hoi"], 1):
            L.append(_vd_md(i, v))
    # 1 câu hỏi cho mỗi LOẠI vấn đề (gom mọi bản vẽ gặp loại đó)
    nhom = {}
    for t in D["ban_ve"]:
        for v in t["van_de"]:
            if v["ai_quyet"] == "nguoi_dung":
                g = nhom.setdefault(v["loai"], {"v": v, "to": []})
                if (t["so"] or t["muc"]) not in g["to"]:
                    g["to"].append(t["so"] or t["muc"])
    cau = [u"%s – %d bản vẽ: %s. Gợi ý: %s" % (g["v"]["ten"], len(g["to"]), u", ".join(g["to"]), g["v"]["cach_sua"][0])
           for g in nhom.values()]
    cau += [u"%s – Gợi ý: %s" % (v["dong"], v["cach_sua"][0]) for v in D["can_hoi"] if v["ai_quyet"] == "nguoi_dung"]
    cau += [u"%s – Gợi ý: %s" % (v["dong"], v["cach_sua"][0]) for v in D["loi_phien"] if not v["duoc_chay_lai"]]
    if cau:
        L += [u"", u"## Gợi ý câu hỏi cho mục CẦN NGƯỜI DÙNG TRẢ LỜI (agent gom, bỏ trùng trước khi hỏi)"]
        L += [u"%d. %s" % (i, c.replace(u" –  Gợi ý", u" – Gợi ý")) for i, c in enumerate(cau, 1)]
    return u"\n".join(L) + u"\n"


def main():
    sc.utf8_ra()
    ap = argparse.ArgumentParser(description=u"Đánh giá 1 lần chạy agent HS TKBVTC.")
    ap.add_argument("lan")
    ap.add_argument("--truoc")
    ap.add_argument("--ra")
    g = ap.parse_args()
    ra = g.ra or sc.doc_ket_qua(g.lan)[1]
    os.makedirs(ra, exist_ok=True)
    D = danh_gia(g.lan, g.truoc, ra)
    pj, pm = sc.file_moi(os.path.join(ra, "danh_gia.json")), sc.file_moi(os.path.join(ra, "danh_gia.md"))
    sc.ghi_json(pj, D)
    sc.ghi_chu(pm, ra_md(D))
    print(u"Trạng thái: %s" % D["trang_thai"])
    for t in D["ban_ve"]:
        print(u"  %-16s %-34s %s (%d vấn đề)" % (t["so"] or u"–", t["muc"], t["trang_thai"], len(t["van_de"])))
    for v in D["loi_phien"]:
        print(u"  LỖI CHẠY [%s] %s → %s" % (v["loai"], v["dong"][:120],
                                          u"chạy lại được" if v["duoc_chay_lai"] else u"KHÔNG chạy lại nữa"))
    print(u"Ghi:", pm)
    return 2 if D["loi_phien"] else (0 if D["trang_thai"] == DAT else 1)


if __name__ == "__main__":
    sys.exit(main())
