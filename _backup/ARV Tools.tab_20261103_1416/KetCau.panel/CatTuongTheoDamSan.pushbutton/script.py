#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Cập nhật chiều cao tường kiến trúc theo dầm / sàn phía trên, bỏ phần tường đè lên dầm, sàn: 1. Lấy các tường trên level chân (IN[0]) có tên type chứa chuỗi lọc (IN[1]). 2. Với mỗi tường: tìm sàn (Floors) và dầm (Structural Framing) có khối giao với khối tường. Đáy phần giao = đáy dầm / sàn ngay trên tường. 3. Hạ đỉnh tường về đáy CAO NHẤT trong các dầm / sàn đó (thường là đáy sàn → tường kín tới sàn, không hở). Giữ ràng buộc Top Constraint, chỉ đổi Top Offset (tường "Unconnected" thì đổi Unconnected Height). 4. Dầm / sàn thấp hơn đỉnh mới (dầm cắt ngang, sàn dày) → Join Geometry, dầm / sàn CẮT tường (Switch Join Order nếu tường đang cắt) → phần tường đè lên bị bỏ, khối lượng tường đúng. Dầm / sàn chỉ phủ một phần đỉnh tường (VD dầm vuông góc nằm trên đầu tường) → giữ đỉnh, chỉ cắt phần đè. 5. Dự phòng: Join không cắt được (còn giao sau khi Join) → bỏ Join đó, TÁCH tường tại mặt dầm/sàn: đoạn dưới dầm lấy đỉnh = đáy dầm, đoạn còn lại giữ đỉnh (tường gốc giữ đoạn đầu, đoạn sau là tường mới cùng type/thông số). 6. Kiểm tra lại: đếm cặp tường – dầm/sàn còn đè sau khi cắt (gồm cả tường mới tách). Chạy lại an toàn: tường đã cắt không còn giao → không đổi gì thêm."""
__title__ = "Cắt tường\ntheo dầm sàn"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
