# -*- coding: utf-8 -*-
# Nút dùng một lần: thêm tường lấp phía trên vách kính Tầng 3 (người dùng duyệt bản mẫu v5, 2026-11-10).
from __future__ import unicode_literals
import io, os, clr
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog
__doc__ = "Thêm 28 đoạn tường lấp phía trên vách kính Tầng 3 (danh sách đã duyệt)."
thu_muc = os.path.dirname(__file__)
core = os.path.join(thu_muc, "core_them_tuong.py")
g = {"doc": __revit__.ActiveUIDocument.Document, "THU_MUC_NUT": thu_muc, "KIEM_TEN": True,
     "FILE_SPEC": os.path.join(thu_muc, "spec_t23.json"),
     "OUT_DIR": r"D:\AI\_tmp\revit_vk_hqv\kq_nut_t3", "__name__": "nut"}
exec(compile(io.open(core, encoding="utf-8").read(), core, "exec"), g)
TaskDialog.Show("Thêm tường trên kính Tầng 3", g["bao_cao"])
