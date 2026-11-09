#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tự động tag cửa đi + cửa sổ trên mặt bằng đang mở của Revit (người dùng chốt 2026-11-02, sửa theo góp ý cùng ngày): - Cửa đi: family tag "AV_Door Tag"; cửa sổ: "AV_Window Tag"; cửa sổ có tên family / type chứa từ khoá lam: "AV_Louver Tag". Đối tượng có Type Comments "Louver", "Cửa nhôm" hoặc "Cửa lam thép" thì KHÔNG tag (người dùng chốt 2026-11-09). - Tag hiện đúng Type Mark: nhãn family có tiền tố (vd. "S3.") thì thay bằng nhãn Type Mark trơn chép từ family tag cùng hạng mục trong dự án (Revit 2027.3 không sửa được tiền tố nhãn qua API), rồi nạp lại family. - Tag nằm ngang, ưu tiên NGAY GIỮA cửa (cửa đi phía không mở cánh, cửa sổ phía ngoài theo FacingOrientation); KHÔNG đè cửa (kể cả cánh mở), cửa sổ, tường, cột, tag / chữ khác. Lưới vị trí quanh cửa xếp theo điểm = lùi xa + 4 × dịch khỏi giữa cửa + phạt phía kia; không chỗ nào trống thì đặt chỗ ít đè nhất và liệt kê để xem lại. - Leader: tag lệch khỏi giữa cửa (hoặc xa hơn 1 bề cao tag) thì bật leader gắn vào cửa. - Nội thất không né mà ẩn: tạo view template riêng "<template gốc> (ẩn nội thất)" (tạo từ view vì API không nhân bản được view template), ẩn các hạng mục nội thất, gán cho view. KHÔNG sửa template gốc. - Cửa có EI (tham số chống cháy có giá trị) thì EI phải hiện trên tag: tag đã đặt mà chữ tag không chứa giá trị EI → báo family tag chưa có nhãn EI. - Cửa / cửa sổ đã có tag trong view thì bỏ qua: bấm lại không tạo trùng. Chỉ khi bật IN[14] mới dời tag đã có (cùng family tag); chỉ khi bật IN[15] mới xoá tag đang gắn trên đối tượng Type Comments "Louver". Dry-run chỉ báo cáo (đặt thử trong SubTransaction rồi huỷ), không sửa mô hình. - Mặt bằng định vị cửa (gộp từ nút "MB định vị cửa" theo yêu cầu người dùng 2026-11-03): view gốc đã là mặt bằng định vị cửa (mang template IN[17] hoặc tên theo mẫu IN[18]) thì tag luôn; không thì nhân bản view gốc (Duplicate, không kèm chú thích) thành "MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>" (đã có thì dùng view đó), gán template IN[17] rồi tag trên đó. Template chưa có thì tạo từ template của view gốc: tường + sàn Halftone, sàn tắt mẫu tô, cửa đi / cửa sổ bỏ Halftone, ẩn các hạng mục IN[7], hiện tag cửa. Template đã có thì dùng nguyên. Không sửa view gốc / template gốc."""
__title__ = "Định vị\n+ tag cửa"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
