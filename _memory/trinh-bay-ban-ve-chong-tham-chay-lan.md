---
name: trinh-bay-ban-ve-chong-tham-chay-lan
description: "Nút Chống thấm / Ngăn cháy lan tự tạo view + template theo tầng (như MB định vị cửa) và tự đặt lên sheet — làm 2026-11-03/04, chưa duyệt"
metadata:
  node_type: memory
  type: project
  originSessionId: 0f443533-d124-465f-9372-72dd58b30ef0
  modified: 2026-11-12T06:38:28.753Z
---

Người dùng yêu cầu 2026-11-03 tối: chống thấm + chống cháy lan Revit "tự động trình bày vào bản vẽ" như nút Tag cửa ([[tag-cua-revit]]). 2026-11-04: model thật báo "Chưa có view mặt bằng chống thấm" → yêu cầu "tạo view, đặt template như MB định vị cửa".
Đã làm: hộp thoại `arv_hoi_sheet.hoi_chong_tham / hoi_ngan_chay`; khối chung `scripts\dynamo\DatSheet_chung.py` (đặt sheet + `sh_tao_view` + crop) chép bằng `gop_dat_sheet.py`; builder khoá `tao_view`. Chi tiết trong CLAUDE.md.

**Why:** model thật của người dùng không có view / template chống thấm như G19; G19 có sẵn sheet trống A.4-201 / A.4-101 nên ưu tiên đặt vào đó.

**How to apply:**
- Sửa ở `DatSheet_chung.py` → `gop_dat_sheet.py` → `build_dyn.py <spec>.json` → `build_from_dynamo.py ... --chi ChongTham,NganChay` (đặt `PYTHONIOENCODING=utf-8`).
- Ghi file bằng Python trên Windows: dùng `newline=""` (không thì LF thành CRLF); không viết `\a`, `\r`, `\t` trong chuỗi thường (CLAUDE.md từng dính `lib\arv` → ký tự BEL).
- Template mới: `DisplayStyle.HLR` (không có `HiddenLine`), tắt filter bằng `SetIsFilterEnabled`, không ẩn hạng mục thiết bị vệ sinh.
- Template công cụ tạo phải có tường / cột / vách + ẩn trục link y như MB định vị cửa (người dùng yêu cầu 2026-11-04); model thật có thể thiếu line style / kiểu hatch / filter sàn của G19 → công cụ tự tạo theo thông số G19.
- Lỗi trên máy người dùng: hỏi rồi đọc log `C:\Users\Khanh\Documents\ARV_Logs\<công cụ>\` (người dùng cho đọc 2026-11-04; lần sau vẫn hỏi).
- Patch script viết bằng Write tool, không heredoc trong Bash (heredoc làm mất `\\`, hỏng đường dẫn).
- Thử: bản sao G19 giả lập model thật (đổi tên template 1.7 / 1.8, kiểu hatch, filter sàn): `_tmp\revit_trinhbay\thu7\chay_thu.py`.
- Model thật G19_A_L3-32 (central, ổ A:) đặt tên kiểu sàn khác G19 mẫu (lô gia không có chữ Logia) → nhận phòng ướt thêm theo tên room (2026-11-04 09:15). Thử thẳng trên bản sao model thật: `_tmp\revit_trinhbay\thu7_L3-32\` (`chay_ct.py`, runner `chay_dynamo_ui2.ps1` bấm Run lại khi Dynamo còn "Ready to run" sau hộp "Open external file?").
- 2026-11-09: chú thích đổi thành `BẢNG GHI CHÚ - <tên>` có cột Diện tích (tổng Area Filled Region); người dùng duyệt ảnh, nút đã sinh lại, chưa bấm thử nút thật. Vá thử trên bản chép `_tmp\revit_dientich\` trước, duyệt rồi mới áp vào nguồn.
- Trạng thái 2026-11-04 09:15: thử Dynamo OK trên bản sao model thật (59 phòng), nút sinh lại; người dùng chưa bấm lại, chưa duyệt.
- 2026-11-11: nút Chống thấm nhận phòng ướt theo CAD link khi mặt bằng đang mở có CAD (gọi bộ nhận diện của skill chong-tham-mat-bang, kết quả lưu theo DWG); IN[21] = "Không dùng CAD link". Thử Site HQV 4 tầng OK trên bản sao (`_tmp\ct_cad\ct_chay.py`); thử nền phải bỏ RequestViewChange (proxy UiAppGia) nếu không lần bấm sau chạy nhầm view. Người dùng chưa bấm.
- 2026-11-12: người dùng chê nhận diện CAD (thiếu N / R / đệm rác, WC, khu WC công cộng; ngăn cháy thiếu trục, hatch cả thang máy) → sửa 2 skill + khoá đệm theo nội dung script + crop nới theo phần đã vẽ (vẽ theo CAD có thể nằm ngoài tường Revit). Thử nút thật Site 4 tầng: `_tmp\ct_cad\kq\`, `kq_nc\`. Debug nhận diện bằng `_tmp\ct_cad\dbg\` (`chay4.sh`, `chay_nc4.sh`, `xem_kq.py`). Revit nền hay văng ở lần chuyển view đầu → chạy lại. Phiên khác có thể cùng dùng nút ARVTestHS: phối hợp trước khi thêm ext / build.
