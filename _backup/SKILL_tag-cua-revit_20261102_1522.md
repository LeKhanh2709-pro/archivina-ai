---
name: tag-cua-revit
description: 'Tag cửa Revit – Tự động tag cửa đi (AV_Door Tag) và cửa sổ (AV_Window Tag) trên mặt bằng Revit đang mở: bỏ đối tượng có Type Comments Louver; tag hiện đúng Type Mark (bỏ tiền tố S3. trong nhãn family); tag nằm ngang, ưu tiên ngay giữa cửa, không đè lên cửa (kể cả cánh mở), cửa sổ, tường, cột, chữ / tag khác; tag lệch khỏi giữa cửa thì có leader; nội thất thì ẩn bằng view template riêng "<template gốc> (ẩn nội thất)"; cửa có EI mà tag không hiện EI thì báo; bấm lại không tạo trùng. Nút pyRevit ARV Tools > Hồ sơ > Tag cửa (một chạm) + graph Dynamo TagCua_TuDong.dyn. Dùng khi người dùng nhờ "tag cửa", "đánh ký hiệu cửa trên mặt bằng Revit", "tag cửa sổ", "tag tự động không đè", hoặc sửa / thử nút Tag cửa.'
---

# Tag cửa Revit (Archivina)

Người dùng là kiến trúc sư, dùng nút **ARV Tools → Hồ sơ → Tag cửa** (pyRevit, Revit 2027) trên mặt bằng đang mở.
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit của người dùng.

## Quy tắc
Chốt 2026-11-02 sáng (8 câu hỏi), sửa theo góp ý của người dùng 2026-11-02 trưa (có ảnh mẫu).

1. **Family tag**:
   - Cửa đi dùng `AV_Door Tag`, cửa sổ dùng `AV_Window Tag`.
   - Cửa sổ có tên family / type chứa `Lam` / `Louver` thì dùng `AV_Louver Tag`; ít gặp vì các đối tượng này thường đã bị
     loại ở quy tắc 2.
   - Thiếu family thì báo và bỏ qua hạng mục đó, không tự load.
2. **Không tag đối tượng có Type Comments `Louver`** (IN[11], so không phân biệt hoa thường / dấu). G19 có 17 lam
   `AV-Lam Thép Logia2`.
   - Tag đang gắn trên các đối tượng này thì liệt kê trong báo cáo.
   - Chỉ xoá khi bật IN[15] (ô có chữ "Xoá": Shift+bấm, tích ô rồi xác nhận).
3. **Tag hiện đúng Type Mark, không tiền tố**. Nhãn family cũ là `S3.` + Type Mark.
   - Revit 2027.3 đọc được định dạng nhãn (`AnnotationLabel.GetParameterFormatting`) nhưng KHÔNG sửa được:
     - gán `Prefix` không ăn;
     - `SetParameterFormatting` / `AnnotationLabel.Create` có trong RevitAPI.xml nhưng chưa công khai.
   - Cách làm: thay nhãn. Chép một nhãn "Type Mark trơn" (1 tham số Type Mark, không tiền tố / hậu tố) từ family tag
     CÙNG hạng mục trong dự án sang (G19: `AV_Door Tag_Full`, `AV_Window Tag_Full`).
     - Chép view sang view (nhãn là đối tượng theo view), kèm `IDuplicateTypeNamesHandler` = dùng kiểu đích. Thiếu handler
       thì hộp thoại Duplicate Types làm treo Revit.
     - Đặt nhãn mới đúng `Coord` / `Width` / căn lề / kiểu chữ của nhãn cũ, xoá nhãn cũ.
     - Nạp lại family bằng `IFamilyLoadOptions` (tên lớp .NET đặt riêng mỗi lần).
   - Không có nhãn nguồn thì báo cách sửa tay: Edit Family → Edit Label → xoá Prefix. Lỗi ở family nào thì báo rồi đi tiếp.
   - Tag đã có trong dự án đổi chữ theo, vd. view CH01 cũng thành `DG17`.
4. **Vị trí**: tag nằm ngang, ưu tiên NGAY GIỮA cửa (theo ảnh mẫu `DG26` người dùng gửi).
   - Cửa đi ưu tiên phía KHÔNG mở cánh. Phía mở cánh là phía dấu chân cửa (hình học trong view, gồm cung cánh) dài hơn.
   - Cửa sổ ưu tiên phía ngoài (+FacingOrientation).
   - Không đè lên cửa (gồm cánh mở), cửa sổ, tường, cột, tag / chữ có sẵn và tag vừa đặt.
5. **Leader** (theo ảnh mẫu `DG20` người dùng bật Leader Line):
   - Tag lệch khỏi giữa cửa, hoặc cách mặt tường quá 1 bề cao tag, thì bật `HasLeader`, `LeaderEndCondition.Attached`
     (gắn vào cửa).
   - Tag ngay giữa cửa thì không leader.
   - IN[13] = luôn bật leader.
6. **Nội thất không né mà ẩn**: tạo view template `<template gốc> (ẩn nội thất)`; view chưa có template thì
   `<tên view> (ẩn nội thất)`. Ẩn `OST_Furniture; OST_FurnitureSystems; OST_Casework; OST_SpecialityEquipment;
   OST_PlumbingFixtures`, rồi gán cho view.
   - KHÔNG sửa template gốc. API không `Duplicate` được view template, nên dùng `view.CreateViewTemplate()`.
   - Bật điều khiển V/G Model; không ẩn Door Tags / Window Tags.
   - Template tên đó đã có thì dùng lại.
   - Việc ẩn cả Plumbing Fixtures: `Cần xác nhận lại` với người dùng.
7. **EI**: cửa có giá trị chống cháy (`Fire Rating; EI; Giới hạn chịu lửa`, instance trước) mà `TagText` không chứa giá
   trị đó thì báo.
   - `AV_Door Tag` chưa có nhãn chống cháy; G19 không có cửa EI.
   - Cách hiện EI chưa chốt (`Cần xác nhận lại`). API 2027.3 không tạo được nhãn mới; có thể chép nhãn Fire Rating từ
     family khác như quy tắc 3, nếu dự án có family như vậy.
8. **Bấm lại không trùng**: cửa / cửa sổ đã có tag (bất kỳ family nào) trong view thì bỏ qua.
   - IN[14] = dời lại các tag đã có cùng family tag theo quy tắc mới. Không xoá, không tạo mới.
   - Dùng IN[14] khi view đã tag bằng bản cũ; tag người dùng đã chỉnh tay cũng bị dời, nên mặc định tắt.

## Thuật toán đặt tag (`TagCua_TuDong.py`)
- Làm trong hệ toạ độ view: u = `RightDirection`, v = `UpDirection`.
- **Vật cản (đa giác lồi 2D)**:
  - Tường thẳng: hình chữ nhật dấu chân theo hình học thật; tường cong lấy khung bao.
  - Cột: khung bao.
  - Cửa đi / cửa sổ (kể cả đối tượng bị loại): hình chữ nhật theo hệ (Hand, Facing) bao toàn bộ hình học trong view.
  - Tag / TextNote / Room tag có sẵn: khung bao.
  - Tag mới thêm vào danh sách vật cản. Tag bị dời / xoá thì bỏ khỏi danh sách.
  - Kiểm giao bằng SAT, lọc trước theo khung bao.
- **Kích thước tag**: đặt tag (không leader) tại điểm đặt cửa, đo `get_BoundingBox(view)`, rồi dời `TagHeadPosition`
  (bù lệch tâm). Bật leader thì đặt lại head sau khi bật.
- **Ứng viên**: lưới quanh cửa, cả hai phía tường.
  - Theo phương vuông tường: từ mặt tường host + khe + nửa bề cao tag, bước nửa bề cao tag, xa nhất 15 mm giấy qua mép
    tường / cánh.
  - Theo dọc tường: bước nửa bề dài tag, tới ½ dấu chân + 3 nửa bề dài tag.
  - Điểm = lùi xa + 4 × dịch khỏi giữa cửa + phạt 8 mm giấy nếu ở phía kia. Xếp tăng dần, lấy chỗ trống đầu tiên.
  - Ra ngoài crop thì bỏ. Không còn chỗ trống thì đặt chỗ ít đè nhất, ghi "CẦN XEM LẠI". Khe 1 mm giấy (IN[9]).
- Bỏ tiền tố nhãn chạy TRƯỚC, ngoài transaction (EditFamily / LoadFamily), sau đó lấy lại kiểu tag. Phần còn lại nằm
  trong 1 transaction `ARV - Tag cửa`. Dry-run: đặt thử trong `SubTransaction` rồi huỷ, nhãn chỉ báo "sẽ bỏ".
- Log `tag_cua_<ngày giờ µs>_<view id>.txt`: báo cáo + "CHI TIẾT VỊ TRÍ" (ứng viên được chọn, lý do bỏ ứng viên trước).

## Tệp
- Lõi: `scripts\dynamo\TagCua_TuDong.py` (16 ô IN). Spec `TagCua_TuDong.json`, sinh `.dyn` bằng
  `python scripts\dynamo\build_dyn.py scripts\dynamo\TagCua_TuDong.json`.
- Nút: `scripts\pyrevit\...\HoSo.panel\TagCua.pushbutton` là file SINH, không sửa tay; khai báo trong `BUTTONS` +
  `MOT_CHAM` (`tu_khoa` rỗng) của `build_from_dynamo.py`. Sinh lại bằng:
  `python scripts\pyrevit\build_from_dynamo.py "<gốc>\file mau revit\dynamo" --chi TagCua` (Git Bash: đặt
  `PYTHONIOENCODING=utf-8`).
- Bấm: chạy trên view đang mở (Floor / Structural Plan có level). Shift+bấm: hộp thoại 16 ô, Dry-run bật sẵn; ô Xoá
  luôn tắt lại mỗi lần mở.
- Khảo sát chỉ đọc: `TagCua_KhaoSat.dyn`, `TagCua_KhaoSat2.dyn`.

## Thử trên bản sao G19 (2026-11-02)
- **Bản 2, Dynamo** (`_tmp\revit_tagcua\thu2\`), chạy trên bản sao ĐÃ tag bằng bản 1, giống model người dùng:
  - Chạy mặc định: bỏ tiền tố ở cả 3 family, liệt kê 17 tag lam, không tạo trùng.
  - Bật đặt lại + xoá: xoá 17 tag lam, dời 137 tag (36 có leader).
  - Chạy lại: không đổi gì.
  - Chữ tag: `DG16…DG29`, `32…37`. Không tag nào đè.
- **Bản 2, nút pyRevit** trên G19 sạch (`_tmp\pyrevit_tagcua\`):
  - Tầng 1: 93 cửa đi + 44 cửa sổ, 34 có leader, không tag 17 lam. Bấm lần 2 không thêm.
  - Ảnh `_tmp\pyrevit_tagcua\Tang1_tag_cua_v2_*.png`, bản lưu `G19_tag_cua_thu.rvt`.
- Bản 1 (sáng): `_tmp\revit_tagcua\thu1\`.
- Người dùng chưa bấm thử bản 2 (`Cần xác nhận lại`).

## Bẫy đã gặp
- Tên view trùng ("Tầng 1" có Floor / Ceiling / Structural Plan): ưu tiên Floor Plan; view đang mở trùng tên thì lấy
  đúng view đang mở.
- `View.Duplicate` trên view template báo lỗi.
- Tường hoàn thiện mỏng ốp sát tường host: ứng viên sát tường bị đè; lưới lùi dần nên vẫn tìm được chỗ.
- `AnnotationLabelParameterFormatting.ParameterId` không có trên 2027.3: dùng `GetParameterDefinition(famDoc)
  .BuiltInParameter`.
- `CopyElements` doc → doc báo "view-specific": phải dùng bản View → View.
- Chép nhãn tag cửa sang family tag cửa sổ bị lỗi "Copying one or more elements failed": lấy nhãn nguồn cùng hạng mục.
- Sau `LoadFamily`, đối tượng `Family` cũ không dùng được nữa: lấy tên trước.
- Dynamo: hộp thoại "Open external file?" có khi là cửa sổ cấp cao của Revit, không nằm trong cửa sổ Dynamo.
  `chay_dynamo_ui.ps1` đã tìm ở mọi cửa sổ của tiến trình (`Bam-Yes-TienTrinh`).
