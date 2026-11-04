#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Nhân bản từ 0.8 ARV_TaoLenGachLogia_v1 (không sửa bản gốc) – mở rộng cho mọi loại sàn của tool 06. Tạo len chân tường (Basic Wall mỏng, wall type có sẵn theo từng loại sàn), cho sàn do ARV_TaoSanCanHoTuCAD_v1 tạo: 1. Nguồn biên: Floor có Comments "ARV-SanCanHo <căn> <loại>" với <loại> trong IN[2] (mặc định KHO;LOGIA;HANHLANG). Ô cửa (…-CUA) và đá chân cửa (CHANCUA) không làm len. Phạm vi: phần tử đang chọn / Id ở IN[3]; không chọn gì → mọi sàn đúng loại trên level của view đang mở. 2. Wall type len theo loại (IN[4]): "KHO=…;LOGIA=…;HANHLANG=…;MAU=…" (một tên không có "=" → mọi loại). Len đồng bộ vật liệu sàn (KTS chốt 2026-10-29): type đã có → dùng nguyên; type chưa có → khi chạy thật nhân bản từ type mẫu MAU (giữ bề dày) và gán vật liệu lớp mặt (Finish) của floor type loại đó cho mọi lớp (VD sàn gỗ → len gỗ cùng vật liệu). Dày ≤ 40 mm. 3. Sàn có Model pattern 2 lưới vuông góc ở lớp mặt (gạch) → chia viên len trùng mạch lát (quy luật mạch như tool 0.8: trục 0° song song cạnh dài nhất, mạch qua tâm hộp bao). Không có lưới (VD sàn gỗ) → len liền. 4. Mỗi cạnh biên: bắn tia vuông góc ra ngoài ở giữa chiều cao len, tìm mặt tường / cột Revit trong 60 mm → len áp mặt tường. Đoạn không có tường (lan can, lối mở) → không len. 5. Ngắt len tại cửa đi / cửa lùa: dải dọc tường bằng phủ bì khối cửa, bề ngang = dày tường + 60 mm mỗi bên. 6. Góc: hai đoạn len kề nhau gặp tại giao tim, kéo thêm nửa chiều dày (góc lồi không hở). 7. Viên vụn < IN[5] ở đầu đoạn gộp vào viên kề (chỉ khi chia viên). 8. Tường len: không Room Bounding, mặt Exterior quay vào phòng, Comments "ARV-LenChanTuong <Id sàn>". Sàn đã có len của tool → bỏ qua (xoá len cũ để làm lại)."""
__title__ = "Len chân tường"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
