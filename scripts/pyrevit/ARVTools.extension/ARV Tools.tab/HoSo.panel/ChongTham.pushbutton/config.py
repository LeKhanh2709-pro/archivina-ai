#! python3
# -*- coding: utf-8 -*-
# File sinh tự động bởi scripts/pyrevit/build_from_dynamo.py – không sửa tay.
"""Vẽ nét vén chân tường chống thấm (Detail Line) trên view mặt bằng chống thấm của Revit. Hatch chống thấm = Filled Region 2D trong view (người dùng chốt 2026-10-27: không đụng hatch / filter của sàn gạch model). - Nhận phòng ướt theo 2 nguồn: a) sàn hoàn thiện ướt trên level (tên kiểu sàn chứa từ khoá, vd. "Gach Lat WC", "Gach Lat Logia") b) bồn cầu / sen tắm / bồn tắm nằm ngoài mọi sàn ướt → WC chưa có sàn ướt (không dùng phễu thoát sàn) - Biên phòng = mép tường thô / mặt lõi tường (room có sẵn tại điểm đó, hoặc room tạm trong SubTransaction rồi rollback, không để lại gì trong model) → không bám theo khấc / lỗ của sàn. Room hở (không khép kín) hoặc tràn sang phòng lớn thì quay về biên sàn. Không bao giờ bo vào lớp trát / hoàn thiện (người dùng chốt 2026-10-28). - Mỗi vòng biên lùi vào trong phòng một khoảng (mặc định 50 mm) → nét vén, ngắt tại cửa đi - Mọi phòng ướt được hatch bằng Filled Region theo biên mặt tường: kiểu "AV_Hatch Chống Thấm WC" / "... Logia" (chưa có thì tạo, mẫu + màu lấy theo filter sàn SHT-WC / SHT-Logia của template), đưa xuống dưới nét vén - View đã có nét vén: không vẽ lại vén (không xoá gì), chỉ bổ sung hatch cho phòng chưa có hatch - Ẩn thiết bị vệ sinh trong view (Hide in View từng đối tượng, không sửa template), giữ phễu thoát sàn - Detail Line kiểu nét "AV.Nét chống thấm" gom group "ARV_ChongTham_Ven"; Filled Region gom group "ARV_ChongTham_Hatch" Dry-run (mặc định) chỉ báo cáo, không sửa mô hình. Không xoá gì: view đã có nét vén cùng kiểu thì dừng và báo."""
__title__ = "Chống\nthấm"
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
_lib = os.path.normpath(os.path.join(_here, "..", "..", "..", "lib"))
if _lib not in sys.path:
    sys.path.insert(0, _lib)

import arv_dynamo_host
arv_dynamo_host.run_button(_here, __revit__)
