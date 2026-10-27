#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo lưới trục (Grid) từ bản CAD đã Link/Import trong Revit. - Đường trục: lấy từ layer trục của bản CAD, gộp các đoạn thẳng hàng, bỏ đoạn ngắn hơn 1 m. - Tên trục: Revit API không đọc được chữ trong CAD, nên script gọi AutoCAD Core Console trên BẢN SAO file DWG đang link, đọc attribute / TEXT / MTEXT trên layer ký hiệu trục rồi gán cho trục gần nhất. Không có Core Console hoặc CAD dạng Import (không có file) → đánh tên tự động theo tiền tố: trục đứng trái → phải, trục ngang trên → dưới."""
__title__ = "Tạo trục\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
