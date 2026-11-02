---
name: tag-cua-revit
description: 'Tag cửa Revit – Tự động tag cửa đi (AV_Door Tag), cửa sổ (AV_Window Tag) và lam / louver (AV_Louver Tag) trên mặt bằng Revit đang mở: tag nằm ngang, không leader, không đè lên cửa (kể cả cánh mở), cửa sổ, tường, cột, chữ / tag khác; cửa đi ưu tiên phía không mở cánh, cửa sổ phía ngoài; nội thất thì ẩn bằng view template riêng "<template gốc> (ẩn nội thất)"; cửa có EI mà tag không hiện EI thì báo; bấm lại không tạo trùng. Nút pyRevit ARV Tools > Hồ sơ > Tag cửa (một chạm) + graph Dynamo TagCua_TuDong.dyn. Dùng khi người dùng nhờ "tag cửa", "đánh ký hiệu cửa trên mặt bằng Revit", "tag cửa sổ / lam", "tag tự động không đè", hoặc sửa / thử nút Tag cửa.'
---

# Tag cửa Revit (Archivina)

Người dùng là kiến trúc sư, dùng nút **ARV Tools → Hồ sơ → Tag cửa** (pyRevit, Revit 2027) trên mặt bằng đang mở.
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit của người dùng.

## Quy tắc (người dùng chốt 2026-11-02)
1. **Family tag**: cửa đi `AV_Door Tag`; cửa sổ `AV_Window Tag`; cửa sổ có tên family / type chứa `Lam` / `Louver`
   (vd. `AV-Lam Thép Logia2`) dùng `AV_Louver Tag`. Thiếu family thì báo và bỏ qua hạng mục đó (không tự load).
   Cả 3 family có sẵn trong G19, chữ hiện `S3.<Type Mark>` (tiền tố `S3.` nằm cứng trong nhãn của family).
2. **Mã lấy từ Type Mark** (nhãn trong family đọc Type Mark; công cụ không ghi Mark / Type Mark).
3. **Không đè**: tag không được đè lên cửa (gồm cánh mở), cửa sổ, tường, cột, tag / chữ có sẵn và tag vừa đặt.
   - Tag nằm ngang (`TagOrientation.Horizontal`), không leader.
   - Cửa đi ưu tiên phía KHÔNG mở cánh, như mẫu `AV-Tag-DOOR` người dùng đặt ở cửa WC Tầng 1. Phía mở cánh là phía dấu
     chân cửa (hình học trong view, gồm cung cánh) dài hơn.
   - Cửa sổ / lam ưu tiên phía ngoài (+FacingOrientation).
4. **Nội thất không né mà ẩn**: tạo view template `<template gốc> (ẩn nội thất)`; view chưa có template thì
   `<tên view> (ẩn nội thất)`. Ẩn `OST_Furniture; OST_FurnitureSystems; OST_Casework; OST_SpecialityEquipment;
   OST_PlumbingFixtures`, rồi gán cho view.
   - KHÔNG sửa template gốc. API không `Duplicate` được view template (`View cannot be duplicated`), nên tạo bằng
     `view.CreateViewTemplate()` từ chính view (view đang hiển thị theo template gốc).
   - Bật điều khiển V/G Model nếu template mới chưa điều khiển; không để ẩn Door Tags / Window Tags.
   - Template tên đó đã có thì dùng lại.
   - Thiết bị vệ sinh (Plumbing Fixtures) đang nằm trong danh sách ẩn (`Cần xác nhận lại` với người dùng).
5. **EI**: cửa có giá trị chống cháy thì EI phải hiện trên tag.
   - Tham số dò: `Fire Rating; EI; Giới hạn chịu lửa` (instance trước, type sau).
   - Tag đặt xong mà `TagText` không chứa giá trị EI thì báo "family tag cửa chưa có nhãn EI".
   - `AV_Door Tag` hiện KHÔNG có nhãn chống cháy (chỉ có nhãn `S3.` + Type Mark). `AV-Tag-DOOR` có tham số `An-EI`
     nhưng không gắn vào đối tượng nào. G19 không có cửa nào có Fire Rating. Cách hiện EI chưa chốt (`Cần xác nhận lại`).
6. **Bấm lại không trùng**: cửa / cửa sổ đã có tag (bất kỳ family nào) trong view thì bỏ qua. Không xoá gì.

## Thuật toán đặt tag (`TagCua_TuDong.py`)
- Làm trong hệ toạ độ view: u = `RightDirection`, v = `UpDirection` (đúng cả view xoay).
- **Vật cản (đa giác lồi 2D)**:
  - Tường thẳng: hình chữ nhật dấu chân theo hình học thật (đúng cả khi location line lệch tâm); tường cong lấy khung bao.
  - Cột: khung bao.
  - Cửa đi / cửa sổ: hình chữ nhật theo hệ (Hand, Facing) bao toàn bộ hình học trong view, gồm nét 2D cánh mở.
  - `IndependentTag`, `TextNote`, `SpatialElementTag` có sẵn: khung bao.
  - Tag mới đặt được thêm vào danh sách vật cản.
  - Kiểm giao bằng định lý trục tách (SAT), lọc trước theo khung bao những vật cản ở gần.
- **Kích thước tag**: tạo tag tại điểm đặt cửa, đo `get_BoundingBox(view)`, rồi dời `TagHeadPosition` (có bù độ lệch
  giữa tâm khung và đầu tag).
- **Ứng viên**: lưới quanh cửa, cả hai phía tường.
  - Theo phương vuông tường: từ mặt tường host (đo theo hình học) + khe + nửa bề dày tag, bước nửa bề dày tag, xa nhất
    15 mm giấy qua mép tường / cánh.
  - Theo dọc tường: bước nửa bề dài tag, tới ½ dấu chân + 3 lần nửa bề dài tag.
  - Điểm = khoảng cách ra khỏi tường + ½ độ dịch dọc tường + phạt 8 mm giấy nếu ở phía không ưu tiên. Xếp tăng dần, lấy
    chỗ trống đầu tiên.
  - Ứng viên ra ngoài vùng crop (khi crop bật) bị bỏ. Không còn chỗ trống thì đặt chỗ ít đè nhất và liệt kê "CẦN XEM LẠI".
  - Khe mặc định 1 mm giấy (IN[9]).
- Toàn bộ nằm trong 1 transaction `ARV - Tag cửa`, Ctrl+Z một lần là hoàn tác. Dry-run đặt thử trong `SubTransaction`
  rồi huỷ.
- Log `tag_cua_<ngày giờ>_<view id>.txt`: báo cáo + "CHI TIẾT VỊ TRÍ" (ứng viên được chọn và lý do bỏ các ứng viên trước
  đó), dùng để soát khi tag nằm xa cửa.

## Tệp
- Lõi: `scripts\dynamo\TagCua_TuDong.py` (Python node PythonNet3). Spec `TagCua_TuDong.json`, sinh `.dyn` bằng
  `python scripts\dynamo\build_dyn.py scripts\dynamo\TagCua_TuDong.json`.
- Nút: `scripts\pyrevit\...\HoSo.panel\TagCua.pushbutton`. Đây là file SINH, không sửa tay; khai báo trong `BUTTONS` +
  `MOT_CHAM` (`tu_khoa` rỗng = mặt bằng đang mở) của `build_from_dynamo.py`. Sinh lại bằng:
  `python scripts\pyrevit\build_from_dynamo.py "<gốc>\file mau revit\dynamo" --chi TagCua` (đặt
  `PYTHONIOENCODING=utf-8` nếu chạy trong Git Bash).
- Bấm: tag luôn trên view đang mở. View phải là Floor / Structural Plan có level; không phải thì nút báo và không làm gì.
  Shift+bấm: hộp thoại 11 ô, Dry-run bật sẵn.
- Khảo sát chỉ đọc: `TagCua_KhaoSat.dyn` (family tag, cửa, tag có sẵn, view) và `TagCua_KhaoSat2.dyn` (cửa sổ, EI, nội
  bộ family tag, kích thước tag, template).

## Thử trên bản sao G19 (2026-11-02)
- **Dynamo** (`_tmp\revit_tagcua\thu1\`, chạy `chay_dynamo_ui.ps1`):
  - `Tầng 1` (1:100): 93 cửa đi + 44 cửa sổ + 17 lam, bỏ qua 1 cửa đã có tag mẫu; 139 / 154 tag nằm ở phía ưu tiên;
    không tag nào đè. Bấm lần 2 không tạo thêm. Tạo template `Floor Plan (ẩn nội thất)`.
  - `CH01 - MB LÁT SÀN` (1:60, không template): 4 + 1 + 2 tag, tạo template `CH01 - MB LÁT SÀN (ẩn nội thất)`.
- **Nút pyRevit** (`_tmp\pyrevit_tagcua\`, nút thử `ARVTestCT` chạy nguyên `script.py`, journal + `chay_test.ps1`; thêm
  Extension Search Path khi thử, xong `forget`): kết quả như trên, ~5 giây mỗi lần bấm. Bản lưu
  `_tmp\pyrevit_tagcua\G19_tag_cua_thu.rvt`, ảnh `_tmp\pyrevit_tagcua\Tang1_tag_cua_*.png`.
- Người dùng chưa bấm thử trong Revit của mình, chưa duyệt vị trí tag (`Cần xác nhận lại`).

## Bẫy đã gặp
- Tên view trùng ("Tầng 1" có cả Floor Plan, Ceiling Plan, Structural Plan): tra theo tên thì ưu tiên Floor Plan; nếu
  view đang mở trùng tên thì lấy đúng view đang mở (nút một chạm truyền tên view đang mở).
- `View.Duplicate` trên view template báo lỗi, nên dùng `CreateViewTemplate()`.
- Tường hoàn thiện mỏng ốp sát tường host: ứng viên sát mặt tường host bị đè. Lưới ứng viên lùi dần theo bước nửa bề
  dày tag nên vẫn tìm được chỗ.
