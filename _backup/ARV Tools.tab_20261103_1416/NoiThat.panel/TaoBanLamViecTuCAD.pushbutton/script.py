#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Đặt bàn làm việc (Furniture 2D) trong phòng ngủ từ mặt bằng DWG đã Link, NHẬN DIỆN THEO HÌNH DẠNG như tool 22, 23 (Revit gộp nét block vào một GeometryInstance nên không dùng tên block). Tách từ phần bàn của tool 21. 1. Bàn trên CAD, layer A-Nội thất = hình chữ nhật sâu 450…650, dài 800…1700 có ghế cách cạnh dài ≤ 200 mm (lục giác 400 trên CAD, vào Revit tách thành chữ U 400 × 300 + nét rời). Lưng = cạnh dài đối diện ghế. Giường, tủ đầu giường, tủ áo chỉ nhận diện để bàn nhường chỗ. 2. Room chứa tâm bàn phải có tên chứa một chuỗi trong IN[4] (mặc định "phòng ngủ"). Báo cáo liệt kê phòng lọc mà không có bàn. 3. Vị trí: lưng áp mặt nhô ra phòng nhất trong biên Room (Finish) và mặt tường Revit (cả len chân tường tool 11), cách lưng CAD ≤ IN[5]; không có → giữ theo CAD, báo "cần soát". Hai đầu bàn cách tường bên ≤ IN[6] thì kéo cho chạm tường. 4. TỦ ĐẦU GIƯỜNG ĐÈ BÀN: tủ chồng lên bàn ≥ DROP_MM mỗi chiều là vị trí tool 23 đã bỏ; bàn giữ nguyên ở đó, không bị cắt theo tủ. Báo cáo đối chiếu từng vị trí với bàn đã căn; vị trí không còn nằm dưới bàn báo "cần soát". Tủ đã có ở vị trí đó → báo để xoá tay, tool không tự xoá. 5. Bàn CAD là block kéo giãn ẩu: chồng lên tủ áo, góc giường, tủ đầu giường còn lại, cột nhô → cắt đầu bàn tới mép món bên cạnh hoặc mặt biên Room, cắt > 100 mm báo "cần soát". Dừng trước đoạn tường dày thêm mà bàn ngắn hơn 700 mm → dựa lưng vào mặt đoạn tường đó, giữ mép trước, giảm sâu (người dùng chọn 2026-10-31; G19: 8 bàn, sâu 400). Cắt xong ngắn hơn 400 → giữ theo CAD, báo "cần soát". 6. Kích thước: tham số instance Chieu dai / Chieu sau của mẫu FPT P4 (khung bàn sâu hơn Chieu sau 200). Tool dò trong SubTransaction trên cái đầu tiên (đổi +100 mm, đo khung, hoàn tác) mọi tham số Double không built-in; không thấy khung đổi mà có tên trên thì vẫn dùng tên đó. Rồi đặt dài và sâu theo bàn đã căn. Không có → giữ cỡ type, báo "cần soát". 7. Hướng family (suy từ khung type −750…750 × −520…0, cần xem trên mặt bằng): gốc giữa lưng bàn, lưng về +Y. Quay ngược → IN[8] = True. 8. Cao độ: Elevation from Level = đỉnh sàn tại tâm bàn − level + IN[7] (mặc định 1 mm như mẫu người dùng đặt tay: family 2D nằm trên mặt sàn mới thấy trên mặt bằng). Không có sàn → IN[7], báo "cần soát". 9. Comments = "ARV-TaoBanLamViecTuCAD". Bàn của tool đã có mà lệch / sai hướng / sai cao độ / sai cỡ / khác type → sửa tại chỗ; bàn cùng family người dùng tự đặt → bỏ qua."""
__title__ = "Bàn làm\nviệc"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
