---
name: vach-kinh-hqv-t1
description: Vách kính bọc ngoài HQV tháp B Tầng 1 dựng từ CAD KT-T1 theo lõi nút Vách kính; thông số người dùng chốt và quy tắc suy ra từ 5 vách mẫu
metadata:
  node_type: memory
  type: project
  originSessionId: a603a177-a0ea-4eb0-9f24-6a20f2b5de40
  modified: 2026-11-10T08:39:50.316Z
---

Người dùng yêu cầu 2026-11-10: dựng vách kính bọc ngoài `2.HQV_A_ThapB_L1-L3.rvt` (central ổ A:) theo CAD `KT-T1.dwg` (xref `xf-facade T1`, layer A-Window / A-Glaz) bằng quy tắc [[vach-kinh-revit]]. Chốt: vách cao 4000, cửa đi cao 3000, xem mẫu là 5 vách họ tự dựng (T1-VK.02..06, thực tế cao 3850).

Quy tắc suy từ mẫu: đầu vách = mép ngoài đố CAD (block 65,8 × 187,2), tim vách = giữa bề sâu đố, cửa mở ra ngoài nhà, chỗ CAD chia không đều thì tách vách tại đố đó (2 vách chồng 1 đố).

**Why:** bản sao v2 (48 đoạn, 33 cửa đi) ở `D:\AI\_tmp\revit_vk_hqv\HQV_B_L1L3_da_dung_VK_v2.rvt` (pt6.py + pt7.py sinh spec, dung_v2_ip.py dựng); chưa đưa vào model thật. Góp ý 2026-11-10: mọi vị trí góc (kể cả góc lõm) dùng đố góc `ARV_Đố góc 150x150`; chỗ cửa trượt sảnh giữa để 1 vách liền, cửa đi rộng 2065 tâm - tâm. Tầng 2 / 3BA (2026-11-10, bản sao `HQV_B_L1L3_VK_T2_T3_v4.rvt`, pt9 + pt10 + dung_t23_ip.py; chưa vào model thật): T2 cao 5300, cửa sổ 1435, thêm đố ngang tim 4092,5; T3 cao 4450, Base Offset 150, chân vách lên bậu 1300 (1450 từ cốt 00), cửa sổ 1270. Tường thường Tầng 2 trùng kính (người dùng báo 2026-11-10, muốn sửa thẳng file gốc nhưng XEM BẢN SAO TRƯỚC): `sua_tuong_t2_ip.py` cắt 31 tường (15 xoá hết, 16 cắt, giữ đoạn ≥ 300 mm), 2 tường 1651006 / 1773756 có kính embed sẵn thì không đụng; bản xem `HQV_B_L1L3_T2_sua_tuong_trung_XEM.rvt` (bản central lưu từ phiên journal mở ra trống trong Revit người dùng, nghi đóng workset; bản xem nên tách, bỏ workset, đặt starting view). Người dùng duyệt 14:30; áp lên file gốc bằng nút dùng một lần `scripts\pyrevit\ARVSuaT2.extension` (người dùng tự bấm rồi Sync; công cụ ghi MCP khoá với file gốc), backup `_backup\2.HQV_A_ThapB_L1-L3_20261110_1434.rvt`; nút cắt tường đã bấm + Sync 15:25. Đổi 2 hàng ô trên cùng Tầng 2 sang A-ALU (542 ô, gồm 14 ô kính góc): duyệt bản mẫu, thêm nút `DoiALUT2` cùng extension, backup `_backup\2.HQV_A_ThapB_L1-L3_20261110_1538.rvt`; bấm xong thì chuyển extension về `_tmp` (không xoá). **How to apply:** cửa sổ phải có `FacingOrientation` quay ra ngoài nhà; `Wall.Orientation` không đổi khi `Wall.Flip`, không dùng để xét hướng; family cửa sổ không flip riêng được thì lật cả vách.
