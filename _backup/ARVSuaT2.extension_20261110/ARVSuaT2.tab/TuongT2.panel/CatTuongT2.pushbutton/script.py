# -*- coding: utf-8 -*-
# Nút dùng một lần: cắt tường Tầng 2 trùng vách kính theo danh sách người dùng đã duyệt 2026-11-10.
from __future__ import unicode_literals
import io, os, clr
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog
__doc__ = "Cắt 31 tường Tầng 2 trùng vách kính (danh sách đã duyệt)."
thu_muc = os.path.dirname(__file__)
core = os.path.join(thu_muc, "core_cat_tuong.py")
g = {"doc": __revit__.ActiveUIDocument.Document, "THU_MUC_NUT": thu_muc, "KIEM_TEN": True,
     "OUT_DIR": r"D:\AI\_tmp\revit_vk_hqv\kq_nut_goc", "__name__": "nut"}
exec(compile(io.open(core, encoding="utf-8").read(), core, "exec"), g)
TaskDialog.Show("Cắt tường trùng kính Tầng 2", g["bao_cao"])
