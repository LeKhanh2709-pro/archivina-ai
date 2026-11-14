#! python3
# -*- coding: utf-8 -*-
"""Dò hatch nào Revit không nhận biên (CHỈ THỬ, không ghi gì vào model): tạo Filled Region của mọi vùng trong
ct_cua.json vào 1 legend có sẵn trong MỘT transaction rồi RollBack. Vùng hỏng (qua hết các biên dự phòng) được ghi ra
kq\\hatch_loi.json kèm lỗi từng vòng để xem lại ngoài Revit.

Biến môi trường: ARV_CTC_JSON (json), ARV_CTC_HLOG (log), ARV_CTC_HOUT (json vùng hỏng).
"""
import locale
locale.setlocale(locale.LC_ALL, "C")
import io, os, json, math, time, traceback

GOC = os.path.dirname(os.path.abspath(__file__))
JSON_ = os.environ.get("ARV_CTC_JSON") or os.path.join(GOC, "ct_cua.json")
LOG = os.environ.get("ARV_CTC_HLOG") or os.path.join(GOC, "kq", "thu_hatch_log.txt")
OUT = os.environ.get("ARV_CTC_HOUT") or os.path.join(GOC, "kq", "hatch_loi.json")
f = io.open(LOG, "w", encoding="utf-8")


def w(s):
    f.write(u"{}\n".format(s)); f.flush()


MM = 1.0 / 304.8
try:
    import clr
    clr.AddReference("RevitAPI")
    import Autodesk.Revit.DB as DB
    from System.Collections.Generic import List as NetList

    doc = __revit__.ActiveUIDocument.Document
    app = doc.Application
    w(u"--- {} | nét ngắn nhất Revit {:.4f} mm | sai số đỉnh {:.5f} mm".format(
        doc.PathName, app.ShortCurveTolerance / MM, app.VertexTolerance / MM))
    d = json.load(io.open(JSON_, encoding="utf-8"))
    FEC = DB.FilteredElementCollector
    lg = [v for v in FEC(doc).OfClass(DB.View) if v.ViewType == DB.ViewType.Legend and not v.IsTemplate][0]
    typ = list(FEC(doc).OfClass(DB.FilledRegionType))[0].Id

    def XYZ(x, y):
        return DB.XYZ(x * MM, y * MM, 0)

    def duong(s):
        if s[0] == "L":
            return DB.Line.CreateBound(XYZ(s[1], s[2]), XYZ(s[3], s[4]))
        return DB.Arc.Create(XYZ(s[1], s[2]), XYZ(s[5], s[6]), XYZ(s[3], s[4]))

    def vong(loop):
        cl = DB.CurveLoop()
        for s in loop:
            cl.Append(duong(s))
        return cl

    def tao(loops):
        ls = NetList[DB.CurveLoop]()
        for l in loops:
            ls.Add(vong(l))
        return DB.FilledRegion.Create(doc, typ, lg.Id, ls)

    def thu(loops):
        try:
            tao(loops)
            return None
        except Exception as ex:
            return str(ex)[:160]

    def xet_vong(l):
        """Lỗi chi tiết của 1 vòng: đoạn nào không dựng được, vòng hở, hay Revit từ chối cả vòng."""
        kq = {"so_doan": len(l), "loi_doan": [], "loi_noi": None, "ho": None, "loi_vung": None}
        cl = DB.CurveLoop()
        for i, s in enumerate(l):
            try:
                c = duong(s)
            except Exception as ex:
                kq["loi_doan"].append([i, s[0], str(ex)[:80]]); continue
            try:
                cl.Append(c)
            except Exception as ex:
                if kq["loi_noi"] is None:
                    kq["loi_noi"] = [i, str(ex)[:80]]
        try:
            kq["ho"] = bool(cl.IsOpen())
        except Exception:
            pass
        kq["loi_vung"] = thu([l])
        return kq

    t = DB.Transaction(doc, u"Thử hatch (sẽ hoàn tác)")
    t.Start()
    hong = []
    tong = {"vung": 0, "ok_goc": 0, "ok_du_phong": 0, "ok_tung_vong": 0, "hong": 0}
    theo_muc = {}
    for o in d["o"]:
        n_h = 0
        for loai in ("vung", "che"):
            for idx, it in enumerate(o[loai]):
                tong["vung"] += 1
                e0 = thu(it["loops"])
                if e0 is None:
                    tong["ok_goc"] += 1; continue
                # các mức biên dự phòng: 'sua' (bản cũ: 1 mức) hoặc 'du_phong' (nhiều mức), mỗi mức = danh sách mảnh
                muc_ds = it.get("du_phong") or ([it["sua"]] if it.get("sua") else [])
                kq_muc = []
                dat = None
                for im, muc in enumerate(muc_ds):
                    ok = 0; loi = []
                    for manh in muc:
                        e = thu(manh)
                        if e is None:
                            ok += 1
                        else:
                            loi.append(e[:60])
                    kq_muc.append([im, len(muc), ok, loi[:2]])
                    if muc and ok == len(muc):
                        dat = im; break
                if dat is not None:
                    tong["ok_du_phong"] += 1
                    theo_muc[dat] = theo_muc.get(dat, 0) + 1
                    continue
                # bản cũ: thử từng vòng riêng, được ≥ 1 vòng là coi như xong
                ok_v = sum(1 for l in it["loops"] if thu([l]) is None)
                if ok_v and not it.get("du_phong"):
                    tong["ok_tung_vong"] += 1
                tong["hong"] += 0 if (ok_v and not it.get("du_phong")) else 1
                n_h += 1
                hong.append({"o": o["ten"], "loai": loai, "idx": idx, "z": it["z"], "kieu": it.get("kieu"),
                             "loi_goc": e0, "muc": kq_muc, "vong_ok": ok_v, "so_vong": len(it["loops"]),
                             "vong": [xet_vong(l) for l in it["loops"]],
                             "loops": it["loops"], "sua": it.get("sua"), "du_phong": it.get("du_phong")})
        w(u"=== Ô {}: {} vùng + {} che, không tạo được bằng biên gốc lẫn dự phòng: {}".format(
            o["ten"], len(o["vung"]), len(o["che"]), n_h))
    t.RollBack()
    w(u"--- Tổng: {} | dự phòng theo mức: {}".format(tong, theo_muc))
    json.dump({"tong": tong, "hong": hong}, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    w(u"--- Đã ghi {} vùng vào {}".format(len(hong), OUT))
    w(u"XONG")
except Exception:
    w(u"LỖI " + traceback.format_exc())
finally:
    f.close()
