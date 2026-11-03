#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt tủ quần áo (Furniture 2D) trong phòng ngủ từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 22 giường (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). Tách từ phần tủ áo của tool 21. 1. Tủ áo trên CAD, layer A-Nội thất = hình chữ nhật sâu 500…700, dài 1000…2400 (G19: sâu 600, dài 1200…2135) có thanh treo dọc gần trục giữa. 2. Room chứa tâm tủ phải có tên chứa một chuỗi trong IN[4] (mặc định "phòng ngủ"). Báo cáo liệt kê phòng lọc mà không có tủ. 3. Vị trí: tủ áo đối xứng theo chiều sâu nên không biết lưng từ hình: thử hai cạnh dài, cạnh gần mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách cạnh CAD ≤ IN[5], là lưng; không có → giữ theo CAD, báo "cần soát". Hai đầu cách tường bên ≤ IN[6] thì kéo chạm tường. 4. Kích thước: tham số instance L (dài, trục X family) / h (sâu, trục Y family) của mẫu người dùng. Tool dò trong SubTransaction trên cái đầu tiên (đổi +100 mm, đo khung, hoàn tác) mọi tham số Double không built-in; không thấy khung đổi mà có tên trên thì vẫn dùng tên đó. Rồi đặt dài và sâu theo tủ đã căn. Không có → giữ cỡ type, báo "cần soát". 5. Hướng family (suy từ khung type 0…2000 × ±300): gốc ở đầu tủ giữa chiều sâu, dài theo +X, lưng quy ước về +Y; hình đối xứng nên chỉ thấy khác khi family có chi tiết một phía. Quay ngược → IN[8] = True. 6. Cao độ: Elevation from Level = đỉnh sàn tại tâm tủ − level + IN[7] (mặc định 21 mm như mẫu người dùng đặt tay: sàn 50, tủ 71). Không có sàn → IN[7], báo "cần soát". 7. Tủ chồng lên đồ Furniture đã đặt hoặc tủ áo khác ≥ 5 mm mỗi chiều → vẫn đặt, báo "cần soát", không tự cắt. 8. Comments = "ARV-TaoTuQuanAoTuCAD". Tủ của tool đã có mà lệch / sai hướng / sai cao độ / sai cỡ / khác type → sửa tại chỗ; tủ cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Tủ\nquần áo"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
