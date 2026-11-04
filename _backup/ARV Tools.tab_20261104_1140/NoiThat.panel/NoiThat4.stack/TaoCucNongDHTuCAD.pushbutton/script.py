#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt cục nóng điều hòa (Mechanical Equipment) ở logia từ mặt bằng DWG đã Link, cùng khuôn với tool 19 máy giặt: 1. Cục nóng trên CAD (đo trên G19 TẦNG 3 2026-10-31, DWG TDH_LINK-REVIT: 17 block "Mini-VRF - 4-6HP (12.0-16.0kW) 1250" layer AUDIT_D_260526144445-144, mỗi căn một cục ở logia LG1) = HÌNH CHỮ NHẬT 1100 × 500 chứa MŨI TÊN hướng thổi. Revit gộp nét block vào một GeometryInstance nên không dùng tên block; nét layer 0 vào Revit mang layer của block (file chẩn đoán 2026-10-31 09:36: hình chữ nhật = PolyLine 5 đỉnh khép kín). IN[1] có chuỗi = chỉ layer chứa chuỗi đó; trống = dò mọi layer, chỉ nhận hình có mũi tên. 2. Hướng: mặt trước = hướng mũi tên trên CAD, cạnh dài đối diện là lưng. Mũi tên trên CAD không đồng nhất giữa các căn (có căn thổi ra lan can, có căn thổi vào logia, CH10 thổi vào tường cuối logia): giữ theo CAD, thổi vào tường thì báo "cần soát". Không thấy mũi tên → cạnh dài gần tường / biên Room nhất làm lưng, báo "cần soát". 3. Room chứa tâm cục nóng phải có tên chứa một chuỗi trong IN[4] (mặc định "logia;lô gia"; trống = mọi phòng). 4. Lưng áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit ngang tầm cục nóng (len chân tường, tường thấp dưới đáy cục không tính), cách lưng CAD ≤ IN[7]. Mặc định 50, nhỏ hơn máy giặt: CAD cố ý để hở 100 mm ở vài căn (CH05, 08, 09, 13), snap xa hơn sẽ dời sai. Không có mặt nào → giữ theo CAD (cục đứng tự do sau lưng, không phải lỗi). 5. Dọc tường: có mặt bên cách cạnh CAD ≤ IN[8] thì áp mặt đó; hai bên đều có thì đặt giữa; không có thì giữ tâm CAD. Hốc hẹp hơn 1100 (CH01, 04, 14, 17: 1085; CH10: 1035) → đặt giữa hoặc áp mặt bên có tường, khung type lấn ra ngoài, báo "lòi khỏi Room". 6. Cao độ: Elevation from Level = IN[11] (mặc định 1500 mm so với LEVEL, không phải so với sàn logia), mọi cục như nhau. 7. Type: chọn ở IN[3], mặc định "AV_MT_cuc nong dieu hoa loai dai1 : AV_Cuc nong DH 3" (Mechanical Equipment, đặt theo level, khung −550…550 × −476…0, cao 880). Giả định gốc ở giữa mép lưng, mặt trước về −Y như family máy giặt, chưa xem được hình family: quay ngược → IN[9] = True. Comments = "ARV-TaoCucNongDHTuCAD". Cục của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; cục cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Cục nóng điều hoà"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
