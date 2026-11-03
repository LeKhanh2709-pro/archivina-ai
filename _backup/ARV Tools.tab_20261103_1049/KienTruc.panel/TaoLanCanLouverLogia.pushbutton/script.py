#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo lan can + louver che cục nóng điều hòa cho logia, lấy thông tin từ mặt bằng DWG đã Link (KTS chốt 2026-10-21): 1. Logia = sàn (Floor) trên level IN[9] có tên type chứa IN[2] (VD "SHT-Gach Lat Logia-300x600"), lấy hộp bao. 2. Mặt ngoài logia = cặp nét song song cách nhau 150 mm (± 3) trên layer IN[1], nằm sát cạnh hộp bao logia (≤ 300 mm) và phủ ≥ 50 % cạnh đó. Tuyến lan can = đường giữa cặp nét, dài từ tường đến tường (đầu nét CAD). Nét dài hơn logia (chạy qua phòng bên cạnh) → cắt ở cạnh logia rồi bắt vào đầu tường Revit nằm trên tuyến (≤ 400 mm); không có tường → giữ mép logia, báo "KIỂM TRA ĐẦU". 3. Cục nóng = cụm nét layer IN[6] nằm gọn trong khung IN[7] (dài x rộng, xoay 0/90°) có ≥ IN[8] nét. - Logia không có cục nóng: lan can suốt chiều dài. - Logia có cục nóng: louver (family IN[4], type IN[5], rộng = Width của type) đặt sát đầu tường GẦN cục nóng hơn, lan can = tổng chiều dài − rộng louver (một đoạn). - Lan can còn lại < IN[11] (1200) → bỏ lan can, louver kéo dài hết tuyến (KTS chốt 2026-10-21). Type louver đúng bề rộng (Height như type IN[5]) có sẵn thì dùng, chưa có → nhân bản IN[5] thành "{rộng}X{cao}". 4. Lan can: Railing type IN[3], chân tại level, tuyến trên đường giữa cặp nét. Louver: family không host, điểm chèn ở một đầu, phát triển theo +Hand, Facing quay ra ngoài nhà; đặt xong đo khối đặc theo phương vuông góc tuyến rồi dời cho tâm bề dày lam nằm đúng giữa cặp nét 150 (AV-Lam Thép Logia2: khối 0…80 mm về phía Facing). Chân lan can + louver (KTS chốt 2026-10-21): logia có gờ bê tông (tường Comments "ARV-GoLogia" của ARV_TaoGoLogia_v1) trên cùng tuyến → đặt ở đỉnh gờ (VD +70 so với level); không có gờ → ở cao độ level (0). 5. Phần tử tạo ra có Comments "ARV-LanCanLogia". Chạy lại, trong phạm vi tuyến từng logia: - Lan can / louver có Comments đó mà đúng kế hoạch (đầu tuyến ± 20 mm, louver đúng bề rộng) → giữ; chỉ sai chân (lệch > 2 mm so với đỉnh gờ / level) → nâng / hạ chân tại chỗ (giữ Id, báo "nâng chân"). - Có Comments đó mà sai kế hoạch (VD lan can ngắn của lần chạy trước) → XOÁ rồi tạo lại (báo "thay"). - Không có Comments đó (dựng tay) → không đụng; phần tương ứng bỏ qua, báo "đã có (dựng tay)"."""
__title__ = "Lan can\nlouver logia"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
