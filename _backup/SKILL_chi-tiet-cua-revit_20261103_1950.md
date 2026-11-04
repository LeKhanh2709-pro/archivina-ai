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
1. **Đầu vào**: 1 cửa đi / cửa sổ, family có sẵn. Cửa đang chọn; chưa chọn thì hỏi chọn trên màn hình. Cửa trong link
   không chọn được.
2. **3 view, tỉ lệ 1/25**, tên `CT CỬA <Type Mark> - MẶT BẰNG / MẶT ĐỨNG / MẶT CẮT` (Type Mark trống thì dùng tên type),
   Title on Sheet = `MẶT BẰNG` / `MẶT ĐỨNG` / `MẶT CẮT`. Khung nhìn = hình family + lề 300 mm; mặt đứng / mặt cắt lấy
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
   - **Cốt sàn thay level** (như mẫu người dùng gửi): nét đứt (line style tên có "khuất" / "đứt", G19 `AV.Nét
     Khuất.W1`) tại mặt trên sàn trong nhà (không có thì ngoài nhà, cuối cùng level) trên mặt đứng + mặt cắt; chữ
     `CỐT SÀN HOÀN THIỆN <TÊN PHÒNG>` (kiểu chữ mặc định, mũi tên chỉ xuống nét sàn) bên trái mặt cắt, NGOÀI khung cắt
     (vùng annotation crop trái nới rộng) để không đè tường. Không có room thì chỉ `CỐT SÀN HOÀN THIỆN`, người dùng tự
     sửa.
3. **Kích thước tổng**: mặt bằng = rộng; mặt đứng = rộng (trên cửa) + cao (bên phải); mặt cắt = cao. Cửa sổ: chuỗi sàn →
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
   - Hết ô thì tạo sheet mới: số = số lớn nhất trong các sheet tên "CHI TIẾT CỬA" + 1 (G19: A.7-101 → A.7-102), chưa
     có sheet nào tên đó thì IN[3].
6. **Mỗi type làm 1 lần**: đã có view `CT CỬA <mark> - ...` thì báo sheet chứa nó, không tạo thêm.
7. Không xoá, không sửa cửa / tường / view gốc / template đã có. Ctrl+Z một lần là hoàn tác cả lượt.

## File
- Lõi: `<gốc>\scripts\dynamo\ChiTietCua_TuDong.py` (graph `.dyn` sinh bằng `build_dyn.py ChiTietCua_TuDong.json`).
- Nút: sinh bằng `scripts\pyrevit\build_from_dynamo.py "file mau revit\dynamo" --chi ChiTietCua` (MOT_CHAM
  `khong_view`: không cần view, lõi tự lấy cửa); không sửa tay `ChiTietCua.pushbutton\`. Shift+bấm = hộp thoại, Dry-run.

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
- Detail line bị model crop cắt (không hiện trong vùng annotation crop) → nét cốt sàn mặt cắt dừng ở mép khung cắt.
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

## Còn mở (`Cần xác nhận lại`)
- Người dùng chưa bấm thử trong Revit của mình, chưa duyệt bố cục ô / template.
- Ẩn level chưa kiểm được trên G19 (template 3.2 / 3.3 đã ẩn level); model thật của người dùng có hiện level.
- Nét cốt sàn mặt cắt không kéo dưới chữ; chữ không có tên phòng khi không có room.
- Chưa thử trên model thật `G19_A_L3-32` (có room → luật ngoài nhà theo room chưa được kiểm).
