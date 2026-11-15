---
name: nut-ho-so-duyet
description: "Nút gộp \"Hồ sơ đã duyệt\" (ARVHoSoDuyet.extension) chạy lại 4 nút HS TKBVTC theo cấu hình đã duyệt; từ 14/11 mọi kiểu tag cửa chạy lõi Archivina (có tag vách kính bằng Mark); chưa bấm trên file chính"
metadata:
  node_type: memory
  type: project
  originSessionId: 3ca9c6a7-6ccd-4b7a-9a0b-e0e088ece9d3
  modified: 2026-11-14T07:04:47.164Z
---

`D:\AI\scripts\pyrevit\ARVHoSoDuyet.extension` (2026-11-13): tab `Ho so duyet` → nút `Hồ sơ đã duyệt`. Không chép phần
tử giữa 2 file; chạy lại Chống thấm / Ngăn cháy lan / Định vị lan can louver / Định vị + tag cửa của Archivina trên từng
mặt bằng, trả lời sẵn hộp thoại theo `lib\ho_so_duyet\<mã>.json` (HQV Site: 14 mục, 1:200). Bảng kiểm trước khi chạy, 1
lần Ctrl+Z, đệm nhận diện CAD mang theo. Chi tiết trong CLAUDE.md mục "Nút gộp `Hồ sơ đã duyệt`".

Tag cửa – lịch sử: 13/11 sáng lõi riêng `lib\loi_rieng\TagCua_xep_lai.py` (xếp lại, kiểu `chu`); 13/11 chiều người dùng
gửi `AV-Tag-DOOR.rfa` → kiểu `mau` (mặc định của HQV json; `lib\tag_rieng\AV-Tag-DOOR.rfa` + bản `_CuaSo` đổi hạng mục
sang Window Tags bằng API), người dùng duyệt "OK" 13/11 20:00, rồi "Đổi cả Archivina" (nút Định vị + tag cửa của Archivina
= lõi riêng + mặc định mới, xem [[tag-cua-revit]]).

**2026-11-14, người dùng "Có, cập nhật"** (cập nhật nút này theo cách mới của Archivina: vách kính tag bằng Mark, cửa nằm
trong vách kính không tag / không thống kê, xem [[tag-vach-kinh-mark]]): MỌI kiểu tag nay chạy đúng lõi của nút Định vị +
tag cửa (Archivina); lõi riêng không còn được nạp (file giữ lại để đối chiếu). Kiểu tag chỉ là cách gọi lõi: `mau` / `goc`
= AV-Tag-DOOR, `chu` / `gon` = `ARV_TAG_GON`, `2o` = IN[30]. Mặt bằng đã tag bằng bản trước: lõi HỎI từng mặt bằng (hộp
Yes / No của Revit) rồi mới xoá tag cửa cũ trên cửa trong vách kính / vẽ lại bảng cũ. Thử nền (`_tmp\ho_so_duyet\thu_vk.py`):
bản sao sạch đã tách central đủ 14 mục, 14 / 14 lên bản vẽ → `xem\20_2.HQV_A_ThapB_Site_vach_kinh_Mark_du_14_muc.rvt`
(tag cửa 55 / 78 / 41 / 188 + 51, tag vách 50 / 56 / 35 / 0); bản sao file 11 bấm lại (Yes thật) → `xem\19_*.rvt`; kiểu
`chu` + `2o` chạy đúng. Bản trước: `_backup\arv_ho_so_duyet_20261114_1323_truoc_vach_kinh.py`.

**Why:** người dùng muốn 1 nút đưa phần đã duyệt (file 15) vào file chính `2.HQV_A_ThapB_Site`, rồi chê bản định vị cửa
1:200 "rối mắt"; 14/11 muốn nút này cũng theo quy tắc vách kính mới.

**How to apply:** thêm dự án khác = thêm 1 file json trong `lib\ho_so_duyet\`. Sửa cách xếp tag / vách kính thì sửa
`scripts\dynamo\TagCua_TuDong.py` (rồi sinh lại nút Archivina) – nút này đổi theo, KHÔNG còn lõi riêng để sửa. Thử:
`_tmp\ho_so_duyet\thu_vk.py` + `_tmp\tk_vach_kinh\chay_nen.ps1` (nút thử `ARVTestVK`, journal `journal_hsd.txt`), bản sao
phải tách central trước ([[ban-sao-revit-tach-central]]). Bảng cửa sổ trống (TỔNG 0) vẫn đặt lên bản vẽ ở
Tầng 2 / 3BA: người dùng chốt 14/11 "Giữ như vậy". Còn mở (14/11): nhãn viewport bảng vẽ tụt ra ngoài khung (có từ
trước); Tầng 1 bảng đè góc mặt bằng. Người dùng chưa bấm
trên file chính. `.gitignore` có `*.rfa` → 2 file trong `lib\tag_rieng` không lên GitHub. Lần đầu pyRevit nạp extension mới
từng báo `Error Loading pyRevit` 1 lần, nạp lại thì được. Liên quan [[revit-vang-locale-cpython]],
[[nut-hs-tkbvtc-nhan-link]], [[nut-moi-extension-rieng]].
