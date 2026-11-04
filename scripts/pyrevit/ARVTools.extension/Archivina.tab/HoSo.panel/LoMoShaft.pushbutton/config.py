#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo lỗ mở bằng MỘT Shaft Opening cho mọi trục / hộp kỹ thuật trên mặt bằng tầng đang mở của Revit (mỗi ô là một vòng biên trong sketch, như mẫu người dùng vẽ 2026-10-28: 1 lệnh shaft để dễ kiểm soát). Nhận trục / hộp đúng theo quy tắc của công cụ Ngăn cháy lan (dùng chung hàm tim_truc): tên room HKT → shaft opening → ống đứng → hình học (ô / khe kín giữa tường không cửa đi, cửa sổ, thiết bị, sàn hoàn thiện); loại thang máy / thang bộ. - Biên lỗ mở = mép tường thô (dải lõi tường), không bo vào lớp trát / hoàn thiện (người dùng chốt 2026-10-28) - Base Constraint = Top Constraint = level của mặt bằng đang mở; Base Offset -100 mm, Top Offset 1500 mm (mặc định, người dùng chốt 2026-10-28) - Tầng đã có shaft lỗ mở cục bộ (Base và Top cùng là level đó) thì thêm vòng vào shaft đó (shaft nhiều vòng nhất), chưa có thì tạo 1 shaft mới. Ô đã có vòng lỗ mở thì bỏ qua: bấm lại không tạo trùng, không xoá. - Dấu X nhận biết lỗ mở = 2 Symbolic Line mỗi vòng (người dùng chốt 2026-10-28). API không tạo được Symbolic Line trong file dự án → chép 2 nét X của một shaft MẪU (nét sketch mang line style khác "<Sketch>", người dùng vẽ tay một lần) rồi kéo về 2 đường chéo; vòng đã có trong shaft mà chưa có X cũng được bổ sung. Chưa có mẫu thì báo. - Thêm vòng + dấu X nằm trong 1 lần sửa sketch (1 bước Undo); tạo shaft mới là 1 bước Undo riêng. Dry-run (mặc định) chỉ báo cáo, không sửa mô hình."""
__title__ = "Lỗ mở\nshaft"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
