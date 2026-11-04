#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt tủ ti vi (Furniture 2D) trong phòng ngủ từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 22 giường (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). Tách từ phần tủ TV của tool 21. 1. Tủ TV trên CAD, layer A-Nội thất = hình chữ nhật sâu 200…350, dài 1200…2000 (G19: 1600 × 250) chứa thanh TV mảnh (G19: 1500 × 40) lệch về phía lưng. Lưng = cạnh dài gần thanh TV. 2. Room chứa tâm tủ phải có tên chứa một chuỗi trong IN[4] (mặc định "phòng ngủ"). Báo cáo liệt kê phòng lọc mà không có tủ. 3. Vị trí: lưng áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách lưng CAD ≤ IN[5]; không có → giữ theo CAD, báo "cần soát". Dọc tường giữ tâm CAD. 4. Kích thước: tham số instance DaiTu (dài, trục Y family) / RongTu (sâu, trục X family) của mẫu FPT P4. Tool dò trong SubTransaction trên cái đầu tiên (đổi +100 mm, đo khung, hoàn tác) mọi tham số Double không built-in; không thấy khung đổi mà có tên trên thì vẫn dùng tên đó. Rồi đặt dài và sâu theo CAD. Không có → giữ cỡ type, báo "cần soát". 5. Hướng family (suy từ khung type −300…0 × ±699,5, cần xem trên mặt bằng): gốc giữa lưng tủ, lưng về +X. Quay ngược → IN[7] = True. 6. Cao độ: Elevation from Level = đỉnh sàn tại tâm tủ − level + IN[6] (mặc định 1 mm như mẫu người dùng đặt tay: family 2D nằm trên mặt sàn mới thấy trên mặt bằng). Không có sàn → IN[6], báo "cần soát". 7. Comments = "ARV-TaoTuTiViTuCAD". Tủ của tool đã có mà lệch / sai hướng / sai cao độ / sai cỡ / khác type → sửa tại chỗ; tủ cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Tủ ti vi"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
