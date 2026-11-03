#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo sàn hoàn thiện (Floor) cho từng CĂN HỘ theo bản CAD mặt bằng lát sàn đã Link (chuẩn CAD công ty): 1. Đọc bản sao DWG qua AutoCAD Core Console (model space + block lồng nhau): - polyline kín layer bo phòng (IN[2], mặc định "A-duong bo phong") = biên sàn hoàn thiện từng phòng; - polyline kín layer căn hộ (IN[3], mặc định "A-Area") = phạm vi căn; - hatch layer lát sàn (IN[4], mặc định "A-Hoan thien san"): mẫu hatch → loại phòng (IN[5]), hatch AR-CONC = đá chân cửa FP-06 (cửa WC, cửa vào căn). 2. Phạm vi: phần tử đang chọn trong Revit (hoặc Id ở IN[1]) – thường chọn CỬA VÀO CĂN. Căn = polyline IN[3] chứa phía trong cửa (hoặc chứa điểm của phần tử). Không có layer căn → lan từ phòng chứa điểm qua các cửa Revit, không đi qua cửa vào căn (IN[8]). 3. Mỗi phòng một tấm sàn: type + cao độ theo loại (IN[6], IN[7]; mặc định khô 0 / WC −15 / logia −30). Phòng không có hatch trong IN[5] → "chưa rõ loại", không tạo. 4. Ô cửa (đo trên hình khối tường Revit, không theo tham số family): - hai bên đều phòng khô (cửa phòng ngủ) → sàn mỗi bên kéo vào ô cửa tới tim tường; - một bên logia, một bên phòng khô       → sàn trong nhà phủ hết ô tường, sàn logia dừng ở bo phòng; - cửa WC / cửa vào căn                    → không kéo sàn; tấm đá chân cửa lấy theo hatch AR-CONC của CAD (thiếu hatch → báo "thiếu đá chân cửa"). 5. Bỏ qua phòng / ô đá đã có sàn (cùng level). Comments = "ARV-SanHoanThien"."""
__title__ = "Sàn hoàn thiện\n(có hatch)"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
