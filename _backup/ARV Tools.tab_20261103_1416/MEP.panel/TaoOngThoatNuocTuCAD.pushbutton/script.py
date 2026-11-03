#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Tạo ống thoát nước uPVC + phụ kiện (co, Y 45°, tê, côn) từ mặt bằng cấp thoát nước (DWG CTN đã Link vào Revit). Đọc từ BẢN SAO DWG qua AutoCAD Core Console (chữ, dim, block trong bản link Revit không đọc được): - Ống: LINE 1 nét trên các layer IN[1]. Đoạn tách tại nút T, khe hở cùng layer ≤ 50 mm được nối. - DN: dimension có dimstyle chứa "Dxxx" (VD "AV-Dim 1-75 (D160)", "0.T D110 (1-200)") gán cho đoạn giữa 2 điểm đo; chữ "D75-2%" gán DN + độ dốc cho ống gần nhất; còn lại lan theo tuyến, rồi theo ống hạ lưu; không có → D75. DN không được giảm về hạ lưu: đoạn nhỏ hơn ống đổ vào nó được nâng lên (ghi log). - Hướng chảy: block mũi tên IN[5]. Điểm xả của mỗi cụm ống = tổ hợp đầu cụt (ống đứng R100, điểm rơi xuống lớp dưới, đầu cụt có mũi tên chỉ vào) khớp mũi tên nhiều nhất. - Cao độ: dốc theo chữ ghi chú, mặc định DN ≤ 90 → 2 %, còn lại 1 %; điểm cao nhất mỗi cụm cách level trên IN[4]. - Nhóm cao độ theo hậu tố layer (IN[3]): VD "T5" = dưới sàn TẦNG 5; layer không hậu tố = dưới sàn TẦNG chuyển. Đầu cụt lớp có hậu tố trùng ống lớp thường cùng loại → ống đứng rơi xuống, nối tê. - Ống đứng: tại điểm xả xuống tới level dưới; tại vòng tròn ống đứng là đầu thượng lưu → lên tới level trên. Phụ kiện: co / côn dùng routing preference của pipe type; Y 45° và tê đặt thủ công (xoay theo 3 ống, đặt bán kính từng cổng) vì NewTeeFitting không làm góc 45° (đã thử cả family công ty u.PVC_WYE) và tra bảng kích thước family thư viện thiếu cỡ uPVC. Family Y / tê lấy từ rule Junctions của pipe type (nhận theo góc nhánh 45° / 90°); pipe type chưa có thì tạo type uPVC + nạp family thư viện ở IN[6]. Mỗi phụ kiện trong một SubTransaction: ống bị cắt lẹm / đổi chiều → hoàn tác phụ kiện đó, ghi vào báo cáo."""
__title__ = "Ống thoát nước\ntừ CAD"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
