#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Trát gờ logia 3 mặt (mặt trong phía logia, mặt trên, mặt ngoài) cho gờ do tool gờ logia tạo (Comments "ARV-GoLogia"): 1. Phạm vi: phần tử đang chọn / Id ở IN[3]; không chọn gì → mọi gờ (Wall, Comments bắt đầu bằng IN[2]) trên level của view mặt bằng đang mở; view khác (3D, mặt cắt…) → mọi gờ trong mô hình. Chỉ gờ thẳng. 2. Mặt bên: tường trát (wall type MATBEN, VD "WA_M15" 15 mm) áp sát mặt bên gờ, dài bằng gờ, đỉnh = đỉnh gờ + dày trát (bọc mép lớp trát trên). Chân trát mặt trong = chân gờ + IN[1] (mặc định 50 = dày sàn logia, không chồng sàn đã có); chân trát mặt ngoài = chân gờ + IN[5]. 3. Phía logia: mặt bên có sàn logia của tool 06 (Comments "ARV-SanCanHo … LOGIA") cách mặt gờ ≤ 100 mm. Không xác định được → bỏ qua gờ đó, báo. 4. Mặt trên: Floor dày = dày trát (type MATTREN), phủ đỉnh gờ + hai lớp trát bên, mặt = đỉnh gờ + dày trát. Type chưa có → khi chạy thật nhân bản một floor type có sẵn, gán 1 lớp (Structure) dày = dày trát, vật liệu = vật liệu lớp của wall type MATBEN (cùng vật liệu trát). 5. Phần tử tạo: không Room Bounding (tường), không tự nối đầu, Comments "ARV-TratGoLogia <Id gờ>". Gờ đã có trát của tool → bỏ qua (xoá để làm lại)."""
__title__ = "Trát gờ logia"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
