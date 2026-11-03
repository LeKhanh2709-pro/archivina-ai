#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt tủ đầu giường (Furniture 2D) trong phòng ngủ từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 22 giường (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). Tách từ phần tủ đầu giường của tool 21. 1. Tủ đầu giường trên CAD, layer A-Nội thất = hình vuông 400 chứa vòng tròn. Tủ sát cạnh giường (≤ STAND_GAP_MM) lấy lưng cùng hướng đầu giường. Tủ không sát giường: lưng = cạnh gần tường hơn, báo "cần soát". 2. Room chứa tâm tủ phải có tên chứa một chuỗi trong IN[4] (mặc định "phòng ngủ"). Báo cáo liệt kê phòng lọc mà không có tủ. 3. TỦ ĐÈ LÊN BÀN LÀM VIỆC THÌ BỎ (người dùng yêu cầu 2026-10-31): vị trí đó để phiên sau chạy tool bàn. Bàn = hình chữ nhật sâu 450…650, dài 800…1700 có ghế sát cạnh dài. Chồng ≥ DROP_MM mỗi chiều mới gọi là đè. Tool này không đặt bàn. 4. Vị trí: lưng tủ áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách lưng CAD ≤ IN[5]; không có → giữ theo CAD, báo "cần soát". Dọc tường giữ tâm CAD. 5. Hướng family (suy từ khung type −400…0 × ±200, cần xem trên mặt bằng): gốc giữa lưng tủ, lưng về +X. Quay ngược → IN[7] = True. 6. Cao độ: Elevation from Level = đỉnh sàn tại tâm tủ − level + IN[6] (mặc định 1 mm như mẫu người dùng đặt tay: family 2D nằm trên mặt sàn mới thấy trên mặt bằng). Không có sàn → IN[6], báo "cần soát". 7. Comments = "ARV-TaoTuDauGiuongTuCAD". Tủ của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; tủ cùng family người dùng tự đặt → bỏ qua. Tủ đã có ở vị trí đè bàn → báo để xoá tay, tool không tự xoá."""
__title__ = "Tủ đầu\ngiường"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
