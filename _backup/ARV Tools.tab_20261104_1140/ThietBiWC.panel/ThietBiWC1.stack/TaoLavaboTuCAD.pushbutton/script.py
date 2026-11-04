#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo lavabo (Plumbing Fixtures) từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG (không cần biết layer): 1. Lavabo trên CAD = MẶT BÀN CHỮ NHẬT có LÒNG CHẬU CONG bên trong (đo trên G19 2026-10-30: block động "设计行-半挂式台盆" layer A-Interior WC = polyline kín 900×500 + elip / cung / spline lòng chậu; lòng chậu ghép nhiều nét hở nên không nhận theo lòng chậu): - chữ nhật: polyline kín 4 đỉnh, hoặc nét thẳng nối đầu mút thành vòng 4 góc vuông (kể cả trong block); - cạnh dài trong [IN[7], IN[8]] (mặc định 600–1500), cạnh ngắn trong [300, IN[9]] (mặc định 650); - các nét cong (cung, elip, spline, tròn) nằm trọn trong mặt bàn gộp lại phủ ≥ 200 × 200 mm (lòng chậu) – loại bàn phấn, tủ. Trong Revit lòng chậu G19 là chữ nhật bo góc (đoạn thẳng + 4 cung góc ~50 mm). Chữ nhật trùng tâm (≤ 80 mm) → lấy cái lớn. IN[1] trống = dò mọi layer; có chuỗi = chỉ layer chứa chuỗi đó. 2. Room chứa tâm mặt bàn phải có tên chứa một chuỗi trong IN[6] (mặc định "WC;vệ sinh"; trống = mọi phòng) – loại chậu rửa bếp. 3. Tường dựa: tường thẳng Revit trên level IN[2] (dày ≥ 50 mm) gần mép mặt bàn nhất (khe ≤ IN[10], mặc định 100 mm), mặt bàn nằm trọn một phía tường. 4. Lavabo bề rộng cố định IN[5] (mặc định 900 – người dùng chốt 2026-10-30), tâm theo tâm mặt bàn CAD dọc tường, mép sau áp mặt tường – hoặc mặt ngoài lớp ốp / hoàn thiện mỏng (tường < 50 mm, VD ốp gạch 10 mm của tool 09) để gương không chìm vào lớp ốp. Mặt bàn chạm tường / lớp ốp vuông góc (lavabo ở góc) → dời áp mặt đó. Lavabo của tool đã có (Comments) mà sai cao độ hoặc lệch vị trí → sửa (Offset 0, dời), không tạo lại. 5. Type: người dùng chọn type mẫu ở IN[3] (node Family Types hoặc chuỗi "Family : Type"). Type cùng family có tham số bề rộng IN[4] = IN[5] → dùng (ưu tiên type mẫu); chưa có → nhân bản type mẫu, đặt bề rộng. Chiều sâu, chiều cao giữ theo type mẫu. 6. Đặt instance tại giữa mép sau (gốc family = giữa mép sát tường, mặt trước theo +Y như các family lavabo của dự án), xoay mặt trước ra khỏi tường; IN[11] = True nếu family quay ngược. Family gắn tường → gắn vào tường dựa. Comments = "ARV-TaoLavaboTuCAD". Đã có thiết bị cùng family tại vị trí → bỏ qua."""
__title__ = "Lavabo từ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
