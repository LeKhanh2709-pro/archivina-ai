#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo trần hoàn thiện (Ceiling) cho phòng ngủ, phòng khách, WC, logia của các căn hộ trên level của view mặt bằng / mặt bằng trần đang mở, theo biên các tấm SÀN HOÀN THIỆN đã có (ARV_TaoSanCanHoTuCAD_v1 / ARV_TaoSanHoanThien_v1): 1. Sàn nguồn = Floor trên level có Comments bắt đầu bằng IN[0] (mặc định "ARV-SanCanHo"). Comments dạng "ARV-SanCanHo CH07 KHO" → căn = từ thứ 2, loại = từ cuối (KHO / WC / LOGIA). Loại không đọc được từ Comments → tra theo floor type (IN[1]). 2. Mỗi tấm sàn → một tấm trần cùng biên (kể cả lỗ; WC giữ biên lùi 25 mm khỏi mặt thô như sàn). 3. Ceiling type + cao độ ĐÁY trần so với Level theo loại (IN[2], IN[3]) – KTS chỉnh theo từng dự án. Type ở IN[2] chưa có → nhân bản từ type mẫu IN[4] đúng tên đó (giữ cấu tạo lớp), chỉ khi chạy thật. 4. Bỏ qua tấm sàn đã có trần phía trên (điểm trong sàn nằm dưới mặt đáy một trần cùng level). Comments trần = "ARV-TranCanHo <căn> <loại>". 5. Cảnh báo khi mặt trên trần (đáy + chiều dày type) vượt Level kế trên."""
__title__ = "Trần\ncăn hộ"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
