#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Nhân bản từ ARV_TaoLenGo_v1 (không sửa bản gốc) – thêm chia viên len trùng mạch lát sàn logia. Tạo len gạch chân tường logia (Basic Wall mỏng, type có sẵn "LCT-Gạch"), mỗi viên len một đoạn tường: 1. Nguồn biên: sàn hoàn thiện logia (Floor, VD do ARV_TaoSanCanHoTuCAD_v1 tạo – type "SHT-Gach Lat Logia-300x600", Comments "ARV-SanCanHo CHxx LOGIA"). Phạm vi: phần tử đang chọn / Id ở IN[3]; không chọn gì → mọi sàn logia trên level của view đang mở. 2. Kích thước viên: đọc Model pattern của vật liệu lớp mặt floor type (VD "300x600": lưới 0° cách 300, lưới 90° cách 600). Không có pattern 2 lưới vuông góc → dừng. 3. Mạch lát sàn (đã đo trên G19 2026-10-21, 9 tấm sàn logia, khớp 100%): Revit đặt mẫu sàn với trục 0° của pattern SONG SONG CẠNH DÀI NHẤT của biên sàn, mạch đi qua TÂM HỘP BAO của biên (theo hệ trục cạnh dài nhất). → mạch dọc cạnh dài cách đều lưới 90° (600), mạch ngang cách đều lưới 0° (300). Sàn đã Align mẫu bằng tay thì tool không biết – kiểm tra 3D sau khi tạo. 4. Mỗi cạnh biên: bắn tia vuông góc ra ngoài ở giữa chiều cao len, tìm mặt tường / cột Revit trong 60 mm → len áp mặt tường (gồm cả gờ bê tông ARV-GoLogia mặt ngoài logia). Đoạn không có tường → không len. 5. Ngắt len tại cửa đi / cửa lùa: dải dọc tường bằng phủ bì khối cửa, bề ngang = dày tường + 60 mm mỗi bên. 6. Góc: hai đoạn len kề nhau gặp tại giao tim, kéo thêm nửa chiều dày (góc lồi không hở). 7. Chia mỗi đoạn len tại mạch lát sàn cắt ngang nó → mỗi viên một Basic Wall, không tự nối đầu (thấy mạch). Viên vụn < IN[5] ở đầu đoạn (thường là phần kéo góc) gộp vào viên kề. 8. Tường len: không Room Bounding, mặt Exterior quay vào phòng, Comments "ARV-LenGachLogia <Id sàn>". Sàn đã có len của tool → bỏ qua (xoá len cũ để làm lại). Wall type phải có sẵn (template công ty) – tool không tạo / đổi type."""
__title__ = "Len gạch\nlogia"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
