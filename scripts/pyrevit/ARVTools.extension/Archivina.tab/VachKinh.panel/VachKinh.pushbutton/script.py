# -*- coding: utf-8 -*-
"""Vách kính: bảng nhập (tên, chiều dài, chiều cao, cửa sổ / cửa đi) -> pick điểm trên mặt bằng -> dựng curtain wall
và chia đố 65 theo quy tắc VK (mỗi ô < 1200, chia đều), cửa đi / cửa sổ theo MDVK. Vách góc vuông: pick 3 điểm
(đầu cánh 1 -> góc ngoài -> đầu cánh 2), đố góc 150 x 150 + kính góc như mẫu. Đổi chiều dài / chiều cao vách sau
này thì tự chia lại (updater trong startup.py). Ctrl+Z một lần là hoàn tác.
Viết tay (không sinh từ Dynamo); lõi ở lib/arv_vach_kinh.py, bảng ở lib/arv_vach_kinh_bang.py."""
from __future__ import division, unicode_literals

__title__ = "Vách\nkính"

import io
import json
import math
import os
import sys
import traceback

_lib = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import clr
clr.AddReference("RevitAPI")
clr.AddReference("RevitAPIUI")
import Autodesk.Revit.DB as DB
import Autodesk.Revit.UI as UI
from Autodesk.Revit.Exceptions import OperationCanceledException

import arv_vach_kinh as vk
import arv_vach_kinh_bang as bang

TIEU_DE = "Vách kính"
NHO = os.path.join(os.environ.get("APPDATA") or os.path.expanduser("~"), "pyRevit", "ARVTools", "VachKinh.json")
LECH_GOC = 1.0      # độ: pick 3 điểm lệch vuông quá mức này thì báo


def bao(s):
    UI.TaskDialog.Show(TIEU_DE, s)


def doc_nho():
    try:
        with io.open(NHO, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def luu_nho(n):
    try:
        if not os.path.isdir(os.path.dirname(NHO)):
            os.makedirs(os.path.dirname(NHO))
        with io.open(NHO, "w", encoding="utf-8") as f:
            f.write(json.dumps(n, ensure_ascii=False, indent=1))
    except Exception:
        pass


def phang(p, z):
    return DB.XYZ(p.X, p.Y, z)


def pick(uidoc, loi_nhac):
    return uidoc.Selection.PickPoint(loi_nhac)


def pick_diem(uidoc, goc, z):
    """Nút Pick: vách thẳng 2 điểm, vách góc 3 điểm. Trả (điểm, [chiều dài mm]) hoặc None (Esc / lệch vuông)."""
    try:
        if not goc:
            p1 = phang(pick(uidoc, "Vách kính: điểm đầu vách (mép ngoài)"), z)
            p2 = phang(pick(uidoc, "Vách kính: điểm cuối vách (mép ngoài)"), z)
            L = vk.mm(p1.DistanceTo(p2))
            return ([p1, p2], [round(L, 2)]) if L > 1 else None
        p1 = phang(pick(uidoc, "Vách góc: đầu cánh 1 (mép ngoài, cánh có đố góc)"), z)
        c = phang(pick(uidoc, "Vách góc: góc NGOÀI của vách"), z)
        p2 = phang(pick(uidoc, "Vách góc: đầu cánh 2 (mép ngoài, cánh có kính góc)"), z)
    except OperationCanceledException:
        return None
    dA = (p1 - c).Normalize()
    v2 = p2 - c
    lech = abs(90.0 - math.degrees(math.acos(max(-1.0, min(1.0, dA.DotProduct(v2.Normalize()))))))
    if lech > LECH_GOC:
        bao("Hai cánh lệch vuông %.2f° (cho phép %.1f°). Pick lại, bật bắt điểm (Snap) để chọn đúng góc." % (lech, LECH_GOC))
        return None
    dB = DB.XYZ(-dA.Y, dA.X, 0)
    if dB.DotProduct(v2) < 0:
        dB = dB.Negate()
    L1, L2 = vk.mm(p1.DistanceTo(c)), vk.mm(v2.DotProduct(dB))
    return [c + dA * vk.ft(L1), c, c + dB * vk.ft(L2)], [round(L1, 2), round(L2, 2)]


def hoi_diem_dat(uidoc, cfg, z):
    """Chiều dài nhập tay: hỏi điểm đặt + hướng. Trả danh sách điểm cho tao_vach hoặc None."""
    try:
        if not cfg["goc"]:
            p1 = phang(pick(uidoc, "Vách kính: điểm đầu vách (mép ngoài)"), z)
            q = phang(pick(uidoc, "Vách kính: điểm chỉ hướng vách"), z)
            if q.DistanceTo(p1) < 1e-6:
                return None
            return [p1, p1 + (q - p1).Normalize() * vk.ft(cfg["canh"][0]["L"])]
        c = phang(pick(uidoc, "Vách góc: góc NGOÀI của vách"), z)
        q1 = phang(pick(uidoc, "Vách góc: điểm chỉ hướng cánh 1 (cánh có đố góc)"), z)
        q2 = phang(pick(uidoc, "Vách góc: điểm chỉ phía cánh 2"), z)
    except OperationCanceledException:
        return None
    if q1.DistanceTo(c) < 1e-6:
        return None
    dA = (q1 - c).Normalize()
    dB = DB.XYZ(-dA.Y, dA.X, 0)
    if dB.DotProduct(q2 - c) < 0:
        dB = dB.Negate()
    return [c + dA * vk.ft(cfg["canh"][0]["L"]), c, c + dB * vk.ft(cfg["canh"][1]["L"])]


def che_do_toi():
    try:
        return UI.UIThemeManager.CurrentTheme == UI.UITheme.Dark
    except Exception:
        return False


def chay():
    uiapp = __revit__
    uidoc = uiapp.ActiveUIDocument
    if uidoc is None:
        return
    doc = uidoc.Document
    view = doc.ActiveView
    level = getattr(view, "GenLevel", None)
    if level is None or view.ViewType not in (DB.ViewType.FloorPlan, DB.ViewType.EngineeringPlan,
                                              DB.ViewType.AreaPlan):
        bao("Mở mặt bằng tầng (Floor Plan) cần đặt vách kính rồi bấm lại.")
        return
    nho = doc_nho()
    for c in nho.get("canh") or []:
        c["ten"] = ""           # tên vách không nhớ sang lần bấm sau (như lệnh VK)
    dang_dung = vk.ten_dang_dung(doc)
    tien_to = vk.tien_to_tang(level)
    z = level.Elevation
    diem, diem_dai = None, None
    while True:
        b = bang.BangVachKinh(nho, dang_dung, tien_to, diem_dai, owner=uiapp.MainWindowHandle, toi=che_do_toi())
        kq = b.hien()
        nho = kq["nho"]
        luu_nho(nho)
        if kq["ma"] == "huy":
            return
        if kq["ma"] == "pick":
            r = pick_diem(uidoc, nho["goc"], z)
            if r:
                diem, diem_dai = r
                for i, L in enumerate(diem_dai):
                    nho["canh"][i]["dai"] = vk.so(L).replace(",", ".") if L != int(L) else "%d" % L
            continue
        cfg = kq["cfg"]
        dai = [c["L"] for c in cfg["canh"]]
        if not (diem and diem_dai and len(diem_dai) == len(dai) and
                all(abs(a - b_) < 0.006 for a, b_ in zip(dai, diem_dai))):
            diem = hoi_diem_dat(uidoc, cfg, z)
            if diem is None:
                diem_dai = None
                continue
        ghi = []
        nguon = vk.mo_nguon(uiapp.Application, doc)     # mô hình thiếu kiểu ARV: chép từ file nguồn mang theo
        t = DB.Transaction(doc, "ARV - Vách kính")
        t.Start()
        try:
            vach = vk.tao_vach(doc, level, cfg, diem, ghi, nguon)
            t.Commit()
        except Exception as ex:
            if t.HasStarted() and not t.HasEnded():
                t.RollBack()
            vk.dong_nguon(nguon)
            bao("Không dựng được vách: %s" % ex)
            continue
        vk.dong_nguon(nguon)
        uidoc.Selection.SetElementIds(_ds_id(vach))
        bao("Đã dựng %d vách:\n%s" % (len(vach), "\n".join(ghi)))
        return


def _ds_id(ws):
    from System.Collections.Generic import List
    lst = List[DB.ElementId]()
    for w in ws:
        lst.Add(w.Id)
    return lst


try:
    chay()
except Exception:
    bao("Lỗi:\n" + traceback.format_exc())
