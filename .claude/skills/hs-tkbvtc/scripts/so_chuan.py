# -*- coding: utf-8 -*-
"""Bộ thử hồi quy cho agent HS TKBVTC (ý tưởng benchmark + chấm điểm tự động của BIMgent), chạy NGOÀI Revit.

Chuẩn = số liệu + kết quả kiểm tra + ảnh của các lần chạy NGƯỜI DÙNG ĐÃ DUYỆT. Sau này (sửa công cụ, đổi phương án, chạy
lại trên bản sao mới) so lần chạy mới với chuẩn → biết ngay mục nào lệch, bản vẽ nào trước ĐẠT nay hỏng, tờ nào ảnh khác.

  python so_chuan.py tao <lan 1> [<lan 2> …] --ra <chuan.json MỚI> --duyet "<ai duyệt, khi nào, câu duyệt nguyên văn>"
  python so_chuan.py so  <lan 1> [<lan 2> …] --chuan <chuan.json> [--anh] [--ra <thư mục kết quả MỚI>]

Mỗi 'lan' = thư mục kết quả 1 phiên (có ket_qua.json + ảnh). Nhiều phiên (chuỗi chi tiết cửa) gộp chung theo khoá mục
'<view>|<nút>|<Mark đầu tiên nếu là chi tiết cửa>'.
So: số nguyên phải bằng; diện tích lệch ≤ 0,05 m²; bản vẽ ĐẠT → KHÔNG ĐẠT là HỒI QUY; loại lỗi kiểm tra mới / mất được
liệt kê; --anh: so ảnh từng tờ với ảnh chuẩn (scripts\\so_anh.py), khác thì chỉ ghi 'CẦN XEM', không tính hồi quy.
Mã thoát: 0 = khớp chuẩn; 1 = có lệch; 2 = có hồi quy.
Không ghi đè: file / thư mục kết quả đã có thì thêm _2, _3.
"""
import argparse
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soat_chung as sc  # noqa: E402

DUNG_SAI = {"dien_tich_m2": 0.05}


def khoa(m):
    k = sc.khoa_muc(m)
    if m.get("nut") == "ChiTietCua":
        mk = [x for x in re.findall(r"(?:Type Mark|Mark) '([^']+)'", u"\n".join(m.get("dong") or []))]
        if mk:
            k += u"|" + mk[0]
    return k


def gom(lans):
    """{khoá mục: {...}} từ nhiều lần chạy; lần sau đè lần trước nếu trùng khoá."""
    kq = {}
    for lan in lans:
        K, td = sc.doc_ket_qua(lan)
        anh = sc.anh_cua_lan(td)
        kt = {}
        for r in K.get("kiem_tra") or []:
            kt.setdefault(r.get("muc"), []).append(r)
        for m in K.get("muc") or []:
            to = []
            for r in kt.get(sc.khoa_muc(m).replace(u"|", u" – "), []):
                if r.get("so") and r["so"] not in (m.get("sheet") or []):
                    continue
                to.append({"so": r.get("so"), "dat": bool(r.get("dat")),
                           "loai_loi": sorted(sc.phan_loai(x) for x in r.get("loi") or []),
                           "anh": anh.get(sc.so_anh_file(r.get("so")))})
            co = set(t["so"] for t in to)
            for s in m.get("sheet") or []:        # tờ có trên mục nhưng lần chạy không kiểm tra (công cụ bản cũ)
                if s not in co:
                    to.append({"so": s, "dat": None, "loai_loi": [], "anh": anh.get(sc.so_anh_file(s))})
            kq[khoa(m)] = {"lan": td, "so_lieu": sc.so_lieu_muc(m), "sheet": m.get("sheet") or [], "loi_lop": bool(m.get("loi")),
                           "to": to}
    return kq


def tao(lans, ra, duyet):
    d = {"tao_luc": datetime.datetime.now().isoformat(timespec="seconds"), "duyet": duyet,
         "lan": [os.path.abspath(x) for x in lans], "muc": gom(lans)}
    ra = sc.file_moi(ra)
    sc.ghi_json(ra, d)
    return ra, d


def _bang(a, b, k):
    if a is None or b is None:
        return a == b
    if k in DUNG_SAI:
        return abs(float(a) - float(b)) <= DUNG_SAI[k]
    return a == b


def so(lans, chuan_p, anh=False, ra=None):
    C = sc.doc_json(chuan_p)
    M = gom(lans)
    kq = {"chuan": os.path.abspath(chuan_p), "duyet": C.get("duyet"), "lan": [os.path.abspath(x) for x in lans],
          "muc": [], "thieu": [], "moi": sorted(set(M) - set(C["muc"])), "hoi_quy": 0, "lech": 0, "can_xem_anh": 0}
    if anh:
        import so_anh as sa
        thu_anh = sc.file_moi(os.path.join(ra, "anh_so_chuan"))
        os.makedirs(thu_anh, exist_ok=True)
    for k, c in sorted(C["muc"].items()):
        if k not in M:
            kq["thieu"].append(k)
            continue
        n = M[k]
        r = {"muc": k, "so_lieu": [], "to": []}
        for t in sorted(set(c["so_lieu"]) | set(n["so_lieu"])):
            a, b = c["so_lieu"].get(t), n["so_lieu"].get(t)
            if not _bang(a, b, t):
                r["so_lieu"].append({"ten": t, "chuan": a, "moi": b})
        if n["loi_lop"] and not c["loi_lop"]:
            r["hoi_quy_loi_lop"] = True
        tn = {x["so"]: x for x in n["to"]}
        for tc in c["to"]:
            x = tn.get(tc["so"])
            if not x:
                r["to"].append({"so": tc["so"], "van_de": u"không còn bản vẽ này", "hoi_quy": True})
                continue
            v = {"so": tc["so"]}
            if x["dat"] is None or tc["dat"] is None:
                if x["dat"] != tc["dat"]:
                    v["van_de"] = u"một trong hai lần không có kết quả kiểm tra tờ này (không so được ĐẠT / KHÔNG ĐẠT)"
            elif tc["dat"] and not x["dat"]:
                v["hoi_quy"] = True
                v["van_de"] = u"chuẩn ĐẠT, nay KHÔNG ĐẠT"
            elif not tc["dat"] and x["dat"]:
                v["van_de"] = u"chuẩn KHÔNG ĐẠT, nay ĐẠT (tốt hơn)"
            them = sorted(set(x["loai_loi"]) - set(tc["loai_loi"]))
            mat = sorted(set(tc["loai_loi"]) - set(x["loai_loi"]))
            if them:
                v["loi_moi"] = them
            if mat:
                v["loi_het"] = mat
            if anh and tc.get("anh") and x.get("anh") and os.path.isfile(tc["anh"]):
                s = sa.so_sanh(tc["anh"], x["anh"], os.path.join(thu_anh, u"%s_so.png" % sc.so_anh_file(tc["so"])))
                v["anh"] = {"giong": s["giong"], "ty_le_khac_phan_tram": s["ty_le_khac_phan_tram"], "so_vung": s["so_vung"],
                            "anh_so": s.get("anh_so")}
                if not s["giong"]:
                    kq["can_xem_anh"] += 1
            if len(v) > 1:
                r["to"].append(v)
        hq = r.get("hoi_quy_loi_lop") or any(t.get("hoi_quy") for t in r["to"])
        le = bool(r["so_lieu"]) or any(("loi_moi" in t or "loi_het" in t or "van_de" in t) for t in r["to"])
        r["ket_luan"] = u"HỒI QUY" if hq else (u"LỆCH" if le else u"KHỚP")
        kq["hoi_quy"] += 1 if hq else 0
        kq["lech"] += 1 if (le and not hq) else 0
        kq["muc"].append(r)
    kq["hoi_quy"] += len(kq["thieu"])
    return kq


def md(kq):
    L = [u"# So với chuẩn `%s`" % os.path.basename(kq["chuan"]), u"",
         u"- Chuẩn đã duyệt: %s" % (kq.get("duyet") or u"(không ghi)"),
         u"- Lần chạy so: %s" % u", ".join(os.path.basename(x) for x in kq["lan"]),
         u"- Kết luận: **%d hồi quy, %d lệch, %d tờ ảnh khác (cần xem)**" % (kq["hoi_quy"], kq["lech"], kq["can_xem_anh"]), u""]
    for r in kq["muc"]:
        L.append(u"## %s – %s" % (r["muc"], r["ket_luan"]))
        for s in r["so_lieu"]:
            L.append(u"- Số liệu `%s`: chuẩn %s → nay %s" % (s["ten"], s["chuan"], s["moi"]))
        if r.get("hoi_quy_loi_lop"):
            L.append(u"- Lõi báo LỖI (chuẩn không lỗi)")
        for t in r["to"]:
            s = [u"- Tờ %s:" % t["so"]]
            if t.get("van_de"):
                s.append(t["van_de"])
            if t.get("loi_moi"):
                s.append(u"lỗi mới %s" % u", ".join(t["loi_moi"]))
            if t.get("loi_het"):
                s.append(u"hết lỗi %s" % u", ".join(t["loi_het"]))
            if t.get("anh"):
                a = t["anh"]
                s.append(u"ảnh giống chuẩn" if a["giong"] else u"ảnh khác %.2f%%, %d vùng → `%s`" % (
                    a["ty_le_khac_phan_tram"], a["so_vung"], a.get("anh_so")))
            L.append(u" ".join(s))
    if kq["thieu"]:
        L += [u"", u"## Mục có trong chuẩn nhưng lần này KHÔNG chạy / không ra (tính là hồi quy)"]
        L += [u"- %s" % k for k in kq["thieu"]]
    if kq["moi"]:
        L += [u"", u"## Mục mới (không có trong chuẩn)"]
        L += [u"- %s" % k for k in kq["moi"]]
    return u"\n".join(L) + u"\n"


def main():
    sc.utf8_ra()
    ap = argparse.ArgumentParser(description=u"Tạo chuẩn từ lần chạy đã duyệt / so lần chạy mới với chuẩn.")
    ap.add_argument("viec", choices=["tao", "so"])
    ap.add_argument("lan", nargs="+")
    ap.add_argument("--ra")
    ap.add_argument("--chuan")
    ap.add_argument("--duyet", default=u"")
    ap.add_argument("--anh", action="store_true")
    g = ap.parse_args()
    if g.viec == "tao":
        if not g.ra:
            ap.error(u"tao cần --ra <chuan.json>")
        if not g.duyet:
            print(u"⚠ Chưa ghi --duyet: chuẩn chỉ nên tạo từ lần chạy người dùng ĐÃ duyệt (ghi ai / khi nào / câu duyệt).")
        p, d = tao(g.lan, g.ra, g.duyet)
        print(u"Đã tạo chuẩn %s: %d mục" % (p, len(d["muc"])))
        for k, v in sorted(d["muc"].items()):
            print(u"  %s  %s  %s" % (k, u", ".join(v["sheet"]), u", ".join(u"%s=%s" % x for x in v["so_lieu"].items())))
        return 0
    if not g.chuan:
        ap.error(u"so cần --chuan <chuan.json>")
    ra = g.ra or os.path.dirname(os.path.abspath(g.chuan))
    os.makedirs(ra, exist_ok=True)
    kq = so(g.lan, g.chuan, g.anh, ra)
    pj, pm = sc.file_moi(os.path.join(ra, "so_chuan.json")), sc.file_moi(os.path.join(ra, "so_chuan.md"))
    sc.ghi_json(pj, kq)
    sc.ghi_chu(pm, md(kq))
    print(u"%d hồi quy, %d lệch, %d tờ ảnh khác" % (kq["hoi_quy"], kq["lech"], kq["can_xem_anh"]))
    for r in kq["muc"]:
        if r["ket_luan"] != u"KHỚP":
            print(u"  %s: %s" % (r["ket_luan"], r["muc"]))
    for k in kq["thieu"]:
        print(u"  THIẾU: %s" % k)
    print(u"Ghi:", pm)
    return 2 if kq["hoi_quy"] else (1 if kq["lech"] or kq["can_xem_anh"] else 0)


if __name__ == "__main__":
    sys.exit(main())
