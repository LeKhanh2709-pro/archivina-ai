# -*- coding: utf-8 -*-
# Đọc đối tượng trong file link cho các bảng hỏi (arv_bang_cua, arv_bang_lan_can). Quy tắc giống khối PHẦN CHUNG FILE LINK
# trong scripts\dynamo\Link_chung.py: chỉ link đang thấy trong view, đúng tầng (level của link khớp cao độ level view, đã tính
# link đặt lệch cao độ). Phần tử trả về là phần tử gốc trong file link, chỉ đọc.
import clr
clr.AddReference("RevitAPI")
import Autodesk.Revit.DB as DB


def _mm(v):
    return DB.UnitUtils.ConvertToInternalUnits(v, DB.UnitTypeId.Millimeters)


def _tren_level(e, ids):
    if e.LevelId.Value in ids:
        return True
    if e.LevelId != DB.ElementId.InvalidElementId:
        return False
    for bip in (DB.BuiltInParameter.INSTANCE_SCHEDULE_ONLY_LEVEL_PARAM, DB.BuiltInParameter.FAMILY_LEVEL_PARAM,
                DB.BuiltInParameter.STAIRS_RAILING_BASE_LEVEL_PARAM):
        try:
            p = e.get_Parameter(bip)
            if p is not None and p.HasValue:
                return p.AsElementId().Value in ids
        except Exception:
            pass
    try:
        return e.Host is not None and e.Host.LevelId.Value in ids
    except Exception:
        return False


def doi_tuong_link(doc, view, bic):
    """Phần tử hạng mục bic trong các file link đang thấy trong view, đúng tầng của view."""
    lv = view.GenLevel
    if lv is None:
        return []
    kq = []
    for li in DB.FilteredElementCollector(doc, view.Id).OfClass(DB.RevitLinkInstance):
        try:
            ld = li.GetLinkDocument()
        except Exception:
            ld = None
        if ld is None:
            continue
        tf = li.GetTotalTransform()
        ids = set(l.Id.Value for l in DB.FilteredElementCollector(ld).OfClass(DB.Level)
                  if abs(l.Elevation + tf.Origin.Z - lv.Elevation) < _mm(5))
        if not ids:
            continue
        for e in DB.FilteredElementCollector(doc, view.Id, li.Id).OfCategory(bic).WhereElementIsNotElementType():
            if _tren_level(e, ids):
                kq.append(e)
    return kq
