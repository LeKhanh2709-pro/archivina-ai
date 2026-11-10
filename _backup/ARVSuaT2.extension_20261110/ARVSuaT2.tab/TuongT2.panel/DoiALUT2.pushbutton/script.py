# -*- coding: utf-8 -*-
# Nút dùng một lần: Tầng 2, 2 hàng ô trên cùng đổi sang A-ALU (người dùng duyệt bản mẫu 2026-11-10).
from __future__ import unicode_literals
import io, os, clr
clr.AddReference("RevitAPIUI")
from Autodesk.Revit.UI import TaskDialog
__doc__ = "Đổi 2 hàng ô trên cùng của vách kính Tầng 2 sang A-ALU."
core = os.path.join(os.path.dirname(__file__), "core_doi_alu.py")
g = {"doc": __revit__.ActiveUIDocument.Document, "KIEM_TEN": True,
     "OUT_DIR": r"D:\AI\_tmp\revit_vk_hqv\kq_nut_alu", "__name__": "nut"}
exec(compile(io.open(core, encoding="utf-8").read(), core, "exec"), g)
TaskDialog.Show("Đổi A-ALU Tầng 2", g["bao_cao"])
