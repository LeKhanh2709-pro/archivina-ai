#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Bảng thống kê cửa của mặt bằng đang mở (người dùng yêu cầu 2026-11-04: "tạo 1 bảng thống kê các cửa có trong mặt bằng đó, những cửa trùng thì hiện 1 lần"): - Mỗi hạng mục 1 bảng: "THỐNG KÊ CỬA ĐI - <tầng>", "THỐNG KÊ CỬA SỔ - <tầng>" (Revit không gộp được cửa đi + cửa sổ vào 1 bảng: bảng nhiều hạng mục không có cột Rộng / Cao và bộ lọc không có "hoặc" – khảo sát Revit 2027.3). - Cột: Ký hiệu (Type Mark) / Rộng / Cao / Số lượng; KHÔNG liệt kê từng cái (Itemize tắt), gộp theo Type Mark → cửa trùng ký hiệu hiện 1 dòng kèm số lượng; dòng tổng cuối bảng. - Lọc: Level = tầng của mặt bằng, bỏ cửa có Type Comments CHỨA chữ loại trừ (Louver; không phân biệt hoa thường / dấu, vd. "Louver", "LOUVER nhôm", "Cửa đi louver" – người dùng yêu cầu 2026-11-09; bảng Revit dùng bộ lọc "does not contain"). "Filter by sheet" TẮT mặc định (bật thì bảng đặt trên sheet không có mặt bằng sẽ trống – thử 2026-11-04); mặt bằng crop 1 phần tầng thì bật IN[6] rồi đặt bảng lên sheet của mặt bằng đó để bảng chỉ đếm cửa thấy trên sheet. - Bảng cùng tên đã có (bấm lại) thì cập nhật lại cột / lọc / gộp, không tạo trùng, không xoá. Chưa có thì nhân bản bảng cùng hạng mục có sẵn của dự án (giữ kiểu trình bày công ty), không có thì tạo mới. - Đổi tên cửa (người dùng yêu cầu 2026-11-04 tối: "1 bảng hiện ra, có các cửa, tên hiện tại, tên đổi, chiều dài, chiều cao"): nút bật bảng lib/arv_bang_cua.py (mỗi loại cửa thấy trong mặt bằng 1 dòng), người dùng gõ tên mới → IN[7] = JSON {id type: tên mới} → đổi Type Mark của type đó (áp cho mọi cửa cùng type trong dự án). Làm TRƯỚC bảng thống kê để bảng hiện tên mới. IN[8] = có tạo / cập nhật bảng thống kê Revit không. - Báo CẦN XEM LẠI: cửa chưa có Type Mark, cùng Type Mark mà khác kích thước (Revit để trống ô), số cửa thấy trong mặt bằng khác số cửa của tầng. Dry-run chỉ báo cáo, không sửa mô hình."""
__title__ = "Thống kê\ncửa"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
