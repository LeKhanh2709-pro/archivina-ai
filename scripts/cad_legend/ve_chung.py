#! python3
# -*- coding: utf-8 -*-
"""Vẽ bản vẽ nhiều tờ (ct_chung.json, có danh sách "to") vào Revit: MỖI TỜ 1 LEGEND đúng tỉ lệ của tờ, mỗi ô 1 group.
Gọi ve_legend.py lần lượt cho từng tờ trong cùng 1 phiên. Cấu hình ở ve_cfg.txt cạnh file này:
  TO=A,B      chỉ vẽ các tờ này (trống = mọi tờ)
  KQ=ve1      thư mục kết quả trong kq\\ (log từng tờ + ảnh legend)
  LUU=1       lưu file sau khi vẽ xong mọi tờ (chỉ dùng cho bản sao)
  CO_CHU=...  bảng cỡ chữ (xem ve_legend.py), BO_DUOI=... ngưỡng bỏ chữ quá nhỏ, PX=... bề rộng ảnh xuất
Báo cáo: kq\\<KQ>\\tong.txt (dòng "=== " mỗi tờ, cuối cùng "XONG")."""
import locale
locale.setlocale(locale.LC_ALL, "C")
import os, io, json, time, traceback

G = os.path.dirname(os.path.abspath(__file__))
cfg = {}
for dong in io.open(os.path.join(G, "ve_cfg.txt"), encoding="utf-8").read().splitlines():
    if "=" in dong and not dong.strip().startswith("#"):
        k, v = dong.split("=", 1)
        cfg[k.strip()] = v.strip()
KQ = os.path.join(G, "kq", cfg.get("KQ") or "ve")
if not os.path.isdir(KQ):
    os.makedirs(KQ)
bc = io.open(os.path.join(KQ, "tong.txt"), "w", encoding="utf-8")


def w(s):
    bc.write(u"{}\n".format(s)); bc.flush()


try:
    JS = os.path.join(G, cfg.get("JSON") or "ct_chung.json")
    d = json.load(io.open(JS, encoding="utf-8"))
    chon = [s for s in cfg.get("TO", "").replace(" ", "").split(",") if s]
    p = os.path.join(G, "ve_legend.py")
    ma = compile(io.open(p, encoding="utf-8").read(), p, "exec")
    w(u"--- {} | json {} | tờ: {}".format(__revit__.ActiveUIDocument.Document.PathName, JS, chon or u"tất cả"))
    # KHAC=<json>|<tên legend>|<thư mục ảnh>: vẽ thêm 1 legend từ json KHÔNG chia tờ (vd. chi tiết cửa, 1 tỉ lệ), với
    # bảng cỡ chữ mặc định của ve_legend.py
    if cfg.get("KHAC"):
        js2, ten2, tm2 = (cfg["KHAC"].split("|") + ["", ""])[:3]
        t0 = time.time()
        log = os.path.join(KQ, "log_%s.txt" % (tm2 or "khac"))
        os.environ["ARV_CTC_JSON"] = os.path.join(G, js2)
        os.environ["ARV_CTC_LOG"] = log
        os.environ["ARV_CTC_ANH"] = os.path.join(KQ, tm2 or "khac")
        os.environ["ARV_CTC_CHI"] = ""
        os.environ["ARV_CTC_TEN"] = ten2
        os.environ["ARV_CTC_LUU"] = "0"
        os.environ["ARV_CTC_PX"] = cfg.get("PX") or "12000"
        for k_env in ("ARV_CTC_KHONG_GROUP", "ARV_CTC_CO_CHU", "ARV_CTC_BO_DUOI", "ARV_CTC_RONG_CHU", "ARV_CTC_GHI_TUNG"):
            os.environ.pop(k_env, None)
        try:
            exec(ma, {"__revit__": __revit__, "__file__": p, "__name__": "__main__", "_nhip": w})
            kq = io.open(log, encoding="utf-8").read().splitlines()
            giu = [x for x in kq if x.startswith((u"Tổng tạo", u"Lỗi:", u"LỖI", u"  lỗi", u"Biên dự phòng", u"Kiểu filled region", u"Legend mới", u"Số ô"))
                   or u"KHÔNG tạo được group" in x]
            w(u"=== Legend '{}' từ {} | {:.0f} s".format(ten2, js2, time.time() - t0))
            for x in giu:
                w(u"    " + x[:400])
        except Exception:
            w(u"=== Legend '{}' | HỎNG {}".format(ten2, traceback.format_exc()[-400:]))
    for t in d["to"]:
        if chon and t["ma"] not in chon:
            continue
        t0 = time.time()
        ten_o = [o["ten"] for o in d["o"] if o["to"] == t["ma"]]
        if cfg.get("CHI"):          # chỉ vẽ các ô này (tên cách nhau |) - dùng khi dò lỗi
            ten_o = [x for x in ten_o if x in cfg["CHI"].split("|")]
            if not ten_o:
                continue
        if cfg.get("GHI_TUNG") == "1":
            os.environ["ARV_CTC_GHI_TUNG"] = "1"
        else:
            os.environ.pop("ARV_CTC_GHI_TUNG", None)
        log = os.path.join(KQ, "log_%s.txt" % t["ma"])
        os.environ["ARV_CTC_JSON"] = JS
        os.environ["ARV_CTC_LOG"] = log
        os.environ["ARV_CTC_ANH"] = os.path.join(KQ, t["ma"])
        os.environ["ARV_CTC_CHI"] = u"|".join(ten_o)
        os.environ["ARV_CTC_TEN"] = t["ten"]
        os.environ["ARV_CTC_LUU"] = "0"
        os.environ["ARV_CTC_PX"] = cfg.get("PX") or "12000"
        os.environ.pop("ARV_CTC_KHONG_GROUP", None)
        for k_env, k_cfg in (("ARV_CTC_CO_CHU", "CO_CHU"), ("ARV_CTC_BO_DUOI", "BO_DUOI"), ("ARV_CTC_RONG_CHU", "RONG_CHU")):
            if cfg.get(k_cfg):
                os.environ[k_env] = cfg[k_cfg]
            else:
                os.environ.pop(k_env, None)
        try:
            exec(ma, {"__revit__": __revit__, "__file__": p, "__name__": "__main__", "_nhip": w})
            kq = io.open(log, encoding="utf-8").read().splitlines()
            giu = [x for x in kq if x.startswith((u"Tổng tạo", u"Lỗi:", u"LỖI", u"  lỗi", u"Biên dự phòng", u"Kiểu filled region", u"Legend mới", u"Số ô"))
                   or u"KHÔNG tạo được group" in x or u"bỏ " in x]
            w(u"=== Tờ {} 1:{} | {} ô | {:.0f} s".format(t["ma"], t["ti_le"], len(ten_o), time.time() - t0))
            for x in giu:
                w(u"    " + x[:400])
        except Exception:
            w(u"=== Tờ {} | HỎNG {}".format(t["ma"], traceback.format_exc()[-400:]))
    if cfg.get("LUU") == "1":
        try:
            __revit__.ActiveUIDocument.Document.Save()
            w(u"--- Đã lưu bản sao.")
        except Exception as ex:
            w(u"--- Không lưu được: {}".format(ex))
    w(u"XONG")
except Exception:
    w(u"LỖI " + traceback.format_exc())
finally:
    bc.close()
