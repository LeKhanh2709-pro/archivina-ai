#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt giường (Furniture 2D) trong phòng ngủ từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 19 máy giặt (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). Tách từ phần giường của tool 21 (Dry-run 2026-10-31 15:23, G19 TẦNG 3: 33/33 giường). 1. Giường trên CAD, layer A-Nội thất = hình chữ nhật 1600 / 1800 × 2000 có gối và nét chéo gấp chăn (G19: 25 giường 1600, 8 giường 1800). Đầu giường = cạnh ngắn gần các nét bên trong (gối) nhất; hướng ra phòng = từ đầu giường về chân giường. 2. Room chứa tâm giường phải có tên chứa một chuỗi trong IN[5] (mặc định "phòng ngủ"). Báo cáo liệt kê phòng lọc mà không có giường. 3. Type: rộng CAD ≤ IN[8] dùng IN[3] (1600), lớn hơn dùng IN[4] (1800). Rộng CAD lệch type > 2 mm thì báo "cần soát". 4. Vị trí: đầu giường áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách đầu giường CAD ≤ IN[6]; không có → giữ theo CAD, báo "cần soát". Dọc tường giữ tâm CAD. 5. Hướng family (suy từ khung type −2000…0 × ±800 / ±900, cần xem trên mặt bằng): gốc giữa đầu giường, đầu giường về +X. Quay ngược → IN[9] = True. 6. Cao độ: Elevation from Level = đỉnh sàn tại tâm giường − level + IN[7] (mặc định 1 mm như mẫu người dùng đặt tay: family 2D nằm trên mặt sàn mới thấy trên mặt bằng). Không có sàn → IN[7], báo "cần soát". 7. Comments = "ARV-TaoGiuongTuCAD". Giường của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; giường cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Giường từ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
