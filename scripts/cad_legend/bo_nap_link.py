#! python3
# -*- coding: utf-8 -*-
# Chỉ dùng cho BẢN SAO trong _tmp: đặt mọi link Revit / CAD của Site.rvt về "không nạp" (TransmissionData),
# để phiên thử mở file không phụ thuộc file link trên ổ mạng. Không sửa file gốc.
import locale
locale.setlocale(locale.LC_ALL, "C")
import io, traceback
OUT = r"D:\AI\_tmp\ct_cua_legend\kq\bo_nap_link.txt"
RVT = r"D:\AI\_tmp\ct_cua_legend\rvt\Site.rvt"
f = io.open(OUT, "w", encoding="utf-8")
try:
    import clr
    clr.AddReference("RevitAPI")
    import Autodesk.Revit.DB as DB
    uidoc = __revit__.ActiveUIDocument
    f.write(u"doc đang mở: {}\n".format(uidoc.Document.PathName if uidoc else None))
    mp = DB.ModelPathUtils.ConvertUserVisiblePathToModelPath(RVT)
    td = DB.TransmissionData.ReadTransmissionData(mp)
    n = 0
    for i in td.GetAllExternalFileReferenceIds():
        ext = td.GetLastSavedReferenceData(i)
        t = ext.ExternalFileReferenceType
        if t in (DB.ExternalFileReferenceType.RevitLink, DB.ExternalFileReferenceType.CADLink):
            td.SetDesiredReferenceData(i, ext.GetPath(), ext.PathType, False)
            n += 1
    td.IsTransmitted = True
    DB.TransmissionData.WriteTransmissionData(mp, td)
    f.write(u"Đặt không nạp: {} link\nXONG\n".format(n))
except Exception:
    f.write(u"LỖI " + traceback.format_exc())
finally:
    f.close()
