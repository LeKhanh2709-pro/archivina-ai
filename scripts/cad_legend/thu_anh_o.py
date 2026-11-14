#! python3
# -*- coding: utf-8 -*-
"""Xuất ảnh TỪNG Ô để duyệt (chỉ dùng khi thử nền, KHÔNG lưu model): với mỗi ô, chạy ve_legend.py vẽ riêng ô đó vào 1
legend tạm (không group) rồi xuất PNG. Legend không crop được và ẩn tạm ~77 nghìn phần tử thì Revit chạy quá 9 phút, nên
vẽ riêng từng ô là cách nhanh nhất để có ảnh đủ nét; cùng mã và cùng json với bản đã lưu.

Cấu hình: thu_anh_cfg.txt cạnh file này, mỗi dòng 1 tên ô (trống = mọi ô trong ct_cua.json). Ảnh ra kq\\anh_o\\<nn>\\."""
import os, io, json, time, traceback
G = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(G, "kq", "anh_o")
BC = os.path.join(G, "kq", "thu_anh_o_log.txt")
if not os.path.isdir(RA):
    os.makedirs(RA)
bc = io.open(BC, "w", encoding="utf-8")


def w(s):
    bc.write(u"{}\n".format(s)); bc.flush()


try:
    o_ds = json.load(io.open(os.path.join(G, "ct_cua.json"), encoding="utf-8"))["o"]
    ten_ds = [o["ten"] for o in o_ds]
    rong_o = dict((o["ten"], o["bounds"][2] - o["bounds"][0]) for o in o_ds)
    cfg = os.path.join(G, "thu_anh_cfg.txt")
    if os.path.isfile(cfg):
        chon = [d.strip() for d in io.open(cfg, encoding="utf-8").read().splitlines() if d.strip()]
        if chon:
            ten_ds = [t for t in ten_ds if t in chon]
    p = os.path.join(G, "ve_legend.py")
    ma = compile(io.open(p, encoding="utf-8").read(), p, "exec")
    for i, ten in enumerate(ten_ds):
        t0 = time.time()
        tm = os.path.join(RA, "%02d" % (i + 1))
        os.environ["ARV_CTC_CHI"] = ten
        os.environ["ARV_CTC_TEN"] = u"ANH THU %02d" % (i + 1)
        os.environ["ARV_CTC_ANH"] = tm
        os.environ["ARV_CTC_LOG"] = os.path.join(RA, "log_%02d.txt" % (i + 1))
        os.environ["ARV_CTC_LUU"] = "0"
        os.environ["ARV_CTC_KHONG_GROUP"] = "1"
        # ô rộng (tờ 17 m): xuất 12000 px, không thì chữ 2,5 mm chỉ cao ~17 px, chữ co hẹp bị vỡ khoảng cách khi dựng ảnh
        os.environ["ARV_CTC_PX"] = "12000" if rong_o.get(ten, 0) > 10000 else "6000"
        try:
            exec(ma, {"__revit__": __revit__, "__file__": p, "__name__": "__main__"})
            kq = io.open(os.environ["ARV_CTC_LOG"], encoding="utf-8").read()
            loi = [d for d in kq.splitlines() if d.startswith(u"Lỗi:") or d.startswith(u"LỖI")]
            w(u"=== {:02d} {} | {:.0f} s | {}".format(i + 1, ten, time.time() - t0, u" ".join(loi)[:160]))
        except Exception:
            w(u"=== {:02d} {} | HỎNG {}".format(i + 1, ten, traceback.format_exc()[-300:]))
    w(u"XONG")
except Exception:
    w(u"LỖI " + traceback.format_exc())
finally:
    bc.close()
