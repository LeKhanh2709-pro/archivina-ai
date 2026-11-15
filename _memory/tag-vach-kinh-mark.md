---
name: tag-vach-kinh-mark
description: "Vách kính tag bằng Mark ở CẢ 2 nút Archivina (Định vị + tag cửa, Thống kê cửa); cửa nằm trong vách kính không tag, không thống kê (người dùng chốt 2026-11-14); chưa bấm trong Revit thật"
metadata:
  node_type: memory
  type: project
  originSessionId: 3ca9c6a7-6ccd-4b7a-9a0b-e0e088ece9d3
  modified: 2026-11-14T07:04:47.147Z
---

Người dùng yêu cầu 2026-11-13: hộp thoại nút Thống kê cửa có "1 cửa sổ đặt tên cửa đi cửa sổ, 1 cửa sổ tag vách kính bằng mark" → duyệt ảnh, đã build 13/11 10:13 (`ThongKeCua_TuDong.py` IN[9] – IN[12], `lib\arv_bang_cua.py` 2 tab).

**Người dùng chốt 2026-11-14** (báo "tag vách kính bằng mark vẫn chưa được cập nhật", rồi trả lời câu hỏi): sửa ở 2 nút Archivina `Định vị + tag cửa` và `Thống kê cửa`; "không tag các cửa, và thống kê các cửa (cửa đi, cửa sổ) khi nằm trong vách kính". Cách hiểu của Claude: cửa có Host là curtain wall thì không tag cửa, không vào bảng; vách kính tag bằng Mark ngay trong nút Định vị + tag cửa.

Đã làm 14/11 (nút sinh lại ~09:22, Revit phải Reload pyRevit):
- Khối chung `scripts\dynamo\VachKinh_chung.py`, chép vào 2 lõi bằng `gop_vach_kinh.py` (không sửa tay giữa 2 mốc).
- `TagCua_TuDong.py`: IN[33] KHÔNG tag vách kính, IN[34] vẫn tag + thống kê cửa trong vách kính như cũ, IN[35] kiểu tag, IN[36] thư mục family (ô bool đặt nghĩa ngược). Tag cửa cũ do công cụ đặt trên cửa trong vách kính: HỎI rồi mới xoá (`ARV_XOA_TAG_VK` trả lời sẵn khi thử). Bảng trên sheet có cửa trong vách kính → bảng vẽ (drafting), bảng cũ sai số ô thì hỏi vẽ lại (`ARV_VE_LAI_BANG`).
- `ThongKeCua_TuDong.py` IN[13] (vẫn thống kê cửa trong vách kính, mặc định tắt); `arv_bang_cua.py` không liệt kê cửa trong vách kính.
- `arv_hoi_sheet._mac_dinh_tpl`: đang đứng trên chính view đích thì giữ template / tỉ lệ của view đó (trước tự chọn `AF.07` khoá 1:100).
- Thử nền nút thật trên bản sao Site HQV có sẵn mặt bằng định vị cửa Tầng 1 (`_tmp\tk_vach_kinh\kq_2nut_site\`): xoá 39 tag cửa trong vách kính, còn 55 tag cửa, tag 50 / 56 vách (6 chưa có Mark; T1-VK.57, T1-VK.33 không tìm được chỗ), bảng TỔNG 55, bấm lại không đổi.

- Thử thêm 14/11 chiều: bản sao L1-L3 Tầng 1 (vách trong model chính) 50 tag cửa, bỏ 25, tag 34 / 40 vách; nút Thống kê cửa sinh lại 13:28 (sửa câu cảnh báo khi bảng là bảng vẽ rời).
- Người dùng "Có, cập nhật" 14/11 → nút `Hồ sơ đã duyệt` cũng theo cách này (mọi kiểu tag chạy lõi Archivina, xem [[nut-ho-so-duyet]]); thử bản sao Site sạch đã tách central: 14 / 14 mục, tag vách 50 / 56 / 35 / 0.
- `CLAUDE.md` + 2 SKILL.md (`tag-cua-revit`, `thong-ke-cua-revit`) đã ghi chi tiết.

Người dùng chốt 2026-11-14 "Giữ như vậy": bảng cửa sổ trống (TỔNG 0) VẪN đặt lên bản vẽ khi mọi cửa sổ của tầng là tấm vách kính (Tầng 2, 3BA Site) – không bỏ, đừng đề xuất lại.

Còn mở: nhãn viewport của bảng vẽ tụt ra ngoài khung và Tầng 1 bảng đè góc mặt bằng (có từ trước); `.dyn` chưa chạy trong Dynamo; gói `_dist` chưa đóng lại.

**Why:** cửa trong vách kính thuộc về vách (vách có tên riêng theo Mark), tag + thống kê riêng từng cửa làm rối bản vẽ định vị cửa.

**How to apply:** khi quay lại, hỏi kết quả bấm trong Revit thật (phải Reload pyRevit); bản sao workshared phải tách central trước khi thử ([[ban-sao-revit-tach-central]]). KHÔNG cần bảng thống kê Revit cho vách kính (chốt 13/11, đừng đề xuất lại). Thử nền dùng nút thử riêng `ARVTestVK` (`_tmp\tk_vach_kinh\chay_nen.ps1`, journal `journal_site_dvc.txt` / `journal_l13.txt`), không dùng `hs_site_link\buoc.txt`. Liên quan [[thong-ke-cua-revit]], [[tag-cua-revit]], [[nut-ho-so-duyet]], [[nut-hs-tkbvtc-nhan-link]], [[anh-duyet-truoc-khi-build]].
