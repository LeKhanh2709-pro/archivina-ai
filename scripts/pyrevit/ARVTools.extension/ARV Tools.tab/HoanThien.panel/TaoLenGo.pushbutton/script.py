#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo len gỗ chân tường (Basic Wall mỏng, type có sẵn "LCT-Gỗ") cho phòng khách + phòng ngủ: 1. Nguồn biên: sàn gỗ hoàn thiện (Floor, VD do ARV_TaoSanCanHoTuCAD_v1 tạo – type "SHT-Gỗ Công Nghiệp", Comments "ARV-SanCanHo CHxx KHO"). Phạm vi: phần tử đang chọn / Id ở IN[3]; không chọn gì → mọi sàn gỗ trên level của view đang mở. 2. Mỗi cạnh biên: bắn tia vuông góc ra ngoài ở giữa chiều cao len, tìm mặt tường / cột Revit trong 60 mm → len áp mặt tường, dày bằng type. Đoạn không có tường (lối mở, vách kính) → không len. 3. Ngắt len tại cửa đi: dải dọc tường bằng phủ bì khối cửa (khuôn + nẹp chỉ, đo trên hình học family), bề ngang = dày tường + 60 mm mỗi bên → không len qua ô cửa, không len trong má cửa. 4. Bỏ len sau đồ gỗ bếp: Casework / Furniture / Specialty Equipment / Generic Model có tên family / type chứa chuỗi IN[5] → điểm len cách mặt tường 30 mm vào phòng nằm trong hộp bao (nới 20 mm) thì bỏ. 5. Góc: hai đoạn len kề nhau gặp tại giao tim, kéo thêm nửa chiều dày (góc lồi không hở). 6. Tường len: không Room Bounding, không tự nối đầu, mặt Exterior quay vào phòng, Comments "ARV-LenGo <Id sàn>". Sàn đã có len của tool → bỏ qua (xoá len cũ để làm lại). Wall type phải có sẵn (template công ty) – tool không tạo / đổi type."""
__title__ = "Len\ngỗ"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
