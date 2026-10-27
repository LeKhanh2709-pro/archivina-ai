#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo ống gió chữ nhật (Duct) từ mặt bằng thông gió (DWG đã Link vào Revit). Đọc từ BẢN SAO DWG qua AutoCAD Core Console (chữ trong bản link Revit không đọc được): - Nổ (explode) mọi block trên bản sao; nét ở layer 0 trong block nhận layer của block cha (như AutoCAD hiển thị); toạ độ LWPOLYLINE đổi OCS → WCS (block mirror). - Ống: thành ống là cặp nét thẳng song song trên layer IN[1] (LINE / cạnh thẳng LWPOLYLINE). Đoạn thẳng hàng nối nhau qua mặt bích (khe ≤ 60 mm) được gộp. Mỗi thành ống ghép với nét song song gần nhất theo từng khoảng dọc tuyến → tim ống + bề rộng W. - Lọc: ống thật phải có ≥ 1 vạch ngang (mặt bích / đầu ống) dài ≈ W nối hai thành; cặp có tim nằm trong ống dài hơn (cặp vạch mặt bích, nét trong quạt / van) bị loại. - Phụ kiện (theo Routing Preferences của duct type): ghép cặp đầu ống cùng layer, gần nhất trước – thẳng hàng khe ≤ 3 m (chỗ van / đổi tiết diện) → nối liền, cùng cỡ đặt bích, khác cỡ đặt côn (lệch tâm ≤ |ΔW|/2 + 30 mm); trục giao nhau → cút; 2 đầu thẳng hàng + 1 đầu vuông góc → tê (không được thì nối thẳng ống chính + chân rẽ); đầu ống đâm vào thân ống khác → chân rẽ. Khác cao độ → đầu ống cao hơn (nhánh với tê) hạ bằng đoạn dốc ≈ 45° + 2 cút. Mỗi mối nối một SubTransaction; lỗi → hoàn tác, ghi log. - Kích thước + cao độ: chữ "WxH ... BOD: FL+2.300" trên layer IN[3]; gán cho ống gần nhất có cạnh khớp W (±15 mm, ≤ 6 m); ống chưa có chữ nhận theo ống cùng layer, cùng W nối liền (qua cút/côn); tuyến dài ≥ 3 m tìm chữ trong 15 m. Bỏ chữ của thiết bị (SAG, EAG, PAG, OBD, MFD, PRD, TA, NRD…). Ống không có chữ / không có BOD → không dựng, ghi log để vẽ tay. - Cao độ: đáy ống = Level IN[4] + BOD + IN[6]; tâm ống = đáy + H/2."""
__title__ = "Ống gió\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
