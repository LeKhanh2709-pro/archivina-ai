#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo cửa sổ và cửa lùa (ra logia) gắn vào tường Revit có sẵn từ mặt bằng DWG đã Link. Tường Revit phải LIỀN qua ô cửa (VD dựng bằng ARV_TaoTuongTuCAD_v1). Ô cửa nhận theo cụm nét nằm TRONG DẢI BỀ DÀY tường chủ: 1. Tường chủ = tường thẳng Revit trên level IN[5]. Nét CAD (line / polyline) trên layer cửa sổ IN[1], cửa lùa IN[2], chỉ báo cáo IN[3] mà mọi đỉnh nằm trong dải bề dày tường (± nửa dày + 30 mm) → gom theo toạ độ dọc tường (khe ≤ 60 mm nối cụm). Cụm dài < 300 mm bỏ qua (khuôn cửa đi mở quay). Cụm có cung cửa (tâm trong dải) → cửa đi mở quay, bỏ qua (dùng ARV_TaoCuaTuCAD_v1). 2. Bề rộng ô = phủ bì cụm nét (khuôn CAD lấp kín khe tường thô), làm tròn IN[16] mm. Khe tường A-Wall chỉ ghi log. 3. Phía ngoài / logia: bắn tia vuông góc tường từ tâm ô về hai phía, phía gặp tường Revit đầu tiên XA hơn là phía ngoài (logia không có tường Revit lan can; cửa sổ nhìn ra sân trong gặp khối đối diện xa hơn phòng). Hai phía chênh < 500 mm → báo "KIỂM TRA HƯỚNG", vẫn tạo theo phía xa hơn. 4. Cửa sổ: rộng ≥ IN[10] → family IN[6] (type mẫu IN[7]); nhỏ hơn → family IN[8] (type mẫu IN[9]). Type có Width = rộng và Height = IN[11] → dùng; chưa có → nhân bản type mẫu, tên theo mẫu "<tiền tố>{rộng}x{cao}". Sill = IN[12]. Facing → phía ngoài. Hand giữ mặc định (CAD không thể hiện cánh lật). 5. Cửa lùa: family IN[13], type có Width = khe − IN[15] và Height = Height của type mẫu IN[14] → dùng; chưa có → nhân bản type mẫu, tên "<tiền tố>{khe}X<cao trong tên mẫu>". Sill 0. Facing → logia. Hand theo CAD: cánh vẽ phía logia nằm bên nào của ô thì cánh phía Facing của family nằm bên đó (DA01: cánh phía Facing ở phía +Hand). 6. Sau khi lật, đo khối đặc của cửa dọc tường rồi dời cửa cho tâm khối trùng tâm ô (SA01 có điểm chèn lệch tâm). Ô đã có cửa sổ / cửa đi (gắn vào bất kỳ tường nào, kể cả lớp ốp: tâm khối cửa nằm trong dải bề dày tường chủ + 100 mm và cách tâm ô ≤ max(100 mm, nửa bề rộng ô)) → bỏ qua; khác bề rộng → báo "SAI RỘNG" kèm Id. Tường dày < 30 mm (lớp ốp / hoàn thiện, VD "GO-Gạch ốp-300x600" 10 mm) không làm tường chủ: cửa đặt vào lớp ốp bị Revit xoá ("Can't cut instance out of Wall")."""
__title__ = "Cửa sổ\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
