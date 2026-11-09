#! python3
# -*- coding: utf-8 -*-
# Đo thời gian nút Định vị + tag cửa trên bản sao HQV tháp B (Tầng 5BA): chạy lõi chỉ định trong chon_core.txt như nút
# thật (hộp thoại arv_hoi_sheet.hoi vẽ ra PNG, coi như bấm Chạy), bấm 2 lần (lần 2 = bấm lại), ghi vị trí tag ra JSON
# để so bản cũ / bản mới. Không lưu file .rvt.
import os, sys, io, json, time, traceback, datetime

GOC = r"D:\AI\_tmp\tagcua_nhanh"
cfg = [x.strip() for x in io.open(os.path.join(GOC, "chon_core.txt"), encoding="utf-8").read().splitlines() if x.strip()]
NHAN, CORE = cfg[0], cfg[1]
KQ_DIR = os.path.join(GOC, "kq_" + NHAN)
if not os.path.isdir(KQ_DIR):
    os.makedirs(KQ_DIR)
KQ = os.path.join(GOC, "ket_qua.txt")
NUT = r"D:\AI\scripts\pyrevit\ARVTools.extension\Archivina.tab\HoSo.panel\TagCua.pushbutton"
LIB = r"D:\AI\scripts\pyrevit\ARVTools.extension\lib"
f = io.open(KQ, "w", encoding="utf-8")


def w(s):
    f.write(u"{}\n".format(s))
    f.flush()


try:
    import clr
    clr.AddReference("RevitAPI")
    import Autodesk.Revit.DB as DB
    if LIB not in sys.path:
        sys.path.insert(0, LIB)
    import arv_dynamo_host
    import arv_hoi_sheet
    arv_hoi_sheet._THU_MUC_LUU = KQ_DIR
    arv_hoi_sheet._LUU = os.path.join(KQ_DIR, "TagCua_sheet.json")     # không ghi đè lựa chọn đã lưu của người dùng
    uiapp = __revit__
    uidoc = uiapp.ActiveUIDocument
    doc = uidoc.Document
    w(u"Bắt đầu {} | lõi {} | file {}".format(datetime.datetime.now(), CORE, doc.PathName))
    TEN_VIEW = cfg[3] if len(cfg) > 3 else u"Tầng 5BA"
    ds_mb = [v for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
             if not v.IsTemplate and v.ViewType == DB.ViewType.FloorPlan]
    w(u"Mặt bằng trong file: " + u" | ".join(sorted(v.Name for v in ds_mb))[:1500])
    mb = [v for v in ds_mb if v.Name == TEN_VIEW][0]
    with io.open(os.path.join(NUT, "inputs.json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    if len(cfg) > 2 and cfg[2] == "gia_nhom":      # gán tạm Type Comments trên bản sao để thử loại trừ (không lưu file)
        tx = DB.Transaction(doc, u"gia type comments")
        tx.Start()
        for bic, ds_gia in ((DB.BuiltInCategory.OST_Doors, [u"Cửa nhôm kính", u"CỬA NHÔM", u""]),
                            (DB.BuiltInCategory.OST_Windows, [u"cua nhom", u"Cửa nhôm"])):
            seen = {}
            for e in DB.FilteredElementCollector(doc, mb.Id).OfCategory(bic).WhereElementIsNotElementType():
                t = doc.GetElement(e.GetTypeId())
                pm = t.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_MARK)
                pc = t.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS)
                if pm is not None and pm.AsString() and pc is not None and (pc.AsString() or u"") != u"Louver":
                    seen[pm.AsString()] = t
            for k_, gt in zip(sorted(seen), ds_gia):
                seen[k_].get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS).Set(gt)
                w(u"Gán tạm: {} → '{}'".format(k_, gt))
        tx.Commit()
    dem_tc = {}
    for bic in (DB.BuiltInCategory.OST_Doors, DB.BuiltInCategory.OST_Windows):
        for e in DB.FilteredElementCollector(doc, mb.Id).OfCategory(bic).WhereElementIsNotElementType():
            t = doc.GetElement(e.GetTypeId())
            pr = t.get_Parameter(DB.BuiltInParameter.ALL_MODEL_TYPE_COMMENTS) if t is not None else None
            k = (str(bic), pr.AsString() or u"" if pr is not None else u"<không có tham số>")
            dem_tc[k] = dem_tc.get(k, 0) + 1
            ds_tc = dem_tc.setdefault(("_id", k), [])
            ds_tc.append(e.Id.Value)
    for k in sorted(x for x in dem_tc if x[0] != "_id"):
        w(u"TypeComments {} | '{}' | {} đối tượng".format(k[0], k[1], dem_tc[k]))
    with io.open(os.path.join(KQ_DIR, "type_comments.json"), "w", encoding="utf-8") as fh:
        json.dump([{"loai": k[1][0], "tc": k[1][1], "ids": v} for k, v in dem_tc.items() if k[0] == "_id"], fh,
                  ensure_ascii=False, indent=0)
    for lan in (1, 2):
        if doc.ActiveView.Id.Value != mb.Id.Value:
            uidoc.ActiveView = mb
        view = doc.ActiveView
        w(u"=== lần {} {}".format(lan, datetime.datetime.now().strftime("%H:%M:%S")))
        os.environ["ARV_HOI_ANH"] = os.path.join(KQ_DIR, "hoi_lan%d.png" % lan)
        t0 = time.perf_counter()
        ov = {5: False, 0: view.Name, 20: os.path.join(LIB, "tag_cua"), 10: KQ_DIR}     # log trên ổ D:
        them = arv_hoi_sheet.hoi(doc, view)
        t1 = time.perf_counter()
        ov.update(them or {})
        if len(cfg) > 2 and cfg[2] == "khong_sheet":
            ov[21] = False
        if len(cfg) > 2 and cfg[2] == "dat_lai" and lan == 2:
            ov[14] = True
        values = arv_dynamo_host.initial_values(spec, spec["key"])
        for i, v in ov.items():
            values[int(i)] = v
        out = arv_dynamo_host.run_core(CORE, values, uiapp, spec["transaction"])
        t2 = time.perf_counter()
        w(u"   hộp thoại {:.1f} s | lõi {:.1f} s".format(t1 - t0, t2 - t1))
        for ln in arv_dynamo_host.flatten_report(out):
            w(u"   | " + ln)
        # Vị trí tag trên mặt bằng định vị cửa để so bản cũ / mới
        vv = [x for x in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan)
              if not x.IsTemplate and x.Name.startswith(u"MẶT BẰNG ĐỊNH VỊ CỬA - ")]
        ds = []
        for v in vv:
            for tg in DB.FilteredElementCollector(doc, v.Id).OfClass(DB.IndependentTag):
                ids = sorted(i.Value for i in tg.GetTaggedLocalElementIds())
                hp = tg.TagHeadPosition
                ds.append({"tag": tg.Id.Value, "doi_tuong": ids, "loai": doc.GetElement(tg.GetTypeId()).FamilyName,
                           "x": round(hp.X * 304.8, 1), "y": round(hp.Y * 304.8, 1), "leader": bool(tg.HasLeader),
                           "huong": str(tg.TagOrientation)})
        with io.open(os.path.join(KQ_DIR, "tag_lan%d.json" % lan), "w", encoding="utf-8") as fh:
            json.dump(ds, fh, ensure_ascii=False, indent=0)
        w(u"   tag trên mặt bằng định vị cửa: {}".format(len(ds)))
        for v in vv:
            w(u"   view còn cô lập tạm: {}".format(v.IsInTemporaryViewMode(DB.TemporaryViewMode.TemporaryHideIsolate)))
        for vs in DB.FilteredElementCollector(doc).OfClass(DB.ViewSchedule):
            if not vs.IsTemplate and vs.Name.startswith(u"BẢNG THỐNG KÊ CỬA"):
                td = vs.GetTableData().GetSectionData(DB.SectionType.Body)
                w(u"   Bảng '{}': {} hàng".format(vs.Name, td.NumberOfRows))
                for r in range(td.NumberOfRows):
                    w(u"      " + u" | ".join(vs.GetCellText(DB.SectionType.Body, r, c) for c in range(td.NumberOfColumns)))
except Exception:
    w(u"LỖI: " + traceback.format_exc())
w(u"XONG {}".format(datetime.datetime.now()))
f.close()
