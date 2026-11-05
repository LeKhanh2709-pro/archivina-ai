---
name: thong-ke-cua-revit
description: 'Thống kê cửa Revit – Đứng ở mặt bằng tầng đang mở, bấm 1 nút là có bảng thống kê (Schedule) cửa đi và cửa sổ của mặt bằng đó: cột Ký hiệu (Type Mark) / Rộng / Cao / Số lượng, gộp theo Type Mark nên cửa trùng ký hiệu chỉ hiện 1 dòng kèm số lượng, dòng TỔNG cuối bảng; lọc theo tầng của mặt bằng, bỏ đối tượng Type Comments Louver; bấm lại thì cập nhật bảng cũ, không tạo trùng, không xoá. Báo cửa chưa có Type Mark, cùng ký hiệu khác kích thước, mặt bằng crop không thấy hết cửa của tầng. Nút pyRevit Archivina > HS TKBVTC > Thống kê cửa + graph Dynamo ThongKeCua_TuDong.dyn. Dùng khi người dùng nhờ "thống kê cửa", "bảng thống kê cửa đi / cửa sổ của tầng", "đếm cửa theo ký hiệu", "schedule cửa gộp trùng", hoặc sửa / thử nút Thống kê cửa.'
---

# Thống kê cửa Revit (Archivina)

Người dùng yêu cầu 2026-11-04: "tạo 1 bảng thống kê các cửa có trong mặt bằng đó, những cửa trùng thì hiện 1 lần", làm
nút riêng (không gắn vào nút Định vị + tag cửa, vốn chỉ tạo bảng khi đặt lên bản vẽ).
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit của người dùng.

## Cách dùng
- Mở mặt bằng tầng → `Archivina` → `HS TKBVTC` → **Thống kê cửa**: tạo / cập nhật ngay (không hộp thoại), mở bảng cửa đi.
  Ctrl+Z một lần là hoàn tác (transaction `ARV - Thống kê cửa`). View đang mở không phải mặt bằng tầng thì nút nhắc.
- Shift+bấm: hộp thoại 7 ô, mặc định Dry-run (chỉ báo cáo).

| IN | Ý nghĩa | Mặc định |
|---|---|---|
| 0 | Tên view mặt bằng (trống = view đang mở) | trống |
| 1 | Hạng mục: `Cửa đi;Cửa sổ` (bỏ bớt nếu chỉ cần 1 bảng) | `Cửa đi;Cửa sổ` |
| 2 | Type Comments không thống kê | `Louver` |
| 3 | Dry-run | True (nút một chạm truyền False) |
| 4 | Mẫu tên bảng (`{loai}`, `{tang}`, `{view}`) | `THỐNG KÊ {loai} - {tang}` |
| 5 | Mở bảng vừa tạo | True |
| 6 | Chỉ đếm cửa thấy trên sheet đặt bảng (Filter by sheet) | False |

## Quy tắc
1. **Mỗi hạng mục 1 bảng**: `THỐNG KÊ CỬA ĐI - <TẦNG>`, `THỐNG KÊ CỬA SỔ - <TẦNG>`. Revit 2027.3 KHÔNG gộp được cửa đi + cửa
   sổ vào 1 bảng (khảo sát 2026-11-04): bảng nhiều hạng mục không có trường Rộng / Cao (DOOR_ / WINDOW_ / FAMILY_WIDTH đều
   thiếu), bộ lọc chỉ "và" không có "hoặc"; lọc Category chỉ nhận `ElementId` hạng mục, không nhận chuỗi "Doors".
2. **Gộp trùng**: Itemize every instance TẮT, sort / group duy nhất theo Type Mark → mỗi ký hiệu 1 dòng, cột Số lượng
   (Count, hiện tổng) + dòng tổng `TỔNG`.
3. **Cột**: Ký hiệu (Type Mark) / Rộng / Cao / Số lượng; Rộng / Cao lấy `DOOR_WIDTH` / `WINDOW_WIDTH` (không có thì
   `FAMILY_WIDTH_PARAM`), tương tự chiều cao. Trường khác của bảng nhân bản thì ẩn, không xoá.
4. **Lọc**: Level = tầng của mặt bằng (`FAMILY_LEVEL_PARAM`), Type Comments khác từng giá trị IN[2].
5. **Bảng cùng tên đã có** → cập nhật lại cột / lọc / gộp (không tạo trùng, không xoá). Chưa có → nhân bản bảng cùng hạng
   mục có sẵn của dự án (ưu tiên tên có "thống kê", giữ kiểu trình bày công ty), không có thì tạo mới. Bảng cùng tên khác
   hạng mục thì báo, không đụng.
6. **Filter by sheet TẮT mặc định**: bật thì bảng đặt trên sheet KHÔNG có mặt bằng sẽ trống trơn (đã gặp khi thử).
   Mặt bằng crop 1 phần tầng (vd. `CAN-04 - MB TƯỜNG XÂY`: 9 / 119 cửa đi) thì bảng vẫn đếm cả tầng → công cụ báo
   CẦN XEM LẠI; muốn chỉ đếm cửa của mặt bằng đó: Shift+bấm bật IN[6] và đặt bảng lên sheet có mặt bằng đó.
7. **Báo CẦN XEM LẠI**: cửa chưa có Type Mark (gộp chung 1 dòng trống), cùng Type Mark mà khác kích thước (Revit để trống
   ô Rộng / Cao), cửa thấy trong mặt bằng nhưng Level khác tầng (bảng không đếm), số cửa của tầng ≠ số thấy trong mặt bằng.
8. Mỗi bảng làm trong `SubTransaction`: bảng lỗi giữa chừng thì huỷ riêng bảng đó.
9. "Blank row before data" của Revit (khoảng trống giữa tiêu đề cột và dữ liệu) API không tắt được → bỏ tay trong
   Appearance nếu cần.

## File
- Lõi: `scripts\dynamo\ThongKeCua_TuDong.py` (+ `.json` spec, `.dyn` sinh bằng `scripts\dynamo\build_dyn.py`).
- Nút: `scripts\pyrevit\ARVTools.extension\Archivina.tab\HoSo.panel\ThongKeCua.pushbutton\` SINH bằng
  `scripts\pyrevit\build_from_dynamo.py "<file mau revit>\dynamo" --chi ThongKeCua` (đặt `PYTHONIOENCODING=utf-8`);
  không sửa tay. Khai báo trong `BUTTONS` + `MOT_CHAM` (`view_in` 0, `tu_khoa` rỗng = mặt bằng tầng đang mở).
- Icon: mdi `table-large` → `scripts\pyrevit\icons\ThongKeCua(.dark).png` (sinh bằng `_tmp\arvtools_icon_thongke\`).

## Cách thử (đã làm 2026-11-04)
- Dynamo trên bản sao `G19_A_L3-32` (`_tmp\revit_thongkecua\thu1..3\`, chạy `_tmp\revit_g19\chay_dynamo_ui.ps1`; journal
  phải ghi UTF-8 KHÔNG BOM, có BOM thì Revit không chạy lệnh và script chờ hết giờ): TẦNG 3 → cửa đi 119 cái / 12 ký hiệu,
  cửa sổ 50 cái / 9 ký hiệu (bỏ 17 Louver), lần 2 cập nhật không trùng. Ảnh bảng: schedule không xuất ảnh trực tiếp →
  đặt lên sheet tạm trong bản sao rồi `ExportImage` (`thu3\anh - Sheet - ZZ-THU - ...png`).
- Nút thật: extension thử `_tmp\pyrevit_thongke\ext\ARVTestTK.extension` (nút `TK` chạy nguyên `script.py` của nút 2 lần),
  `pyrevit extensions paths add` → `_tmp\pyrevit_test\chay_test.ps1 -Journal _tmp\pyrevit_thongke\journal.txt -BaoCao
  _tmp\pyrevit_thongke\kq\ket_qua.txt` → `paths forget`. Kết quả: tạo 2 bảng, mở bảng cửa đi, lần 2 không trùng.

## Trạng thái
Người dùng chưa bấm thử trong Revit của mình, chưa duyệt (`Cần xác nhận lại`). Revit phải Reload pyRevit mới thấy nút.
