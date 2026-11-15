---
name: ban-sao-revit-tach-central
description: "Bản sao .rvt của model workshared mở thẳng vẫn là local của central THẬT trên ổ mạng: sửa phần tử có sẵn là mượn phần tử từ central thật; phải lưu thành central mới (tách) trước khi thử"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 3ca9c6a7-6ccd-4b7a-9a0b-e0e088ece9d3
  modified: 2026-11-14T06:53:06.201Z
---

Bản sao `.rvt` (chép từ file central hoặc file local của người dùng) mở thẳng bằng journal KHÔNG độc lập: Revit báo "This central model has been copied or moved from \\192.168.100.242\… to D:\…" rồi coi nó là file local của central thật. Tạo phần tử mới thì không sao; nhưng sửa phần tử ĐÃ CÓ trong central (view / sheet có sẵn, Mark của tường, …) thì Revit tự MƯỢN phần tử đó từ central thật dưới tên người dùng (`khanhlnnQVSLQ`), ghi quyền vào central trên ổ mạng.

Tìm ra 2026-11-14 khi thử nút Hồ sơ đã duyệt trên `_tmp\ho_so_duyet\rvt\2.HQV_A_ThapB_Site.rvt` (bản chép 12/11): central đã đổi nên Revit báo `IDS_OWN_ELEMENTS_BUT_OUT_OF_DATE` ("You now own the element, but your file is out of date"), journal tự huỷ bước đó → 2 mục (ngăn cháy Tầng 1 dùng view có sẵn `MẶT BẰNG CHONG CHAY LAN`, lan can 3BA dùng sheet trống có sẵn `ACD.14.02`) không lên bản vẽ ở lần bấm đầu. Soát journal: các phiên thử 13/11 và sáng 14/11 cũng đã mượn (view + sheet đó trong central Site; 1 phần tử của view `Tầng 1` trong central L1-L3). Không phiên nào Synchronize nên nội dung central không đổi; quyền mượn tự trả khi người dùng Synchronize (ô Borrowed Elements) / Relinquish All Mine. Đã báo người dùng 14/11.

**Why:** quy tắc 7 + 9 của CLAUDE.md – không đụng model thật / ổ khác khi chưa hỏi; mượn phần tử dưới tên người dùng có thể chặn đồng nghiệp sửa phần tử đó, và làm kết quả thử sai khi central đã đổi.

**How to apply:** trước khi thử GHI trên bản sao của model workshared, tách nó khỏi central thật: trong phiên nền, TRƯỚC khi sửa gì, `doc.SaveAs(<đường dẫn mới trên D:>, SaveAsOptions + WorksharingSaveAsOptions.SaveAsCentral = True)` rồi thử tiếp trên chính document đó (mẫu: `_tmp\ho_so_duyet\thu_vk.py`, biến `ARV_THU_TACH`). Bản đã tách của Site HQV: `_tmp\ho_so_duyet\rvt_tach\2.HQV_A_ThapB_Site.rvt` (central riêng trên D:; bản sao của nó mượn từ chính nó, vô hại). Kiểm sau mỗi phiên: journal không có `borrowFromCentral` tới `\\192.168.100.242` và không có `IDS_OWN_ELEMENTS_BUT_OUT_OF_DATE`. Các bản sao CHƯA tách (đừng dùng để thử ghi): `_tmp\ho_so_duyet\rvt\2.HQV_A_ThapB_Site.rvt`, `_tmp\tk_vach_kinh\rvt\Site.rvt`, `_tmp\tk_vach_kinh\rvt\L1-L3.rvt`, các bản trong `_tmp\site_duyet`, `_tmp\hs_site_link` (`Cần xác nhận lại` từng bản). Bản sao của file đã "SaveAs central" trên D: (vd. `tk_vach_kinh\rvt\Site_dvc.rvt` = bản sao file 11) thì an toàn. Liên quan [[khong-lam-phien-may-nguoi-dung]], [[pyrevit-arvtools-revit2027]], [[nut-ho-so-duyet]].
