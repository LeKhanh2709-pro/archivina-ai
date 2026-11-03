#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt bàn ăn (Furniture 2D) trong phòng khách ăn từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 28 sofa (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). 1. Bàn trên CAD, layer A-Nội thất / A-Interior = polyline chữ nhật kín, rộng 650…950, dài 1000…1600, có nét ghế ở CẢ HAI cạnh dài (G19: 700 × 1200 ghế tựa; 800 × 1200 ghế tròn). 2. Room chứa tâm bàn phải có tên chứa một chuỗi trong IN[4] (mặc định "phòng khách"). Báo cáo liệt kê phòng lọc mà không có bàn. 3. Vị trí: đầu bàn áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách đầu bàn CAD ≤ IN[5]; không có tường thì áp mặt đồ Furniture đã đặt (bàn nối tủ bếp phụ CH06, CH11). Không có gì → giữ tâm CAD, báo "cần soát". Ngang bàn: giữa khung family trùng giữa bàn CAD. 4. Kích thước: family cố định theo type, khung gồm cả ghế (2 chỗ: 1250 × 1557). Tool không đổi cỡ theo CAD. 5. Hướng family (suy từ khung type −1250…0 × ±778,6, như sofa): gốc ở giữa đầu bàn, đầu bàn về +X. Quay ngược → IN[7] = True. 6. Cao độ: Elevation from Level = đỉnh sàn tại tâm khung − level + IN[6] (mặc định 21 mm như sofa, tủ bếp: sàn 50, bàn 71). Không có sàn → IN[6], báo "cần soát". 7. Khung chồng lên đồ Furniture đã đặt hoặc bàn khác ≥ 5 mm mỗi chiều → vẫn đặt, báo "cần soát", không tự cắt. 8. Comments = "ARV-TaoBanAnTuCAD". Bàn của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; bàn cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Bàn ăn từ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
