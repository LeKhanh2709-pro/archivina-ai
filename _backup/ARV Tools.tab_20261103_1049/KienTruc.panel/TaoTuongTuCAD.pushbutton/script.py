#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Bản Dynamo của nút pyRevit KienTruc.panel/TaoTuongTuCAD – mỗi chiều dày CAD một wall type (bảng IN[2]). Tạo tường kiến trúc từ mặt bằng tường xây (DWG đã Link/Import vào Revit): 1. Đọc đoạn thẳng (line, polyline, kể cả trong block) trên layer tường. 2. Ghép cặp hai nét song song cách nhau trong dải chiều dày → đường tim tường. Cặp gần nhau nhất trước; không ghép hai nét có nét thứ ba nằm giữa (tường vẽ cả mặt thô lẫn mặt hoàn thiện không bị tạo đôi). 3. Gộp đoạn thẳng hàng cùng chiều dày bị ngắt tại chỗ giao tường. 4. Tường liền qua ô cửa: hai đoạn thẳng hàng cách nhau ≤ IN[7] mà trong khe có nét của layer cửa (IN[6]) → nối thành tường liền (chèn cửa sau). Khe không có nét cửa (lối đi mở) giữ nguyên. Khe ≤ 150 mm giữa hai tường thẳng hàng khác chiều dày cũng được nối. 5. Kéo dài đầu tường tới tim tường không song song để nối góc L / chữ T (cả khi đầu tường hụt mặt tường giao ≤ 50 mm). Bỏ mẩu tường nằm trọn trong thân tường khác (cặp nét giả ở nút giao), kéo dài lại; cắt chỗ hai tường thẳng hàng chồng đầu nhau → không có tường đè. 6. Tạo tường theo wall type gán cho chiều dày CAD (IN[2]), chân / đỉnh theo level, Location Line = Core Centerline (lõi tường trùng hai nét CAD, lớp trát chia đều hai bên). Chiều dày CAD = chiều dày LÕI (nét A-Wall là mặt thô; nét trát nằm ở layer khác). Type trong IN[2] chưa có → nhân bản type mẫu IN[3], đổi lõi = chiều dày CAD. Chiều dày không có trong IN[2] chỉ báo cáo. Bỏ qua tường chồng lên tường đã có."""
__title__ = "Tường\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
