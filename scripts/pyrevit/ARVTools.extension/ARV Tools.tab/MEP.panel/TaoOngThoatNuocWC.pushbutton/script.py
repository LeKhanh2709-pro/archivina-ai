#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Dựng ống thoát nước WC (uPVC) theo TUYẾN ĐÃ DUYỆT nhập dạng toạ độ – không đọc CAD: - Ống đứng (IN[1]): xí / rửa / thông hơi trong HKT, từ level + IN[2] (dưới) tới level + IN[2] (trên), cắt tại chỗ nhánh vào, đặt tê u.PVC_BEND TEE 90 (rule Junctions của pipe type). - Tuyến nhánh (IN[0]): polyline mặt bằng x,y (mm, toạ độ Revit của mô hình đang mở), điểm cuối là tâm một ống đứng hoặc một đỉnh của tuyến khác (→ Y 45°, tuyến kia phải đi thẳng qua đỉnh đó). Đầu tuyến: '@' = ống xuống từ connector Sanitary của thiết bị (kể cả trong file link) gần điểm đầu ≤ 150 mm; số = cao độ (mm so với level) đỉnh ống xuống tại điểm đầu; 'PHEU=-15' = đặt phễu thu IN[8] tại điểm đầu, chân ở cao độ −15, ống nối vào connector phễu; 'PHEUD=-15' = phễu ĐẤU TỪ TRÊN XUỐNG: tuyến 2 điểm "phễu;điểm Y", phễu nằm ngay trên ống chính, thượng lưu điểm Y ≥ 137 mm – ống xuống → co 45° → nhánh nghiêng 45° theo phương đứng vào Y (cho phễu đặt sát góc tường, KTS 2026-10-21); 'TT' = thông tắc: nút bịt (Caps của pipe type) ở điểm đầu; trống = không có ống xuống. - Cao độ: dốc IN[4] % về ống đứng; điểm cao nhất của mỗi cây nhánh có tâm ống = level − IN[3]. - Co 45° / 90° bằng NewElbowFitting (rule Elbows); Y / tê đặt thủ công, mỗi phụ kiện một SubTransaction. Không nối được với thiết bị trong file link (Revit không cho) → đầu ống đặt trùng connector thiết bị."""
__title__ = "Ống thoát\nnước WC"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
