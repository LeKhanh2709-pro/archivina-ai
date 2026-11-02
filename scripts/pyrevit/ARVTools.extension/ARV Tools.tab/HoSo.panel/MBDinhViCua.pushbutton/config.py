#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo mặt bằng định vị cửa từ mặt bằng đang mở (người dùng yêu cầu 2026-11-02, mẫu theo ảnh mặt bằng chống cháy lan): - Nhân bản view mặt bằng gốc (Duplicate, KHÔNG kèm chú thích / filled region), đặt tên theo mẫu IN[5] (vd. "MẶT BẰNG ĐỊNH VỊ CỬA - Tầng 1"). View tên đó đã có thì không tạo thêm, chỉ mở view đó. - Gán view template IN[1] ("MẶT BẰNG ĐỊNH VỊ CỬA"). Template đã có trong dự án thì dùng nguyên, KHÔNG sửa (giữ phần người dùng đã chỉnh tay). Chưa có thì tạo: lấy template nền (mặc định template của view gốc, tức đồ hoạ người dùng đang thấy; IN[2] có từ khoá thì lấy template mặt bằng có chữ đó, ưu tiên cùng tỉ lệ), rồi + tường, sàn: Halftone (xám như ảnh mẫu); sàn: tắt mẫu tô bề mặt (nền trắng); + cửa đi, cửa sổ: bỏ Halftone (nét đậm để định vị cửa, IN[8]); + ẩn nội thất / thiết bị vệ sinh (IN[4]) để công cụ Tag cửa không phải tạo template "(ẩn nội thất)"; + bật hiện cửa đi, cửa sổ, tag cửa đi, tag cửa sổ. API không nhân bản được view template → áp một lần template nền vào view mới (ApplyViewTemplateParameters) rồi CreateViewTemplate. (CreateViewTemplate lấy thiết lập riêng của view, KHÔNG theo template đang gán.) - Không xoá, không sửa view gốc, không sửa template nền."""
__title__ = "MB định\nvị cửa"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
