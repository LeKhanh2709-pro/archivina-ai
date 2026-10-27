#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo dầm kết cấu từ mặt bằng kết cấu sàn (DWG đã Link vào Revit). Cách nhận dầm (theo NHÃN, không đoán theo nét): - Mỗi nhãn tiết diện "bxh" (VD "25X40", "D1 (220x500)") trên layer nhãn là một dầm. - Phương dầm = phương chữ của nhãn. Tìm cặp nét song song (layer cạnh dầm) cách nhau đúng b, nằm sát nhãn → trục dầm là đường giữa cặp nét. - Chiều dài dầm = đoạn hai cạnh cùng có nét; chỗ một cạnh bị ngắt do dầm khác đâm vào (cạnh kia liền) được nối qua. Đầu dầm chạm cạnh một dầm vuông góc thì kéo tới trục dầm đó. - Dầm liên tục ghi 1 nhãn: các nhịp tiếp theo của cùng cặp nét (cách nhau qua cột ≤ IN[10]) được tạo theo nhãn đó cho tới nhịp có nhãn khác. - Nhãn không tìm được cặp nét → bỏ qua, ghi vào báo cáo để vẽ tay. Chữ trong bản link Revit không đọc được nên nhãn được đọc từ BẢN SAO file DWG qua AutoCAD Core Console."""
__title__ = "Dầm\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
