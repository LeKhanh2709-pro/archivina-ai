#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Hatch ngăn cháy lan trục / hộp kỹ thuật (Filled Region 2D) trên view mặt bằng chống cháy lan của Revit. Thể hiện theo skill CAD ngan-chay-truc-hkt: lưới NET 125 mm xoay 45° màu 220,30,30, viền tím (màu 6), chỉ hatch trong lòng ô. - Vùng = khoảng trống khép kín giữa tường / cột trên level của view: quét lưới 20 mm theo DẢI LÕI của tường (mép tường thô theo cấu tạo lớp của kiểu tường, bỏ lớp trát / hoàn thiện và tường ốp mỏng), lưới xoay theo phương chính của tường → bắt được cả khe hộp gen hẹp ~120 mm mà room của Revit không bắt được. Biên = mép tường thô trong lòng ô, sai số ≤ 1 ô lưới (người dùng chốt 2026-10-28: trong hộp kỹ thuật không có lớp trát, không bao giờ bo vào mặt hoàn thiện). Tường cong / không có cấu tạo lớp: lấy mặt đáy khối. Chỉ đọc. - Nhận trục / hộp kỹ thuật theo thứ tự bằng chứng: a) tên room có từ khoá (HKT, hộp kỹ thuật, trục kỹ thuật, shaft…) hoặc chứa Shaft Opening b) chứa ống / ống gió / ống luồn dây đi đứng, ô không có cửa đi và thiết bị vệ sinh c) không có ống, dấu X trong model (như G19): ô / khe kín KHÔNG có cửa đi, cửa sổ, thiết bị vệ sinh, sàn hoàn thiện, diện tích ≤ ngưỡng (mặc định 3 m2: ô 1770 x 2520 ở hành lang G19 không phải trục), bề rộng lòng ≥ ngưỡng - Loại: ô chứa thang máy / thang bộ (tên family / type / room có từ khoá loại trừ) - Ô lớn hơn 1400 x 1400 mm vẫn hatch nhưng liệt kê riêng để xem lại (như bản CAD) - Kiểu Filled Region + mẫu lưới + line style viền chưa có thì tự tạo; Filled Region gom group "ARV_NganChay" - Ẩn thiết bị vệ sinh / nội thất trong view (Hide in View từng đối tượng, không sửa template) - Bấm lại: ô đã có hatch cùng kiểu thì bỏ qua, không vẽ trùng, không xoá gì Dry-run (mặc định) chỉ báo cáo, không sửa mô hình."""
__title__ = "Ngăn\ncháy lan"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
