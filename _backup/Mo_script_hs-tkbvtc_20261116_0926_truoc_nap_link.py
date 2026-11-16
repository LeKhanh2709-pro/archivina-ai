# -*- coding: utf-8 -*-
# Nút thử 1/2 của agent hs-tkbvtc (IronPython – CỐ Ý không phải CPython): mở file "mo" của file việc trong buoc.txt.
# File workshared thì mở TÁCH khỏi central (DetachAndPreserveWorksets, mở mọi workset) → không mượn phần tử từ central
# thật. Mở bằng API trong IronPython TRƯỚC khi engine CPython chạy: nếu CPython đã chạy rồi mới mở file bằng API thì Revit
# nạp AcDbMgd (tham chiếu DesktopConnectorInterop 26 không có trên máy) và mọi clr.AddReference sau đó của CPython lỗi.
# Ghi kết quả vào <ket_qua>\mo.txt. Nút 2 (Chay, CPython) chạy tiếp trên file đang mở.
import io, os, json
from Autodesk.Revit.DB import (ModelPathUtils, OpenOptions, DetachFromCentralOption, WorksetConfiguration,
                               WorksetConfigurationOption, BasicFileInfo)
_d = os.path.dirname(os.path.abspath(__file__))
for _ in range(5):
    _d = os.path.dirname(_d)
_viec = io.open(os.path.join(_d, "ext", "buoc.txt"), encoding="utf-8-sig").read().strip()
V = json.loads(io.open(_viec, encoding="utf-8-sig").read())
kq = os.path.normpath(V["ket_qua"])
if not os.path.isdir(kq):
    os.makedirs(kq)
f = io.open(os.path.join(kq, "mo.txt"), "w", encoding="utf-8")
# 2026-11-16 (FPT P5 mở lỗi ArchiveException 105 corruptData khi đọc bảng phần tử): locale CRT của tiến trình khác "C"
# làm Revit đọc sai dữ liệu có tên tiếng Việt (xem CLAUDE.md "Nguyên nhân Revit văng"). Ghi locale đang có rồi đặt "C"
# trước khi mở file. Không được thì bỏ qua (mở như cũ).
try:
    import ctypes
    _crt = ctypes.cdll.ucrtbase
    _crt.setlocale.restype = ctypes.c_char_p
    _cu = _crt.setlocale(0, None)
    _moi = _crt.setlocale(0, b"C")
    f.write(u"LOCALE truoc %s -> %s\n" % (_cu, _moi))
except Exception as _ex:
    f.write(u"LOCALE khong dat duoc: %s\n" % _ex)
uiapp = __revit__
loi = None
if V.get("revit") and (u"%s" % uiapp.Application.VersionNumber) != (u"%s" % V["revit"]):
    loi = u"Phiên Revit %s nhưng file việc yêu cầu Revit %s – không mở file" % (uiapp.Application.VersionNumber, V["revit"])
elif V.get("che_do") != "tao_mo_dau":
    mo = os.path.normpath(V["mo"])
    dau = uiapp.ActiveUIDocument.Document if uiapp.ActiveUIDocument is not None else None
    try:
        ws = BasicFileInfo.Extract(mo).IsWorkshared
        oo = OpenOptions()
        if V.get("audit"):
            # 2026-11-16: khoá "audit" của file việc = mở kèm Audit (chỉ dùng cho BẢN SAO; Revit báo CArchiveException
            # 105 "needs to be recovered ... select the Audit option")
            oo.Audit = True
            f.write(u"AUDIT bat\n")
        if ws:
            oo.DetachFromCentralOption = DetachFromCentralOption.DetachAndPreserveWorksets
            oo.SetOpenWorksetsConfiguration(WorksetConfiguration(WorksetConfigurationOption.OpenAllWorksets))
        ud = uiapp.OpenAndActivateDocument(ModelPathUtils.ConvertUserVisiblePathToModelPath(mo), oo, False)
        f.write(u"MO %s | workshared %s | tach %s\n" % (mo, ws, ud.Document.IsDetached))
        if dau is not None and dau.Title != ud.Document.Title:
            dau.Close(False)
    except Exception as ex:
        loi = u"%s" % ex
if loi:
    f.write(u"LOI %s\n" % loi)
f.write(u"XONG\n")
f.close()
