#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo cửa đi gắn vào tường Revit có sẵn từ mặt bằng DWG đã Link (cửa trong CAD là nét rời / block ẩn danh, nên nhận cửa theo CUNG MỞ CÁNH trên layer cửa): 1. Đọc cung tròn trên layer cửa (IN[1]): bán kính 300–1500 mm, góc quét 30°–100° (cửa vẽ mở 90° hoặc 45°). Tâm cung = bản lề, bán kính = bề rộng cánh. Cung trùng nhau (cùng tâm, cùng bán kính) tính một lần. 2. Tường chủ: tường Revit trên level IN[4] có tim đi qua bản lề (lệch ≤ nửa bề dày tường + 60 mm) và một đầu cung nằm dọc theo tim tường (cánh ở vị trí đóng). Không có → báo cáo, không tạo. 3. Cửa 2 cánh: hai cung trên cùng tường, bản lề hai đầu, cánh đóng gặp nhau giữa ô → chỉ báo cáo (chưa có family 2 cánh). 4. Bề rộng = PHỦ BÌ KHUÔN CỬA CAD (= Width của family; khuôn cách mặt tường ~10 mm nên khe tường lớn hơn 20 mm): khe lỗ tường = đầu mút nét layer IN[2] trong dải bề dày tường gần nhất phía bản lề / phía đối diện; khuôn = nét layer cửa IN[1] trong dải đó, nằm trong khe – từ bản lề lùi về sau và từ đầu cánh tiến ra, lấy mép xa nhất. Làm tròn IN[6] mm. Thiếu đầu tường hoặc khuôn ở một bên → báo cáo, không tạo. 5. Type: type có sẵn của family IN[3] có Width khớp (±IN[6]/2 mm) và Height = IN[7] → dùng; chưa có → nhân bản type mẫu IN[5] thành "DW01_{rộng}X{cao}", đặt Width / Height. 6. Đặt cửa giữa ô (trên tim tường chủ), Sill = 0, lật hướng mở (Facing) và bản lề (Hand) theo cung CAD. Bỏ qua ô đã có cửa (cửa cùng tường, tâm cách ≤ 100 mm); cửa cũ khác bề rộng → báo "SAI RỘNG" kèm Id để xoá."""
__title__ = "Cửa đi\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
