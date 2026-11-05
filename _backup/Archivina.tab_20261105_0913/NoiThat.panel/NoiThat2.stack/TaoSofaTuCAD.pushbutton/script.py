#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt sofa (Furniture 2D) trong phòng khách ăn từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 22 giường (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). 1. Sofa trên CAD, layer A-Nội thất / A-Interior = hình chữ U: hai tay vịn song song cùng dài 600…1100, nối bằng nét tựa lưng dài 1200…2600 nằm cách đầu tay vịn 100…300 (G19: rộng 1600, tay vịn 810, nét tựa 170; rộng 1800, tay vịn 850, nét tựa 150). Lưng = đầu tay vịn gần nét tựa. 2. Room chứa tâm sofa phải có tên chứa một chuỗi trong IN[4] (mặc định "phòng khách"). Báo cáo liệt kê phòng lọc mà không có sofa. 3. Vị trí: lưng áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách lưng CAD ≤ IN[5]; không có → giữ theo CAD, báo "cần soát". Dọc tường: giữa khung family trùng giữa sofa CAD. 4. Kích thước: family sofa cố định theo type, khung gồm cả bàn tròn (2 chỗ: 2060 × 2000). DaiTu, RongTu của family không đổi khung type (2 chỗ, 3 chỗ cùng 1399 × 300 mà khung khác nhau) nên tool không đặt. 5. Hướng family (suy từ khung type −2060…0 × ±1000 và các cặp đặt tay tựa lưng nhau ở FPT P4): gốc ở giữa lưng, lưng về +X. Quay ngược → IN[7] = True. 6. Cao độ: Elevation from Level = đỉnh sàn tại tâm khung − level + IN[6] (mặc định 21 mm như mẫu người dùng đặt tay: sàn 50, sofa 71). Không có sàn → IN[6], báo "cần soát". 7. Khung chồng lên đồ Furniture đã đặt hoặc sofa khác ≥ 5 mm mỗi chiều → vẫn đặt, báo "cần soát", không tự cắt. 8. Comments = "ARV-TaoSofaTuCAD". Sofa của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; sofa cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Sofa từ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
