# pyRevit – ARVTools.extension (tab **ARV Tools**)

21 công cụ chuyển từ bộ graph Dynamo `ARV_*_v1` (`file mau revit\dynamo\`) + nút Chống thấm, tổng 22 nút pyRevit. TRẠNG THÁI: **CHƯA DUYỆT** (như bản Dynamo).

**Cập nhật 2026-11-03 từ bộ `AI REVIT` của đồng nghiệp** (repo `antt-cell/arv-bim-claude`, commit `b7381e6`): thêm 17 nút (Kiến trúc: Trát gờ logia; Hoàn thiện: Len chân tường; panel mới **Thiết bị WC**: Lavabo, Sen tắm, Bồn cầu, Vách kính tắm, Vòi xịt lô giấy; panel mới **Nội thất**: Máy giặt, Cục nóng điều hoà, Giường, Tủ đầu giường, Bàn làm việc, Tủ ti vi, Nội thất bếp, Tủ quần áo, Sofa, Bàn ăn) và thay mã 9 nút bằng bản mới hơn của đồng nghiệp (Cột vách, Lan can louver, Sàn căn hộ, Sàn hoàn thiện, Gờ logia, Ốp tường WC, Cửa đi, Cửa sổ, Len gạch logia; Cửa đi lưu input dự án HQV, Cửa sổ là bản "cửa sổ nhỏ phòng ngủ / WC" — chi tiết và trạng thái duyệt BIM Manager từng tool trong `file mau revit\dynamo\README_AI_REVIT.md`). Bản cũ: `_backup\*_20261103_1049.*`, cả tab `_backup\ARV Tools.tab_20261103_1049\`. Builder: ô bool "Tạo lại: xoá …" có chữ dry-run trong mô tả nay là ô xoá (chữ đỏ), không còn bị coi là Dry-run. Nút mới chưa thử trong Revit trên máy này (`Cần xác nhận lại`).
- `ARV.extension\` (cạnh `ARVTools.extension`): extension pyRevit gốc của đồng nghiệp (tab **ARV**: TaoCotTuCAD, TaoCotVachTuCAD, TaoTrucTuCAD, TaoTuongTuCAD, KhoaSanVaoTuong; IronPython) – mới chép mã nguồn, CHƯA đăng ký vào pyRevit; skill `bim-qaqc` viết script QA/QC vào `ARV.extension\ARV.tab\QAQC.panel\`.

Yêu cầu: **pyRevit ≥ 6.5.5** gắn vào Revit 2027. pyRevit 6.4 lỗi engine CPython trên Revit 2027 (`The input string '3.12.3' was not in a correct format` trong `CPythonEngine.GetPythonDll`) → mọi nút báo "Revit could not complete the external command". Cấu hình `cpyengine = 3123` (engine `CPY3123` đi kèm pyRevit).

## Cách hoạt động
- **Bố cục gọn** (người dùng yêu cầu 2026-11-03): panel Kết cấu, Kiến trúc, Hoàn thiện, MEP, Thiết bị WC, Nội thất xếp nút nhỏ thành chồng 2–3 nút, tiêu đề 1 dòng (`STACKS` trong builder; thư mục `<Panel>.panel\<Panel><k>.stack\<Tên>.pushbutton\`). Panel `HoSo` (tên hiện trên ribbon: **HS TKBVTC**) và Vách kính giữ nút lớn. Builder tự chuyển thư mục nút giữa nút lớn ↔ chồng, không xoá gì. Bản trước khi gọn: `_backup\ARV Tools.tab_20261103_1416\`.
- **Icon nút** (người dùng duyệt 2026-11-03): bộ Material Design Icons (mdi, Apache 2.0, tải qua `api.iconify.design/mdi`), cùng kiểu trắng đen với K-TOOL. Nguồn ở `icons\`: `<Tên nút>.png` nét đen (giao diện sáng) + `<Tên nút>.dark.png` nét trắng (giao diện tối), 96 px; builder chép thành `icon.png` / `icon.dark.png` trong từng nút (thiếu thì in CẢNH BÁO). Nút Vách kính (viết tay) chép icon trực tiếp. Bảng tên nút → tên hình mdi: `icons\bang_icon.json`; ảnh xem trước `icons\xem_ribbon.png`, `icons\bang_icon.png`; đổi icon thì sửa `bang_icon.json`, tải lại `mdi.json`, chạy `dotnet run -- <thư mục>` với `icons\nguon\XemRibbon.csproj` (thư mục chứa 2 file json) → chép `out\*.png` vào `icons\` rồi chạy builder.
- Mỗi nút `ARV Tools.tab\<Panel>.panel\[<Panel><k>.stack\]<Tên>.pushbutton\` gồm:
  - `core.py`: nguyên văn mã Python node của graph (chép từ `ARV_<Tên>_v1.py`), logic không đổi.
  - `inputs.json`: các ô `IN[i]` (nhãn lấy từ chú thích đầu file, giá trị mặc định lấy từ Input node trong `.dyn`).
  - `script.py`, `bundle.yaml`: vỏ pyRevit (engine CPython 3, dòng `#! python3`).
- `lib\arv_dynamo_host.py` thay phần Dynamo: hộp thoại nhập `IN[i]`, `DocumentManager` / `TransactionManager` giả, in `OUT` ra cửa sổ báo cáo pyRevit. Phần xem trước hình học của Dynamo (ProtoGeometry) không có trong pyRevit nên bỏ qua; báo cáo chữ và file log giữ nguyên.
  - `List[T](list Python)` không chạy được trong pythonnet của pyRevit (vd. `List[BuiltInCategory]([...])` báo "'list' value cannot be converted") → thư viện thay `List` khi nạp `core.py` bằng bản tạo List rỗng rồi `Add` từng phần tử (cùng kết quả như trong Dynamo).
  - Chạy thử tự động: đặt biến môi trường `ARV_TOOLS_AUTO_REPORT=<file .txt>` trước khi mở Revit → bấm nút không hiện hộp thoại, chạy dry-run với giá trị mặc định, ghi báo cáo vào file đó.
- **Không sửa tay** các file trong `ARVTools.extension\ARV Tools.tab\`. Sửa `.py` / `.dyn` gốc rồi sinh lại:
  ```
  D:\AI\_tools\venv\Scripts\python.exe build_from_dynamo.py "D:\AI\file mau revit\dynamo"
  ```

## Dùng trong Revit
1. Mở Revit 2027 → tab **ARV Tools** (pyRevit đã gắn vào Revit 2027, extension nằm trong Extension Search Path `D:\AI\scripts\pyrevit`). Mới thêm nút thì bấm **pyRevit → Reload**.
2. Bấm nút → hộp thoại liệt kê `IN[0]…IN[n]` như Input node trong Dynamo → **Chạy**.
3. Ô **Dry-run** luôn bật lại mỗi lần mở (chỉ báo cáo, không ghi). Tắt Dry-run để ghi vào mô hình; mọi thay đổi nằm trong 1 Transaction tên `ARV - …` (Ctrl+Z được).
4. Ô có **xoá / làm lại** (chữ đỏ) luôn tắt lại mỗi lần mở; bật khi đã tắt Dry-run thì phải xác nhận thêm một lần.
5. Giá trị đã nhập được nhớ riêng từng máy tại `%APPDATA%\pyRevit\ARVTools\<nút>.json`.

## Cài sang máy khác
- Đóng gói: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\pyrevit\dong_goi.ps1` → `_dist\ARVTools_<ngày>\` + `.zip` (extension bỏ `__pycache__`, `CAI_DAT.bat` / `cai_dat.ps1` / `HUONG_DAN.txt` từ `goi_cai_dat\`, kèm bộ cài pyRevit trong `_tmp\pyrevit_setup\` nếu có; `-KhongKemPyRevit` để bỏ).
- Máy đích: giải nén vào chỗ cố định → `CAI_DAT.bat` (chưa có pyRevit thì hỏi cài; đăng ký `<gói>\ARVTools` vào Extension Search Path; có bản ARVTools.extension khác thì hỏi gỡ đăng ký, không xoá file). `CAI_DAT.bat -Go` = gỡ đăng ký.
- 3 family vách kính (`lib\vach_kinh\*.rfa`) lưu định dạng Revit 2027 → nút Vách kính không chạy trên Revit cũ hơn.

Một số công cụ lấy đối tượng đang chọn (sàn, Room) hoặc level của view đang mở – chọn trước rồi bấm nút, giống khi chạy trong Dynamo.

## Danh sách nút
| Panel | Nút | Graph gốc |
|---|---|---|
| Kết cấu | Tạo trục từ CAD | `ARV_TaoTrucTuCSV_v1` |
| Kết cấu | Cột vách từ CAD | `ARV_TaoCotVachTuCAD_v1` (core lấy bản `.py` mới hơn `.dyn`: có thêm `IN[10]` file `.rfa`) |
| Kết cấu | Dầm từ CAD | `ARV_TaoDamTuCAD_v1` |
| Kết cấu | Bao sàn từ CAD | `ARV_VeBaoSanTuCAD_v1` |
| Kết cấu | Cắt tường theo dầm sàn | `ARV_CatTuongTheoDamSan_v1` |
| Kiến trúc | Tường từ CAD | `ARV_TaoTuongTuCAD_v1` |
| Kiến trúc | Cửa đi từ CAD | `ARV_TaoCuaTuCAD_v1` |
| Kiến trúc | Cửa sổ từ CAD | `ARV_TaoCuaSoTuCAD_v1` |
| Kiến trúc | Gờ logia | `ARV_TaoGoLogia_v1` |
| Kiến trúc | Lan can louver logia | `ARV_TaoLanCanLouverLogia_v1` |
| Hoàn thiện | Sàn hoàn thiện (có hatch) | `ARV_TaoSanHoanThien_v1` |
| Hoàn thiện | Sàn căn hộ từ CAD | `ARV_TaoSanCanHoTuCAD_v1` |
| Hoàn thiện | Trần căn hộ | `ARV_TaoTranCanHo_v1` |
| Hoàn thiện | Ốp tường WC | `ARV_OpTuongWC_v1` |
| Hoàn thiện | Len gỗ | `ARV_TaoLenGo_v1` |
| Hoàn thiện | Len gạch logia | `ARV_TaoLenGachLogia_v1` |
| Hoàn thiện | Dàn trang căn hộ | `ARV_DanTrangCanHo_v1` |
| MEP | Thiết bị WC từ CAD | `ARV_TaoThietBiWCTuCAD_v1` |
| MEP | Ống thoát nước WC | `ARV_TaoOngThoatNuocWC_v1` |
| MEP | Ống thoát nước từ CAD | `ARV_TaoOngThoatNuocTuCAD_v1` |
| MEP | Ống gió từ CAD | `ARV_TaoOngGioTuCAD_v1` |
| Kiến trúc | Trát gờ logia | `ARV_TraGoLogia_v1` (AI REVIT, 2026-11-03) |
| Hoàn thiện | Len chân tường | `ARV_TaoLenChanTuong_v1` (AI REVIT) |
| Thiết bị WC | Lavabo / Sen tắm / Bồn cầu / Vách kính tắm / Vòi xịt lô giấy | `ARV_TaoLavaboTuCAD_v1`, `ARV_TaoSenTamTuCAD_v1`, `ARV_TaoBonCauTuCAD_v1`, `ARV_TaoVachKinhTamTuCAD_v1`, `ARV_TaoVoiXitLoGiayWC_v1` (AI REVIT) |
| Nội thất | Máy giặt / Cục nóng ĐH / Giường / Tủ đầu giường / Bàn làm việc / Tủ ti vi / Nội thất bếp / Tủ quần áo / Sofa / Bàn ăn | `ARV_TaoMayGiatTuCAD_v1`, `ARV_TaoCucNongDHTuCAD_v1`, `ARV_TaoGiuongTuCAD_v1`, `ARV_TaoTuDauGiuongTuCAD_v1`, `ARV_TaoBanLamViecTuCAD_v1`, `ARV_TaoTuTiViTuCAD_v1`, `ARV_TaoNoiThatBepTuCAD_v1`, `ARV_TaoTuQuanAoTuCAD_v1`, `ARV_TaoSofaTuCAD_v1`, `ARV_TaoBanAnTuCAD_v1` (AI REVIT) |
| HS TKBVTC | Chống thấm | `scripts\dynamo\ChongTham_VeVenChanTuong` (nét vén + hatch Filled Region trên view chống thấm; người dùng duyệt trên G19 2026-10-27) |
| HS TKBVTC | Ngăn cháy lan | `scripts\dynamo\NganChay_TrucHKT` (hatch Filled Region lưới NET 125 / 45° đỏ trong lòng trục / hộp kỹ thuật trên view chống cháy lan; 2026-10-28, người dùng đã duyệt bản bo lõi tường) |
| HS TKBVTC | Lỗ mở shaft | `scripts\dynamo\LoMo_ShaftOpening` (Shaft Opening cho mọi trục / hộp kỹ thuật trên mặt bằng tầng đang mở; file gộp, xem dưới; 2026-10-28) |
| HS TKBVTC | Định vị + tag cửa | `scripts\dynamo\TagCua_TuDong` (một chạm trên mặt bằng tầng đang mở: tạo / mở `MẶT BẰNG ĐỊNH VỊ CỬA - <tầng>` (template `MẶT BẰNG ĐỊNH VỊ CỬA`: tường + sàn Halftone, ẩn nội thất / thiết bị vệ sinh / Mechanical Equipment) rồi tag cửa đi / cửa sổ không đè; gộp nút MB định vị cửa 2026-11-03; ô rộngXcao trên tag (IN[19]) tạm tắt; family nguồn nhãn ở `lib	ag_cua\`; skill `tag-cua-revit`; chưa duyệt) |
| Vách kính | Vách kính | **Viết tay** (không từ Dynamo): `VachKinh.panel\VachKinh.pushbutton\script.py` + `lib\arv_vach_kinh*.py` + `startup.py` (updater). Xem dưới. |

**Nút Vách kính** (2026-11-01, IronPython, chưa duyệt): bảng nhập → pick điểm → dựng curtain wall chia đố 65 theo quy tắc lệnh VK / MDVK; vách góc vuông pick 3 điểm (đố góc 150 x 150 + kính góc). Đổi chiều dài / chiều cao vách thì updater trong `startup.py` chia lại. Quy tắc, file, cách thử: skill `.claude\skills\vach-kinh-revit\SKILL.md`. Panel `VachKinh` nằm trong `PANEL_VIET_TAY` của `build_from_dynamo.py`: builder chỉ thêm vào layout tab, không ghi vào thư mục panel.

**Nút Chống thấm là nút "một chạm"** (người dùng chốt 2026-10-27; khai báo trong `MOT_CHAM` của builder):
- **Bấm**: vẽ luôn vào mô hình, không hộp thoại, không Dry-run (Ctrl+Z một lần là hoàn tác), trên view chống thấm. Người dùng tự tạo view (gán template `1.7 Mặt Bằng Chống thấm`) và tự đặt lên sheet.
  - View đang mở có chữ "chống thấm" trong tên view hoặc tên view template → vẽ vào view đó.
  - Không thì: có đúng 1 view như vậy → vẽ vào view đó rồi chuyển sang view đó; nhiều view → hiện danh sách để chọn; không có view nào → báo, không làm gì.
  - Bấm lại trên view đã vẽ: không vẽ lại vén, không xoá gì, chỉ bổ sung hatch cho phòng chưa có.
- **Shift+bấm** (`config.py`): hộp thoại đầy đủ `IN[0…9]` như các nút khác, Dry-run bật sẵn.
- Giá trị các ô khác (từ khoá sàn, khoảng lùi, line style, thư mục log…) lấy theo lần nhập gần nhất trong hộp thoại Shift+bấm, chưa nhập thì lấy mặc định.
- Đã thử 2026-10-27 (Revit 2027.3 + pyRevit 6.5.5, bản sao G19 chưa vẽ `_backup\G19_20261027_1405.rvt`, chạy nguyên `script.py` của nút khi đang mở view `Tầng 1`): tự chọn view `Level 1 Copy 1 Copy 2`, vẽ 364 nét vén + 59 hatch Filled Region (2 group), ẩn 64 thiết bị; bấm lần 2 không vẽ thêm gì. Kết quả ở `_tmp\pyrevit_chongtham\motcham\kq\`. Chưa thử hộp thoại chọn view (khi có nhiều view chống thấm) và Shift+bấm.

**Nút Ngăn cháy lan cũng là nút một chạm** (2026-10-28), cách chọn view giống Chống thấm nhưng với chữ "cháy lan" (template `1.8 Mặt Bằng Chống Cháy Lan`).
- Đã thử trên bản sao G19 (`_tmp\pyrevit_nganchay\`), bấm khi đang mở `Tầng 1`:
  - tự chọn view `Level 1 Copy 1 Copy 2 Copy 1`;
  - vẽ 38 hatch (group `ARV_NganChay`), ẩn 65 thiết bị;
  - bấm lần 2 không vẽ thêm gì.
- G19 không có ống đứng / shaft / dấu X, nên mọi ô được nhận theo hình học. Bản 2 (sửa theo góp ý người dùng 2026-10-28) **quét lưới 20 mm dấu chân thật của tường** thay cho room tạm:
  - bắt được khe hộp gen ~120 mm, là chỗ room của Revit bỏ sót;
  - nối đầu tường hở ≤ 400 mm, đóng miệng hốc chữ U;
  - bỏ ô > 3 m², tức ô 1770×2520 ở hành lang mà người dùng chỉ là sai.
  
  Người dùng chưa duyệt bản 2 (`Cần xác nhận lại`).

**Bo sát mép tường thô** (người dùng chốt 2026-10-28, áp cho cả Chống thấm và Ngăn cháy lan): vùng hatch và nét bo theo mặt lõi tường, không theo lớp trát / hoàn thiện.
- Chống thấm: room dùng `CoreBoundary`.
- Ngăn cháy lan: quét theo dải lõi tường, rồi bắt cạnh vùng vào đúng mép lõi.
- Khe hộp gen G19 ra đúng 150×800 mm (lõi–lõi).

**Nút Lỗ mở shaft** (2026-10-28, một chạm, làm trên **mặt bằng tầng đang mở**; không mở mặt bằng tầng thì nút báo và không làm gì):
- **MỘT Shaft Opening cho cả tầng**, mỗi trục / hộp kỹ thuật là một vòng biên trong sketch (người dùng chốt 2026-10-28, theo mẫu tự vẽ: "1 lệnh shaft để dễ kiểm soát").
  - Nhận trục giống hệt nút Ngăn cháy lan (dùng chung hàm `tim_truc`).
  - Tầng đã có shaft lỗ mở cục bộ (Base và Top cùng là level đó) thì thêm vòng vào shaft đó (shaft nhiều vòng nhất); chưa có thì tạo 1 shaft mới.
  - Phần thêm vòng + dấu X là 1 lần sửa sketch (1 bước Undo); tạo shaft mới là 1 bước riêng.
- Biên lỗ mở = mép tường thô.
- Base Constraint = Top Constraint = level của mặt bằng; Base Offset -100 mm, Top Offset 1500 mm (người dùng chốt; đổi được qua Shift+bấm).
- Bấm lại: ô đã có vòng lỗ mở (theo tâm từng vòng của mọi shaft cắt qua tầng) thì bỏ qua, không tạo trùng, không xoá.
- **Dấu X nhận biết lỗ mở** = 2 Symbolic Line trong sketch shaft (người dùng chốt 2026-10-28).
  - Revit API không tạo được Symbolic Line trong file dự án. Trong sketch, Symbolic Line là `ModelLine` mang line style khác `<Sketch>`; tạo bằng `NewModelCurve` thì luôn thành nét biên, không đổi style được.
  - Cách làm: chép 2 nét X của một **shaft mẫu** (người dùng vẽ tay 1 lần) vào sketch từng lỗ bằng `SketchEditScope` + `CopyElements`, rồi `SetGeometryCurve` về 2 đường chéo theo phương cạnh dài.
  - Chưa có shaft mẫu thì vẫn tạo lỗ mở, báo cách vẽ mẫu. Bấm lại thì bổ sung X cho vòng chưa có X.
  - Phải đóng hẳn transaction trước `SketchEditScope.Start` (Dynamo giữ transaction tới cuối lượt chạy).
- Mã nguồn:
  - `LoMo_ShaftOpening.py` là **file gộp, không sửa tay**. Phần riêng sửa ở `LoMo_ShaftOpening_nguon.py`; quy tắc nhận trục sửa trong khối `PHẦN CHUNG` của `NganChay_TrucHKT.py`.
  - Sau khi sửa thì gộp lại bằng `python scripts\dynamo\gop_lomo_shaft.py`, rồi `build_dyn.py LoMo_ShaftOpening.json` và builder `--chi LoMoShaft`.
- Thử trên bản sao G19 (Tầng 1):
  - 38 lỗ mở, đọc lại đúng Base Tầng 1 / -100, Top Tầng 1 / 1500 (cao độ -100…1500 mm); bấm lần 2 không tạo thêm.
  - Sau đó nút Ngăn cháy lan nhận đủ 38 trục theo bằng chứng shaft opening.
  - Bản lưu `_tmp\pyrevit_lomo\G19_lo_mo_ngan_chay_thu.rvt`. Shaft opening không có tham số Comments.

**Bẫy pythonnet 3.0.3 (CPython của pyRevit), gặp khi làm nút một chạm:**
- Tên nào bị `from Autodesk.Revit.DB import <tên>` **đầu tiên** trong phiên Revit thì bị loại khỏi `from Autodesk.Revit.DB import *` về sau. Ví dụ `lib\arv_dynamo_host.py` import `Transaction, TransactionStatus` trước, nên `core.py` dùng `import *` sẽ thiếu 2 tên này.
  - Đã kiểm chứng: `__all__` còn 1323/1326 tên.
  - Cách tránh: script nút dùng `import Autodesk.Revit.DB as DB`; `core.py` chống thấm bổ sung đủ tên bằng `dir()` ngay sau `import *`.
- `List[T](list Python)` không chạy. Thư viện chỉ thay khi dòng import đúng dạng `from System.Collections.Generic import List`; viết `... import List as NetList` thì không được thay. `core.py` chống thấm tự tạo List rỗng rồi `Add` (hàm `ds_id`).

Nút nguồn ngoài `file mau revit\dynamo` (vd. Chống thấm) khai báo trong `BUTTONS` bằng đường dẫn `../dynamo/<tên>`. Sinh lại riêng 1 nút, không đụng các nút khác:
```
D:\AI\_tools\venv\Scripts\python.exe build_from_dynamo.py "D:\AI\file mau revit\dynamo" --chi ChongTham
```

## Kết quả chạy thử (2026-10-27, Revit 2027.3 + pyRevit 6.5.5, bản sao G19, dry-run)
Mở Revit bằng journal, bấm nút thử chạy lần lượt 22 nút với giá trị mặc định. Không nút nào lỗi phần vỏ pyRevit.
- Chạy hết, ra báo cáo: Chống thấm, Dàn trang căn hộ, Ốp tường WC, Len gạch logia (141 đoạn / 528 viên), Len gỗ, Trần căn hộ, Cắt tường theo dầm sàn, Ống thoát nước WC.
- Dừng đúng kiểm tra đầu vào vì G19 **không có bản CAD link**: Tạo trục, Cột vách, Dầm, Bao sàn, Tường, Cửa đi, Cửa sổ, Gờ logia, Lan can louver, Sàn căn hộ từ CAD, Thiết bị WC, Ống thoát nước từ CAD, Ống gió → phần đọc CAD / Core Console **chưa được thử trong pyRevit** (`Cần xác nhận lại`).
- Sàn hoàn thiện: cần chọn cửa vào căn trước khi bấm → chưa thử phần dựng sàn.
- Chưa thử chế độ ghi thật (Dry-run tắt) trong pyRevit. Hộp thoại đã chụp ảnh kiểm tra (Cửa sổ 18 ô, Dàn trang có ô xoá chữ đỏ).

## Kết quả chạy thử trên `G19 CAD.rvt` (2026-10-28, bản sao `_tmp\pyrevit_cad\`)
Model có 1 CAD link `G19.dwg` (chỉ trong view Tầng 1). File DWG gốc nằm ở máy khác (`C:\Users\dungb\...`, Revit báo NotFound): hình học vẫn đọc được, nhưng chữ trong DWG thì không đọc được. Model đã dựng gần hết, nên phần lớn đối tượng được báo "đã có, bỏ qua".
- Dry-run 24/24 nút: không lỗi vỏ.
  - Tạo trục bị crash vì đoạn nét CAD ngắn hơn dung sai của Revit → đã sửa ở `ARV_TaoTrucTuCSV_v1.py` / `.dyn` (bỏ đoạn < `ShortCurveTolerance`), sinh lại nút.
- Ghi thật 19 nút, kết quả lưu ở `_tmp\pyrevit_cad\G19_CAD_ghi_thu.rvt`. Đối chiếu Id trong log với model sau khi lưu:
  - **Chạy đúng:** Trục (16; layer `A-axis`, tên tự động), Sàn căn hộ (10), Trần (10), Len gỗ (66), Len gạch logia (553 viên), Lan can (chỉnh chân 27), Chống thấm (369 nét + 60 hatch), Ngăn cháy lan (36 hatch), Lỗ mở shaft (1 shaft / 36 vòng), Dàn trang CH02 (3 sheet, 16 view).
  - **Cửa đi:** báo tạo 28, Revit xoá 26 (`not cutting anything`). **Cửa sổ:** báo tạo 65, Revit xoá 32 (`Can't cut instance out of Wall`).
    - Nguyên nhân: nút lấy cả tường ốp gạch `GO-Gạch ốp-300x600` (10 mm) làm tường chủ, nên mỗi ô cửa sổ bị nhận thêm một lần trên lớp ốp. Ngoài ra nút chỉ coi là "ô đã có cửa" khi cửa cũ nằm cùng tường.
    - **Đã sửa 2026-10-28:** tường < 30 mm không làm tường chủ. Ô đã có cửa = cửa bất kỳ (kể cả gắn vào lớp ốp) có điểm chèn hoặc tâm hộp bao nằm trong dải bề dày tường + 100 mm và cách tâm ô ≤ max(100 mm, nửa bề rộng ô).
    - Thử lại trên bản sao: chạy trên model đầy đủ thì cửa đi nhận 74 ô đã có và tạo 1 (tại (10250, 21490), tường 1005836, model chưa có cửa ở đó, `Cần xác nhận lại`), cửa sổ 44/44 và cửa lùa 18/18 đã có.
    - Xoá hết cửa rồi dựng lại (`_tmp\pyrevit_cad\G19_CAD_cua_dung_lai.rvt`): 75 cửa đi + 18 cửa lùa + 44 cửa sổ, Revit không xoá cái nào, không báo lỗi. Model gốc có 61 cửa sổ trên toàn bộ các tầng; CAD Tầng 1 có 44 ô cửa sổ + 6 ô `A-Glaz` (chỉ báo cáo).
  - **Tường:** 9 → mất 3 (`Can't make Wall`).
  - **Cột vách** theo layer `A-Column`: 36 vách / 2 cột. Cảnh báo tường chồng nhau tăng 32 → 44.
- Không chạy được vì file thiếu dữ liệu:
  - Dầm, Bao sàn: CAD không có layer `S-…`.
  - Ống thoát nước từ CAD, Ống gió: không có CAD MEP và DWG phải còn ở đường dẫn gốc.
  - Sàn hoàn thiện: CAD không có layer `A-duong bo phong` / `A-Area`, và phải chọn cửa vào căn.
  - Ống thoát nước WC: model không có pipe type `AV_u.PVC PN6`.
- Khi chạy tự động bằng journal, hộp lỗi của Revit được tự bấm, nên phần tử lỗi bị xoá ngay. Chạy bằng tay thì người dùng sẽ thấy hộp lỗi đó.

## Giới hạn đã biết
- Các công cụ đọc chữ trong DWG gọi AutoCAD Core Console (`C:\Program Files\Autodesk\AutoCAD *\accoreconsole.exe`, lấy bản mới nhất) – máy không có AutoCAD thì công cụ báo dừng hoặc đặt tên tự động.
- Giá trị mặc định trong `inputs.json` là giá trị đang đặt trong `.dyn` (dự án G19: level `Tầng 1`, tên type `AV-…`, đường dẫn template MEP `C:\ProgramData\Autodesk\RVT 20…`) – dự án khác phải sửa trong hộp thoại.
- Extension `ARV.extension` cũ ở `D:\AI REVIT\tools\pyrevit` (tab **ARV**, 4 nút) vẫn được nạp song song, không đụng tới.
