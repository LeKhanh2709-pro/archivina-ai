#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt máy giặt (Furniture) ở logia từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool lavabo (không cần tên block): 1. Máy giặt trên CAD (đo trên G19 TẦNG 3 2026-10-30, DWG TDH_LINK-REVIT: 17 block "X-U-2PN-7$0$May giat" layer A-Nội thất, nét layer 0, mỗi căn một máy, đều ở logia LG1) = HÌNH VUÔNG 650 × 650 chứa VÒNG TRÒN lồng giặt R 171 và một NÉT DẢI song song một cạnh, cách cạnh đó 138 mm. Cả 17 máy: dải ở phía RA PHÒNG, cạnh đối diện sát tường → hướng mặt trước = từ tâm ra phía nét dải. Không thấy nét dải → lấy cạnh gần biên Room nhất làm lưng, báo "cần soát". Nét vào Revit (file chẩn đoán 2026-10-31 09:10): hình vuông = PolyLine 9 đỉnh đi hai vòng, nét dải + nét chéo = PolyLine 3 đỉnh, lồng giặt = Arc không giới hạn R 171, layer A-Nội thất. Vì vậy hình vuông ghép từ cạnh, không chỉ từ vòng kín; nhận khi có lồng giặt HOẶC nét dải. Dry-run ghi file CHANDOAN (mọi nét trong logia + tên block). IN[1] trống = dò mọi layer, kể cả nét Revit không trả tên layer; có chuỗi = chỉ layer chứa chuỗi đó. Block tên chứa "may giat" cũng được đọc. 2. Room chứa tâm máy phải có tên chứa một chuỗi trong IN[4] (mặc định "logia;lô gia"; trống = mọi phòng). 3. Lưng máy áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit trên level, cách lưng CAD ≤ IN[7]. Tính cả len chân tường tool 11 (`WF_03_10…` dày 10, cao 100, nằm trước biên Room): bản đầu bỏ qua nên máy ăn vào len 10 mm (người dùng báo 2026-10-31). Không có mặt nào → giữ theo CAD, báo "cần soát". 4. Dọc tường: CAD rộng 650, family rộng 600 → có tường bên (cả len) cách cạnh CAD ≤ IN[8] thì máy áp tường bên (như lavabo góc); hai bên đều có thì đặt giữa; không có thì giữ tâm CAD. 5. Cao độ: máy đứng trên MẶT SÀN LOGIA, không phải trên level (G19: sàn Comments "ARV-SanCanHo CAN-02 LOGIA", đỉnh = level + 50). Elevation from Level = đỉnh sàn logia tại vị trí máy − level; không có sàn → 0, báo "cần soát". 6. Type: chọn ở IN[3], mặc định "AV_FT_may giat1 : AV_FT_may giat 2" (Furniture 3D, đặt theo level, khung −300,3…300,3 × −600…0, cao 900: gốc ở giữa mép lưng, mặt trước về −Y → FacingOrientation chỉ VÀO TƯỜNG). Quay ngược → IN[9] = True. Căn theo khung type (dùng được cả family 2.5D không có khối đặc); dry-run cũng đặt thử rồi hoàn tác. Comments = "ARV-TaoMayGiatTuCAD". Máy của tool đã có mà lệch / sai hướng / sai cao độ / khác type → sửa tại chỗ; máy cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Máy giặt\nlogia"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
