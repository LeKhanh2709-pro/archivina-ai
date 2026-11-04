---
name: chi-tiet-cua-revit
description: 'Chi tiết cửa Revit – Chọn 1 cửa đi / cửa sổ (family có sẵn) trên Revit, tự tạo MẶT BẰNG (callout), MẶT ĐỨNG (nhìn từ ngoài nhà; cửa trong nhà nhìn từ phía không mở cánh), MẶT CẮT (cắt qua cánh, ngoài nhà bên phải) tỉ lệ 1/25 kèm kích thước tổng, đặt vào ô trống tiếp theo của sheet "CHI TIẾT CỬA" (khung A1 chia 6 ô 2 × 3, dải trống dưới mỗi ô để người dùng tự điền ký hiệu, vật liệu, phụ kiện; hết ô thì tạo sheet mới, số sheet tăng tiếp). View template "CHI TIẾT CỬA - MẶT BẰNG / MẶT ĐỨNG / MẶT CẮT" tạo từ template 1/25 có sẵn. Mỗi type cửa chỉ làm 1 lần. Nút pyRevit ARV Tools > HS TKBVTC > Chi tiết cửa (một chạm) + graph Dynamo ChiTietCua_TuDong.dyn. Dùng khi người dùng nhờ "triển khai chi tiết cửa", "chi tiết cửa Revit", "mặt đứng / mặt cắt cửa 1/25", "sheet chi tiết cửa", hoặc sửa / thử nút Chi tiết cửa.'
---

# Chi tiết cửa Revit (Archivina)

Người dùng là kiến trúc sư, chọn 1 cửa trên Revit 2027 rồi bấm **ARV Tools → HS TKBVTC → Chi tiết cửa** (pyRevit). Mẫu cần
đạt: tờ A1 "CHI TIẾT CỬA" (ảnh người dùng gửi 2026-11-03, ký hiệu A.CD.22.13) gồm 6 ô, mỗi ô có mặt đứng, mặt cắt,
mặt bằng + bảng thông tin. Công cụ CHỈ dựng 3 view và chia ô; thông tin cửa người dùng tự điền.
Claude sửa công cụ và tự thử trên BẢN SAO `.rvt` trong `<gốc>\_tmp\`, không đụng model đang mở trong Revit của người dùng.

## Quy tắc (người dùng chốt 2026-11-03)
1. **Đầu vào**: 1 hoặc NHIỀU cửa đi / cửa sổ, family có sẵn (người dùng chốt 2026-11-03 tối: chọn nhiều cửa trước rồi
   bấm nút). Các cửa đang chọn (bỏ qua đối tượng khác); chưa chọn thì chọn trên màn hình (PickObjects, Finish). Làm lần
   lượt, xếp tiếp các ô; cửa trong link không chọn được. Nút pyRevit hiện **bảng hỏi** trước khi chạy (`lib\
   arv_hoi_sheet.py` → `hoi_chi_tiet_cua`, dùng chung `_bang` với Tag cửa): dòng "Đã chọn N cửa", giai đoạn, hạng mục
   (gõ mới = thêm), khổ giấy A1 / A0 → khung tên, số hiệu, tên bản vẽ (mặc định `CHI TIẾT CỬA`); nhớ lần trước ở
   `%APPDATA%\pyRevit\ARVTools\ChiTietCua_sheet.json`. Số hiệu gợi ý = sheet chi tiết cửa của công cụ cùng tên + giai
   đoạn + hạng mục số lớn nhất còn ô trống; không có thì số tiếp theo trong hạng mục; trống = công cụ tự đánh số.
2. **3 view, tỉ lệ 1/25**, tên `CT CỬA <Type Mark> - MẶT BẰNG / MẶT ĐỨNG / MẶT CẮT` (Type Mark trống thì dùng tên type),
   Title on Sheet = `MẶT BẰNG` / `MẶT ĐỨNG` / `MẶT CẮT 1-1`. Khung nhìn = hình family + lề 300 mm; mặt đứng / mặt cắt lấy
   xuống tới sàn (cửa sổ thấy cả bậu).
   - **Mặt bằng**: callout trên mặt bằng tầng của cửa (ưu tiên view đang mở nếu đúng tầng, rồi view tên = tên level).
     Khung callout trên mặt bằng gốc ẩn bằng Hide in View; ký hiệu section trong mặt bằng chi tiết cũng ẩn (như mẫu).
     **Mặt bằng XOAY theo mặt đứng** (người dùng chốt 2026-11-03): phía phải mặt bằng = phía phải mặt đứng, ngoài nhà
     ở dưới (cửa trên tường phương Y / tường xiên cũng nằm ngang).
   - **Mặt đứng nhìn từ NGOÀI NHÀ**: một bên không có room → bên đó; cả hai bên có room → bên có tên lô gia / ban công /
     sân; không rõ → cửa có cung mở thì nhìn từ phía KHÔNG mở cánh; còn lại theo Facing của family (G19: Facing của cửa
     sổ / cửa lô gia hướng ra ngoài). Ô IN[11] ép `facing` / `nguoc`.
   - **Mặt cắt**: vuông góc tường, cắt qua cánh (cách tâm cửa 1/4 bề rộng), ngoài nhà bên phải.
   - **Mặt đứng CHỈ CÓ CỬA** (người dùng chốt 2026-11-03): tường, sàn, phần tử model khác Hide in View (giữ cửa +
     family lồng). Level ẩn trên mặt đứng + mặt cắt; mặt phẳng tham chiếu / scope box / lưới trục ẩn ở cả 3 view.
   - **Cốt sàn thay level** (như mẫu người dùng gửi): cao độ = mặt trên sàn trong nhà (không có thì ngoài nhà, cuối
     cùng level). **Nét đứt suốt bề rộng ô** vẽ trên SHEET (line style tên có "khuất" / "đứt", G19 `AV.Nét Khuất.W1`)
     qua cả mặt đứng + mặt cắt (đã gióng cùng cao độ); trong mỗi view có nét sàn kiểu `<Invisible lines>` chỉ để dim bám.
     Chữ đúng `CỐT SÀN HOÀN THIỆN` (KHÔNG thêm tên phòng; kiểu chữ mặc định, mũi tên chỉ xuống nét) bên trái mặt cắt,
     NGOÀI khung cắt (vùng annotation crop trái nới rộng) để không đè tường.
   - **Mặt bằng chỉ hiện cửa + tường** (người dùng chốt 2026-11-03 tối): sàn, cửa khác, đồ đạc Hide in View; khung nhìn
     trùm HẾT hình mặt bằng của cửa (cả cung mở cánh, lấy hình theo view gốc), lề 150.
   - Ký hiệu / khung callout của mọi view `CT CỬA ...` ẩn trong nhau, kể cả view đã làm trước (khung callout cửa làm sau
     hiện trên mặt bằng chi tiết cửa làm trước nếu 2 cửa gần nhau).
   - **Kiểu view riêng** (Project Browser có mục riêng): Floor Plan `CT CỬA`, Section `MẶT CẮT CỬA` (cả mặt đứng + mặt
     cắt); chưa có thì chép từ kiểu của mặt bằng gốc / kiểu Section. **Viewport** kiểu `AV-Title No Line` (không có
     thì giữ mặc định và báo).
3. **Kích thước tổng**: mặt bằng = rộng; mặt đứng = rộng (DƯỚI CHÂN, dưới đuôi ký hiệu mặt cắt 5 mm giấy – người dùng
   chốt 2026-11-04) + cao (bên phải); mặt cắt = cao. Cửa sổ: chuỗi sàn →
   bậu → đỉnh. Reference: family (Left / Right / Top / Bottom) → không có thì mặt lỗ mở của tường (mép, đỉnh, bậu);
   trên MẶT ĐỨNG (tường đã ẩn) lấy mặt trong hình cửa gần mép / đỉnh / bậu lỗ tường nhất (≤ 60 mm); chân = nét cốt sàn
   của từng view.
4. **View template**: `CHI TIẾT CỬA - MẶT BẰNG`, `- MẶT ĐỨNG`, `- MẶT CẮT`. Đã có thì dùng nguyên, KHÔNG sửa. Chưa có thì
   tạo từ template nền theo từ khoá IN[9] (G19: `3.1 Chi Tiết Mặt Bằng`, `3.2 Chi Tiết Mặt Đứng`, `3.3 Mặt Cắt Chi
   tiết`), không có thì template cùng tỉ lệ 1/25; đặt 1/25, Fine, ẩn nội thất + thiết bị vệ sinh + lưới trục; Far Clipping
   và crop để view tự giữ.
5. **Sheet "CHI TIẾT CỬA"**: khung `AV-Khung A1(841x594)-Kien Truc`, vùng vẽ (trong viền, trái dải khung tên) chia 6 ô
   2 hàng × 3 cột bằng Detail Line, mỗi ô có dải 22 % chiều cao phía dưới để điền thông tin. Trong ô: mặt đứng trên trái,
   mặt cắt bên phải (gióng sàn), mặt bằng dưới mặt đứng (gióng tâm cửa).
   - CHỈ đặt view vào sheet do công cụ tạo (có group lưới `ARV_ChiTietCua_Luoi <số sheet>`). Sheet người dùng tự làm dù
     trùng tên (G19: `A.7-101 CHI TIẾT CỬA`) không đụng tới.
   - Giai đoạn / hạng mục (IN[16] / IN[17]) chọn thì chỉ dùng sheet cùng giai đoạn + hạng mục, sheet mới được gán 2 giá
     trị đó (tham số theo cấp nhóm Project Browser, cách tìm như Tag cửa: `cap_thu_muc_sheet` / `ts_giai_doan`).
   - Số hiệu IN[3] có: xếp vào sheet đó (của công cụ, còn ô) rồi các sheet cùng tiền tố số lớn hơn; hết ô thì tạo sheet
     số đó / số tiếp theo chưa dùng. IN[3] trống: số lớn nhất của các sheet tên đó + 1 (G19: A.7-101 → A.7-102), chưa có
     thì `A.CD.01`.
6. **Mỗi type làm 1 lần**: đã có view `CT CỬA <mark> - ...` thì báo sheet chứa nó, không tạo thêm (chọn 2 cửa cùng type
   thì cửa sau báo đã có).
7. Không xoá, không sửa cửa / tường / view gốc / template đã có. Nút pyRevit gom cả lượt nhiều cửa trong 1
   TransactionGroup → Ctrl+Z một lần là hoàn tác hết; lỗi giữa chừng thì hoàn tác toàn bộ lượt.
8. **Ẩn level ở mặt đứng + mặt cắt**: tắt hạng mục Levels của view (bắt cả level file link; template mới cũng ẩn
   Levels) + Hide in View từng level của dự án.
9. **Vết cắt = ký hiệu SECTION của Revit** (người dùng chốt 2026-11-04 "vết cắt thể hiện bằng section"; thay vạch +
   mũi tên + nét đứt vẽ tay của bản 2026-11-03): ký hiệu của mặt cắt KHÔNG ẩn trên mặt đứng. Khung mặt cắt sát chiều cao
   (min(chân cửa, cốt sàn) → đỉnh ± 3 mm giấy) để đường cắt chỉ dài bằng cửa. Kiểu `MẶT CẮT CỬA` (của công cụ) phải dùng
   section tag có đầu: G19 "Wall Section" dùng tag Head / Tail = none (chỉ có đường) → đổi sang tag của kiểu mặt cắt
   "chi tiết" (`AV_Section Detail`: đầu `AV_Section Head` có số chi tiết / số sheet, đuôi `AV_Section Tail_Filled`).
   Tên mặt cắt = `MẶT CẮT n-n`, n = số chi tiết của viewport mặt cắt (khớp số ở đầu ký hiệu). Khung mặt đứng: trên = đầu
   ký hiệu (chừa 12 mm giấy), dưới = đuôi (Height của family đuôi + 1 mm) + dim ngang. **Bẫy**: hộp viewport của mặt đứng
   tính cả hộp bao ký hiệu section (G19 ±603 mm ở 1/25, rộng hơn phần in ra ~8 mm giấy mỗi đầu) → xếp ô theo PHẦN THẤY
   (khung crop + 3 mm, `hop_ht`), dời tên view lên sát phần thấy (`Viewport.LabelOffset`), ô bị lấn > 10 mm mới coi là có
   view. Lần thử 2026-11-03 (ký hiệu section làm vượt ô) là do tính theo hộp viewport.
10. **Vách kính (curtain wall)** (người dùng yêu cầu 2026-11-03 tối: "áp dụng cho cả vách kính"): chọn vách, hoặc tấm
    kính / đố / cửa đi, cửa sổ làm tấm của vách (→ lấy vách chứa nó, trùng thì gộp). Cùng 3 view + sheet + bảng hỏi.
    - Tên `CT VÁCH KÍNH <Mark của vách> - ...` (type vách dùng chung nhiều vách → nhận theo Mark; trống thì
      `VK <dài>x<cao>`); mỗi Mark làm 1 lần. Vách cong: báo, không làm.
    - Khung: trục tường (H = phương đường định vị), ngoài nhà theo luật room như cửa, không rõ → phía không mở cánh của
      cửa trong vách → `Wall.Orientation`.
    - Mặt đứng giữ vách + mọi tấm + đố + lưới (ẩn phần tử khác). Mặt cắt qua giữa ô cửa sổ, không có thì ô cửa đi (lệch
      1/4), rồi ô kính gần giữa vách; nhìn sâu nửa ô + 150 mm.
    - Dim: mép = mặt ngoài đố biên (không có đố thì mặt tấm). Mặt đứng: chuỗi theo lưới đứng + tổng DƯỚI CHÂN (dưới
      đuôi ký hiệu mặt cắt 5 / 12 mm giấy), chuỗi sàn → (chân vách nếu cao hơn sàn) → lưới ngang → đỉnh + tổng bên phải
      (cách 9 / 16 mm giấy). Mặt bằng (người dùng yêu cầu 2026-11-04): chuỗi khoảng cách đố (trục đố = lưới đứng) + tổng
      phía ngoài nhà, cách 6 / 13 mm giấy, bám nét ẩn tại mép + trục đố (reference mặt đố biên theo view mặt bằng không
      ổn định: VK.11 mất đoạn cuối).
      Mặt cắt: sàn → đỉnh. Reference mặt đố lấy theo hình CỦA CHÍNH VIEW (mặt bằng / mặt cắt cắt qua đố: reference hình
      3D làm Revit xoá dim); dim mất (lúc tạo hoặc sau khi ẩn phần tử) thì dựng lại vào nét `<Invisible lines>` tại mép.
    - **Tỉ lệ GIỮ 1:IN[4]** (người dùng chốt 2026-11-04: "để tỉ lệ 1/25 sắp xếp cho phù hợp"; bản lùi 1/50 → 1/100
      đã bỏ). Ước lượng cụm 3 view trước khi tạo (khớp cụm thật ± 1 %); không lọt 1 ô thì chiếm KHỐI ô liền nhau
      2 × 1 → 3 × 1 → 2 × 2 → 3 × 2 (cột × hàng, ít ô trước) trên SHEET MỚI: lưới bỏ nét chia trong khối, 1 dải thông
      tin dưới hàng cuối khối, ô còn lại dùng tiếp cho cửa / vách nhỏ. Vẫn không lọt 3 × 2 → báo "VƯỢT KHỔ" (chia
      đoạn / xếp tay). Lề dưới mặt đứng vách kính chỉ chứa nét cắt + số 1 (40 mm + 1,1 chữ + 2 mm giấy).
    - Ô trống (cả cửa): ô có nét dải thông tin RIÊNG trong group lưới và không viewport nào lấn vào > 2 mm (thay cách
      cũ theo tâm viewport, để ô nằm trong khối ghép không bị dùng lại).

## File
- Lõi: `<gốc>\scripts\dynamo\ChiTietCua_TuDong.py` (graph `.dyn` sinh bằng `build_dyn.py ChiTietCua_TuDong.json`).
- Nút: sinh bằng `scripts\pyrevit\build_from_dynamo.py "file mau revit\dynamo" --chi ChiTietCua` (MOT_CHAM
  `khong_view`: không cần view, lõi tự lấy cửa; `hoi` = `arv_hoi_sheet.hoi_chi_tiet_cua`, gọi `(doc, view, uidoc)`);
  không sửa tay `ChiTietCua.pushbutton\`. Shift+bấm = hộp thoại đầy đủ, Dry-run (Dry-run nhiều cửa báo cùng ô vì
  không tạo sheet thật).
- `arv_hoi_sheet.py` dùng chung với nút Tag cửa (`hoi(doc, view)` → IN[21] – IN[27] của TagCua): sửa `_bang` thì thử
  cả 2 nút.

## Bẫy đã gặp (Revit 2027.3)
- `ViewSection.CreateSection`: view NHÌN THEO +BasisZ (ViewDirection = -BasisZ), mặt cắt ở Min.Z, cắt xa ở Max.Z,
  RightDirection = -BasisX. Bản đầu tưởng ngược lại nên mặt đứng nhìn từ trong nhà. Lõi kiểm lại ViewDirection /
  RightDirection sau khi tạo và báo CẢNH BÁO nếu lệch.
- Khung tên trên sheet: `get_Geometry` trả None (cả có / không View) → đọc nét trong family bằng `EditFamily` (ngoài
  transaction, đóng không lưu); nét viền có thể chia đoạn → cộng dồn chiều dài theo toạ độ.
- PythonNet3 không đọc được `Element.Name` của ElementType → đọc `SYMBOL_NAME_PARAM` / `ALL_MODEL_TYPE_NAME`.
- Family `D1_WO_OP1` (G19) không có reference Left / Right / Top → dim theo mặt lỗ tường.
- Bật Annotation Crop (lề 3 mm) cho 3 view, không thì ký hiệu section / đầu level ngoài khung làm viewport to ra, xếp
  sai ô. Offset annotation crop tính trên GIẤY (feet giấy), không phải model.
- Xoay mặt bằng = `ElementTransformUtils.RotateElement` phần tử crop của callout quanh trục Z tại tâm cửa, góc
  atan2(X_d) → RightDirection = X_d. Phần tử crop của callout mặt bằng: id = id view - 1, hạng mục **"Views"** (KHÔNG
  phải `OST_CropBoundary`); tìm bằng rule `ID_PARAM` = id view (bỏ chính view).
- Dim tham chiếu phần tử bị Hide in View thì MẤT khi regenerate → mặt đứng dim vào hình cửa (reference symbol đổi sang
  instance bằng chuỗi `<UniqueId>:0:INSTANCE:<ConvertToStableRepresentation>`) và vào nét cốt sàn.
- Detail Line thuộc hạng mục Lines = `CategoryType.Model` → khi ẩn "mọi phần tử model" phải bỏ qua `ViewSpecific`, không
  thì ẩn luôn nét cốt sàn và dim theo nó mất.
- Detail line bị model crop cắt (không hiện trong vùng annotation crop) → nét cốt sàn hiện vẽ trên sheet.
- `FilteredElementCollector(doc, view.Id)` KHÔNG trả Level → ẩn level bằng `OfClass(Level)` toàn dự án +
  `CanBeHidden` / `IsHidden`.
- Khung callout mặt bằng hiện trong view khác là phần tử crop hạng mục "Views" (không phải OST_Viewers).
- Graph `.dyn` ở thư mục mới: Dynamo có thể báo "Run blocked" (không hiện hộp thoại tin cậy) → chạy thử từ thư mục đã
  dùng (`_tmp\revit_ctcua\thu3\`).

## Cách thử
- Dynamo: `_tmp\revit_ctcua\thu2\chay_thu.py` (dry-run, 7 cửa → sang sheet thứ 2, bấm lại không trùng; xuất PNG, lưu
  bản sao), chạy bằng `_tmp\revit_g19\chay_dynamo_ui.ps1`.
- Nút pyRevit: `_tmp\pyrevit_ctcua\ARVTestCT.extension` (chọn sẵn cửa rồi exec `script.py` của nút); thêm vào Extension
  Search Path khi thử, xong `pyrevit extensions paths forget`.
- Kết quả 2026-11-03 trên bản sao G19: 7 cửa (trượt 2 cánh DG26, cửa đi 1 cánh DG16 / 17 / 20 / 21, cửa sổ 32 / 36),
  2 sheet A.7-102 / A.7-103, đủ dim. Bản 2 (xoay mặt bằng, mặt đứng chỉ cửa, cốt sàn): mặt bằng xoay 0 / 180 / -90°,
  mọi dim còn sau khi ẩn, 7 cụm đều nằm trong ô; ảnh `_tmp\revit_ctcua\thu3\`; nút thật (DG26, DG21, bấm lại)
  `_tmp\pyrevit_ctcua\kq\` (bản 1 ở `thu2\`, `kq_v1\`).

- Vách kính 2026-11-03 trên bản sao `file mau revit\file vach kinh.rvt` (`_tmp\revit_ctcua\thu3\VK.rvt`, `chay_vk.py`):
  Bản 1/25 + section + dim chân (2026-11-04): T1-VK.11 9080×5000 có cửa đi + kính góc → khối 3 × 2 (cụm 508 × 345); T2-VK.05 11015×2800 có 2 cửa sổ → khối 3 × 2 (584 × 224; trước khi có ký hiệu section + dim chân vừa 1 hàng 216 / 218); 7 cửa G19 vẫn vừa ô (DG21 218 / 218);
  T1-VK.12 dài 54,5 m → vượt khổ (báo); chọn tấm + đố + vách cùng vách → gộp 1; bấm lại không trùng. Ảnh
  `_tmp\revit_ctcua\thu3\anhvk\`.

## Còn mở (`Cần xác nhận lại`)
- Vách kính 1/25 chiếm khối ô: người dùng chưa xem bố cục; vách rất dài (> ~13 m) vượt khổ A1, chưa có cách chia đoạn.
- Người dùng chưa bấm thử trong Revit của mình, chưa duyệt bố cục ô / template.
- Ẩn level chưa kiểm được trên G19 (template 3.2 / 3.3 đã ẩn level); model thật của người dùng có hiện level.
- Nét cốt sàn trên sheet đứng yên: dời viewport bằng tay thì phải dời nét theo.
- Chưa thử trên model thật `G19_A_L3-32` (có room → luật ngoài nhà theo room chưa được kiểm).
