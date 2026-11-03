---
name: tag-cua-revit
description: 'Tag cửa Revit – Tự động tag cửa đi (AV_Door Tag) và cửa sổ (AV_Window Tag) trên mặt bằng Revit đang mở: bỏ đối tượng có Type Comments Louver; tag hiện đúng Type Mark (bỏ tiền tố S3. trong nhãn family); tag nằm ngang, ưu tiên ngay giữa cửa, không đè lên cửa (kể cả cánh mở), cửa sổ, tường, cột, chữ / tag khác; tag lệch khỏi giữa cửa thì có leader; nội thất thì ẩn bằng view template riêng "<template gốc> (ẩn nội thất)"; cửa có EI mà tag không hiện EI thì báo; bấm lại không tạo trùng. Nút pyRevit ARV Tools > HS TKBVTC > Định vị + tag cửa (một chạm: tạo / mở mặt bằng định vị cửa "MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>", template "MẶT BẰNG ĐỊNH VỊ CỬA" tường + sàn Halftone, ẩn nội thất / thiết bị vệ sinh / Mechanical Equipment, rồi tag trên đó) + graph Dynamo TagCua_TuDong.dyn. Dùng khi người dùng nhờ "tạo mặt bằng định vị cửa", hoặc khi người dùng nhờ "tag cửa", "đánh ký hiệu cửa trên mặt bằng Revit", "tag cửa sổ", "tag tự động không đè", hoặc sửa / thử nút Tag cửa.'
---

# Tag cửa Revit (Archivina)

Người dùng là kiến trúc sư, dùng nút **ARV Tools → HS TKBVTC → Tag cửa** (pyRevit, Revit 2027) trên mặt bằng đang mở.
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

## Gộp vào 1 nút `Định vị + tag cửa` (người dùng yêu cầu 2026-11-03)
- Bấm trên mặt bằng tầng: tạo / mở `MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>` rồi tag luôn trên view đó (`TagCua_TuDong.py`
  IN[16] – IN[18], hàm `mb_dinh_vi_cua`). View gốc đã là mặt bằng định vị cửa (mang template / tên theo mẫu) thì tag luôn.
- Template `MẶT BẰNG ĐỊNH VỊ CỬA` ẩn thêm **Mechanical Equipment** (người dùng chốt 2026-11-03, `MB_AN_THEM`); template
  đã có trong dự án cũng được bổ sung ẩn (chỉ ẩn thêm, không đổi gì khác).
- Nút `MB định vị cửa` riêng đã bỏ (thư mục nút chuyển vào `_backup\MBDinhViCua.pushbutton_20261103_1108_da_gop_vao_TagCua`);
  `MatBang_DinhViCua.py/.dyn` giữ để chạy riêng bằng Dynamo, không cập nhật thêm.
- Thử bản sao G19 (`_tmp\revit_tagcua\thu3\`) với mặc định của nút: tạo view + template (ẩn cả Mechanical Equipment),
  94 cửa đi + 44 cửa sổ, 35 leader, không đè; bấm lần 2 không thêm. Đã build nút 2026-11-03; người dùng chưa bấm thử
  (`Cần xác nhận lại`).

## Tag khung 2 ô "mã / rộngXcao" (người dùng yêu cầu 2026-11-03, đang làm, mặc định TẮT – IN[19])
Mẫu CAD người dùng: khung chữ nhật chia 2 ô bằng 1 nét ngang, ô trên `DF03`, ô dưới `1400X2195` (mm, lấy tham số
**Width** và **Height** của cửa). Hàm `them_kich_thuoc` + `ve_khung_2_o`:
- Khung: tắt khung bo góc cũ (tham số hiện khung của family = 0), vẽ 5 detail line (chữ nhật 17 × 8 mm giấy + nét giữa).
  Nạp lại family với `tuy_chon_nap(True)` (lấy giá trị tham số của family, không thì dự án giữ giá trị cũ).
- Ô dưới: nhãn Width (căn phải) + TextNote `X` + nhãn Height KHÔNG tiền tố (căn trái); nhãn gộp Width + Height có sẵn
  trong dự án (người dùng tự sửa) được ưu tiên. Đơn vị Length của file family tag đặt mm / 0 số lẻ.
- API 2027.3 KHÔNG tạo được nhãn, KHÔNG đổi được đơn vị / tiền tố nhãn (`AnnotationLabelParameterFormatting` không có
  setter; `GetParameterFormatOptions(paramId)` luôn báo "default", không tin được). Phải chép nhãn có sẵn đúng định dạng:
  - Width của `AV_Door Tag_Full` khoá theo mét ("0.740"), đổi đơn vị family không ăn → KHÔNG dùng được cho mm.
  - Height mm không tiền tố: `AV-Tag-Window-Lomo.rfa` (thư viện người dùng, đã chép vào
    `scripts\pyrevit\ARVTools.extension\lib\tag_cua\`); đổi tạm hạng mục family nguồn thì chép được cả sang tag cửa đi.
  - Width mm không tiền tố: CHỈ có nhãn `B1` của family `AV-Tag-Window-Lomo` trong `D:\khanh\21.8.2025\FPT P4_A_L1-L2_…rvt`
    (448 MB); mở bản sao bị treo khi máy thiếu RAM. Có file này (`_tmp\revit_tagcua\nguon\tao_nguon.py` dựng
    `ARV_TagNguon_Door/Window.rfa`) thì bật IN[19] mặc định.
  - Mượn nhãn Description KHÔNG được: Description của 22 loại cửa đi / 17 loại cửa sổ G19 đang chứa mô tả vật liệu.
- Ảnh thử khung 2 ô: `_tmp\revit_tagcua\thu3\lan4\` (ô dưới còn "0.740 X 2500"). Người dùng chưa duyệt.

## Mặt bằng định vị cửa (nút `MB định vị cửa`, 2026-11-02 chiều – ĐÃ GỘP vào nút Tag cửa 2026-11-03)
Người dùng yêu cầu tạo mặt bằng mới từ mặt bằng đã cho, template tên `MẶT BẰNG ĐỊNH VỊ CỬA`, sàn và tường như ảnh mẫu.
Ảnh mẫu là view mang template `1.8  Mặt Bằng Chống Cháy Lan` (mọi hạng mục Halftone). Lõi
`scripts\dynamo\MatBang_DinhViCua.py` (9 ô IN):
1. Nhân bản mặt bằng đang mở bằng `Duplicate`, không kèm chú thích / filled region (hatch chống cháy lan không theo
   sang). Tên mặc định `MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>`. View tên đó đã có thì không tạo thêm, chỉ mở view đó.
2. Template `MẶT BẰNG ĐỊNH VỊ CỬA` đã có thì dùng nguyên, không sửa. Chưa có thì tạo:
   - Nền = template của view gốc, tức đồ hoạ người dùng đang thấy. IN[2] có từ khoá thì lấy template mặt bằng có chữ
     đó, ưu tiên cùng tỉ lệ.
   - Tường, sàn: Halftone. Sàn: tắt mẫu tô bề mặt.
   - Cửa đi, cửa sổ: bỏ Halftone để cửa nét đậm. Đây là Claude tự chọn vì người dùng chỉ nêu sàn + tường
     (`Cần xác nhận lại`); muốn cửa xám như ảnh thì để trống IN[8].
   - Ẩn nội thất + thiết bị vệ sinh; hiện cửa, cửa sổ và tag của chúng.
3. Mở view mới (`RequestViewChange`). Bấm `Tag cửa` tiếp trên view này thì Tag cửa dùng luôn template đó, vì template đã
   ẩn đủ nội thất (`gan_template` → `da_an_du`), không tạo thêm `(ẩn nội thất)`.
- Nút `ARV Tools` → `HS TKBVTC` → `MB định vị cửa`: một chạm trên mặt bằng tầng đang mở (`MOT_CHAM` từ khoá rỗng),
  Shift+bấm = hộp thoại (Dry-run). Khảo sát chỉ đọc: `MBCua_KhaoSat.dyn`.
- Thử bản sao G19 (`_tmp\revit_mbcua\thu3\`), view gốc `Level 1 Copy 1 Copy 2 Copy 1` (template 1.8):
  - Kết quả: tạo view + template, bấm lại không trùng, Tag cửa trên view mới cho 94 cửa đi + 44 cửa sổ, không thêm
    template.
  - Ảnh `view - Floor Plan - MẶT BẰNG ĐỊNH VỊ CỬA - Tầng 1.png`, bản lưu `G19_mb_dinh_vi_cua_thu.rvt`.
  - Vỏ nút pyRevit chưa bấm thử; người dùng chưa duyệt (`Cần xác nhận lại`).
- Bẫy:
  - `CreateViewTemplate` lấy thiết lập của view, chưa theo template vừa gán. Phải `doc.Regenerate()` sau khi gán
    `ViewTemplateId`.
  - `ApplyViewTemplateParameters` làm Revit 2027.3 lỗi nặng khi vẽ lại tường trong view (thử 2, `thu2\`): không dùng.

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
