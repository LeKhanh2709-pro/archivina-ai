#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Dàn trang hồ sơ chi tiết căn hộ theo mẫu CAD CT1-CH02-CTCH (TAOVP / TAOVPWC / TAOVPLG bên ACA), trên level của view mặt bằng đang mở. Căn hộ nhận theo sàn hoàn thiện "ARV-SanCanHo <căn> <loại>" (ARV_TaoSanCanHoTuCAD_v1). 1. Room: mỗi vùng kín (PlanCircuit ≥ 1 m²) nằm trong sàn của căn mà chưa có Room → tạo Room. Tên theo Room mẫu của template: sàn KHO lớn nhất = Phòng khách-ăn (KA), còn lại Phòng ngủ (NG); WC = Vệ sinh; logia lớn nhất = Logia phòng khách (LG1), còn lại Logia phơi đồ (LG2). Number = "<căn>-<mã>", Occupant = căn. KTS soát lại tên phòng sau khi chạy. 2. Sheet CTCH (khung A1, 2 cột + cột ghi chú bên phải), 3 hàng như mẫu FPT P5-04.01: MC 1-1 | MC 2-2 căn hộ (4.6) · MB tường xây, định vị cửa (4.1) | MB trần (4.4) · MB bố trí nội thất (4.2) | MB lát sàn (4.3). MC 1-1 song song trục X, MC 2-2 song song trục Y: một mặt cắt qua tâm logia (vuông góc cạnh dài logia), mặt kia qua tâm WC – KTS kéo lại đường cắt nếu cần. Tỷ lệ chung: lớn nhất trong danh sách IN[1] mà cả 6 view vừa khung (hàng cao theo view thật). Cột phải 592–742: SƠ ĐỒ VỊ TRÍ CĂN HỘ (MB cả tầng VFT 1.1, 1/200–1/1000, sàn của căn tô đỏ bằng override riêng view) + legend ghi chú dùng chung (bảng tường xây / trần / lát sàn: mã = Type Mark như tag, cấu tạo theo các lớp của type, hatch tường theo filled region type có sẵn trùng mẫu cắt vật liệu lõi). 3. Sheet WC: mỗi WC một hàng (tối đa 2) × 3 MB: thiết bị (5.1) · lát sàn (5.2) · trần (5.3); tỷ lệ chung của sheet = lớn nhất trong danh sách IN[2] mà mọi view vừa ô (sheet logia / sheet gộp cũng vậy). 4. Sheet logia: mỗi logia một hàng (tối đa 2) × MB lát sàn + thiết bị (6.1) · MB trần (4.4) · MC 1-1 (6.2). Mặt cắt vuông góc cạnh dài nhất của sàn logia, qua tâm, nhìn về một nửa logia. Căn có đúng 1 WC + 1 logia → gộp chi tiết WC (hàng trên) và logia (hàng dưới) vào MỘT sheet số hiệu WC, tên "CHI TIẾT VỆ SINH, LOGIA CĂN HỘ …" (KTS chốt 2026-10-22). 5. View tạo từ View Family Type của template công ty (tự gắn view template). Tỷ lệ khác tỷ lệ template → chép thông số template vào view rồi bỏ gắn template (KHÔNG sửa view template). 6. Tag: Room (MB nội thất), cửa đi / cửa sổ / louver (MB tường xây, MB thiết bị WC, MB logia), sàn (MB lát sàn, đá chân cửa có đường dẫn), trần (MB trần), thiết bị vệ sinh (MB thiết bị WC). 7. Chưa làm: dim tường / cửa, cao độ, ghi chú vật liệu tường (WF-…) – KTS bổ sung tay hoặc tool sau."""
__title__ = "Dàn trang\ncăn hộ"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
