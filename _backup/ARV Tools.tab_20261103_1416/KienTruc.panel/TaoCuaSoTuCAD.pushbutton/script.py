#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo cửa sổ nhỏ cho phòng ngủ và WC, gắn vào tường Revit có sẵn, từ mặt bằng DWG đã Link: 1. Nét thẳng / polyline trên layer cửa sổ IN[1] (mặc định "A-Window") nằm trong dải bề dày một tường Revit (tường thẳng trên level IN[2], dày ≥ 50 mm) → chiếu lên trục tường, gộp các đoạn chồng / cách ≤ 20 mm thành một ô cửa sổ. Ưu tiên tường song song với nét. Tường Revit đứt tại ô cửa sổ (dựng theo nét tường CAD dừng ở má cửa sổ) → nét vẫn gán cho trục tường đó nếu cách đầu tường ≤ 1500 mm. Bề rộng = độ dài ô (làm tròn IN[8] mm). Ô rộng > IN[3] (mặc định 1500 – cửa sổ lớn W2 cùng layer) hoặc < 300 mm → bỏ qua, ghi vào báo cáo. Nét không gán được cho tường nào → liệt kê vị trí trong báo cáo để soát. 2. Loại phòng: dò Room Revit hai bên tường (cách mặt tường 250 mm, cao Level + 1000 mm). Phía có Room tên chứa IN[4] (mặc định "WC") → family:type IN[5]; tên chứa IN[6] (mặc định "Phòng ngủ") → family:type IN[7]. Phía còn lại là phía ngoài. Không có hoặc cả hai phía đều là phòng cần làm → báo cáo, không tạo. 3. Type: type có sẵn của family có Width khớp (±IN[8]/2) và Height = type mẫu → dùng; chưa có → nhân bản type mẫu, đổi số bề rộng trong tên (VD "SA01-600x1000" → "SA01-800x1000"), đặt Width. Cao độ bệ (Sill Height) đặt theo IN[10] (WC, mặc định 1450) / IN[11] (phòng ngủ, mặc định 450) – người dùng chốt 2026-10-29. Cửa sổ phòng ngủ: đỉnh = IN[12] (mặc định 2800 = đỉnh cửa sổ W2 / đáy dầm, người dùng chốt) → chiều cao = IN[12] − IN[11]; type mang chiều cao này (chưa có thì nhân bản, đổi cả số chiều cao trong tên, VD W1_740X2350). IN[12] = 0 → giữ chiều cao type mẫu. WC giữ chiều cao type mẫu. 4. Tường cùng trục bị chia nhiều đoạn tại ô (Revit xoá cửa sổ có lỗ vượt quá đầu tường chủ): như tool 10, chọn đoạn chứa phần lớn ô làm tường chủ, kéo dài phủ hết ô, cắt ngắn đoạn kế bên tới mép ô (sửa Location Curve, không xoá tường); đoạn nằm trọn trong ô → báo cáo, không tạo. Tường đứt tại ô: kéo dài đoạn gần nhất qua ô; còn hở tới đoạn cùng trục kế tiếp ≤ 300 mm thì kéo tới chạm đoạn đó (tường liền). 5. Đặt cửa sổ giữa ô trên tim tường chủ, lật Facing ra phía ngoài (FACING_TO_OUTSIDE), đặt Sill Height. Ô đã có cửa sổ của family IN[5] / IN[7] → SỬA cửa sổ đó: lật hướng nếu ngược, đặt lại Sill nếu khác, đổi type nếu chiều cao khác (dry-run báo trước); ô đã có cửa sổ / cửa đi khác → bỏ qua. Tường / cửa sổ đang bị người khác mượn → bỏ qua. Sau khi Commit kiểm tra lại cửa sổ vừa tạo; cửa sổ bị Revit xoá → báo trong log."""
__title__ = "Cửa sổ\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
