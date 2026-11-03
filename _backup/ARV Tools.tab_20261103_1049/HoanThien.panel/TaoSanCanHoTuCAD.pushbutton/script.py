#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo sàn hoàn thiện kiến trúc (Floor) cho phòng ngủ, phòng khách, WC, logia của các căn hộ trên level của view mặt bằng đang mở, lấy thông tin từ bản CAD mặt bằng đã Link (không cần đường bo phòng / hatch trong CAD): 1. Căn hộ  = polyline kín layer IN[1] (mặc định "00 do dt", > 20 m²); tên căn = TEXT/MTEXT layer IN[2] khớp mẫu IN[3] (mặc định CH01…), gán cho polyline gần nhất. Chữ đọc từ bản sao DWG qua AutoCAD Core Console. 2. Biên sàn = mặt hoàn thiện tường Revit (tường thẳng, tường liền qua ô cửa): vùng bao các căn trừ khối tường (dài tới mặt tường nối ở hai đầu) và trừ cột CAD layer IN[4] nới thêm IN[5] mm (lớp trát, mặc định 15) → tách thành các vùng rời. Vùng kín nằm trong căn giữ nguyên; vùng hở (logia không có tường lan can, sảnh hở ra hành lang, phía ngoài nhà) cắt theo polyline căn. 3. Loại phòng: có điểm dò cửa ra logia (family chứa IN[6], dò IN[7] mm về phía Facing) → LOGIA; có ≥ 5 điểm nét thiết bị CAD layer IN[8] → WC (> 10 m² → chỉ báo "KIỂM TRA", không tạo); vùng hở ≤ 6 m² (không có tường Revit bao kín, VD logia giặt có máy giặt, cửa đi mở quay) → LOGIA; còn lại → phòng khô (lớn nhất căn = khách, ≥ 6 m² = ngủ, nhỏ hơn = sảnh / kho). Phòng khô dùng chung một floor type. 4. WC lùi biên thêm IN[11] = 10 mm khỏi mặt trát (= dày gạch ốp, KTS chốt 2026-10-20). Tường ốp mỏng < 30 mm (VD "GO-Gạch ốp-300x600" 10 mm) không làm biên sàn → biên WC trùng mặt gạch ốp. 5. Floor type / cao độ mặt sàn theo loại (IN[9], IN[10]). Bỏ qua vùng < 0,5 m² (hộp kỹ thuật) và dải mảnh rộng TB < 300 mm. Bỏ qua phòng đã có sàn tạo bởi tool này. Comments = "ARV-SanCanHo <căn> <loại>"."""
__title__ = "Sàn căn hộ\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
