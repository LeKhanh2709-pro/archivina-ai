# -*- coding: utf-8 -*-
# Chạy bằng chay_hs.py che_do "script" (KHÔNG lưu). 2026-11-20 trưa: xuất DXF (gộp link, mm, toạ độ model) các view
# "MẶT BẰNG CHỐNG THẤM - <tầng>" để soi đường bo bằng CHÍNH NÉT REVIT VẼ (layer A-WALL = mặt lớp thô, A-WALL-FNSH = lớp trát /
# ốp, S-COLS… kết cấu) – không suy vị trí tường bằng công thức (bài học 19 – 20/11). Ghi kèm đường dẫn link đang nạp.
from System.Collections.Generic import List as NetList

TANG = V.get("tang_dxf") or [u"TẦNG 1", u"TẦNG 3", u"TẦNG 4-32"]
for lt in DB.FilteredElementCollector(doc).OfClass(DB.RevitLinkType):
    try:
        ref = DB.ExternalFileUtils.GetExternalFileReference(doc, lt.Id)
        p = DB.ModelPathUtils.ConvertModelPathToUserVisiblePath(ref.GetAbsolutePath())
    except Exception as ex:
        p = u"? %s" % ex
    w(u"   link %s: %s | nạp: %s" % (lt.Name, p, DB.RevitLinkType.IsLoaded(doc, lt.Id)))

for v in DB.FilteredElementCollector(doc).OfClass(DB.ViewPlan):
    if v.IsTemplate or not v.Name.startswith(u"MẶT BẰNG CHỐNG THẤM - "):
        continue
    tg = v.Name.split(u" - ")[-1]
    if tg not in TANG:
        continue
    ids = NetList[DB.ElementId]()
    ids.Add(v.Id)
    o = DB.DXFExportOptions()
    try:
        o.MergedViews = True
    except Exception:
        pass
    try:
        o.TargetUnit = DB.ExportUnit.Millimeter
    except Exception:
        pass
    ten = u"CT_" + tg.replace(u"TẦNG ", u"T").replace(u" ", u"_")
    try:
        ok = doc.Export(KQ, ten, ids, o)
        w(u"   DXF %s → %s.dxf: %s" % (v.Name, ten, ok))
    except Exception as ex:
        w(u"   DXF lỗi %s: %s" % (v.Name, ex))
