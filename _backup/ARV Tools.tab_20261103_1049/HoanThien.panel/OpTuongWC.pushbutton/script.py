#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo lớp ốp gạch tường WC (Basic Wall mỏng, type "GO-Gạch ốp-…") cao IN[2] tính từ mặt sàn hoàn thiện WC: 1. Nguồn biên WC: sàn hoàn thiện WC (Floor, VD do ARV_TaoSanCanHoTuCAD_v1 tạo – Comments "ARV-SanCanHo CHxx WC") hoặc Room tên WC / vệ sinh (biên "At wall finish"). Phạm vi: phần tử đang chọn / Id ở IN[5]; không chọn gì → mọi WC trên level của view đang mở (ưu tiên sàn; không có sàn WC mới lấy Room). 2. Mỗi cạnh biên: bắn tia vuông góc ra phía ngoài (ở cao 300 trên chân ốp và sát đỉnh ốp) tìm mặt tường / cột Revit → khoảng hở d (sàn WC lùi 10 mm so với mặt tường; Room = 0). Lớp ốp: mặt ngoài áp mặt tường, dày bằng type. Đoạn không có tường ở cả hai cao độ (lối mở, hộp kỹ thuật hở) → không ốp. Ô cửa (có lanh tô) ốp liền rồi nối khối (Join) với tường chủ → cửa đi / cửa sổ tự cắt lớp ốp (đã kiểm: cửa 830 cắt 1,87 m²). 3. Góc: hai lớp ốp kề nhau gặp nhau tại giao tim, kéo thêm nửa chiều dày (không hở góc lồi / cột). 4. Wall type theo kích thước gạch IN[0] + hướng IN[1]: "GO-Gạch ốp-{nhỏ}x{lớn}" (+ "-dọc"). Chưa có → nhân bản type mẫu IN[6], vật liệu "Gạch Ceramic {nhỏ}x{lớn}mm" (+ " dọc") với mẫu Model pattern đúng ô gạch (lưới ngang cách = cao viên, lưới đứng cách = rộng viên; dùng lại pattern có sẵn nếu trùng lưới). 5. Tường ốp: không Room Bounding, không tự nối đầu (DisallowWallJoinAtEnd), Comments "ARV-OpTuongWC <Id nguồn>". WC đã có ốp của tool (tường ốp nằm trong biên WC, không phụ thuộc Id sàn – sàn dựng lại đổi Id) → bỏ qua, hoặc xoá ốp cũ rồi dựng lại khi IN[10] = True (chỉ xoá tường có Comments "ARV-OpTuongWC…"). 6. Căn mạch theo lát sàn (IN[9], thêm 2026-10-21) – đã đo trên G19: - Mạch ĐỨNG của mẫu gạch trên tường bắt đầu từ ĐIỂM ĐẦU đường định vị tường (dời điểm đầu → mạch dời theo, Flip không đổi). Vị trí mạch sàn đo trực tiếp trên mặt sàn WC (Dimension tới đường mạch của Model pattern trên view mặt bằng tạm, rồi hoàn tác) → mỗi đoạn ốp tách đôi tại một mạch sàn, hai nửa cùng bắt đầu từ điểm đó → mạch đứng ốp nối tiếp mạch sàn (bước gạch tường / sàn là bội của nhau thì mọi mạch sàn đều có mạch tường). - Mạch NGANG bắt đầu từ cốt LEVEL chân tường (không theo Base Offset). Sàn WC −15 → dùng Model pattern có gốc lưới ngang dời −15 (Origin V) để hàng gạch đầu tiên bắt đầu từ mặt sàn: type "GO-Gạch ốp-300x600 (mạch -15)". Nguồn là Room (không có sàn) → không căn được mạch đứng, báo cáo."""
__title__ = "Ốp tường\nWC"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
