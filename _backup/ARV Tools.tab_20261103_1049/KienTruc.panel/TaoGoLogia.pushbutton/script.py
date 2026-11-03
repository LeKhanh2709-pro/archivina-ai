#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo gờ bê tông mặt ngoài logia (Basic Wall), lấy tuyến từ mặt bằng DWG đã Link (KTS chốt 2026-10-21): 1. Logia = sàn (Floor) trên level IN[5] có tên type chứa IN[2] (VD "SHT-Gach Lat Logia-300x600"), lấy hộp bao. 2. Tuyến gờ = đường giữa cặp nét song song cách nhau 150 mm (± 3) trên layer IN[1], sát cạnh hộp bao logia (≤ 300 mm), phủ ≥ 50 % cạnh đó, dài từ tường đến tường (đầu nét CAD) – cùng cách dò với ARV_TaoLanCanLouverLogia_v1. Nét dài hơn logia → cắt ở cạnh logia rồi bắt vào đầu tường Revit trên tuyến (≤ 400 mm); không có tường → giữ mép logia, báo "KIỂM TRA ĐẦU". 3. Gờ = Wall type IN[3] (VD "VBT-150"), tâm tường trên đường giữa cặp nét, không nối (join) đầu tường. Type chưa có → nhân bản type mẫu IN[4] (VD "VBT-200", một lớp bê tông) với tên IN[3], đổi chiều dày lớp = bề dày cặp nét CAD (150). Dry-run chỉ báo "SẼ NHÂN BẢN". 4. Cao độ theo từng logia (so với level): đỉnh gờ = mặt sàn hoàn thiện logia + IN[6] (VD -30 + 100 = +70); chân gờ = IN[7] nếu có, trống = đáy sàn hoàn thiện logia (VD -30 - 50 = -80). 5. Gờ tạo ra có Comments "ARV-GoLogia". Chạy lại, trong phạm vi tuyến từng logia: - Tường có Comments đó, đúng kế hoạch (đầu tuyến ± 20 mm, chân/đỉnh ± 2 mm, đúng type) → giữ. - Có Comments đó mà sai kế hoạch → XOÁ rồi tạo lại (báo "thay"). - Tường khác trùng tuyến (dựng tay) → không đụng, logia đó bỏ qua, báo "đã có tường dựng tay"."""
__title__ = "Gờ\nlogia"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
