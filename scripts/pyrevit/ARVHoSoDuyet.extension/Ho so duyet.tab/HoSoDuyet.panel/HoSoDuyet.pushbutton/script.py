#! python3
# -*- coding: utf-8 -*-
# Nút viết tay của ARVHoSoDuyet.extension (extension RIÊNG, gỡ được: bỏ thư mục extension rồi Reload pyRevit).
# Chạy các nút HS TKBVTC của ARVTools.extension (tab Archivina) nhưng KHÔNG sửa gì trong ARVTools.extension.
"""Trình bày lại hồ sơ đã duyệt vào file đang mở: chạy lần lượt Chống thấm, Ngăn cháy lan, Định vị lan can louver,
Định vị + tag cửa trên từng mặt bằng theo phương án đã duyệt (lib/ho_so_duyet/<mã>.json), không hỏi lại từng nút."""
__title__ = "Hồ sơ\nđã duyệt"
import os
import sys
import glob

try:
    # Engine CPython của pyRevit đặt LC_CTYPE theo máy cho cả tiến trình Revit; sau đó Revit nạp phần tử có tên có dấu
    # (model HQV Site: ExportDWGSettings "AV-Export Cad") thì báo corruptData rồi thoát (Unmarshaller.cpp 357, tìm ra
    # 2026-11-12). Trả locale về "C" trước khi đụng tới model.
    import locale
    locale.setlocale(locale.LC_ALL, "C")
except Exception:
    pass

_here = os.path.dirname(os.path.abspath(__file__))
_ext = os.path.normpath(os.path.join(_here, "..", "..", ".."))


def tim_panel_archivina():
    """Thư mục HoSo.panel của ARVTools.extension: cạnh extension này, không thì trong các Extension Search Path."""
    goc = [os.path.dirname(_ext)]
    try:
        from pyrevit.userconfig import user_config
        goc += list(user_config.get_ext_root_dirs())
    except Exception:
        pass
    for g in goc:
        arv = os.path.join(g, "ARVTools.extension")
        if os.path.isfile(os.path.join(arv, "lib", "arv_hoi_sheet.py")):
            ds = glob.glob(os.path.join(arv, "*.tab", "HoSo.panel"))
            if ds:
                return arv, ds[0]
    return None, None


_arv, _panel = tim_panel_archivina()
if _arv is None:
    import clr
    clr.AddReference("RevitAPIUI")
    from Autodesk.Revit.UI import TaskDialog
    TaskDialog.Show(u"Hồ sơ đã duyệt", u"Không thấy bộ nút Archivina (ARVTools.extension) cạnh extension này hoặc trong "
                                      u"Extension Search Path của pyRevit. Nút này chạy lại các nút HS TKBVTC của Archivina "
                                      u"nên cần bộ đó.")
else:
    for _p in (os.path.join(_arv, "lib"), os.path.join(_ext, "lib")):
        if _p not in sys.path:
            sys.path.insert(0, _p)
    import arv_ho_so_duyet
    arv_ho_so_duyet.chay(__revit__, _panel)
