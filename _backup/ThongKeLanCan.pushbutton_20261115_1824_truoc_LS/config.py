#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Thống kê lan can, louver của mặt bằng đang mở (người dùng yêu cầu 2026-11-05: "tạo thống kê lan can louver như cửa"): - Tên = MARK của từng đối tượng (không phải Type Mark như cửa). Nút bật bảng lib/arv_bang_lan_can.py, người dùng gõ tên mới → IN[7] = JSON [{"ids": [...], "moi": "LK-01", "cu": ..., "nhan": ...}] → đặt Mark cho các đối tượng đó. - Mỗi lớp 1 bảng: "BẢNG THỐNG KÊ LAN CAN <TẦNG>" (Railings), "BẢNG THỐNG KÊ LOUVER <TẦNG>" (hạng mục có nhiều louver nhất trong view: Windows / Generic Models). Cùng tên với bảng của nút Định vị lan can, louver nên bảng đã đặt trên sheet được cập nhật theo, không tạo trùng, không xoá. - Cột như bảng cửa: Tên / Chiều dài (lan can: Tổng chiều dài) / Chiều cao / Số lượng; KHÔNG liệt kê từng cái, gộp theo Mark → trùng tên hiện 1 dòng; dòng TỔNG cuối bảng. - Lọc: Level = tầng của mặt bằng + Mark bắt đầu bằng tiền tố đang dùng (bộ lọc Revit không có "hoặc": dùng cả LK và LC thì lọc "Mark có giá trị"). Chưa có Mark đúng tiền tố thì không vào bảng, báo CẦN XEM LẠI. - Chưa có bảng cùng tên thì nhân bản bảng cùng hạng mục có sẵn (ưu tiên tên có "thống kê", giữ kiểu trình bày công ty), không có thì tạo mới. Bảng cùng tên khác hạng mục thì báo, không đụng. Dry-run chỉ báo cáo, không sửa mô hình."""
__title__ = "Thống kê\nlan can, louver"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
