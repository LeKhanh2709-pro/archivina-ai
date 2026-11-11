#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Trình bày MẶT BẰNG TƯỜNG XÂY (định vị tường) cả tầng theo mẫu FPT P5 A.CD.04.07 (KTS chốt 2026-11-03, G19): 1. View mặt bằng mới trên level IN[0] (tên IN[1]), chép thông số view template IN[2] vào view rồi BỎ gắn template (template công ty để 1/150 – KHÔNG sửa template). Ẩn nội thất, thiết bị, Room, sàn. Tỷ lệ = số đầu tiên trong IN[3] mà hình (kể cả dim, đầu trục) ước tính vừa vùng vẽ khung tên. 2. Trục của file: đầu trục 2D ở CẢ 2 ĐẦU, cách tường ngoài cùng GRID_END mm giấy. Dim trục 4 phía, mỗi phía 2 chuỗi: khoảng trục + kích thước tổng (dim type IN[8]). 3. Chuỗi định vị tường (dim type IN[9]): gom tường (lõi ≥ 80, thẳng, song song trục X / Y) thành TUYẾN thẳng hàng (lệch tim ≤ 60, hở ≤ 2500, tổng dài ≥ 4000). Mỗi tuyến xét 2 phía (điểm mẫu cách mặt tường 400): - một phía phần lớn KHÔNG có Room → mặt ngoài nhà: chuỗi đặt phía ngoài, cách mặt tường WALL_EXT mm giấy; - không, mà một phía là Room công cộng IN[12] (hành lang, khu vực chung) → chuỗi phía đó, cách WALL_INT; - cả 2 phía là phòng trong căn → không dim (chi tiết căn hộ đã dim). Mốc: MẶT LÕI (gạch thô, bỏ trát) tường vuông góc chạm tuyến, mép cửa đi / cửa sổ trên tuyến (tham chiếu Left / Right của family), đầu tường của tuyến, mặt cột / vách BTCT của file Revit link (kết cấu), trục. Mốc cách nhau < DIM_MIN gộp; chữ số đoạn ngắn chồng nhau → kéo sang phía ngoài đường dim, lệch xen kẽ. 4. Legend IN[10] (nhân bản một legend có sẵn rồi vẽ): BẢNG KÝ HIỆU GHI CHÚ TƯỜNG – mỗi vật liệu lõi tường một dòng (hatch theo IN[11], loại, các chiều dày lõi) + lưu ý chỉ ghi điều đúng với mô hình. 5. Sheet IN[4] / IN[5], khung tên IN[6], viewport type IN[7]: MB ở trên, giữa vùng vẽ; legend góc dưới trái. 6. Trục file link KC: tắt hiển thị view filter có sẵn IN[16] trong view (trục type không phải '…KT'). Không tạo / sửa type, style, view template, filter. Chưa làm: tag căn hộ, chi tiết điển hình cột vách giao tường xây, dim trong lòng căn."""
__title__ = "Tường\nxây"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
