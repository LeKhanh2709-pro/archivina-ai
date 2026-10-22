---
name: ngan-chay-truc-hkt
description: 'Ngăn cháy lan trục và hộp kỹ thuật – Trên mặt bằng tầng AutoCAD (.dwg), tìm mọi trục kỹ thuật / hộp kỹ thuật (HKT nước, điện; trục hút khói, tăng áp, bù khí, hút mùi) theo ký hiệu ống đứng và dấu X, loại trừ giếng thang máy, lỗ mở sàn không ống và đồ nội thất, rồi vẽ polyline biên (màu 6) + hatch NET 1000/315° RGB 220,30,30, cả hai trên layer A-Material, vào BẢN SAO, kèm Excel và ảnh xem lại. Dùng khi người dùng nhờ "hatch ngăn cháy lan", "mặt bằng ngăn cháy lan", "hatch trục / hộp kỹ thuật", "chống cháy lan HKT", "trục hút khói tăng áp", hoặc soát xem trục nào chưa hatch.'
---

# Ngăn cháy lan trục và hộp kỹ thuật (Archivina)

Từ mặt bằng tầng: (1) chuyển DWG sang DXF trên bản sao, (2) dò dấu X để tìm trục/hộp, (3) vẽ hatch ngăn cháy vào bản sao DWG mới, (4) mở lại bản sao kiểm tra. Người dùng là kiến trúc sư: báo kết quả và điểm cần quyết định trước, ngắn gọn.

Quy tắc nhận diện, thông số hatch, cách phân biệt thang máy: đọc `references/nhan-dien.md` khi gặp tình huống lạ hoặc bản vẽ khác chuẩn mẫu.

**Nguyên tắc cốt lõi:** trục / hộp kỹ thuật nhận theo **ký hiệu ống đứng** (block `*pipe*`: ống tròn + cùm U) và **dấu X của hộp**; đường bo là ô X / khung lỗ mở MEP **bao quanh nhóm ống**. Lỗ mở sàn kiến trúc (`lo mo`) không có ống → không hatch. Trục thông gió lõi (TA, HK, HM, BK) không có ống → nhận theo dấu X.

**Bản vẽ có xref đang attach (chưa bind):** DXFOUT không chứa nội dung xref nên script Python bên dưới KHÔNG thấy trục / hộp trong xref. Với bản vẽ này dùng lệnh LISP `NCL` (đọc được xref đã nạp, chỉ đọc, không bind) — người dùng tự chạy trong AutoCAD, hoặc Claude chạy qua Core Console trên bản sao đặt **cùng thư mục với file xref** (đường dẫn xref tương đối). Tuyệt đối không bind xref để chạy Python.

**Bản LISP** để người dùng tự chạy trong AutoCAD: `D:\AI\scripts\lisp\fire_stop_shaft.lsp`, lệnh `NCL` (vẽ luôn, không hỏi; `KT-NGANCHAY` = hỏi trước khi vẽ), cùng logic với script Python. Sửa quy tắc ở một bên thì sửa cả bên kia.

## Công cụ
- `<python>` = `D:\AI\_tools\venv\Scripts\python.exe`, đặt `PYTHONUTF8=1`. `<skill>` = "Base directory for this skill".
- AutoCAD Core Console tự tìm trong `C:\Program Files\Autodesk\AutoCAD *\` (máy này chọn bản 2027).
- Không đọc script để hiểu cách dùng: chạy `--help` hoặc theo các bước dưới.

## Các bước
1. **DWG → DXF** (bản sao, không nổ AEC):
   `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\dwg_to_dxf.ps1 -Dwg "<file.dwg>" -OutDir "D:\AI\_tmp\<việc>"`
2. **Dò trục / hộp:**
   `<python> <skill>\scripts\tim_truc_ky_thuat.py "<file.dxf>" --out-dir "<thư mục kết quả NN_>"`
   Tạo `<tên>_vung.json`, `<tên>_vung.xlsx`, `<tên>_vung.png` (xanh = sẽ hatch, xám = đã có, đỏ = loại).
   Xem ảnh PNG. Dự án đặt tên block thang máy khác thì thêm `--block-thang-may "*cabin*,<mẫu khác>"`.
   **Bản vẽ đặt layer không chuẩn** (vd. `A- Truc ME` thừa dấu cách, dấu X trên layer lạ): tên layer đã được so bỏ dấu cách và không phân biệt hoa/thường; nếu vẫn thiếu thì thêm `--layer-x "*"` để dò mọi layer. Khi đó layer chắc chắn không phải trục (`--layer-bo`: nội thất, cửa, dim, text, ký hiệu) và block đồ đạc có dấu X (`--block-bo`: máy giặt, máy rửa bát, tủ lạnh…) bị bỏ qua. So số vùng của 2 lần chạy; vùng chỉ xuất hiện khi dò mọi layer thì báo người dùng xem lại.
3. **Vẽ vào bản sao** (chỉ vùng `se_hatch`):
   `powershell -NoProfile -ExecutionPolicy Bypass -File <skill>\scripts\ve_hatch_vao_ban_sao.ps1 -Dwg "<file.dwg gốc>" -Json "<tên>_vung.json" -OutDwg "<thư mục NN_>\<tên>_ngan chay.dwg"`
   Log in ra `VUNG_YEU_CAU = POLYLINE_DA_TAO = HATCH_DA_TAO` thì đạt. File lớn (~50 MB, >100 vùng) chạy hơn 15 phút: chạy nền và thêm `-TimeoutSec 3600`.
   Muốn bỏ vùng nào thì sửa `trang_thai` của vùng đó trong JSON thành `bo_qua` trước khi chạy.
4. **Kiểm tra:** chạy lại bước 1 và 2 (thêm `--khong-anh`) trên bản sao kết quả → phải còn **0 vùng "sẽ hatch"**. Xuất PNG vài vị trí bằng `-PLOT` vùng `W` (mẫu `D:\AI\_tools\plot_png.scr`, bảng in `.`) để nhìn tận mắt.

## Áp dụng tại D:\AI
- **Layer bo và hatch ngăn cháy lan luôn là `A-Material`, cho mọi bản vẽ** (người dùng chốt 22/10/2026). Không vẽ lên `A-HATCH- Color` như bản mẫu cũ; hatch cũ trên layer đó chỉ được nhận là "đã có".
- Tuân thủ 7 QUY TẮC BẮT BUỘC trong `D:\AI\CLAUDE.md`.
- File đầu vào và kết quả trên ổ `D:`; ổ khác phải hỏi trước. Thư mục kết quả đánh số `NN_` (vd. `D:\AI\<dự án>\05_NganChay\`).
- Script **không ghi đè** file đã có, **không xoá** thư mục tạm (`D:\AI\_tmp\nganchay_*`, `dwg2dxf_*`).
- **Không sửa DWG gốc, không đụng tab AutoCAD đang mở**: mọi việc chạy ngầm bằng Core Console trên bản sao.
- Không tô SOLID tường bao trục (người dùng chốt 22/10/2026: chỉ NET trong lòng).
- **Gom vào block** (người dùng chốt 22/10/2026): toàn bộ đường bo + hatch vừa vẽ được gom vào 1 block `NGAN CHAY LAN` (trùng tên thì `NGAN CHAY LAN 2`…, không định nghĩa lại block cũ), chèn tại 0,0 trên `A-Material`. Hatch trong block này được nhận là "đã có" khi chạy lại.
- **Sau khi bo + hatch** (người dùng chốt 22/10/2026): tắt layer nội thất / thiết bị vệ sinh (`A-Interior*`, `A-Nội thất`, `*Furn*`, `A-WC*`, `*ga thu*`…) và đổi **mọi layer khác** sang True Color **150,150,150**, để mặt bằng chỉ nổi đường bo và hatch. Script vẽ làm việc này tự động (bỏ: `-KhongLamMo`); LISP `NCL` cũng vậy và lưu layer state `TRUOC NGAN CHAY LAN` trước khi đổi. **Chỉ đổi màu / tắt trong bảng layer**: không sửa màu từng đối tượng, **không bind** xref, block, link (người dùng chốt 22/10/2026). Đối tượng gán màu riêng (không BYLAYER), kể cả trong xref, vì thế vẫn giữ màu.
- Người dùng chốt: **hatch hết ô có dấu X của trục / hộp** (trừ thang máy, nội thất, lỗ mở sàn `lo mo` không có ống). Ô lớn > 1400 × 1400 mm, ô ống gió nằm giữa hành lang không tường bao: vẫn hatch nhưng liệt kê riêng trong báo cáo để người dùng xem lại (`Cần xác nhận lại`).
- Không ghi trị số giới hạn chịu lửa (EI…) hay điều khoản QCVN nếu người dùng chưa cung cấp (`[Chờ bổ sung]`).

## Báo cáo cho người dùng
- Số vùng: sẽ hatch / đã có / loại; số hatch đã tạo; đường dẫn bản sao DWG + Excel + PNG.
- Danh sách vùng cần xem lại (ô lớn, ô giữa hành lang, ô bị loại vì chạm thang máy) kèm tọa độ tâm.
- Nêu **đã kiểm tra thực tế** (dò lại bản sao còn 0 vùng chưa hatch, ảnh PNG) và **chưa kiểm tra** (chưa mở trong AutoCAD thật, tầng khác chưa chạy).
