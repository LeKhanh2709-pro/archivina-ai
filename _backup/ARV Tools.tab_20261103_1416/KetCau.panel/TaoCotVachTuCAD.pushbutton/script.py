#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo cột và vách/lõi kết cấu từ mặt bằng định vị cột vách lõi (DWG đã Link/Import vào Revit). - Hình chữ nhật đơn có cạnh dài / cạnh ngắn < tỉ lệ  → CỘT (đúng b × h, góc xoay) - Hình chữ nhật dài hơn                            → VÁCH - Lõi hình L, T, U, lõi rỗng (cạnh vuông góc)        → tách thành các đoạn VÁCH chữ nhật - Hình tròn, hình có cạnh xiên                      → bỏ qua, ghi vào báo cáo"""
__title__ = "Cột vách\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
