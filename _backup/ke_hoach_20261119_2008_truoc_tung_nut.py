# -*- coding: utf-8 -*-
"""Lập kế hoạch 2 cấp cho 1 việc HS TKBVTC (ý tưởng high-level / low-level planner của BIMgent), chạy NGOÀI Revit.

Cấp cao: thứ tự loại bản vẽ × tầng theo quy tắc 9 của agent (mỗi loại: làm thử 1 tầng → DỪNG duyệt → các tầng còn lại).
Mỗi bước gắn nhãn ai làm: [TỰ ĐỘNG] chạy nút trong phiên nền · [CLAUDE SOÁT] danh_gia.py + xem ảnh · [NGƯỜI DÙNG] duyệt / trả lời.
Cấp thấp: chia phiên (chi tiết cửa ≤ 7 cửa / mục, ≤ 2 mục / phiên – bài học G19 Side 16/11), và với --tao-viec thì sinh
sẵn phương án con + file việc + chuỗi phiên (.ps1, phiên hỏng thì chạy lại ĐÚNG 1 lần từ bản .rvt trước rồi mới dừng).
Xem trước khi làm (khi có --khao-sat): mặt bằng nguồn có không, template có / khoá tỉ lệ khác yêu cầu không, khung tên,
giai đoạn, hạng mục, tờ số hiệu đã có (trống / đã có nội dung), tầng có nhiều view đích → câu hỏi trước khi chạy.

  python ke_hoach.py <phuong_an.json> [--khao-sat <khao_sat.json>]
        → <thư mục việc>\\ke_hoach.md + ke_hoach.json (thư mục việc = thư mục chứa phương án; không ghi đè)
  python ke_hoach.py <phuong_an.json> --tao-viec <Nút> thu|con_lai --mo <.rvt bắt đầu>
        [--thu-tang <view>] [--nap-lai-link <file json {tên link: bản sao}>] [--them-viec '<json gộp vào mỗi file việc>']
        [--nhom-cua 7] [--muc-moi-phien 2]
        → phương án con, viec\\NN_*.json (+ NN_*_lan2.json), viec\\chuoi_NN_MM.ps1 + khoi_dong_chuoi_NN_MM.ps1
Đánh số NN tiếp theo số lớn nhất đang có trong viec\\, rvt\\, lan\\ (quy tắc 3). Không chạy gì, chỉ ghi file.
"""
import argparse
import io
import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import soat_chung as sc  # noqa: E402

THU_TU_NUT = ["NganChay", "TagCua", "LanCanLouver", "ChiTietCua", "ChongTham"]
TEN_NUT = {"NganChay": u"Ngăn cháy lan", "TagCua": u"Định vị + tag cửa", "LanCanLouver": u"Định vị lan can, louver",
           "ChiTietCua": u"Chi tiết cửa", "ChongTham": u"Chống thấm"}
# như arv_ho_so_duyet.view_dich: chữ khoá trong tên view hoặc tên template của mặt bằng cùng tầng; Định vị + tag cửa
# không hỏi chọn view (chay_hs không xét view_dich cho TagCua)
CHU_KHOA_VIEW = {"NganChay": u"chay lan", "LanCanLouver": u"dinh vi lan can", "ChongTham": u"chong tham"}
CHAY_NEN = os.path.join(sc.THU_MUC, "chay_nen.ps1")


def kd(s):
    s = unicodedata.normalize("NFD", s or u"")
    return u"".join(c for c in s if unicodedata.category(c) != "Mn").replace(u"đ", u"d").replace(u"Đ", u"D").lower()


def cho_trong(v):
    return isinstance(v, str) and (re.search(r"<[^>]+>", v) or u"[Chờ bổ sung]" in v)


def tim_cho_trong(o, duong=u""):
    ds = []
    if isinstance(o, dict):
        for k, v in o.items():
            if not str(k).startswith("_"):
                ds += tim_cho_trong(v, u"%s.%s" % (duong, k) if duong else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            ds += tim_cho_trong(v, u"%s[%d]" % (duong, i))
    elif cho_trong(o):
        ds.append((duong, o))
    return ds


def thu_tu_nut(P):
    co = []
    for mb in P.get("mat_bang") or []:
        for n in mb.get("viec") or {}:
            if n not in co:
                co.append(n)
    goi = [n for n in (P.get("nut") or {}) if n in co]
    return goi + [n for n in THU_TU_NUT if n in co and n not in goi] + [n for n in co if n not in goi and n not in THU_TU_NUT]


def muc_cua_nut(P, nut):
    return [(i, mb) for i, mb in enumerate(P.get("mat_bang") or []) if nut in (mb.get("viec") or {})]


# ------------------------------------------------------------------------------------------- xem trước khi làm
def xem_truoc(P, KS):
    hoi, bao = [], []
    if not KS:
        return hoi, [u"Chưa có khao_sat.json: chưa kiểm được tên view / template / khung tên / tờ (chạy che_do khao_sat trước)."]
    mb_ks = {m["ten"]: m for m in KS.get("mat_bang") or []}
    tpl = {t["ten"]: t for t in KS.get("template_mat_bang") or []}
    to = {s["so"]: s for s in KS.get("sheet") or []}
    ch = P.get("chung") or {}
    if ch.get("khung_ten") and not cho_trong(ch["khung_ten"]) and ch["khung_ten"] not in (KS.get("khung_ten") or []):
        hoi.append(u"Khung tên '%s' không có trong model (có: %s)." % (ch["khung_ten"], u"; ".join(KS.get("khung_ten") or [])))
    gd = KS.get("giai_doan") or {}
    if ch.get("giai_doan") and not cho_trong(ch["giai_doan"]) and ch["giai_doan"] not in gd:
        hoi.append(u"Giai đoạn '%s' chưa có trong model (có: %s) – xác nhận tạo mới?" % (ch["giai_doan"], u"; ".join(gd)))
    hm = KS.get("hang_muc") or {}
    for nut, cfg in (P.get("nut") or {}).items():
        t = cfg.get("template")
        if t and not cho_trong(t):
            if t not in tpl:
                hoi.append(u"%s: template '%s' không có trong model." % (TEN_NUT.get(nut, nut), t))
            elif tpl[t].get("khoa_ti_le") and ch.get("ti_le") and int(tpl[t].get("ti_le") or 0) != int(ch["ti_le"]):
                hoi.append(u"%s: template '%s' KHOÁ tỉ lệ 1:%s, khác tỉ lệ yêu cầu 1:%s (bẫy AF.07 của HQV) – chọn template "
                           u"khác hay theo tỉ lệ của template?" % (TEN_NUT.get(nut, nut), t, tpl[t].get("ti_le"), ch["ti_le"]))
        h = cfg.get("hang_muc")
        if h and not cho_trong(h) and h not in hm:
            bao.append(u"%s: hạng mục '%s' chưa có trong model → hộp thoại sẽ tạo mới (xác nhận khi báo kế hoạch)." % (
                TEN_NUT.get(nut, nut), h))
    for mb in P.get("mat_bang") or []:
        v = mb.get("view")
        k = mb_ks.get(v)
        if not k:
            hoi.append(u"Mặt bằng nguồn '%s' không có trong model → các mục của tầng này KHÔNG chạy được." % v)
            continue
        for nut, vc in (mb.get("viec") or {}).items():
            so = vc.get("so")
            if so and not cho_trong(so) and so in to and nut != "ChiTietCua":
                s = to[so]
                if s.get("so_view"):
                    hoi.append(u"%s – %s: tờ %s '%s' ĐÃ có %d view → làm lại trên tờ này, đổi số hiệu, hay bỏ qua?" % (
                        v, TEN_NUT.get(nut, nut), so, s.get("ten"), s["so_view"]))
                else:
                    bao.append(u"%s – %s: tờ trống có sẵn %s '%s' → lõi đặt vào tờ này, giữ tên / khung tên." % (
                        v, TEN_NUT.get(nut, nut), so, s.get("ten")))
            ck = CHU_KHOA_VIEW.get(nut)
            if ck and not vc.get("view_dich"):
                cung = [m["ten"] for m in KS.get("mat_bang") or [] if m.get("tang") == k.get("tang")
                        and (ck in kd(m["ten"]) or ck in kd(m.get("template") or u""))]
                if len(cung) >= 2:
                    hoi.append(u"%s – %s: tầng '%s' có %d view đích (%s) → chọn 1 (khoá view_dich), không thì mục không chạy." % (
                        v, TEN_NUT.get(nut, nut), k.get("tang"), len(cung), u"; ".join(cung[:6])))
    return hoi, bao


# ------------------------------------------------------------------------------------------- chia phiên
def chia_phien(P, nut, idx, nhom_cua, muc_moi_phien):
    """[[(chỉ số mat_bang gốc, mb con), …] mỗi phiên]. Chi tiết cửa: tách mark thành nhóm, mỗi nhóm 1 mục."""
    muc = []
    for i in idx:
        mb = P["mat_bang"][i]
        if nut == "ChiTietCua":
            mk = list(mb["viec"]["ChiTietCua"].get("mark") or [])
            for j in range(0, max(1, len(mk)), nhom_cua):
                c = json.loads(json.dumps(mb))
                c["viec"] = {"ChiTietCua": dict(mb["viec"]["ChiTietCua"], mark=mk[j:j + nhom_cua])}
                muc.append((i, c))
        else:
            c = json.loads(json.dumps(mb))
            c["viec"] = {nut: mb["viec"][nut]}
            muc.append((i, c))
    n = muc_moi_phien if muc_moi_phien > 0 else len(muc)
    return [muc[k:k + n] for k in range(0, len(muc), n)]


def lap(P, KS, nhom_cua=7, muc_moi_phien_cua=2, thu_tang=None):
    hoi, bao = xem_truoc(P, KS)
    hoi = [u"Phương án còn chỗ trống %s = %s" % (d, v) for d, v in tim_cho_trong(P)] + hoi
    buoc = []
    for nut in thu_tu_nut(P):
        ds = muc_cua_nut(P, nut)
        if not ds:
            continue
        i_thu = next((i for i, mb in ds if thu_tang and mb.get("view") == thu_tang), ds[0][0])
        con = [i for i, _ in ds if i != i_thu]
        mpp = muc_moi_phien_cua if nut == "ChiTietCua" else 0
        ph_thu = chia_phien(P, nut, [i_thu], nhom_cua, mpp)
        ph_con = chia_phien(P, nut, con, nhom_cua, mpp) if con else []
        buoc.append({"nut": nut, "ten": TEN_NUT.get(nut, nut), "thu": P["mat_bang"][i_thu]["view"],
                     "con_lai": [P["mat_bang"][i]["view"] for i in con], "phien_thu": len(ph_thu), "phien_con_lai": len(ph_con),
                     "muc_thu": sum(len(p) for p in ph_thu), "muc_con_lai": sum(len(p) for p in ph_con)})
    return {"hoi_truoc": hoi, "bao": bao, "buoc": buoc}


def md(KH, P):
    L = [u"# Kế hoạch – %s" % (P.get("ten") or u""), u"",
         u"Nhãn: **[TỰ ĐỘNG]** chạy nút trong phiên nền · **[CLAUDE SOÁT]** `danh_gia.py` + xem ảnh từng tờ · "
         u"**[NGƯỜI DÙNG]** duyệt / trả lời. Kế hoạch này gửi người dùng cùng lần báo đầu (cùng xác nhận template).", u""]
    if KH["hoi_truoc"]:
        L.append(u"## Cần hỏi TRƯỚC khi chạy")
        L += [u"%d. %s" % (i, h) for i, h in enumerate(KH["hoi_truoc"], 1)]
        L.append(u"")
    if KH["bao"]:
        L.append(u"## Ghi nhận khi xem trước model")
        L += [u"- %s" % b for b in KH["bao"]]
        L.append(u"")
    L.append(u"## Các bước")
    k = 0
    for b in KH["buoc"]:
        k += 1
        L.append(u"### %d. %s" % (k, b["ten"]))
        L.append(u"- %d.1 **[TỰ ĐỘNG]** Làm thử tầng **%s** – %d mục / %d phiên." % (k, b["thu"], b["muc_thu"], b["phien_thu"]))
        L.append(u"- %d.2 **[CLAUDE SOÁT]** `danh_gia.py` lần chạy thử; xem ảnh từng tờ; lỗi phiên thì chạy lại theo luật "
                 u"trong danh_gia (tối đa theo `goi_y_sua.json`)." % k)
        L.append(u"- %d.3 **[NGƯỜI DÙNG]** Duyệt tầng thử. Duyệt xong: `so_chuan.py tao` từ lần thử (ghi câu duyệt)." % k)
        if b["con_lai"]:
            L.append(u"- %d.4 **[TỰ ĐỘNG]** Các tầng còn lại: %s – %d mục / %d phiên%s." % (
                k, u", ".join(b["con_lai"]), b["muc_con_lai"], b["phien_con_lai"],
                u" (chuỗi phiên, mỗi phiên lưu file mới)" if b["phien_con_lai"] > 1 else u""))
            L.append(u"- %d.5 **[CLAUDE SOÁT]** `danh_gia.py` từng phiên; chạy lại tầng thử (nếu có) thì `so_chuan.py so` "
                     u"với chuẩn của bước %d.3." % (k, k))
            L.append(u"- %d.6 **[NGƯỜI DÙNG]** Duyệt các tầng còn lại." % k)
    k += 1
    L.append(u"### %d. Bàn giao" % k)
    L.append(u"- **[TỰ ĐỘNG]** chế độ `kiem_tra` trên file cuối (ảnh + kiểm tra MỌI tờ) → **[CLAUDE SOÁT]** `danh_gia.py` → "
             u"bàn giao theo bước 6 của agent.")
    return u"\n".join(L) + u"\n"


# ------------------------------------------------------------------------------------------- sinh file việc + chuỗi
def so_tiep(job):
    mx = 0
    for d in ("viec", "rvt", "lan"):
        p = os.path.join(job, d)
        if os.path.isdir(p):
            for f in os.listdir(p):
                m = re.match(r"(\d{2})_", f)
                if m:
                    mx = max(mx, int(m.group(1)))
    return mx + 1


def ten_an_toan(s):
    s = kd(s).upper()
    return re.sub(r"[^A-Z0-9]+", "_", s).strip("_")[:24] or "TANG"


def tao_viec(P, p_phuong_an, nut, giai_doan, mo, thu_tang, nap_lai_link, them, nhom_cua, muc_moi_phien_cua):
    job = os.path.dirname(os.path.abspath(p_phuong_an))
    for d in ("viec", "rvt", "lan", "log"):
        os.makedirs(os.path.join(job, d), exist_ok=True)
    ds = muc_cua_nut(P, nut)
    if not ds:
        raise ValueError(u"Phương án không có mục %s" % nut)
    i_thu = next((i for i, mb in ds if thu_tang and mb.get("view") == thu_tang), ds[0][0])
    idx = [i_thu] if giai_doan == "thu" else [i for i, _ in ds if i != i_thu]
    if not idx:
        raise ValueError(u"Không còn tầng nào cho giai đoạn %s" % giai_doan)
    phien = chia_phien(P, nut, idx, nhom_cua, muc_moi_phien_cua if nut == "ChiTietCua" else 0)
    nn = so_tiep(job)
    j = lambda *a: os.path.join(job, *a).replace("\\", "/")
    ds_viec, truoc = [], mo.replace("\\", "/")
    for k, ph in enumerate(phien):
        so = u"%02d" % (nn + k)
        nhan = u"%s_%s_%s" % (so, nut, giai_doan if len(phien) == 1 else u"%s%d" % (giai_doan, k + 1))
        if len(set(i for i, _ in ph)) == 1:
            nhan += u"_" + ten_an_toan(P["mat_bang"][ph[0][0]]["view"])
        q = dict(P)
        q["mat_bang"] = [c for _, c in ph]
        p_pa = j(u"phuong_an_%s.json" % nhan)
        sc.ghi_json(sc.file_moi(p_pa), q)
        chi = []
        for _, c in ph:
            x = u"%s|%s" % (c["view"], nut)
            if x not in chi:
                chi.append(x)
        luu = j("rvt", u"%s.rvt" % nhan)
        v = {"che_do": "chay", "mo": truoc, "phuong_an": p_pa, "chi": chi, "luu": luu, "ket_qua": j("lan", nhan),
             "log": j("log"), "anh": True, "tra_loi_xoa": "khong"}
        if nap_lai_link:
            v["nap_lai_link"] = nap_lai_link
        v.update(them or {})
        pv = j("viec", u"%s.json" % nhan)
        sc.ghi_json(sc.file_moi(pv), v)
        v2 = dict(v, ket_qua=v["ket_qua"] + u"_lan2")
        pv2 = j("viec", u"%s_lan2.json" % nhan)
        sc.ghi_json(sc.file_moi(pv2), v2)
        ds_viec.append((pv, pv2, luu, len(ph)))
        truoc = luu
    w = lambda s: s.replace("/", "\\")
    ten_c = u"chuoi_%02d_%02d" % (nn, nn + len(phien) - 1)
    pc = j("viec", ten_c + u".ps1")
    L = [u"# Chuỗi %d phiên %s (%s) sinh bằng ke_hoach.py. Mỗi phiên mở file phiên trước lưu ra; phiên không ra file thì "
         u"chạy lại ĐÚNG 1 lần (cùng file mở, kết quả _lan2), vẫn không ra thì DỪNG chuỗi." % (len(phien), nut, giai_doan),
         u"$cn = '%s'" % CHAY_NEN.replace("'", "''"),
         u"$tham = @{ ChoToiDa = 9000; KhongTienTrien = 120; JournalDung = 30 }   # bảng có tên (mảng thì PS 5.1 hiểu sai)"]
    for pv, pv2, luu, n in ds_viec:
        ten = os.path.basename(pv)
        L += [u"\"===== %s (%d mục) bắt đầu $(Get-Date -Format HH:mm:ss)\"" % (ten, n),
              u"& $cn -Viec '%s' @tham" % w(pv),
              u"if (-not (Test-Path -LiteralPath '%s')) {" % w(luu),
              u"    \"===== %s không ra file – chạy lại 1 lần $(Get-Date -Format HH:mm:ss)\"" % ten,
              u"    & $cn -Viec '%s' @tham" % w(pv2),
              u"    if (-not (Test-Path -LiteralPath '%s')) { \"===== DỪNG CHUỖI: %s hỏng 2 lần\"; exit 1 }" % (w(luu), ten),
              u"}"]
    L.append(u"\"===== CHUỖI XONG $(Get-Date -Format HH:mm:ss)\"")
    pc = sc.file_moi(pc)
    with io.open(pc, "w", encoding="utf-8-sig") as f:
        f.write(u"\n".join(L) + u"\n")
    pk = sc.file_moi(j("viec", u"khoi_dong_" + ten_c + u".ps1"))
    with io.open(pk, "w", encoding="utf-8-sig") as f:
        f.write(u"# Chạy chuỗi trong tiến trình riêng (sống qua lúc phiên Claude kết thúc), ghi log vào lan\\.\n"
                u"& '%s' *> '%s'\n" % (w(pc), w(j("lan", ten_c + u".log"))))
    return {"phien": [{"viec": a, "viec_lan2": b, "luu": c, "so_muc": n} for a, b, c, n in ds_viec], "chuoi": pc,
            "khoi_dong": pk}


def main():
    sc.utf8_ra()
    ap = argparse.ArgumentParser(description=u"Kế hoạch 2 cấp + sinh file việc / chuỗi phiên cho agent HS TKBVTC.")
    ap.add_argument("phuong_an")
    ap.add_argument("--khao-sat")
    ap.add_argument("--thu-tang")
    ap.add_argument("--nhom-cua", type=int, default=7)
    ap.add_argument("--muc-moi-phien", type=int, default=2, help=u"chi tiết cửa: số mục / phiên")
    ap.add_argument("--tao-viec", nargs=2, metavar=("NUT", "thu|con_lai"))
    ap.add_argument("--mo")
    ap.add_argument("--nap-lai-link")
    ap.add_argument("--them-viec")
    g = ap.parse_args()
    P = sc.doc_json(g.phuong_an)
    KS = sc.doc_json(g.khao_sat) if g.khao_sat else None
    job = os.path.dirname(os.path.abspath(g.phuong_an))
    if os.path.normcase(job).startswith(os.path.normcase(sc.SKILL)):
        ap.error(u"Phương án nằm trong thư mục skill – chép sang thư mục việc (<gốc>\\_tmp\\hs_agent\\NN_<mã>\\) rồi chạy, "
                 u"kế hoạch / file việc được ghi cạnh phương án.")
    if g.tao_viec:
        if not g.mo:
            ap.error(u"--tao-viec cần --mo <.rvt bắt đầu>")
        if g.tao_viec[1] not in ("thu", "con_lai"):
            ap.error(u"giai đoạn là thu hoặc con_lai")
        nl = sc.doc_json(g.nap_lai_link) if g.nap_lai_link else None
        kq = tao_viec(P, g.phuong_an, g.tao_viec[0], g.tao_viec[1], g.mo, g.thu_tang, nl,
                      json.loads(g.them_viec) if g.them_viec else None, g.nhom_cua, g.muc_moi_phien)
        for p in kq["phien"]:
            print(u"  %s (%d mục) → %s" % (os.path.basename(p["viec"]), p["so_muc"], os.path.basename(p["luu"])))
        print(u"Chuỗi:", kq["chuoi"])
        print(u"Khởi động (tiến trình riêng):", kq["khoi_dong"])
        return 0
    KH = lap(P, KS, g.nhom_cua, g.muc_moi_phien, g.thu_tang)
    pj, pm = sc.file_moi(os.path.join(job, "ke_hoach.json")), sc.file_moi(os.path.join(job, "ke_hoach.md"))
    sc.ghi_json(pj, KH)
    sc.ghi_chu(pm, md(KH, P))
    print(u"%d câu hỏi trước khi chạy, %d bước" % (len(KH["hoi_truoc"]), len(KH["buoc"])))
    for h in KH["hoi_truoc"]:
        print(u"  ?", h)
    for b in KH["buoc"]:
        print(u"  %s: thử %s (%d phiên) → còn lại %d tầng (%d phiên)" % (b["ten"], b["thu"], b["phien_thu"],
                                                                     len(b["con_lai"]), b["phien_con_lai"]))
    print(u"Ghi:", pm)
    return 1 if KH["hoi_truoc"] else 0


if __name__ == "__main__":
    sys.exit(main())
