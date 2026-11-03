#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Vẽ đường bao sàn kết cấu (Detail Line) và tạo sàn (Floor) theo vùng hatch của ghi chú, từ mặt bằng kết cấu sàn (DWG đã Link vào Revit). Đường bao vẽ (Detail Line, trong view mặt bằng đang mở): - BAO NGOÀI: mép ngoài cùng của mặt bằng (mép ngoài dầm biên / mép sàn) – bỏ mọi nét bên trong. - BAO LỖ MỞ: quanh từng lỗ mở có gạch chéo X (hai ô lỗ chung cạnh gộp một). - BAO VÙNG HATCH: quanh từng vùng hatch có trong ghi chú (VD ANSI31 = sàn DƯL dày 230). Nét chung giữa các đường bao chỉ vẽ một lần. Sàn tạo (Floor kết cấu, level của view): - Mỗi vùng hatch một tấm sàn, chiều dày / hạ cốt theo ghi chú (IN[4]). - Sàn nền (phần không hatch, IN[5]) = bao ngoài − lỗ mở − vùng hatch (khoét, không chồng khối lượng). - Type sàn: dùng type có sẵn đúng chiều dày (ưu tiên tên FLOOR_TYPE_NAME); chưa có → nhân bản type mẫu (IN[6]) và chỉnh lớp kết cấu cho đúng chiều dày. Cách dò: - Nét trên layer mép sàn (mặc định S-Thay + S-Cot vach) tách tại giao điểm, dò ô kín nhỏ nhất. Bao ngoài = biên ngoài của cụm nét không nằm lọt trong ô nào. Lỗ mở = ô chứa tâm dấu X. - Hatch không đọc được trong bản link Revit nên được đọc từ BẢN SAO file DWG qua AutoCAD Core Console (model space + trong block lồng nhau). Biên hatch được hút về nét mép sàn gần nhất (≤ HATCH_SNAP_MM), rồi chia mặt bằng thành ô: ô trong lỗ mở → lỗ; ô trong hatch có ghi chú → vùng đó; còn lại → sàn nền."""
__title__ = "Bao sàn\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
